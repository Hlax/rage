#!/usr/bin/env python3
"""Validate OpenAI synthesis adapter spec (ticket-059; no API calls)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from rge.modules.openai_synthesis_adapter_spec import run_openai_synthesis_adapter_spec  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="OpenAI synthesis adapter spec validation (no paid API calls).",
    )
    parser.add_argument(
        "--sync-public",
        action="store_true",
        help="Sync atlas-safe spec artifact to apps/public-site/public/data/.",
    )
    args = parser.parse_args()
    result = run_openai_synthesis_adapter_spec(sync_public=args.sync_public)
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
