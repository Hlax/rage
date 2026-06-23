"""Tests for execute-safe hook chain, draft status revalidation row, and golden fixture shape."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.modules.instruction_packet_ticket_draft import (
    inspect_instruction_packet_ticket_draft_status,
    run_execute_safe_tier2_hook_chain,
)
from rge.modules.operator_loop import WorkingTreeStatus, build_operator_plan, execute_safe_checks
from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state
from tests.unit.test_tier2_local_implementation import _seed_draft


def test_execute_safe_tier2_hook_chain_runs_patch_staging_after_controlled_dirty_backfill(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_EXECUTE_SAFE_DRAFT_BACKFILL", "1")
    monkeypatch.setenv("RGE_EXECUTE_SAFE_PATCH_STAGING", "1")
    monkeypatch.setenv("RGE_REVALIDATE_PATCH_AFTER_BACKFILL", "0")
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    _seed_draft(
        tmp_path,
        expected_files_inferred=False,
        extra={"expected_files": ["rge/modules/release_governor.py"]},
    )
    target = tmp_path / "tests/unit/test_release_governor.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# test\n", encoding="utf-8")

    tree_before = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    tree_after = WorkingTreeStatus(
        clean=False,
        branch="main",
        dirty_paths=["data/operator/draft_tickets/draft_tier2_test.json"],
    )
    inspect_calls = {"count": 0}

    def _fake_inspect(_root: Path) -> WorkingTreeStatus:
        inspect_calls["count"] += 1
        return tree_after

    with patch(
        "rge.modules.operator_loop.inspect_working_tree",
        side_effect=_fake_inspect,
    ):
        chain = run_execute_safe_tier2_hook_chain(
            root=tmp_path,
            working_tree=tree_before,
            action_id="run_draft_expected_files_backfill",
        )

    assert chain["status"] == "completed"
    assert chain["backfill"]["status"] == "completed"
    assert chain["tree_became_controlled_dirty"] is True
    assert chain["chained_patch_staging"] is True
    assert chain["patch_staging"] is not None
    assert chain["patch_staging"]["status"] == "completed"


def test_execute_safe_checks_uses_tier2_hook_chain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_EXECUTE_SAFE_DRAFT_BACKFILL", "1")
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
    chain = result.get("execute_safe_tier2_hook_chain")
    assert chain is not None
    assert chain.get("backfill") is not None


def test_operator_loop_plan_includes_last_patch_revalidation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    clean = seed_operator_neutral_plan_state(tmp_path)
    draft_path = _seed_draft(tmp_path)
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    draft["last_patch_revalidation"] = {
        "status": "validated",
        "validation_verdict": "GO",
        "passed": True,
        "reason_count": 0,
        "bundle_path_summary": "bundle.json",
    }
    draft["expected_files_backfilled_at"] = "2026-06-22T12:00:00Z"
    draft_path.write_text(json.dumps(draft, indent=2) + "\n", encoding="utf-8")

    status = inspect_instruction_packet_ticket_draft_status(root=tmp_path)
    assert status["last_patch_revalidation"]["validation_verdict"] == "GO"
    assert status["expected_files_backfilled_at"] == "2026-06-22T12:00:00Z"

    plan = build_operator_plan(root=tmp_path, working_tree=clean)
    plan_status = plan["instruction_packet_ticket_draft_status"]
    assert plan_status["last_patch_revalidation"]["status"] == "validated"
    assert plan_status["last_patch_revalidation"]["validation_verdict"] == "GO"
