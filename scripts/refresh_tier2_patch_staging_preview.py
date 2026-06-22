#!/usr/bin/env python3
"""Refresh Atlas Tier 2 patch staging operator preview artifact."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from rge.modules.tier2_patch_staging_preview import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
