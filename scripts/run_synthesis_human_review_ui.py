#!/usr/bin/env python3
"""Build Atlas synthesis human-review panel artifact (mock/fixture default; no API calls)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from rge.modules.synthesis_human_review_ui import run_synthesis_human_review_ui  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build synthesis human-review Atlas artifact (fixture default).",
    )
    parser.add_argument(
        "--sync-public",
        action="store_true",
        help="Sync atlas-safe artifact to apps/public-site/public/data/.",
    )
    parser.add_argument(
        "--scan-exports",
        action="store_true",
        help="Scan data/exports for synthesis outputs (requires RGE_ALLOW_SYNTHESIS_HUMAN_REVIEW_UI=1).",
    )
    parser.add_argument(
        "--exports-dir",
        default="data/exports",
        help="Export scan root when --scan-exports is set.",
    )
    args = parser.parse_args()
    result = run_synthesis_human_review_ui(
        sync_public=args.sync_public,
        fixture_mode=not args.scan_exports,
        exports_dir=Path(args.exports_dir),
        root=_REPO_ROOT,
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
