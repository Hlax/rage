"""Run PDF / TEI milestone proof smoke."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rge.modules.pdf_tei_milestone import (  # noqa: E402
    PDF_TEI_ARTIFACT_NAME,
    PdfTeiMilestoneGateError,
    assert_pdf_tei_milestone_env,
    required_env_setup_commands,
    run_pdf_tei_milestone_with_fresh_db,
    sync_pdf_tei_artifact_to_public_site,
)

PUBLIC_ARTIFACT = (
    REPO_ROOT
    / "apps"
    / "public-site"
    / "public"
    / "data"
    / PDF_TEI_ARTIFACT_NAME
)


def _missing_gates() -> dict[str, str]:
    missing: dict[str, str] = {}
    try:
        assert_pdf_tei_milestone_env()
    except PdfTeiMilestoneGateError as exc:
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
            "PDF / TEI milestone: TEI + PDF parsing, dirty-PDF quality gate, "
            "quote-first extraction, evidence atoms, and Atlas trace summary."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "data" / "exports" / "pdf_tei_milestone",
    )
    parser.add_argument(
        "--grobid-url",
        default="",
        help="Optional GROBID base URL for PDF→TEI comparison (operator opt-in).",
    )
    parser.add_argument(
        "--sync-public",
        action="store_true",
        help="Copy validated PDF / TEI artifact to public-site preview data.",
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

    result = run_pdf_tei_milestone_with_fresh_db(
        output_dir=args.output_dir,
        grobid_url=args.grobid_url,
    )

    if args.sync_public:
        artifact = result.get("atlas_safe_artifact") or {}
        sync_result = sync_pdf_tei_artifact_to_public_site(
            artifact,
            public_path=PUBLIC_ARTIFACT,
        )
        result["public_sync"] = sync_result
        result["public_artifact"] = str(
            PUBLIC_ARTIFACT.relative_to(REPO_ROOT).as_posix()
        )

    print(json.dumps(result, indent=2, default=str))
    if result.get("pdf_tei_verdict") == "NO-GO":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
