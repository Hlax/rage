"""Operator loop autonomous researcher loop hook (ticket-338)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import GOLDEN_MVP_TOPIC
from rge.modules.autonomous_researcher_loop import COMMAND
from rge.modules.operator_loop import (
    WorkingTreeStatus,
    autonomous_loop_safe_commands,
    build_operator_plan,
    execute_safe_checks,
    inspect_autonomous_researcher_loop_status,
    safe_verification_commands,
)




@pytest.fixture(autouse=True)
def _operator_autonomous_live_smoke_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    from tests.unit.operator_loop_helpers import apply_live_smoke_env_gates
    apply_live_smoke_env_gates(monkeypatch)

def _seed_done_only_queue(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "agent_reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        """
| 337 | ticket-337 | done | prev | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "tickets" / "ticket-337.json").write_text(
        json.dumps({"id": "ticket-337", "status": "done", "risk_level": "low"}),
        encoding="utf-8",
    )
    (tmp_path / "agent_reports" / "2026-06-18_phase-3_ticket-336_principal-audit-post-ticket-335.md").write_text(
        "# audit",
        encoding="utf-8",
    )
    from tests.unit.operator_loop_helpers import seed_public_site_preview_paths
    seed_public_site_preview_paths(tmp_path, include_source_health=True)


def _seed_open_ticket_queue(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "agent_reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        """
| 337 | ticket-337 | done | prev | | |
| 338 | ticket-338 | proposed | next | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "tickets" / "ticket-338.json").write_text(
        json.dumps(
            {
                "id": "ticket-338",
                "title": "Next ticket",
                "status": "proposed",
                "risk_level": "low",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "agent_reports" / "2026-06-18_phase-3_ticket-336_principal-audit-post-ticket-335.md").write_text(
        "# audit",
        encoding="utf-8",
    )


def test_plan_recommends_autonomous_loop_when_queue_clear(tmp_path: Path) -> None:
    _seed_done_only_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    action = plan["next_recommended_action"]
    status = plan["autonomous_researcher_loop_status"]

    assert action["action_id"] == "run_autonomous_researcher_loop"
    assert action["gate"] == "safe_autonomous"
    assert status["command"] == COMMAND
    assert status["mock_llm_only"] is True
    assert status["no_auto_promotion"] is True
    assert "autonomous-researcher-loop" in status["operator_commands"]["fixture_loop"]
    assert "--staged-spine" in status["operator_commands"]["staged_spine_loop"]
    assert GOLDEN_MVP_TOPIC in status["operator_commands"]["fixture_loop"]
    assert "promote-improvement-ticket" not in action["commands"][0]["shell"]


def test_autonomous_loop_deferred_when_open_ticket_exists(tmp_path: Path) -> None:
    _seed_open_ticket_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)

    assert plan["next_recommended_action"]["action_id"] == "begin_ticket_implementation"


def test_execute_safe_runs_autonomous_loop_fixture_proof(tmp_path: Path) -> None:
    _seed_done_only_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    captured_argv: list[list[str]] = []

    def fake_runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured_argv.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    result = execute_safe_checks(
        root=tmp_path,
        working_tree=clean_tree,
        command_runner=fake_runner,
    )

    assert result["execution_status"] == "pass"
    assert result["next_recommended_action"]["action_id"] == "run_autonomous_researcher_loop"
    assert len(result["execution_results"]) == len(safe_verification_commands(tmp_path)) + 1
    autonomous = next(
        item for item in result["execution_results"]
        if item["name"] == "autonomous_loop_fixture_proof"
    )
    assert autonomous["passed"] is True
    assert "autonomous-researcher-loop" in " ".join(captured_argv[-1])


def test_execute_safe_autonomous_loop_real_fixture_proof(tmp_path: Path) -> None:
    _seed_done_only_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    with patch(
        "rge.modules.operator_loop.safe_verification_commands",
        return_value=[],
    ):
        result = execute_safe_checks(root=tmp_path, working_tree=clean_tree)

    assert result["execution_status"] == "pass"
    loop_result = next(
        item for item in result["execution_results"]
        if item["name"] == "autonomous_loop_fixture_proof"
    )
    assert loop_result["passed"] is True
    artifact = tmp_path / "data" / "reports" / "operator_autonomous_loop" / "autonomous_loop_report.json"
    assert artifact.is_file()
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["status"] == "completed"
    assert payload["research_path"] == "fixture_mode"


def test_inspect_autonomous_researcher_loop_status_paths(tmp_path: Path) -> None:
    status = inspect_autonomous_researcher_loop_status(root=tmp_path)

    assert status["scratch_db_path"] == "data/db/operator_autonomous_loop_scratch.sqlite"
    assert status["artifact_dir"] == "data/reports/operator_autonomous_loop"
    assert status["staging_dir"] == "data/sources/staged/operator_autonomous_loop"


def test_autonomous_loop_safe_commands_use_mock_env(tmp_path: Path) -> None:
    commands = autonomous_loop_safe_commands(tmp_path)

    assert len(commands) == 1
    assert commands[0]["name"] == "autonomous_loop_fixture_proof"
    assert commands[0]["env"]["RGE_LLM_MODE"] == "mock"
    assert commands[0]["env"]["RGE_ALLOW_LIVE_LLM"] == "0"
