"""Run demo loop polish proof smoke."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rge.modules.demo_loop_polish import (  # noqa: E402
    DEMO_LOOP_ARTIFACT_NAME,
    DemoLoopPolishGateError,
    assert_demo_loop_polish_env,
    required_env_setup_commands,
    run_demo_loop_polish_smoke,
    run_demo_loop_polish_with_fresh_db,
    sync_demo_loop_artifact_to_public_site,
)

PUBLIC_ARTIFACT = (
    REPO_ROOT
    / "apps"
    / "public-site"
    / "public"
    / "data"
    / DEMO_LOOP_ARTIFACT_NAME
)


def _missing_gates() -> dict[str, str]:
    missing: dict[str, str] = {}
    try:
        assert_demo_loop_polish_env()
    except DemoLoopPolishGateError as exc:
        message = str(exc)
        for line in message.splitlines():
            stripped = line.strip()
            if "=" in stripped and stripped.startswith("RGE_"):
                name, hint = stripped.split("=", 1)
                missing[name.strip()] = hint.strip()
        if not missing:
            missing["gates"] = message
    return missing


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Demo loop polish: fixture research-run through abstract evidence, "
            "selective full-text summary, improvement recommendation, and Atlas artifact."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "data" / "exports" / "demo_loop_polish",
    )
    parser.add_argument(
        "--topic",
        default="AI assisted creativity and idea diversity",
    )
    parser.add_argument(
        "--top-sources",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--full-text-top-n",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--persist-claims",
        action="store_true",
        help="Persist full-text claims to a fresh temp DB and include trace summary.",
    )
    parser.add_argument(
        "--sync-public",
        action="store_true",
        help="Copy validated demo loop artifact to public-site preview data.",
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

    if args.persist_claims:
        result = run_demo_loop_polish_with_fresh_db(
            output_dir=args.output_dir,
            topic=args.topic,
            top_sources=args.top_sources,
            full_text_top_n=args.full_text_top_n,
        )
    else:
        result = run_demo_loop_polish_smoke(
            topic=args.topic,
            top_sources=args.top_sources,
            full_text_top_n=args.full_text_top_n,
            output_dir=args.output_dir,
        )

    if args.sync_public:
        artifact = result.get("atlas_safe_artifact") or {}
        sync_result = sync_demo_loop_artifact_to_public_site(
            artifact,
            public_path=PUBLIC_ARTIFACT,
        )
        result["public_sync"] = sync_result
        result["public_artifact"] = str(
            PUBLIC_ARTIFACT.relative_to(REPO_ROOT).as_posix()
        )

    print(json.dumps(result, indent=2, default=str))
    if result.get("demo_loop_verdict") == "NO-GO":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
