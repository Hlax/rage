#!/usr/bin/env python3
"""Standalone operator CLI for Tier 2 patch staging."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from rge.modules.tier2_patch_staging import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
