"""Run web adapter / Scrapling proof smoke."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rge.modules.scrapling_html_parser import PARSER_HTML_TO_TEXT, PARSER_SCRAPLING
from rge.modules.web_adapter_scrapling_proof import (  # noqa: E402
    WEB_ADAPTER_ARTIFACT_NAME,
    WebAdapterScraplingProofGateError,
    assert_web_adapter_scrapling_proof_env,
    required_env_setup_commands,
    run_web_adapter_scrapling_with_fresh_db,
    sync_web_adapter_artifact_to_public_site,
)

PUBLIC_ARTIFACT = (
    REPO_ROOT
    / "apps"
    / "public-site"
    / "public"
    / "data"
    / WEB_ADAPTER_ARTIFACT_NAME
)


def _missing_gates(*, live_fetch: bool) -> dict[str, str]:
    missing: dict[str, str] = {}
    try:
        assert_web_adapter_scrapling_proof_env(require_live_fetch=live_fetch)
    except (WebAdapterScraplingProofGateError, RuntimeError) as exc:
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
            "Web adapter / Scrapling proof: fixture webpage through quality gate, "
            "quote-first extraction, evidence atoms, and Atlas trace summary."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "data" / "exports" / "web_adapter_scrapling_proof",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=REPO_ROOT / "fixtures" / "sources" / "web_article_creativity_fixture.html",
    )
    parser.add_argument(
        "--parser-backend",
        choices=[PARSER_HTML_TO_TEXT, PARSER_SCRAPLING, "auto"],
        default=PARSER_HTML_TO_TEXT,
    )
    parser.add_argument(
        "--live-fetch",
        action="store_true",
        help="Opt-in live fetch of a public webpage URL (requires network gates).",
    )
    parser.add_argument(
        "--sync-public",
        action="store_true",
        help="Copy validated web adapter artifact to public-site preview data.",
    )
    args = parser.parse_args()

    missing = _missing_gates(live_fetch=args.live_fetch)
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

    result = run_web_adapter_scrapling_with_fresh_db(
        output_dir=args.output_dir,
        fixture_path=args.fixture,
        parser_backend=args.parser_backend,
        live_fetch=args.live_fetch,
    )

    if args.sync_public:
        artifact = result.get("atlas_safe_artifact") or {}
        sync_result = sync_web_adapter_artifact_to_public_site(
            artifact,
            public_path=PUBLIC_ARTIFACT,
        )
        result["public_sync"] = sync_result
        result["public_artifact"] = str(
            PUBLIC_ARTIFACT.relative_to(REPO_ROOT).as_posix()
        )

    print(json.dumps(result, indent=2, default=str))
    if result.get("web_adapter_verdict") == "NO-GO":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
