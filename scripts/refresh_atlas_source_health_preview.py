"""Copy validated Atlas-safe source-health artifact into public-site preview data.

Operator helper. Default path runs the local-safe arbitrary proof on a temp DB.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rge.db.connection import ensure_database
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.live_arbitrary_source_health import (
    LIVE_SOURCE_HEALTH_ARTIFACT_NAME,
    LOCAL_SAFE_ATLAS_ARTIFACT_SCHEMA_VERSION,
    run_local_safe_arbitrary_source_health_proof,
)

PUBLIC_ARTIFACT_PATH = (
    REPO_ROOT / "apps" / "public-site" / "public" / "data" / LIVE_SOURCE_HEALTH_ARTIFACT_NAME
)


def validate_source_health_artifact(artifact: dict) -> list[str]:
    """Return validation errors; empty list means artifact is safe to publish."""
    errors: list[str] = []
    if artifact.get("schema_version") != LOCAL_SAFE_ATLAS_ARTIFACT_SCHEMA_VERSION:
        errors.append(
            f"schema_version must be {LOCAL_SAFE_ATLAS_ARTIFACT_SCHEMA_VERSION!r}."
        )
    summary = artifact.get("source_health_summary")
    if not isinstance(summary, dict):
        errors.append("source_health_summary must be an object.")
    elif int(summary.get("sources_with_metadata") or 0) < 1:
        errors.append("source_health_summary.sources_with_metadata must be >= 1.")
    leaks = assert_no_private_fields({"artifact": artifact})
    if leaks:
        errors.append(f"private fields detected: {', '.join(leaks[:5])}")
    return errors


def generate_local_safe_artifact(output_dir: Path) -> Path:
    os.environ.setdefault("RGE_LLM_MODE", "mock")
    conn = ensure_database(output_dir / "refresh_source_health.sqlite")
    try:
        result = run_local_safe_arbitrary_source_health_proof(
            conn,
            output_dir=output_dir,
        )
    finally:
        conn.close()
    artifact_path = Path(result["artifact_path"] or "")
    if not artifact_path.is_file():
        raise RuntimeError("Local-safe proof did not write atlas_source_health_run_latest.json.")
    return artifact_path


def refresh_public_source_health_preview(
    *,
    input_path: Path | None = None,
    output_path: Path = PUBLIC_ARTIFACT_PATH,
) -> dict:
    if input_path is None:
        with tempfile.TemporaryDirectory(prefix="rge_refresh_source_health_") as td:
            generated = generate_local_safe_artifact(Path(td))
            artifact = json.loads(generated.read_text(encoding="utf-8"))
    else:
        artifact = json.loads(input_path.read_text(encoding="utf-8"))

    errors = validate_source_health_artifact(artifact)
    if errors:
        raise ValueError("Source-health artifact failed validation: " + "; ".join(errors))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return {
        "status": "completed",
        "input_path": str(input_path) if input_path else "generated_local_safe_proof",
        "output_path": str(output_path),
        "schema_version": artifact.get("schema_version"),
        "sources_with_metadata": artifact.get("source_health_summary", {}).get(
            "sources_with_metadata"
        ),
        "question": artifact.get("question"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refresh public atlas source-health preview JSON with validation."
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Existing atlas_source_health_run_latest.json to copy (default: generate local-safe proof).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PUBLIC_ARTIFACT_PATH,
        help="Destination public-site JSON path.",
    )
    args = parser.parse_args()
    result = refresh_public_source_health_preview(
        input_path=args.input,
        output_path=args.output,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
