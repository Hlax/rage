"""Operator autocycle autonomous loop scratch status passthrough (ticket-342)."""

from __future__ import annotations

import json
from pathlib import Path

from rge.modules.operator_autocycle import evaluate_autocycle_cycle, run_autocycle
from rge.modules.operator_loop import WorkingTreeStatus


def _seed_done_only_queue(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "agent_reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        """
| 341 | ticket-341 | done | prev | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "tickets" / "ticket-341.json").write_text(
        json.dumps({"id": "ticket-341", "status": "done", "risk_level": "low"}),
        encoding="utf-8",
    )
    (
        tmp_path
        / "agent_reports"
        / "2026-06-18_phase-3_ticket-340_principal-audit-post-ticket-338.md"
    ).write_text("# audit", encoding="utf-8")


def _write_loop_report(
    artifact_dir: Path,
    *,
    verdict: str = "PARTIAL",
    weakest: str = "weak_ticket_generation",
    weakest_score: int = 70,
) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "autonomous_loop_report.json").write_text(
        json.dumps(
            {
                "status": "completed",
                "research_path": "fixture_mode",
                "research_quality": {
                    "research_quality_verdict": verdict,
                    "weakest_dimension": weakest,
                    "weakest_dimension_label": weakest.replace("_", " "),
                    "weakest_dimension_score": weakest_score,
                    "evaluated_after_ticket_seeding": True,
                },
            }
        ),
        encoding="utf-8",
    )


def test_autocycle_cycle_includes_scratch_status_when_report_exists(
    tmp_path: Path,
) -> None:
    _seed_done_only_queue(tmp_path)
    artifact_dir = tmp_path / "data" / "reports" / "operator_autonomous_loop"
    _write_loop_report(artifact_dir, verdict="PARTIAL", weakest="weak_ticket_generation")
    clean = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    evaluation = evaluate_autocycle_cycle(root=tmp_path, working_tree=clean)
    scratch = evaluation["autonomous_loop_scratch_status"]

    assert scratch["status"] == "ok"
    assert scratch["research_quality_verdict"] == "PARTIAL"
    assert scratch["weakest_dimension"] == "weak_ticket_generation"
    assert evaluation["recommended_action"]["action_id"] == "run_autonomous_researcher_loop"


def test_autocycle_cycle_reports_not_run_when_report_missing(tmp_path: Path) -> None:
    _seed_done_only_queue(tmp_path)
    clean = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    evaluation = evaluate_autocycle_cycle(root=tmp_path, working_tree=clean)
    scratch = evaluation["autonomous_loop_scratch_status"]

    assert scratch["status"] == "not_run"
    assert scratch["research_quality_verdict"] is None
    assert scratch["weakest_dimension"] is None


def test_run_autocycle_payload_includes_autonomous_loop_scratch_status(
    tmp_path: Path,
) -> None:
    _seed_done_only_queue(tmp_path)
    artifact_dir = tmp_path / "data" / "reports" / "operator_autonomous_loop"
    _write_loop_report(artifact_dir, verdict="GO", weakest="weak_run_lineage", weakest_score=85)

    payload = run_autocycle(mode="plan", max_cycles=1, root=tmp_path)
    scratch = payload["autonomous_loop_scratch_status"]

    assert scratch["status"] == "ok"
    assert scratch["research_quality_verdict"] == "GO"
    assert scratch["weakest_dimension"] == "weak_run_lineage"
    assert payload["cycles"][0]["autonomous_loop_scratch_status"] == scratch
