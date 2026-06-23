"""Tests for backfill operator loop, post-backfill revalidation, and verdict badge."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.modules.instruction_packet_ticket_draft import backfill_draft_expected_files
from rge.modules.operator_loop import build_operator_plan
from rge.modules.tier2_patch_staging import (
    revalidate_latest_patch_bundle_for_draft,
    run_tier2_patch_staging_command,
)
from rge.modules.tier2_patch_staging_preview import atlas_artifact_path
from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state
from tests.unit.test_tier2_local_implementation import _seed_draft
from tests.unit.test_tier2_patch_staging import _stage_bundle


def test_operator_loop_recommends_backfill_before_staging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    clean = seed_operator_neutral_plan_state(tmp_path)
    _seed_draft(tmp_path, expected_files_inferred=False)
    plan = build_operator_plan(root=tmp_path, working_tree=clean)
    action = plan["next_recommended_action"]
    assert action["action_id"] == "run_draft_expected_files_backfill"
    assert action["gate"] == "safe_autonomous"
    assert "run_draft_expected_files_backfill.py --latest" in action["commands"][0]["shell"]


def test_backfill_revalidates_staged_bundle_when_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_REVALIDATE_PATCH_AFTER_BACKFILL", "1")
    monkeypatch.setenv("RGE_AUTO_SYNC_TIER2_PATCH_PREVIEW", "1")
    _seed_draft(
        tmp_path,
        expected_files_inferred=False,
        extra={"expected_files": ["rge/modules/release_governor.py"]},
    )
    rel = "rge/modules/tier2_local_implementation.py"
    _, bundle_path = _stage_bundle(tmp_path, changed=[rel])
    if atlas_artifact_path(root=tmp_path).is_file():
        atlas_artifact_path(root=tmp_path).unlink()
    draft_path = tmp_path / "data/operator/draft_tickets/draft_tier2_test.json"
    result = backfill_draft_expected_files(draft_path, root=tmp_path)
    assert result["status"] == "updated"
    assert result.get("patch_revalidation") is not None
    assert result["patch_revalidation"]["status"] == "validated"
    assert result["patch_revalidation"]["validation_verdict"] in {"GO", "PARTIAL", "NO-GO"}
    assert atlas_artifact_path(root=tmp_path).is_file()


def test_backfill_skips_revalidation_when_disabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_REVALIDATE_PATCH_AFTER_BACKFILL", "0")
    _seed_draft(
        tmp_path,
        expected_files_inferred=False,
        extra={"expected_files": ["rge/modules/release_governor.py"]},
    )
    rel = "rge/modules/tier2_local_implementation.py"
    _stage_bundle(tmp_path, changed=[rel])
    draft_path = tmp_path / "data/operator/draft_tickets/draft_tier2_test.json"
    result = backfill_draft_expected_files(draft_path, root=tmp_path)
    assert result["status"] == "updated"
    assert "patch_revalidation" not in result


def test_revalidate_latest_patch_bundle_for_draft_no_bundle(tmp_path: Path) -> None:
    _seed_draft(tmp_path)
    payload = revalidate_latest_patch_bundle_for_draft("draft-tier2-test", root=tmp_path)
    assert payload["status"] == "skipped"


def test_atlas_preview_page_renders_validation_verdict_badge() -> None:
    page = Path(__file__).resolve().parents[2] / "apps/public-site/app/atlas-preview/page.tsx"
    lib = Path(__file__).resolve().parents[2] / "apps/public-site/lib/atlasPreview.ts"
    page_text = page.read_text(encoding="utf-8")
    lib_text = lib.read_text(encoding="utf-8")
    assert "tier2PatchValidationVerdictBadgeColor" in page_text
    assert "tier2PatchValidationVerdictBadgeLabel" in page_text
    assert "Patch validation GO" in lib_text
    assert "Patch validation NO-GO" in lib_text
