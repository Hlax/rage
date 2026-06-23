"""Operator loop release batch candidate recommendation tests."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from rge.modules.autonomous_synthesis_governor import save_circuit_breaker
from rge.modules.operator_loop import WorkingTreeStatus, build_operator_plan
from rge.modules.release_batch_assembler import assemble_release_batch_payload
from rge.modules.release_governor import (
    build_safe_fixture_batch,
    inspect_release_governor_plan_status,
    promote_draft_tickets_to_candidates,
    release_batch_dir,
)
from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state


def _seed_draft(
    tmp_path: Path,
    *,
    draft_id: str = "draft-release-loop-test",
    instruction_packet: str | None = "data/operator/instruction_packets/test.md",
) -> Path:
    draft_dir = tmp_path / "data/operator/draft_tickets"
    draft_dir.mkdir(parents=True, exist_ok=True)
    draft = {
        "id": draft_id,
        "status": "draft",
        "title": "Release loop test draft",
        "source_instruction_packet": instruction_packet,
        "expected_files": ["rge/modules/release_governor.py"],
        "expected_files_inferred": True,
        "rollback_plan": "Delete batch and branch.",
        "test_plan": ["python -m pytest tests/unit/test_release_governor.py -q"],
    }
    path = draft_dir / "draft_release_loop_test.json"
    path.write_text(json.dumps(draft), encoding="utf-8")
    return path


def _seed_batch_for_draft(tmp_path: Path, draft_id: str = "draft-release-loop-test") -> Path:
    batch_dir = release_batch_dir(root=tmp_path)
    batch_dir.mkdir(parents=True, exist_ok=True)
    batch = build_safe_fixture_batch(batch_id="batch_loop_test")
    batch["draft_ticket_ids"] = [draft_id]
    path = batch_dir / "batch_loop_test.json"
    path.write_text(json.dumps(batch), encoding="utf-8")
    return path


def test_operator_loop_recommends_tier2_when_draft_and_no_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    clean_tree = seed_operator_neutral_plan_state(tmp_path)
    _seed_draft(tmp_path)
    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    action = plan["next_recommended_action"]
    assert action["action_id"] == "run_tier2_patch_staging"
    assert action["gate"] == "safe_autonomous"
    assert any(
        "run_tier2_patch_staging.py" in cmd.get("shell", "")
        for cmd in action["commands"]
    )


def test_operator_loop_recommends_batch_candidate_after_impl_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    clean_tree = seed_operator_neutral_plan_state(tmp_path)
    _seed_draft(tmp_path)
    branch = "phase-3/tier2-draft-release-loop-test"
    impl_tree = WorkingTreeStatus(clean=True, branch=branch, dirty_paths=[])
    with patch(
        "rge.modules.tier2_local_implementation._branch_has_commits_ahead_of_main",
        return_value=True,
    ):
        plan = build_operator_plan(root=tmp_path, working_tree=impl_tree)
    action = plan["next_recommended_action"]
    assert action["action_id"] == "create_release_batch_candidate"


def test_operator_loop_recommends_dry_run_when_batch_exists(tmp_path: Path) -> None:
    clean_tree = seed_operator_neutral_plan_state(tmp_path)
    _seed_draft(tmp_path)
    _seed_batch_for_draft(tmp_path)
    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    action = plan["next_recommended_action"]
    assert action["action_id"] == "run_release_governor_dry_run"
    assert action["gate"] == "safe_autonomous"


def test_circuit_breaker_open_takes_priority_over_batch_candidate(tmp_path: Path) -> None:
    clean_tree = seed_operator_neutral_plan_state(tmp_path)
    _seed_draft(tmp_path)
    save_circuit_breaker(
        {
            "schema_version": "autonomy_circuit_breaker_v0.1.0",
            "status": "open",
            "latest_stop_reason": "fixture circuit open",
            "consecutive_synthesis_failures": 3,
            "consecutive_unsupported_outputs": 0,
        },
        root=tmp_path,
    )
    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    action = plan["next_recommended_action"]
    assert action["action_id"] == "run_circuit_breaker_inspection"
    status = inspect_release_governor_plan_status(root=tmp_path)
    assert status["batch_candidate_recommended"] is False


def test_unsafe_dirty_tree_blocks_batch_candidate(tmp_path: Path) -> None:
    seed_operator_neutral_plan_state(tmp_path)
    _seed_draft(tmp_path)
    dirty_tree = WorkingTreeStatus(
        clean=False,
        branch="main",
        dirty_paths=[" M rge/modules/release_governor.py"],
    )
    plan = build_operator_plan(root=tmp_path, working_tree=dirty_tree)
    action = plan["next_recommended_action"]
    assert action["action_id"] == "resolve_unsafe_working_tree"
    assert action["gate"] == "blocked"
    status = inspect_release_governor_plan_status(root=tmp_path, working_tree=dirty_tree)
    assert status["batch_assembly_blocked"] is True


def test_controlled_dirty_allows_tier2_recommendation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    seed_operator_neutral_plan_state(tmp_path)
    _seed_draft(tmp_path)
    dirty_tree = WorkingTreeStatus(
        clean=False,
        branch="main",
        dirty_paths=[" M agent_reports/2026-06-22_test-report.md"],
    )
    plan = build_operator_plan(root=tmp_path, working_tree=dirty_tree)
    action = plan["next_recommended_action"]
    assert action["action_id"] == "run_tier2_patch_staging"


def test_batch_candidate_includes_required_metadata(tmp_path: Path) -> None:
    _seed_draft(tmp_path, instruction_packet="data/operator/instruction_packets/packet.md")
    (tmp_path / "agent_reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "agent_reports" / "2026-06-22_phase-3_ticket-999_test-report.md").write_text(
        "# report",
        encoding="utf-8",
    )
    clean_tree = WorkingTreeStatus(clean=True, branch="phase-3/release-test", dirty_paths=[])
    with patch(
        "rge.modules.release_batch_assembler.inspect_working_tree",
        return_value=clean_tree,
    ), patch(
        "rge.modules.release_batch_assembler._git_value",
        return_value="abc123deadbeef",
    ):
        batch = assemble_release_batch_payload(latest=True, root=tmp_path)
    metadata = batch["candidate_metadata"]
    assert metadata["source_draft_ticket_path"].endswith("draft_release_loop_test.json")
    assert metadata["source_instruction_packet_path"] == "data/operator/instruction_packets/packet.md"
    assert metadata["branch_name"] == "phase-3/release-test"
    assert metadata["commit_hash"] == "abc123deadbeef"
    assert metadata["rollback_plan"]
    assert metadata["reports"]
    assert metadata["autonomy_tier_required_for_next_action"] == 0
    assert metadata["next_release_action"] == "release_governor_dry_run"
    assert ".env.local" not in batch["changed_files"]


def test_batch_candidate_filters_forbidden_changed_files(tmp_path: Path) -> None:
    _seed_draft(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    with patch(
        "rge.modules.release_batch_assembler.inspect_working_tree",
        return_value=clean_tree,
    ), patch(
        "rge.modules.release_batch_assembler._git_value",
        return_value="abc123deadbeef",
    ), patch(
        "rge.modules.release_batch_assembler._collect_changed_files",
        return_value=["rge/modules/foo.py", ".env.local", "data/sources/manual/secret.txt"],
    ):
        batch = assemble_release_batch_payload(latest=True, root=tmp_path)
    assert batch["changed_files"] == ["rge/modules/foo.py"]


def test_unsafe_dirty_blocks_batch_assembly(tmp_path: Path) -> None:
    _seed_draft(tmp_path)
    dirty_tree = WorkingTreeStatus(
        clean=False,
        branch="main",
        dirty_paths=[" M rge/modules/foo.py"],
    )
    with patch(
        "rge.modules.release_batch_assembler.inspect_working_tree",
        return_value=dirty_tree,
    ):
        with pytest.raises(Exception, match="unsafe dirty paths|non-operator dirty"):
            assemble_release_batch_payload(latest=True, root=tmp_path)


def test_batch_candidate_never_touches_canonical_queue(tmp_path: Path) -> None:
    seed_operator_neutral_plan_state(tmp_path)
    draft_id = "draft-release-loop-test"
    _seed_draft(tmp_path, draft_id=draft_id)
    batch_path = _seed_batch_for_draft(tmp_path, draft_id=draft_id)
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    queue_before = (tmp_path / "tickets" / "TICKET_QUEUE.md").read_text(encoding="utf-8")
    promote_draft_tickets_to_candidates(batch, root=tmp_path, dry_run=True)
    queue_after = (tmp_path / "tickets" / "TICKET_QUEUE.md").read_text(encoding="utf-8")
    assert queue_before == queue_after


def test_inspect_status_next_release_action_assemble(tmp_path: Path) -> None:
    _seed_draft(tmp_path)
    status = inspect_release_governor_plan_status(root=tmp_path)
    assert status["next_release_action"] == "assemble_release_batch"
    assert status["autonomy_tier_required_for_next_action"] == 1


def test_inspect_status_next_release_action_dry_run(tmp_path: Path) -> None:
    _seed_draft(tmp_path)
    _seed_batch_for_draft(tmp_path)
    status = inspect_release_governor_plan_status(root=tmp_path)
    assert status["next_release_action"] == "release_governor_dry_run"
    assert status["release_governor_dry_run_recommended"] is True
