#!/usr/bin/env python3
"""Repeated mock-first synthesis packet benchmark (throughput + review cadence dry run)."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from rge.modules.synthesis_packet_benchmark import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
