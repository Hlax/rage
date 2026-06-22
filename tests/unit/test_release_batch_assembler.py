"""Release batch assembler and follow-up integration tests."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.operator_autocycle import run_autocycle
from rge.modules.operator_loop import WorkingTreeStatus, execute_safe_checks
from rge.modules.release_batch_assembler import (
    assemble_release_batch_payload,
    main,
    run_release_batch_assembler_command,
)
from rge.modules.release_governor import (
    atlas_artifact_path,
    build_atlas_safe_release_governor_artifact,
    release_batch_dir,
    sync_public_release_governor_artifact,
)


def _seed_draft(tmp_path: Path) -> Path:
    draft_dir = tmp_path / "data/operator/draft_tickets"
    draft_dir.mkdir(parents=True)
    draft = {
        "id": "draft-from-assembler-test",
        "status": "draft",
        "title": "Assembler test draft",
        "source_instruction_packet": "data/operator/instruction_packets/test.md",
        "test_plan": ["python -m pytest tests/unit/test_release_governor.py -q"],
        "rollback_plan": "Delete batch and branch.",
    }
    path = draft_dir / "draft_fixture.json"
    path.write_text(json.dumps(draft), encoding="utf-8")
    return path


def _seed_reports(tmp_path: Path) -> None:
    reports = tmp_path / "agent_reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "2026-06-22_phase-3_ticket-999_test-report.md").write_text("# report", encoding="utf-8")
    (reports / "2026-06-22_phase-3_ticket-999_test-report-latest.json").write_text("{}", encoding="utf-8")
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        "| 999 | ticket-999 | done | test | | |\n",
        encoding="utf-8",
    )


def test_assemble_batch_from_latest_draft(tmp_path: Path) -> None:
    _seed_reports(tmp_path)
    draft_path = _seed_draft(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="phase-3/assembler-test", dirty_paths=[])
    with patch(
        "rge.modules.release_batch_assembler.inspect_working_tree",
        return_value=clean_tree,
    ), patch(
        "rge.modules.release_batch_assembler._git_value",
        side_effect=lambda argv, root: "abc123deadbeef" if "rev-parse" in argv else "",
    ):
        batch = assemble_release_batch_payload(latest=True, root=tmp_path)
    assert batch["draft_ticket_ids"] == ["draft-from-assembler-test"]
    assert batch["branch_names"] == ["phase-3/assembler-test"]
    assert batch["commit_hashes"] == ["abc123deadbeef"]
    assert batch["assembler_metadata"]["draft_ticket_path"].endswith("draft_fixture.json")
    assert draft_path.is_file()


def test_assembler_writes_batch_file(tmp_path: Path) -> None:
    _seed_reports(tmp_path)
    _seed_draft(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="phase-3/assembler-test", dirty_paths=[])
    with patch(
        "rge.modules.release_batch_assembler.inspect_working_tree",
        return_value=clean_tree,
    ), patch(
        "rge.modules.release_batch_assembler._git_value",
        return_value="abc123deadbeef",
    ):
        payload, exit_code = run_release_batch_assembler_command(latest=True, root=tmp_path)
    assert exit_code == 0
    assert payload["batch_path"]
    assert list(release_batch_dir(root=tmp_path).glob("*.json"))
    assert atlas_artifact_path(root=tmp_path).is_file()


def test_assembler_dry_run_writes_no_batch(tmp_path: Path) -> None:
    _seed_reports(tmp_path)
    _seed_draft(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="phase-3/assembler-test", dirty_paths=[])
    with patch(
        "rge.modules.release_batch_assembler.inspect_working_tree",
        return_value=clean_tree,
    ), patch(
        "rge.modules.release_batch_assembler._git_value",
        return_value="abc123deadbeef",
    ):
        payload, exit_code = run_release_batch_assembler_command(
            latest=True,
            dry_run=True,
            sync_public=False,
            root=tmp_path,
        )
    assert exit_code == 0
    assert payload["dry_run"] is True
    assert payload["batch_path"] is None
    assert not list(release_batch_dir(root=tmp_path).glob("*.json"))


def test_atlas_artifact_is_public_safe(tmp_path: Path) -> None:
    sync_public_release_governor_artifact(root=tmp_path)
    artifact = json.loads(atlas_artifact_path(root=tmp_path).read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "atlas_release_governor_v0.1.0"
    assert assert_no_private_fields({"artifact": artifact}) == []


def test_build_atlas_artifact_includes_tier_and_batch(tmp_path: Path) -> None:
    _seed_draft(tmp_path)
    batch_dir = release_batch_dir(root=tmp_path)
    batch_dir.mkdir(parents=True)
    (batch_dir / "batch_test.json").write_text(
        json.dumps({"schema_version": "release_batch_v0.1.0", "batch_id": "batch_test"}),
        encoding="utf-8",
    )
    artifact = build_atlas_safe_release_governor_artifact(root=tmp_path)
    assert artifact["autonomy_tier"]["effective_tier"] >= 0
    assert artifact["batch_status"] in {"available", "missing"}


def test_autocycle_execute_safe_syncs_release_dry_run(tmp_path: Path) -> None:
    from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state

    seed_operator_neutral_plan_state(tmp_path)
    draft_dir = tmp_path / "data/operator/draft_tickets"
    draft_dir.mkdir(parents=True)
    draft = {
        "id": "draft-from-syn-packet-fixture",
        "status": "draft",
        "title": "Assembler autocycle draft",
        "governor_verdict": "GO",
        "test_plan": ["python -m pytest tests/unit/test_release_governor.py -q"],
        "rollback_plan": "Delete batch and branch.",
    }
    (draft_dir / "draft_fixture.json").write_text(json.dumps(draft), encoding="utf-8")
    batch_dir = release_batch_dir(root=tmp_path)
    batch_dir.mkdir(parents=True)
    from rge.modules.release_governor import build_safe_fixture_batch

    _seed_reports(tmp_path)
    batch = build_safe_fixture_batch(batch_id="batch_autocycle_sync")
    (batch_dir / "batch_autocycle_sync.json").write_text(json.dumps(batch), encoding="utf-8")
    clean = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    def _fake_runner(argv, cwd, env):  # noqa: ANN001
        import subprocess

        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    with patch("rge.modules.operator_autocycle.inspect_working_tree", lambda root=None: clean), patch(
        "rge.modules.operator_loop.safe_verification_commands",
        return_value=[],
    ):
        result = run_autocycle(mode="execute-safe", root=tmp_path, max_cycles=1)

    cycle = result["cycles"][0]
    assert cycle.get("release_governor_status")
    assert cycle.get("release_governor_dry_run") is not None or "release_governor_dry_run" in cycle


def test_cli_wrapper_latest_draft(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    _seed_reports(tmp_path)
    _seed_draft(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="phase-3/assembler-test", dirty_paths=[])
    with patch(
        "rge.modules.release_batch_assembler.inspect_working_tree",
        return_value=clean_tree,
    ), patch(
        "rge.modules.release_batch_assembler._git_value",
        return_value="abc123deadbeef",
    ):
        exit_code = main(["--latest", "--dry-run", "--no-sync-public", "--root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["verdict"] == "GO"


def test_execute_safe_refresh_release_dry_run_when_batch_exists(tmp_path: Path) -> None:
    from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state

    clean_tree = seed_operator_neutral_plan_state(tmp_path)
    _seed_reports(tmp_path)
    from rge.modules.release_governor import build_safe_fixture_batch

    batch_dir = release_batch_dir(root=tmp_path)
    batch_dir.mkdir(parents=True)
    (batch_dir / "batch_exec_safe.json").write_text(
        json.dumps(build_safe_fixture_batch()),
        encoding="utf-8",
    )

    def _fake_runner(argv, cwd, env):  # noqa: ANN001
        import subprocess

        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    result = execute_safe_checks(
        root=tmp_path,
        working_tree=clean_tree,
        command_runner=_fake_runner,
    )
    assert result.get("release_governor_dry_run") is not None
    assert atlas_artifact_path(root=tmp_path).is_file()
