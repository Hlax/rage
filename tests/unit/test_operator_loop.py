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
    is_audit_only_ticket,
    pending_improvement_tickets,
    resolve_npm_executable,
    safe_verification_commands,
    ticket_has_implementation_commit,
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
                    "title": "Improve concept mapping validation",
                    "status": "draft",
                    "failure_reason": "weak_concept_mapping",
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


def test_pending_improvement_skips_golden_covered_drafts(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "data" / "tickets"
    artifact_dir.mkdir(parents=True)
    artifact = artifact_dir / "improvement_ticket_latest.json"
    artifact.write_text(
        json.dumps(
            [
                {
                    "status": "draft",
                    "title": "Improve claim quote span validation",
                    "evidence": [
                        "run_report:run_golden_fixture_mvp:missing_quote_span_count=1"
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    report = pending_improvement_tickets(root=tmp_path, artifact_path=artifact)

    assert report["pending"] is False
    assert report["draft_count"] == 0


def test_pending_improvement_skips_golden_covered_overgeneralized_drafts(
    tmp_path: Path,
) -> None:
    artifact_dir = tmp_path / "data" / "tickets"
    artifact_dir.mkdir(parents=True)
    artifact = artifact_dir / "improvement_ticket_latest.json"
    artifact.write_text(
        json.dumps(
            [
                {
                    "status": "draft",
                    "title": "Improve claim extractor scope preservation",
                    "evidence": [
                        "run_report:run_golden_fixture_mvp:overgeneralized_scope_count=1"
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    report = pending_improvement_tickets(root=tmp_path, artifact_path=artifact)

    assert report["pending"] is False
    assert report["draft_count"] == 0


def test_audit_only_ticket_skips_done_without_commit_check(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir(parents=True)
    (tmp_path / "tickets" / "ticket-033.json").write_text(
        json.dumps(
            {
                "id": "ticket-033",
                "title": "Pre-phase-2 principal audit checkpoint",
                "affected_modules": [],
                "expected_files": ["agent_reports/2026-06-12_pre-phase-2_principal-audit.md"],
                "status": "done",
            }
        ),
        encoding="utf-8",
    )
    assert is_audit_only_ticket("ticket-033", root=tmp_path) is True

    (tmp_path / ".git").mkdir()
    rows = [QueueTicketRow(order=33, ticket_id="ticket-033", status="done")]

    def empty_log(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    violations = detect_documentation_git_drift(
        root=tmp_path,
        working_tree=WorkingTreeStatus(clean=True, branch="main", dirty_paths=[]),
        rows=rows,
        active_row=None,
        active_ticket_json=None,
        latest_report_path=None,
        log_runner=empty_log,
    )
    assert not any(
        item["kind"] == "done_without_implementation_commit" for item in violations
    )


def test_merged_ticket_report_branch_allowed_on_main(tmp_path: Path) -> None:
    reports = tmp_path / "agent_reports"
    reports.mkdir(parents=True)
    report = reports / "2026-06-12_phase-2_ticket-041_operator-loop-runner.md"
    report.write_text(
        "Branch: `phase-2/ticket-041-operator-loop-runner`\n",
        encoding="utf-8",
    )
    (tmp_path / ".git").mkdir()

    def log_with_commit(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        if "--grep=ticket-041" in " ".join(argv):
            return subprocess.CompletedProcess(
                argv, 0, stdout="80a12a6 Implement ticket-041\n", stderr=""
            )
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    violations = detect_documentation_git_drift(
        root=tmp_path,
        working_tree=WorkingTreeStatus(
            clean=True,
            branch="main",
            dirty_paths=[],
        ),
        rows=[],
        active_row=None,
        active_ticket_json=None,
        latest_report_path=str(report.relative_to(tmp_path)),
        log_runner=log_with_commit,
    )
    assert not any(item["kind"] == "report_branch_mismatch" for item in violations)


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


def test_ticket_json_on_main_satisfies_implementation_check(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    tickets = tmp_path / "tickets"
    tickets.mkdir(parents=True)
    (tickets / "ticket-043.json").write_text(
        json.dumps({"id": "ticket-043", "status": "done"}),
        encoding="utf-8",
    )

    def log_without_message_grep(
        argv: list[str], cwd: Path
    ) -> subprocess.CompletedProcess[str]:
        joined = " ".join(argv)
        if "--grep=ticket-043" in joined:
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
        if "-- tickets/ticket-043.json" in joined or joined.endswith(
            "tickets/ticket-043.json"
        ):
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout="cc1c17c Extend safety auditor to validate data exports\n",
                stderr="",
            )
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    assert ticket_has_implementation_commit(
        "ticket-043",
        root=tmp_path,
        log_runner=log_without_message_grep,
    )


def test_done_ticket_with_json_on_main_not_flagged(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    tickets = tmp_path / "tickets"
    tickets.mkdir(parents=True)
    (tickets / "ticket-043.json").write_text(
        json.dumps({"id": "ticket-043", "status": "done"}),
        encoding="utf-8",
    )
    rows = [QueueTicketRow(order=43, ticket_id="ticket-043", status="done")]

    def log_without_message_grep(
        argv: list[str], cwd: Path
    ) -> subprocess.CompletedProcess[str]:
        joined = " ".join(argv)
        if "--grep=ticket-043" in joined:
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
        if "tickets/ticket-043.json" in joined:
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout="cc1c17c Extend safety auditor to validate data exports\n",
                stderr="",
            )
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    violations = detect_documentation_git_drift(
        root=tmp_path,
        working_tree=WorkingTreeStatus(clean=True, branch="main", dirty_paths=[]),
        rows=rows,
        active_row=None,
        active_ticket_json={"id": "ticket-043", "status": "done"},
        latest_report_path=None,
        log_runner=log_without_message_grep,
    )
    assert not any(
        item["kind"] == "done_without_implementation_commit" for item in violations
    )


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


def test_operator_loop_uses_corrected_principal_audit_cadence(tmp_path: Path) -> None:
    _seed_queue(
        tmp_path,
        """
| 42 | ticket-042 | done | prev | | |
| 43 | ticket-043 | done | latest | | |
| 44 | ticket-044 | proposed | next | | |
""",
    )
    (tmp_path / "agent_reports" / "2026-06-12_principal-audit-post-ticket-042.md").write_text(
        "# audit", encoding="utf-8"
    )
    (tmp_path / "tickets" / "ticket-044.json").write_text(
        json.dumps({"id": "ticket-044", "risk_level": "low", "status": "proposed"}),
        encoding="utf-8",
    )
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)

    assert plan["audit_cadence"]["cadence_status"] == "satisfied"
    assert plan["audit_cadence"]["done_tickets_since_latest_checkpoint"] == 1
    assert plan["next_recommended_action"]["action_id"] != "run_principal_audit"


def test_plan_mode_is_read_only(tmp_path: Path) -> None:
    _seed_queue(tmp_path, "| 40 | ticket-040 | done | prev | | |\n")
    queue_before = (tmp_path / "tickets" / "TICKET_QUEUE.md").read_text(encoding="utf-8")
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    build_operator_plan(root=tmp_path, working_tree=clean_tree)
    queue_after = (tmp_path / "tickets" / "TICKET_QUEUE.md").read_text(encoding="utf-8")

    assert queue_before == queue_after


def test_safe_verification_commands_use_resolved_npm_executable(
    monkeypatch, tmp_path: Path
) -> None:
    site = tmp_path / "apps" / "public-site"
    site.mkdir(parents=True)
    (site / "package.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "rge.modules.operator_loop.resolve_npm_executable",
        lambda: r"C:\Program Files\nodejs\npm.CMD",
    )

    commands = safe_verification_commands(tmp_path)
    site_build = [item for item in commands if item["name"] == "public_site_build"]
    assert len(site_build) == 1
    assert site_build[0]["argv"] == [
        r"C:\Program Files\nodejs\npm.CMD",
        "run",
        "build",
    ]


def test_safe_verification_commands_omit_site_build_when_npm_missing(
    monkeypatch, tmp_path: Path
) -> None:
    site = tmp_path / "apps" / "public-site"
    site.mkdir(parents=True)
    (site / "package.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "rge.modules.operator_loop.resolve_npm_executable",
        lambda: None,
    )

    commands = safe_verification_commands(tmp_path)
    assert all(item["name"] != "public_site_build" for item in commands)


def test_resolved_npm_executable_runs_subprocess() -> None:
    npm_executable = resolve_npm_executable()
    if npm_executable is None:
        import pytest

        pytest.skip("npm not on PATH in this environment")

    completed = subprocess.run(
        [npm_executable, "--version"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    assert completed.returncode == 0
