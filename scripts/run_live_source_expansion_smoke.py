"""Run live source expansion smoke (OpenAlex + arXiv + Unpaywall enrichment)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rge.db.connection import ensure_database
from rge.modules.live_source_expansion import (  # noqa: E402
    assert_live_source_expansion_smoke_env,
    required_env_setup_commands,
    run_live_source_expansion_smoke,
    sync_source_expansion_artifact_to_public_site,
)

PUBLIC_ARTIFACT = (
    REPO_ROOT
    / "apps"
    / "public-site"
    / "public"
    / "data"
    / "atlas_source_health_run_latest.json"
)


def _missing_gates() -> dict[str, str]:
    missing: dict[str, str] = {}
    try:
        assert_live_source_expansion_smoke_env()
    except RuntimeError as exc:
        message = str(exc)
        for line in message.splitlines():
            stripped = line.strip()
            if "=" in stripped and (
                stripped.startswith("RGE_") or stripped.startswith("OPENALEX")
            ):
                name, hint = stripped.split("=", 1)
                missing[name.strip()] = hint.strip()
        if not missing:
            missing["gates"] = message
    return missing


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Live source expansion smoke: OpenAlex + arXiv discovery with "
            "Unpaywall DOI/OA enrichment and Atlas resolver breakdown."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "data" / "exports" / "live_source_expansion",
    )
    parser.add_argument(
        "--sync-public",
        action="store_true",
        help="Copy validated atlas artifact to public-site preview data.",
    )
    args = parser.parse_args()

    missing = _missing_gates()
    if missing:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "missing_gates": missing,
                    "env_setup": required_env_setup_commands(),
                },
                indent=2,
            )
        )
        raise SystemExit(1)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    conn = ensure_database(args.output_dir / "live_source_expansion.sqlite")
    try:
        result = run_live_source_expansion_smoke(conn, output_dir=args.output_dir)
    finally:
        conn.close()

    if args.sync_public:
        artifact = result.get("atlas_safe_artifact") or {}
        sync_result = sync_source_expansion_artifact_to_public_site(
            artifact,
            public_path=PUBLIC_ARTIFACT,
        )
        result["public_sync"] = sync_result
        result["public_artifact"] = str(
            PUBLIC_ARTIFACT.relative_to(REPO_ROOT).as_posix()
        )

    print(json.dumps(result, indent=2, default=str))
    verdict = result.get("source_expansion_verdict")
    if verdict == "NO-GO":
        raise SystemExit(2)
    if verdict == "PARTIAL":
        raise SystemExit(3)


if __name__ == "__main__":
    main()
