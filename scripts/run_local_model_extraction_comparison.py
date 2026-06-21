"""Run local model extraction comparison (mock vs Ollama on same live abstracts)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rge.modules.local_model_extraction_comparison import (  # noqa: E402
    COMPARISON_ARTIFACT_NAME,
    LocalModelExtractionComparisonGateError,
    assert_local_model_extraction_comparison_env,
    required_env_setup_commands,
    run_local_model_extraction_comparison,
    sync_comparison_artifact_to_public_site,
)

PUBLIC_ARTIFACT = (
    REPO_ROOT
    / "apps"
    / "public-site"
    / "public"
    / "data"
    / COMPARISON_ARTIFACT_NAME
)


def _missing_gates() -> dict[str, str]:
    missing: dict[str, str] = {}
    try:
        assert_local_model_extraction_comparison_env()
    except (LocalModelExtractionComparisonGateError, RuntimeError) as exc:
        message = str(exc)
        for line in message.splitlines():
            stripped = line.strip()
            if "=" in stripped and (
                stripped.startswith("RGE_") or stripped.startswith("OPENALEX")
            ):
                name, hint = stripped.split("=", 1)
                missing[name.strip()] = hint.strip()
        if not missing:
            missing["gates"] = message
    return missing


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compare deterministic mock abstract extraction vs local Qwen/Ollama "
            "on the same live OpenAlex/arXiv abstracts (evaluation only)."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "data" / "exports" / "local_model_extraction_comparison",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum live abstract sources to compare.",
    )
    parser.add_argument(
        "--sync-public",
        action="store_true",
        help="Copy validated comparison artifact to public-site preview data.",
    )
    parser.add_argument(
        "--skip-health-check",
        action="store_true",
        help="Skip Ollama health probe (unit tests only).",
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

    result = run_local_model_extraction_comparison(
        output_dir=args.output_dir,
        limit=args.limit,
        skip_health_check=args.skip_health_check,
    )

    if args.sync_public:
        artifact = result.get("atlas_safe_artifact") or {}
        sync_result = sync_comparison_artifact_to_public_site(
            artifact,
            public_path=PUBLIC_ARTIFACT,
        )
        result["public_sync"] = sync_result
        result["public_artifact"] = str(
            PUBLIC_ARTIFACT.relative_to(REPO_ROOT).as_posix()
        )

    print(json.dumps(result, indent=2, default=str))
    verdict = result.get("comparison_verdict")
    if verdict == "NO-GO":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
