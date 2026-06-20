"""Atlas source-health run artifact preview wiring tests."""

from __future__ import annotations

import json
from pathlib import Path

from rge.modules.atlas_snapshot_builder import assert_no_private_fields

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_PATH = (
    REPO_ROOT / "apps" / "public-site" / "public" / "data" / "atlas_source_health_run_latest.json"
)
ATLAS_PREVIEW_PAGE = REPO_ROOT / "apps" / "public-site" / "app" / "atlas-preview" / "page.tsx"
ATLAS_PREVIEW_LIB = REPO_ROOT / "apps" / "public-site" / "lib" / "atlasPreview.ts"


def test_atlas_source_health_run_artifact_is_public_safe() -> None:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "atlas_source_health_run_v0.1.0"
    assert artifact["source_health_summary"]["sources_with_metadata"] >= 1
    assert assert_no_private_fields({"artifact": artifact}) == []


def test_atlas_preview_wires_source_health_resolver() -> None:
    page = ATLAS_PREVIEW_PAGE.read_text(encoding="utf-8")
    lib = ATLAS_PREVIEW_LIB.read_text(encoding="utf-8")
    assert "resolveSourceHealthPreview" in lib
    assert "resolveSourceHealthPreview" in page
    assert "resolveGapsNextMovePreview" in lib
    assert "resolveGapsNextMovePreview" in page
    assert "atlas_source_health_run_latest.json" in lib
    assert "fetch(" not in page


def test_atlas_source_health_run_artifact_includes_gaps_fields() -> None:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert artifact.get("readiness_warnings")
    assert artifact.get("next_recommended_packet")
    assert artifact.get("next_recommended_reason")
