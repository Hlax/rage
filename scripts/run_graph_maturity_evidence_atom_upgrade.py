"""Run graph maturity / evidence atom upgrade smoke."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rge.modules.graph_maturity_evidence_atom_upgrade import (  # noqa: E402
    GRAPH_MATURITY_ARTIFACT_NAME,
    GraphMaturityGateError,
    assert_live_graph_maturity_evidence_atom_upgrade_env,
    required_env_setup_commands,
    run_graph_maturity_with_fresh_db,
    sync_graph_maturity_artifact_to_public_site,
)

PUBLIC_ARTIFACT = (
    REPO_ROOT
    / "apps"
    / "public-site"
    / "public"
    / "data"
    / GRAPH_MATURITY_ARTIFACT_NAME
)


def _missing_gates() -> dict[str, str]:
    missing: dict[str, str] = {}
    try:
        assert_live_graph_maturity_evidence_atom_upgrade_env()
    except (GraphMaturityGateError, RuntimeError) as exc:
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
            "Graph maturity upgrade: multi-question live abstract ingest, "
            "deterministic concept seeding, atom re-clustering, and Atlas report."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "data" / "exports" / "graph_maturity_evidence_atom_upgrade",
    )
    parser.add_argument(
        "--limit-per-question",
        type=int,
        default=3,
        help="Live sources per question profile (default 3).",
    )
    parser.add_argument(
        "--sync-public",
        action="store_true",
        help="Copy validated graph maturity artifact to public-site preview data.",
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

    result = run_graph_maturity_with_fresh_db(
        output_dir=args.output_dir,
        limit_per_question=args.limit_per_question,
    )

    if args.sync_public:
        artifact = result.get("atlas_safe_artifact") or {}
        sync_result = sync_graph_maturity_artifact_to_public_site(
            artifact,
            public_path=PUBLIC_ARTIFACT,
        )
        result["public_sync"] = sync_result
        result["public_artifact"] = str(
            PUBLIC_ARTIFACT.relative_to(REPO_ROOT).as_posix()
        )

    print(json.dumps(result, indent=2, default=str))
    if result.get("graph_maturity_verdict") == "NO-GO":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
