"""Tests for execute-safe backfill hook, Atlas revalidation summary, and action priority."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.modules.instruction_packet_ticket_draft import (
    backfill_draft_expected_files,
    execute_safe_draft_backfill_enabled,
    run_execute_safe_draft_backfill_hook,
)
from rge.modules.operator_loop import build_operator_plan, execute_safe_checks
from rge.modules.tier2_patch_staging_preview import (
    atlas_artifact_path,
    build_atlas_safe_tier2_patch_staging_artifact,
    refresh_tier2_patch_staging_preview,
)
from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state
from tests.unit.test_tier2_local_implementation import _seed_draft
from tests.unit.test_tier2_patch_staging import _stage_bundle


def test_operator_loop_backfill_beats_fix_tier2_patch_staging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    clean = seed_operator_neutral_plan_state(tmp_path)
    bundle, _ = _stage_bundle(
        tmp_path,
        changed=[".env.local"],
        file_contents={".env.local": "X=1\n"},
        draft_extra={"expected_files_inferred": False},
    )
    assert bundle["validation_verdict"] in {"PARTIAL", "NO-GO"}
    plan = build_operator_plan(root=tmp_path, working_tree=clean)
    assert plan["next_recommended_action"]["action_id"] == "run_draft_expected_files_backfill"


def test_execute_safe_draft_backfill_hook_runs_when_only_blocker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_EXECUTE_SAFE_DRAFT_BACKFILL", "1")
    monkeypatch.setenv("RGE_REVALIDATE_PATCH_AFTER_BACKFILL", "0")
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    clean = seed_operator_neutral_plan_state(tmp_path)
    _seed_draft(
        tmp_path,
        expected_files_inferred=False,
        extra={"expected_files": ["rge/modules/release_governor.py"]},
    )
    target = tmp_path / "tests/unit/test_release_governor.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# test\n", encoding="utf-8")

    def _fake_runner(argv, cwd, env):  # noqa: ANN001
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    with patch(
        "rge.modules.operator_loop.safe_verification_commands",
        return_value=[],
    ):
        result = execute_safe_checks(
            root=tmp_path,
            working_tree=clean,
            command_runner=_fake_runner,
        )
    assert result["execution_status"] == "pass"
    assert result["next_recommended_action"]["action_id"] == "run_draft_expected_files_backfill"
    hook = result.get("draft_backfill_execute_safe_hook")
    assert hook is not None
    assert hook["status"] == "completed"
    assert hook.get("updated_count", 0) >= 1
    draft = json.loads(
        (tmp_path / "data/operator/draft_tickets/draft_tier2_test.json").read_text(
            encoding="utf-8"
        )
    )
    assert draft.get("expected_files_inferred") is True


def test_execute_safe_draft_backfill_hook_skipped_when_not_blocker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_EXECUTE_SAFE_DRAFT_BACKFILL", "1")
    hook = run_execute_safe_draft_backfill_hook(
        root=tmp_path,
        action_id="run_tier2_patch_staging",
    )
    assert hook == {"status": "skipped", "reason": "draft backfill is not the current blocker"}


def test_execute_safe_draft_backfill_hook_disabled_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_EXECUTE_SAFE_DRAFT_BACKFILL", raising=False)
    assert execute_safe_draft_backfill_enabled() is False
    assert run_execute_safe_draft_backfill_hook(
        root=tmp_path,
        action_id="run_draft_expected_files_backfill",
    ) is None


def test_atlas_preview_includes_patch_revalidation_summary(
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
    bundle, bundle_path = _stage_bundle(tmp_path, changed=[rel])
    draft_path = tmp_path / "data/operator/draft_tickets/draft_tier2_test.json"
    backfill_draft_expected_files(draft_path, root=tmp_path)
    refresh_tier2_patch_staging_preview(bundle=bundle_path, sync_public=True, root=tmp_path)
    artifact = json.loads(atlas_artifact_path(root=tmp_path).read_text(encoding="utf-8"))
    summary = artifact.get("patch_revalidation_summary")
    assert summary is not None
    assert summary.get("status") == "validated"
    assert summary.get("validation_verdict") in {"GO", "PARTIAL", "NO-GO"}
    assert summary.get("backfilled_at")

    built = build_atlas_safe_tier2_patch_staging_artifact(bundle, root=tmp_path)
    assert built.get("patch_revalidation_summary") is not None
