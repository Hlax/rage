"""Run multi-question live abstract evidence quality smoke (operator opt-in)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rge.modules.multi_question_live_abstract import (  # noqa: E402
    MULTI_QUESTION_BUNDLE_NAME,
    assert_live_multi_question_abstract_smoke_env,
    required_env_setup_commands,
    run_live_multi_question_abstract_smoke,
    sync_multi_question_bundle_to_public_site,
)

DEFAULT_OUTPUT = REPO_ROOT / "data" / "exports" / "multi_question_live_abstract"
PUBLIC_BUNDLE = (
    REPO_ROOT
    / "apps"
    / "public-site"
    / "public"
    / "data"
    / MULTI_QUESTION_BUNDLE_NAME
)


def _missing_gates() -> dict[str, str]:
    missing: dict[str, str] = {}
    try:
        assert_live_multi_question_abstract_smoke_env()
    except RuntimeError as exc:
        message = str(exc)
        for line in message.splitlines():
            stripped = line.strip()
            if stripped.startswith("RGE_") or stripped.startswith("OPENALEX"):
                if "=" in stripped:
                    name, hint = stripped.split("=", 1)
                    missing[name.strip()] = hint.strip()
                else:
                    missing[stripped] = "1"
        if not missing:
            missing["gates"] = message
    return missing


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Multi-question live abstract evidence quality smoke with purpose-gating proof."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Directory for per-question DBs, artifacts, and bundle JSON.",
    )
    parser.add_argument(
        "--sync-public",
        action="store_true",
        help="Copy validated bundle to apps/public-site/public/data/.",
    )
    parser.add_argument(
        "--public-output",
        type=Path,
        default=PUBLIC_BUNDLE,
        help="Public-site destination for bundle when --sync-public is set.",
    )
    args = parser.parse_args()

    missing = _missing_gates()
    if missing:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": "missing live gates",
                    "missing_gates": missing,
                    "env_setup": required_env_setup_commands(),
                },
                indent=2,
            )
        )
        raise SystemExit(1)

    result = run_live_multi_question_abstract_smoke(output_dir=args.output_dir)
    if args.sync_public:
        sync_result = sync_multi_question_bundle_to_public_site(
            Path(result["bundle_path"]),
            public_path=args.public_output,
        )
        result["public_sync"] = sync_result

    print(json.dumps(result, indent=2))
    if result.get("verdict") == "NO-GO":
        raise SystemExit(2)
    if result.get("verdict") == "PARTIAL":
        raise SystemExit(3)


if __name__ == "__main__":
    main()
