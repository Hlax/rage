#!/usr/bin/env python3
"""Run multi-claim atom clustering mock proof."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from rge.modules.multi_claim_atom_clustering import (  # noqa: E402
    MultiClaimAtomClusteringGateError,
    run_multi_claim_atom_clustering_with_fresh_db,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Multi-claim evidence atom clustering mock proof.",
    )
    parser.add_argument(
        "--output-dir",
        help="Export directory (default: data/exports/multi_claim_atom_clustering).",
    )
    parser.add_argument(
        "--sync-public",
        action="store_true",
        help="Sync atlas-safe artifact to apps/public-site/public/data/.",
    )
    args = parser.parse_args()
    output_dir = Path(args.output_dir) if args.output_dir else None
    try:
        result = run_multi_claim_atom_clustering_with_fresh_db(
            output_dir=output_dir,
            sync_public=args.sync_public,
        )
        print(json.dumps(result, indent=2))
        return 0 if result.get("status") == "completed" else 1
    except MultiClaimAtomClusteringGateError as exc:
        print(json.dumps({"status": "error", "detail": str(exc)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
