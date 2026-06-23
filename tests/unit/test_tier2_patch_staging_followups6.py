"""Tests for synthesis draft revalidation UI, autocycle replan, and README tier2 docs."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.modules.autonomous_synthesis_governor import summarize_governor_status
from rge.modules.operator_autocycle import (
    evaluate_autocycle_cycle,
    post_tier2_hook_action_continues_autocycle,
    run_autocycle,
    tier2_hook_chain_warrants_replan,
)
from rge.modules.synthesis_human_review_ui import build_atlas_safe_human_review_artifact
from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state
from tests.unit.test_tier2_local_implementation import _seed_draft


def test_tier2_hook_chain_warrants_replan_helpers() -> None:
    assert tier2_hook_chain_warrants_replan(None) is False
    assert tier2_hook_chain_warrants_replan({"status": "skipped"}) is False
    assert tier2_hook_chain_warrants_replan(
        {"status": "completed", "backfill": {"status": "completed"}}
    )
    assert tier2_hook_chain_warrants_replan(
        {"status": "completed", "chained_patch_staging": True}
    )
    assert post_tier2_hook_action_continues_autocycle(
        {"action_id": "run_tier2_patch_validation", "gate": "safe_autonomous"}
    )
    assert not post_tier2_hook_action_continues_autocycle(
        {"action_id": "fix_tier2_patch_staging", "gate": "blocked"}
    )


def test_summarize_governor_status_includes_last_patch_revalidation(
    tmp_path: Path,
) -> None:
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

    summary = summarize_governor_status([], root=tmp_path)
    assert summary["last_patch_revalidation"]["validation_verdict"] == "GO"
    assert summary["expected_files_backfilled_at"] == "2026-06-22T12:00:00Z"

    artifact = build_atlas_safe_human_review_artifact([], root=tmp_path)
    assert artifact["governor_summary"]["last_patch_revalidation"]["status"] == "validated"


def test_atlas_preview_synthesis_panel_renders_revalidation_row() -> None:
    page = (
        Path(__file__).resolve().parents[2]
        / "apps/public-site/app/atlas-preview/page.tsx"
    )
    text = page.read_text(encoding="utf-8")
    assert "Post-backfill patch revalidation" in text
    assert "last_patch_revalidation" in text


def test_autocycle_multi_cycle_after_tier2_hook_chain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    clean = seed_operator_neutral_plan_state(tmp_path)
    execute_calls = {"count": 0}

    def _fake_execute(*, root=None, working_tree=None, command_runner=None):  # noqa: ANN001
        execute_calls["count"] += 1
        if execute_calls["count"] == 1:
            return {
                "execution_status": "pass",
                "post_tier2_hook_replan": True,
                "execute_safe_tier2_hook_chain": {
                    "status": "completed",
                    "backfill": {"status": "completed"},
                    "chained_patch_staging": True,
                },
                "next_recommended_action": {
                    "action_id": "run_tier2_patch_validation",
                    "gate": "safe_autonomous",
                    "label": "Validate staged patch",
                    "reason": "replan after backfill",
                    "commands": [],
                },
            }
        return {
            "execution_status": "pass",
            "next_recommended_action": {
                "action_id": "run_deterministic_verification",
                "gate": "safe_autonomous",
                "label": "Verify",
                "reason": "second cycle",
                "commands": [],
            },
        }

    real_evaluate = evaluate_autocycle_cycle

    def _eligible_evaluate(**kwargs):  # noqa: ANN003
        payload = real_evaluate(**kwargs)
        if payload.get("status") == "stopped":
            payload["status"] = "proceed"
            payload["stop_reason"] = None
        payload["execute_safe_eligible"] = True
        return payload

    with patch(
        "rge.modules.operator_autocycle.inspect_working_tree",
        return_value=clean,
    ), patch(
        "rge.modules.operator_autocycle.evaluate_autocycle_cycle",
        side_effect=_eligible_evaluate,
    ):
        payload = run_autocycle(
            mode="execute-safe",
            max_cycles=2,
            root=tmp_path,
            execute_runner=_fake_execute,
        )

    assert payload["cycles_completed"] == 2
    assert execute_calls["count"] == 2
    assert payload["post_tier2_hook_replan"] is True


def test_readme_documents_tier2_hook_chain() -> None:
    readme = (Path(__file__).resolve().parents[2] / "README.md").read_text(encoding="utf-8")
    assert "Tier 2 patch staging operator spine" in readme
    assert "Execute-safe Tier 2 hook chain" in readme
    assert "RGE_EXECUTE_SAFE_DRAFT_BACKFILL=1" in readme
    assert "Autocycle Tier 2 multi-cycle replan" in readme
