"""Tests for validate preview sync, freshness badge, and draft expected_files backfill."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.modules.instruction_packet_ticket_draft import (
    backfill_draft_expected_files,
    draft_needs_expected_files_backfill,
    run_draft_expected_files_backfill_command,
)
from rge.modules.tier2_patch_staging import run_tier2_patch_staging_command
from rge.modules.tier2_patch_staging_preview import atlas_artifact_path
from tests.unit.test_tier2_local_implementation import _seed_draft
from tests.unit.test_tier2_patch_staging import _stage_bundle


def test_validate_only_syncs_atlas_preview(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_AUTO_SYNC_TIER2_PATCH_PREVIEW", "1")
    rel = "rge/modules/tier2_local_implementation.py"
    _seed_draft(tmp_path)
    _, bundle_path = _stage_bundle(tmp_path, changed=[rel])
    if atlas_artifact_path(root=tmp_path).is_file():
        atlas_artifact_path(root=tmp_path).unlink()
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["validation_verdict"] = "pending"
    bundle_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    payload, code = run_tier2_patch_staging_command(
        bundle=bundle_path,
        validate_only=True,
        root=tmp_path,
    )
    assert code == 0
    assert payload.get("preview_sync") is not None
    assert atlas_artifact_path(root=tmp_path).is_file()
    artifact = json.loads(atlas_artifact_path(root=tmp_path).read_text(encoding="utf-8"))
    assert artifact["validation_verdict"] == "GO"
    assert artifact["preview_freshness"] == "fresh"


def test_atlas_preview_page_renders_freshness_badge() -> None:
    page = Path(__file__).resolve().parents[2] / "apps/public-site/app/atlas-preview/page.tsx"
    lib = Path(__file__).resolve().parents[2] / "apps/public-site/lib/atlasPreview.ts"
    page_text = page.read_text(encoding="utf-8")
    lib_text = lib.read_text(encoding="utf-8")
    assert "tier2PatchFreshnessBadgeColor" in page_text
    assert "tier2PatchFreshnessBadgeLabel" in page_text
    assert "Atlas preview stale" in lib_text
    assert "Atlas preview missing" in lib_text


def test_backfill_adds_companion_test_to_draft(tmp_path: Path) -> None:
    draft_dir = tmp_path / "data/operator/draft_tickets"
    draft_dir.mkdir(parents=True)
    draft_path = draft_dir / "draft_old.json"
    draft_path.write_text(
        json.dumps(
            {
                "schema_version": "instruction_packet_ticket_draft_v0.1.0",
                "id": "draft-old",
                "status": "draft",
                "expected_files": ["rge/modules/release_governor.py"],
                "test_plan": [],
            }
        ),
        encoding="utf-8",
    )
    target = tmp_path / "tests/unit/test_release_governor.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# test\n", encoding="utf-8")
    result = backfill_draft_expected_files(draft_path, root=tmp_path)
    assert result["status"] == "updated"
    assert "tests/unit/test_release_governor.py" in result["inferred_expected_files"]
    updated = json.loads(draft_path.read_text(encoding="utf-8"))
    assert updated["expected_files_inferred"] is True
    assert "expected_files_backfilled_at" in updated


def test_backfill_dry_run_does_not_write(tmp_path: Path) -> None:
    draft_dir = tmp_path / "data/operator/draft_tickets"
    draft_dir.mkdir(parents=True)
    draft_path = draft_dir / "draft_old.json"
    original = {
        "id": "draft-old",
        "expected_files": ["rge/modules/tier2_patch_staging.py"],
    }
    draft_path.write_text(json.dumps(original), encoding="utf-8")
    result = backfill_draft_expected_files(draft_path, dry_run=True, root=tmp_path)
    assert result["status"] == "dry_run"
    assert json.loads(draft_path.read_text(encoding="utf-8")) == original


def test_backfill_latest_command(tmp_path: Path) -> None:
    draft_dir = tmp_path / "data/operator/draft_tickets"
    draft_dir.mkdir(parents=True)
    (draft_dir / "draft_latest.json").write_text(
        json.dumps(
            {
                "id": "draft-latest",
                "expected_files": ["rge/modules/tier2_patch_staging.py"],
            }
        ),
        encoding="utf-8",
    )
    payload, code = run_draft_expected_files_backfill_command(latest=True, root=tmp_path)
    assert code == 0
    assert payload["draft_count"] == 1


def test_draft_needs_backfill_when_not_inferred() -> None:
    assert draft_needs_expected_files_backfill({"expected_files": ["rge/x.py"]}) is True
    assert draft_needs_expected_files_backfill({"expected_files_inferred": True}) is False
