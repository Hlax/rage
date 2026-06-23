"""Tier 2 local branch implementation runner tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.modules.autonomous_synthesis_governor import save_circuit_breaker
from rge.modules.operator_loop import WorkingTreeStatus, build_operator_plan
from rge.modules.release_governor import inspect_release_governor_plan_status, release_batch_dir
from rge.modules.tier2_local_implementation import (
    Tier2ImplementationError,
    build_tier2_branch_name,
    default_git_runner,
    inspect_tier2_implementation_status,
    main,
    public_safe_summary,
    run_tier2_local_implementation_command,
    validate_draft_ticket_for_tier2,
)
from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state


def _valid_draft(
    *,
    draft_id: str = "draft-tier2-test",
    instruction_packet: str | None = None,
    expected_files_inferred: bool = True,
    extra: dict | None = None,
) -> dict:
    payload = {
        "schema_version": "instruction_packet_ticket_draft_v0.1.0",
        "id": draft_id,
        "status": "draft",
        "governor_verdict": "GO",
        "source_instruction_packet": instruction_packet,
        "title": "Tier 2 test draft",
        "expected_files": ["rge/modules/tier2_local_implementation.py"],
        "expected_files_inferred": expected_files_inferred,
        "test_plan": ["python -c \"import sys; sys.exit(0)\""],
        "rollback_plan": "Revert branch and delete batch.",
        "validation": {"passed": True, "reasons": []},
    }
    if extra:
        payload.update(extra)
    return payload


def _seed_draft(tmp_path: Path, **kwargs) -> Path:
    draft_dir = tmp_path / "data/operator/draft_tickets"
    draft_dir.mkdir(parents=True, exist_ok=True)
    path = draft_dir / "draft_tier2_test.json"
    path.write_text(json.dumps(_valid_draft(**kwargs)), encoding="utf-8")
    return path


class FakeGit:
    def __init__(self, *, branch: str = "main", changed: list[str] | None = None) -> None:
        self.branch = branch
        self.changed = changed or []
        self.commits: list[str] = []
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str], root: Path) -> subprocess.CompletedProcess[str]:
        self.calls.append(argv)
        cmd = " ".join(argv).lower()
        if "push" in cmd or "merge" in cmd:
            raise Tier2ImplementationError("forbidden")
        if argv[:3] == ["git", "diff", "--name-only"]:
            return subprocess.CompletedProcess(argv, 0, stdout="\n".join(self.changed), stderr="")
        if argv[:2] == ["git", "show-ref"]:
            return subprocess.CompletedProcess(argv, 1, stdout="", stderr="")
        if argv[:2] == ["git", "checkout"]:
            if "-b" in argv:
                self.branch = argv[-1]
            else:
                self.branch = argv[-1]
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
        if argv[:2] == ["git", "add"]:
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
        if argv[:2] == ["git", "commit"]:
            self.commits.append(" ".join(argv))
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
        if argv[:3] == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(argv, 0, stdout="deadbeefcafebabe", stderr="")
        if argv[:3] == ["git", "rev-list", "--count"]:
            return subprocess.CompletedProcess(argv, 0, stdout=str(len(self.commits)), stderr="")
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")


def _fake_test_runner(argv, cwd, env):  # noqa: ANN001
    return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")


def test_dry_run_does_not_modify_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    _seed_draft(tmp_path)
    fake = FakeGit(changed=["rge/modules/tier2_local_implementation.py"])
    payload, code = run_tier2_local_implementation_command(
        latest=True,
        dry_run=True,
        root=tmp_path,
        git_runner=fake,
    )
    assert code == 0
    assert payload["verdict"] == "GO"
    assert payload["dry_run"] is True
    assert not fake.commits
    assert not list(release_batch_dir(root=tmp_path).glob("*.json"))


def test_missing_draft_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    with pytest.raises(Tier2ImplementationError, match="no draft ticket"):
        run_tier2_local_implementation_command(latest=True, root=tmp_path)


def test_invalid_draft_verdict_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    _seed_draft(tmp_path, extra={"governor_verdict": "NO-GO"})
    payload, code = run_tier2_local_implementation_command(latest=True, dry_run=True, root=tmp_path)
    assert code == 1
    assert "NO-GO" in str(payload.get("stop_reason"))


def test_forbidden_action_in_draft_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    _seed_draft(tmp_path, extra={"test_plan": ["git push origin main"]})
    payload, code = run_tier2_local_implementation_command(latest=True, dry_run=True, root=tmp_path)
    assert code == 1


def test_circuit_breaker_open_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    _seed_draft(tmp_path)
    save_circuit_breaker(
        {
            "schema_version": "autonomy_circuit_breaker_v0.1.0",
            "status": "open",
            "latest_stop_reason": "fixture",
            "consecutive_synthesis_failures": 3,
            "consecutive_unsupported_outputs": 0,
        },
        root=tmp_path,
    )
    payload, code = run_tier2_local_implementation_command(latest=True, dry_run=True, root=tmp_path)
    assert code == 1
    assert "circuit breaker" in str(payload.get("stop_reason"))


def test_unsafe_dirty_tree_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    _seed_draft(tmp_path)
    dirty = WorkingTreeStatus(
        clean=False,
        branch="main",
        dirty_paths=[" M rge/modules/foo.py"],
    )
    with patch("rge.modules.tier2_local_implementation.inspect_working_tree", return_value=dirty):
        payload, code = run_tier2_local_implementation_command(latest=True, root=tmp_path)
    assert code == 1


def test_safe_branch_name_generated() -> None:
    name = build_tier2_branch_name("draft-from-syn-packet-fixture")
    assert name.startswith("phase-3/tier2-")
    assert " " not in name


def test_no_push_merge_publish_attempted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    with pytest.raises(Tier2ImplementationError):
        default_git_runner(["git", "push", "origin", "main"], tmp_path)


def test_failed_tests_block_commit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    _seed_draft(tmp_path, extra={"test_plan": ["python -c \"import sys; sys.exit(1)\""]})
    fake = FakeGit(changed=["rge/modules/tier2_local_implementation.py"])

    def fail_runner(argv, cwd, env):  # noqa: ANN001
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="fail")

    with patch(
        "rge.modules.tier2_local_implementation.inspect_working_tree",
        return_value=WorkingTreeStatus(clean=False, branch="main", dirty_paths=[]),
    ):
        payload, code = run_tier2_local_implementation_command(
            latest=True,
            root=tmp_path,
            git_runner=fake,
            command_runner=fail_runner,
        )
    assert code == 1
    assert not fake.commits


def test_passed_tests_allow_local_commit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    _seed_draft(tmp_path)
    fake = FakeGit(changed=["rge/modules/tier2_local_implementation.py"])
    with patch(
        "rge.modules.tier2_local_implementation.inspect_working_tree",
        return_value=WorkingTreeStatus(clean=False, branch="main", dirty_paths=[]),
    ), patch(
        "rge.modules.tier2_local_implementation.run_release_batch_assembler_command",
        return_value=({"batch_path": "data/operator/release_batches/batch.json"}, 0),
    ):
        payload, code = run_tier2_local_implementation_command(
            latest=True,
            root=tmp_path,
            git_runner=fake,
            command_runner=_fake_test_runner,
        )
    assert code == 0
    assert payload["commit_hash"] == "deadbeefcafebabe"
    assert fake.commits


def test_release_batch_refreshed_after_commit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    _seed_draft(tmp_path)
    fake = FakeGit(changed=["rge/modules/tier2_local_implementation.py"])
    with patch(
        "rge.modules.tier2_local_implementation.inspect_working_tree",
        return_value=WorkingTreeStatus(clean=False, branch="main", dirty_paths=[]),
    ), patch(
        "rge.modules.tier2_local_implementation.run_release_batch_assembler_command",
        return_value=({"batch_path": "data/operator/release_batches/batch_tier2.json"}, 0),
    ) as batch_mock:
        payload, code = run_tier2_local_implementation_command(
            latest=True,
            root=tmp_path,
            git_runner=fake,
            command_runner=_fake_test_runner,
        )
    assert code == 0
    assert payload["release_batch_path"] == "data/operator/release_batches/batch_tier2.json"
    batch_mock.assert_called_once()


def test_operator_loop_recommends_tier2_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    clean = seed_operator_neutral_plan_state(tmp_path)
    _seed_draft(tmp_path)
    plan = build_operator_plan(root=tmp_path, working_tree=clean)
    assert plan["next_recommended_action"]["action_id"] == "run_tier2_patch_staging"


def test_operator_loop_recommends_batch_after_impl_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    clean = seed_operator_neutral_plan_state(tmp_path)
    _seed_draft(tmp_path)
    branch = build_tier2_branch_name("draft-tier2-test")
    fake = FakeGit(branch=branch, changed=[])
    fake.commits.append("commit")
    with patch(
        "rge.modules.tier2_local_implementation.inspect_working_tree",
        return_value=WorkingTreeStatus(clean=True, branch=branch, dirty_paths=[]),
    ), patch(
        "rge.modules.tier2_local_implementation._branch_has_commits_ahead_of_main",
        return_value=True,
    ):
        plan = build_operator_plan(root=tmp_path, working_tree=clean)
    assert plan["next_recommended_action"]["action_id"] == "create_release_batch_candidate"


def test_public_safe_summary_passes_private_field_scan() -> None:
    from rge.modules.atlas_snapshot_builder import assert_no_private_fields

    summary = public_safe_summary(
        {
            "verdict": "GO",
            "draft_ticket_path": "data/operator/draft_tickets/x.json",
            "branch_name": "phase-3/tier2-draft",
        }
    )
    assert assert_no_private_fields({"tier2_summary": summary}) == []


def test_runner_blocks_when_public_summary_fails_private_field_scan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    _seed_draft(tmp_path)
    fake = FakeGit(changed=["rge/modules/tier2_local_implementation.py"])
    with patch(
        "rge.modules.tier2_local_implementation.inspect_working_tree",
        return_value=WorkingTreeStatus(clean=False, branch="main", dirty_paths=[]),
    ), patch(
        "rge.modules.tier2_local_implementation.run_release_batch_assembler_command",
        return_value=({"batch_path": "data/operator/release_batches/batch.json"}, 0),
    ), patch(
        "rge.modules.tier2_local_implementation.assert_no_private_fields",
        return_value=["blocked private field"],
    ):
        payload, code = run_tier2_local_implementation_command(
            latest=True,
            root=tmp_path,
            git_runner=fake,
            command_runner=_fake_test_runner,
        )
    assert code == 1
    assert payload["verdict"] == "NO-GO"
    assert "private-field scan" in str(payload.get("stop_reason"))


def test_validate_draft_invalid_instruction_packet(tmp_path: Path) -> None:
    draft = _valid_draft(instruction_packet="data/operator/instruction_packets/missing.md")
    reasons = validate_draft_ticket_for_tier2(
        draft,
        draft_path=tmp_path / "data/operator/draft_tickets/d.json",
        root=tmp_path,
    )
    assert any("instruction packet missing" in reason for reason in reasons)


def test_cli_dry_run(capsys: pytest.CaptureFixture[str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    _seed_draft(tmp_path)
    exit_code = main(["--latest", "--dry-run", "--root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["verdict"] == "GO"


def test_inspect_tier2_status_recommends_implementation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    _seed_draft(tmp_path)
    status = inspect_tier2_implementation_status(root=tmp_path)
    assert status["tier2_implementation_recommended"] is True
    release_status = inspect_release_governor_plan_status(root=tmp_path)
    assert release_status["tier2_implementation_recommended"] is True
