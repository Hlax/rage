"""Unit tests for bounded operator autocycle planner."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from rge.modules.operator_autocycle import (
    MAX_CYCLES_HARD_CAP,
    _clamp_max_cycles,
    evaluate_autocycle_cycle,
    run_autocycle,
)
from rge.modules.operator_loop import WorkingTreeStatus


def _seed_queue(tmp_path: Path, body: str) -> None:
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "agent_reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(body, encoding="utf-8")


def _seed_audit_report(tmp_path: Path) -> None:
    (
        tmp_path
        / "agent_reports"
        / "2026-06-15_principal-audit-post-ticket-164.md"
    ).write_text("# audit", encoding="utf-8")


def test_clamp_max_cycles_hard_cap() -> None:
    assert _clamp_max_cycles(0) == 1
    assert _clamp_max_cycles(99) == MAX_CYCLES_HARD_CAP


def test_plan_mode_stops_on_dirty_tree(tmp_path: Path) -> None:
    _seed_queue(
        tmp_path,
        """
| 166 | ticket-166 | proposed | Autocycle | | |
""",
    )
    dirty = WorkingTreeStatus(clean=False, branch="main", dirty_paths=[" M README.md"])
    evaluation = evaluate_autocycle_cycle(root=tmp_path, working_tree=dirty)
    assert evaluation["status"] == "stopped"
    assert evaluation["stop_reason"] == "working_tree_dirty"


def test_plan_mode_stops_on_medium_risk_without_pre_ticket_audit(tmp_path: Path) -> None:
    _seed_queue(
        tmp_path,
        """
| 166 | ticket-166 | proposed | Safe autocycle | | |
""",
    )
    _seed_audit_report(tmp_path)
    (tmp_path / "tickets" / "ticket-166.json").write_text(
        json.dumps(
            {
                "id": "ticket-166",
                "title": "Safe autocycle command",
                "risk_level": "medium",
                "status": "proposed",
                "pre_ticket_audit_required": True,
            }
        ),
        encoding="utf-8",
    )
    clean = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    evaluation = evaluate_autocycle_cycle(root=tmp_path, working_tree=clean)
    assert evaluation["status"] == "stopped"
    assert "pre_ticket_audit_missing" in evaluation["stop_reason"]


def test_allow_medium_reports_run_next_ticket_blocked(tmp_path: Path, monkeypatch) -> None:
    _seed_queue(
        tmp_path,
        """
| 165 | ticket-165 | done | README maturity | | |
| 166 | ticket-166 | proposed | Safe autocycle | | |
""",
    )
    _seed_audit_report(tmp_path)
    (
        tmp_path
        / "agent_reports"
        / "2026-06-15_pre-ticket-166_safe-autocycle-audit.md"
    ).write_text("# pre-ticket GO", encoding="utf-8")
    (tmp_path / "tickets" / "ticket-166.json").write_text(
        json.dumps(
            {
                "id": "ticket-166",
                "title": "Safe autocycle command for audit loop",
                "risk_level": "medium",
                "status": "proposed",
                "affected_modules": ["rge/modules/operator_autocycle.py"],
            }
        ),
        encoding="utf-8",
    )

    def _fake_commit_check(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, stdout="", stderr="")

    monkeypatch.setattr(
        "rge.modules.operator_loop.ticket_has_implementation_commit",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        "rge.modules.operator_loop.run_captured",
        lambda argv, cwd: _fake_commit_check(argv, cwd),
    )

    clean = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    evaluation = evaluate_autocycle_cycle(
        root=tmp_path,
        working_tree=clean,
        allow_medium=True,
        allow_docs_streak=True,
    )
    assert evaluation["status"] == "stopped"
    assert evaluation["run_next_ticket_allowed"] is True
    assert evaluation["next_command"] == "/rge-run-next-ticket"


def test_plan_mode_stops_on_docs_only_streak(tmp_path: Path, monkeypatch) -> None:
    _seed_queue(
        tmp_path,
        """
| 163 | ticket-163 | done | README maturity relabel prior | | |
| 165 | ticket-165 | proposed | README maturity table Phase 3 staged mock spine status | | |
""",
    )
    _seed_audit_report(tmp_path)
    (tmp_path / "tickets" / "ticket-165.json").write_text(
        json.dumps(
            {
                "id": "ticket-165",
                "title": "README maturity table Phase 3 staged mock spine status",
                "risk_level": "low",
                "status": "proposed",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "rge.modules.operator_loop.ticket_has_implementation_commit",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        "rge.modules.operator_loop.run_captured",
        lambda argv, cwd: subprocess.CompletedProcess(argv, 0, stdout="", stderr=""),
    )

    clean = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    evaluation = evaluate_autocycle_cycle(root=tmp_path, working_tree=clean)
    assert evaluation["status"] == "stopped"
    assert "docs_only_streak" in evaluation["stop_reason"]


def test_run_autocycle_respects_max_cycles_cap(tmp_path: Path, monkeypatch) -> None:
    _seed_queue(tmp_path, "| 166 | ticket-166 | proposed | Autocycle | | |\n")
    dirty = WorkingTreeStatus(clean=False, branch="main", dirty_paths=[" M x"])

    monkeypatch.setattr(
        "rge.modules.operator_autocycle.inspect_working_tree",
        lambda root=None: dirty,
    )
    payload = run_autocycle(mode="plan", max_cycles=25, root=tmp_path)
    assert payload["cycles_requested"] == MAX_CYCLES_HARD_CAP
    assert payload["cycles_completed"] == 1
    assert payload["status"] == "stopped"


def test_plan_mode_is_read_only_on_real_repo() -> None:
    payload = run_autocycle(mode="plan", max_cycles=1)
    assert payload["report_type"] == "operator_autocycle_status"
    assert payload["cycles_completed"] >= 1
    assert payload["forbidden_actions"]
