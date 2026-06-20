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
    run_live_network_abstract_evidence_atom_trace_smoke,
    run_local_safe_arbitrary_source_health_proof,
)

PUBLIC_ARTIFACT_PATH = (
    REPO_ROOT / "apps" / "public-site" / "public" / "data" / LIVE_SOURCE_HEALTH_ARTIFACT_NAME
)


def validate_source_health_artifact(
    artifact: dict,
    *,
    require_trace_summary: bool = False,
) -> list[str]:
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
    if require_trace_summary:
        trace_summary = artifact.get("trace_summary")
        if not isinstance(trace_summary, dict):
            errors.append("trace_summary must be an object when trace summary is required.")
        else:
            trace_count = int(trace_summary.get("trace_count") or 0)
            preview_rows = trace_summary.get("atlas_trace_preview") or []
            if trace_count < 1:
                errors.append("trace_summary.trace_count must be >= 1.")
            if not preview_rows:
                errors.append("trace_summary.atlas_trace_preview must be non-empty.")
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


def generate_live_atom_trace_artifact(output_dir: Path) -> Path:
    """Operator-only live OpenAlex/arXiv abstract → atom → trace artifact."""
    os.environ.setdefault("RGE_LLM_MODE", "mock")
    conn = ensure_database(output_dir / "refresh_live_atom_trace.sqlite")
    try:
        result = run_live_network_abstract_evidence_atom_trace_smoke(
            conn,
            output_dir=output_dir,
            limit=5,
        )
    finally:
        conn.close()
    artifact_path = Path(result["artifact_path"] or "")
    if not artifact_path.is_file():
        raise RuntimeError(
            "Live abstract atom trace smoke did not write atlas_source_health_run_latest.json."
        )
    return artifact_path


def refresh_public_source_health_preview(
    *,
    input_path: Path | None = None,
    output_path: Path = PUBLIC_ARTIFACT_PATH,
    source: str = "local-safe",
    require_trace_summary: bool = False,
) -> dict:
    if input_path is not None:
        artifact = json.loads(input_path.read_text(encoding="utf-8"))
        resolved_source = "input"
    elif source == "live-atom-trace":
        with tempfile.TemporaryDirectory(prefix="rge_refresh_live_atom_trace_") as td:
            generated = generate_live_atom_trace_artifact(Path(td))
            artifact = json.loads(generated.read_text(encoding="utf-8"))
        resolved_source = "live-atom-trace"
    elif source == "local-safe":
        with tempfile.TemporaryDirectory(prefix="rge_refresh_source_health_") as td:
            generated = generate_local_safe_artifact(Path(td))
            artifact = json.loads(generated.read_text(encoding="utf-8"))
        resolved_source = "local-safe"
    else:
        raise ValueError(f"Unsupported source mode: {source!r}")

    errors = validate_source_health_artifact(
        artifact,
        require_trace_summary=require_trace_summary,
    )
    if errors:
        raise ValueError("Source-health artifact failed validation: " + "; ".join(errors))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    trace_summary = artifact.get("trace_summary") or {}
    return {
        "status": "completed",
        "source": resolved_source,
        "input_path": str(input_path) if input_path else resolved_source,
        "output_path": str(output_path),
        "schema_version": artifact.get("schema_version"),
        "sources_with_metadata": artifact.get("source_health_summary", {}).get(
            "sources_with_metadata"
        ),
        "trace_count": trace_summary.get("trace_count"),
        "atom_count": trace_summary.get("atom_count"),
        "accepted_claim_count": trace_summary.get("accepted_claim_count"),
        "question": artifact.get("question"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refresh public atlas source-health preview JSON with validation."
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Existing atlas_source_health_run_latest.json to copy (overrides --source).",
    )
    parser.add_argument(
        "--source",
        choices=("local-safe", "live-atom-trace"),
        default="local-safe",
        help="Generation mode when --input is omitted (default: local-safe mock proof).",
    )
    parser.add_argument(
        "--require-trace-summary",
        action="store_true",
        help="Require trace_summary.trace_count >= 1 and non-empty atlas_trace_preview.",
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
        source=args.source,
        require_trace_summary=args.require_trace_summary,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
