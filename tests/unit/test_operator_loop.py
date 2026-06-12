"""Unit tests for bounded operator loop runner."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from rge.modules.operator_loop import (
    WorkingTreeStatus,
    build_operator_plan,
    detect_documentation_git_drift,
    execute_safe_checks,
    pending_improvement_tickets,
)
from rge.modules.principal_audit_gate import QueueTicketRow


def _seed_queue(tmp_path: Path, body: str) -> None:
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "agent_reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(body, encoding="utf-8")


def test_next_ticket_ready_is_review_gated(tmp_path: Path) -> None:
    _seed_queue(
        tmp_path,
        """
| 40 | ticket-040 | done | prev | | |
| 41 | ticket-041 | ready | Operator loop | | |
""",
    )
    (tmp_path / "tickets" / "ticket-041.json").write_text(
        json.dumps(
            {
                "id": "ticket-041",
                "title": "Bounded operator loop runner",
                "risk_level": "low",
                "status": "ready",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "agent_reports" / "2026-06-12_pre-phase-2_principal-audit.md").write_text(
        "# audit", encoding="utf-8"
    )
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    action = plan["next_recommended_action"]

    assert plan["current_ticket"]["ticket_id"] == "ticket-041"
    assert plan["current_ticket"]["queue_status"] == "ready"
    assert action["action_id"] == "begin_ticket_implementation"
    assert action["gate"] == "review_gated"


def test_audit_overdue_is_review_gated(tmp_path: Path) -> None:
    _seed_queue(
        tmp_path,
        """
| 33 | ticket-033 | done | audit | | |
| 34 | ticket-034 | done | a | | |
| 35 | ticket-035 | done | b | | |
| 36 | ticket-036 | done | c | | |
""",
    )
    (tmp_path / "agent_reports" / "2026-06-01_pre-phase-2_principal-audit.md").write_text(
        "# old", encoding="utf-8"
    )
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    action = plan["next_recommended_action"]

    assert plan["audit_cadence"]["cadence_status"] == "overdue"
    assert action["action_id"] == "run_principal_audit"
    assert action["gate"] == "review_gated"


def test_medium_risk_pre_audit_required(tmp_path: Path) -> None:
    _seed_queue(
        tmp_path,
        """
| 40 | ticket-040 | done | prev | | |
| 41 | ticket-041 | proposed | Next medium | | |
""",
    )
    (tmp_path / "tickets" / "ticket-041.json").write_text(
        json.dumps({"id": "ticket-041", "risk_level": "medium", "status": "proposed"}),
        encoding="utf-8",
    )
    (tmp_path / "agent_reports" / "2026-06-12_pre-phase-2_principal-audit.md").write_text(
        "# audit", encoding="utf-8"
    )
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    action = plan["next_recommended_action"]

    assert plan["audit_cadence"]["implementation_gate"] == (
        "blocked_missing_pre_ticket_audit"
    )
    assert action["action_id"] == "complete_pre_ticket_audit"
    assert action["gate"] == "review_gated"


def test_pending_improvement_ticket_requires_human_confirmation(tmp_path: Path) -> None:
    _seed_queue(
        tmp_path,
        """
| 40 | ticket-040 | done | prev | | |
""",
    )
    (tmp_path / "agent_reports" / "2026-06-12_pre-phase-2_principal-audit.md").write_text(
        "# audit", encoding="utf-8"
    )
    artifact_dir = tmp_path / "data" / "tickets"
    artifact_dir.mkdir(parents=True)
    artifact = artifact_dir / "improvement_ticket_latest.json"
    artifact.write_text(
        json.dumps(
            [
                {
                    "title": "Improve claim extractor scope preservation",
                    "status": "draft",
                    "failure_reason": "overgeneralized_scope",
                    "risk_level": "medium",
                }
            ]
        ),
        encoding="utf-8",
    )
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(
        root=tmp_path,
        working_tree=clean_tree,
        improvement_artifact=artifact,
    )
    action = plan["next_recommended_action"]

    assert plan["pending_improvement_tickets"]["pending"] is True
    assert action["action_id"] == "review_improvement_ticket_promotion"
    assert action["gate"] == "review_gated"
    assert "promote-improvement-ticket" in action["commands"][0]["shell"]


def test_clean_safe_check_pass_when_no_open_ticket(tmp_path: Path) -> None:
    _seed_queue(
        tmp_path,
        """
| 40 | ticket-040 | done | prev | | |
""",
    )
    (tmp_path / "agent_reports" / "2026-06-12_pre-phase-2_principal-audit.md").write_text(
        "# audit", encoding="utf-8"
    )
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    action = plan["next_recommended_action"]

    assert action["action_id"] == "run_deterministic_verification"
    assert action["gate"] == "safe_autonomous"
    assert plan["execute_safe_eligible"] is True
    assert len(plan["safe_verification_commands"]) >= 3


def test_blocked_dirty_working_tree(tmp_path: Path) -> None:
    _seed_queue(
        tmp_path,
        """
| 40 | ticket-040 | done | prev | | |
""",
    )
    dirty_tree = WorkingTreeStatus(
        clean=False,
        branch="main",
        dirty_paths=[" M rge/modules/operator_loop.py"],
    )

    plan = build_operator_plan(root=tmp_path, working_tree=dirty_tree)
    action = plan["next_recommended_action"]

    assert action["action_id"] == "resolve_dirty_working_tree"
    assert action["gate"] == "blocked"
    assert plan["execute_safe_eligible"] is False


def test_execute_safe_blocked_on_dirty_tree(tmp_path: Path) -> None:
    _seed_queue(tmp_path, "| 40 | ticket-040 | done | prev | | |\n")
    dirty_tree = WorkingTreeStatus(clean=False, branch="main", dirty_paths=["?? foo"])

    result = execute_safe_checks(root=tmp_path, working_tree=dirty_tree)

    assert result["execution_status"] == "blocked"
    assert result["execution_results"] == []


def test_execute_safe_runs_allowlisted_commands(tmp_path: Path) -> None:
    _seed_queue(tmp_path, "| 40 | ticket-040 | done | prev | | |\n")
    (tmp_path / "agent_reports" / "2026-06-12_pre-phase-2_principal-audit.md").write_text(
        "# audit", encoding="utf-8"
    )
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    def fake_runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    result = execute_safe_checks(
        root=tmp_path,
        working_tree=clean_tree,
        command_runner=fake_runner,
    )

    assert result["execution_status"] == "pass"
    assert len(result["execution_results"]) == 3
    assert all(item["passed"] for item in result["execution_results"])


def test_pending_improvement_helper_detects_drafts(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "data" / "tickets"
    artifact_dir.mkdir(parents=True)
    artifact = artifact_dir / "improvement_ticket_latest.json"
    artifact.write_text(
        json.dumps([{"status": "draft", "title": "Draft ticket"}]),
        encoding="utf-8",
    )

    report = pending_improvement_tickets(root=tmp_path, artifact_path=artifact)

    assert report["pending"] is True
    assert report["draft_count"] == 1


def test_branch_mismatch_blocks_in_progress_ticket(tmp_path: Path) -> None:
    rows = [
        QueueTicketRow(order=41, ticket_id="ticket-041", status="in_progress"),
    ]
    tree = WorkingTreeStatus(
        clean=True,
        branch="phase-2/ticket-040-ci-golden-gate",
        dirty_paths=[],
    )
    violations = detect_documentation_git_drift(
        root=tmp_path,
        working_tree=tree,
        rows=rows,
        active_row=rows[0],
        active_ticket_json={"id": "ticket-041", "status": "in_progress"},
        latest_report_path=None,
    )
    assert any(item["kind"] == "branch_ticket_mismatch" for item in violations)


def test_report_branch_mismatch_blocks(tmp_path: Path) -> None:
    reports = tmp_path / "agent_reports"
    reports.mkdir(parents=True)
    report = reports / "2026-06-12_phase-2_ticket-041_operator-loop-runner.md"
    report.write_text(
        "Branch: `phase-2/ticket-041-operator-loop-runner`\n",
        encoding="utf-8",
    )
    tree = WorkingTreeStatus(
        clean=True,
        branch="phase-2/ticket-040-ci-golden-gate",
        dirty_paths=[],
    )
    violations = detect_documentation_git_drift(
        root=tmp_path,
        working_tree=tree,
        rows=[],
        active_row=None,
        active_ticket_json=None,
        latest_report_path=str(report.relative_to(tmp_path)),
    )
    assert any(item["kind"] == "report_branch_mismatch" for item in violations)


def test_done_without_commit_blocks(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    rows = [QueueTicketRow(order=41, ticket_id="ticket-041", status="done")]

    def empty_log(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    violations = detect_documentation_git_drift(
        root=tmp_path,
        working_tree=WorkingTreeStatus(clean=True, branch="main", dirty_paths=[]),
        rows=rows,
        active_row=None,
        active_ticket_json={"id": "ticket-041", "status": "done"},
        latest_report_path=None,
        log_runner=empty_log,
    )
    kinds = {item["kind"] for item in violations}
    assert "done_without_implementation_commit" in kinds
    assert "json_done_without_implementation_commit" in kinds


def test_multi_ticket_dirty_paths_block(tmp_path: Path) -> None:
    dirty_tree = WorkingTreeStatus(
        clean=False,
        branch="phase-2/ticket-041-operator-loop-runner",
        dirty_paths=[
            " M rge/modules/operator_loop.py",
            " M rge/modules/principal_audit_gate.py",
        ],
    )
    plan = build_operator_plan(root=tmp_path, working_tree=dirty_tree)
    kinds = {item["kind"] for item in plan["documentation_git_drift"]["violations"]}
    assert "multi_ticket_dirty_tree" in kinds
    assert plan["next_recommended_action"]["gate"] == "blocked"


def test_plan_mode_is_read_only(tmp_path: Path) -> None:
    _seed_queue(tmp_path, "| 40 | ticket-040 | done | prev | | |\n")
    queue_before = (tmp_path / "tickets" / "TICKET_QUEUE.md").read_text(encoding="utf-8")
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    build_operator_plan(root=tmp_path, working_tree=clean_tree)
    queue_after = (tmp_path / "tickets" / "TICKET_QUEUE.md").read_text(encoding="utf-8")

    assert queue_before == queue_after
