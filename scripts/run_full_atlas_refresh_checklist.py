"""Run the operator full Atlas refresh checklist (full-cycle validation → sync → build → report)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rge.modules.full_atlas_refresh_checklist import (  # noqa: E402
    missing_live_gates,
    missing_operator_full_atlas_refresh_gate,
    required_env_setup_commands,
    run_full_atlas_refresh_checklist,
    write_checklist_reports,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Operator full Atlas refresh: live abstract smoke (optional), fixture packet "
            "refresh, operator artifact validation, trace validation, site build, report."
        )
    )
    parser.add_argument(
        "--fixture-only",
        action="store_true",
        help=(
            "Skip live OpenAlex smoke; refresh fixture packets and validate all "
            "operator artifacts (requires RGE_ALLOW_OPERATOR_FULL_ATLAS_REFRESH=1 only)."
        ),
    )
    parser.add_argument(
        "--skip-fixture-refresh",
        action="store_true",
        help="Skip web/pdf/demo fixture packet refresh (validate existing artifacts only).",
    )
    parser.add_argument(
        "--skip-site",
        action="store_true",
        help="Skip public-site npm build (still syncs artifact and writes report).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory for temp DB and intermediate atlas artifact (default: data/exports/full_atlas_refresh).",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip writing agent_reports markdown/JSON.",
    )
    args = parser.parse_args()

    missing = dict(missing_operator_full_atlas_refresh_gate())
    if not args.fixture_only:
        missing.update(missing_live_gates())
    if missing:
        payload = {
            "status": "blocked",
            "reason": "missing gates",
            "missing_gates": missing,
            "env_setup": required_env_setup_commands(fixture_only=args.fixture_only),
        }
        print(json.dumps(payload, indent=2))
        raise SystemExit(1)

    report = run_full_atlas_refresh_checklist(
        root=REPO_ROOT,
        output_dir=args.output_dir,
        skip_site=args.skip_site,
        fixture_only=args.fixture_only,
        refresh_fixture_packets=not args.skip_fixture_refresh,
    )
    if not args.no_report:
        paths = write_checklist_reports(report, root=REPO_ROOT)
        report["report_paths"] = paths

    print(json.dumps(report, indent=2))
    if report.get("overall_verdict") == "FAIL":
        raise SystemExit(2)
    if report.get("overall_verdict") == "PARTIAL":
        raise SystemExit(3)


if __name__ == "__main__":
    main()
