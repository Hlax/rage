#!/usr/bin/env python3
"""Run local-safe scheduled research loop (Windows Task Scheduler entry)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from rge.modules.scheduled_research_loop import (  # noqa: E402
    ScheduledResearchLoopBlockedError,
    execute_scheduled_research_loop,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Local-safe scheduled research loop (mock-only by default).",
    )
    parser.add_argument(
        "--profile",
        default="local_mock_daily",
        help="Scheduled profile name (default: local_mock_daily).",
    )
    parser.add_argument(
        "--topic",
        default="Does AI improve creative output while reducing diversity?",
        help="Research topic for mock run.",
    )
    parser.add_argument(
        "--domain",
        default="creativity",
        help="Domain pack id (default: creativity).",
    )
    parser.add_argument(
        "--report-dir",
        help="Output directory for scheduled status JSON.",
    )
    parser.add_argument(
        "--no-atlas-refresh",
        action="store_true",
        help="Skip atlas export during scheduled mock research run.",
    )
    args = parser.parse_args()
    report_dir = Path(args.report_dir) if args.report_dir else None
    try:
        payload = execute_scheduled_research_loop(
            profile=args.profile,
            topic=args.topic,
            domain=args.domain,
            report_dir=report_dir,
            refresh_atlas=not args.no_atlas_refresh,
        )
        print(json.dumps(payload, indent=2))
        return 0 if payload.get("overall_verdict") in {"GO", "PARTIAL"} else 1
    except ScheduledResearchLoopBlockedError as exc:
        print(json.dumps({"status": "error", "detail": str(exc)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
