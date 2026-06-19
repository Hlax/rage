"""Operator autocycle autonomous loop improvement status passthrough (ticket-349)."""

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
| 348 | ticket-348 | done | prev | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "tickets" / "ticket-348.json").write_text(
        json.dumps({"id": "ticket-348", "status": "done", "risk_level": "low"}),
        encoding="utf-8",
    )
    (
        tmp_path
        / "agent_reports"
        / "2026-06-18_principal-audit-post-ticket-346.md"
    ).write_text("# audit", encoding="utf-8")


def _write_loop_improvement_artifacts(
    artifact_dir: Path,
    *,
    recommended_id: str = "ticket-350",
) -> None:
    ticket_dir = artifact_dir / "tickets"
    ticket_dir.mkdir(parents=True, exist_ok=True)
    improvement_path = ticket_dir / "improvement_ticket_latest.json"
    recommended_path = artifact_dir / "recommended_improvement_ticket.json"
    improvement_path.write_text(
        json.dumps(
            [
                {
                    "title": "Strengthen quality-driven ticket seeding",
                    "status": "draft",
                    "failure_reason": "weak_ticket_generation",
                    "risk_level": "low",
                    "problem": "Quality eval flagged weak ticket generation.",
                    "acceptance_criteria": ["Seed actionable draft when dimension weak."],
                }
            ]
        ),
        encoding="utf-8",
    )
    recommended_path.write_text(
        json.dumps(
            {
                "id": recommended_id,
                "title": "Follow-on from autonomous loop",
                "status": "proposed",
                "source_weakness": "weak_ticket_generation",
                "problem": "Address weakest research quality dimension.",
                "acceptance_criteria": ["Close quality gap."],
            }
        ),
        encoding="utf-8",
    )
    loop_report_path = artifact_dir / "autonomous_loop_report.json"
    loop_report_path.write_text(
        json.dumps(
            {
                "status": "completed",
                "research_path": "fixture_mode",
                "recommended_improvement_ticket_id": recommended_id,
                "research_quality": {
                    "research_quality_verdict": "GO",
                    "weakest_dimension": "weak_claim_extraction",
                    "weakest_dimension_score": 90,
                },
                "artifacts": {
                    "improvement_tickets": str(improvement_path),
                    "recommended_improvement_ticket": str(recommended_path),
                    "loop_report": str(loop_report_path),
                },
                "run_summary": {
                    "quality_driven_ticket_ids": ["improvement_quality_001"],
                },
            }
        ),
        encoding="utf-8",
    )


def test_autocycle_cycle_includes_improvement_status_when_artifacts_exist(
    tmp_path: Path,
) -> None:
    _seed_done_only_queue(tmp_path)
    artifact_dir = tmp_path / "data" / "reports" / "operator_autonomous_loop"
    _write_loop_improvement_artifacts(artifact_dir, recommended_id="ticket-350")
    clean = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    evaluation = evaluate_autocycle_cycle(root=tmp_path, working_tree=clean)
    improvement = evaluation["autonomous_loop_improvement_status"]

    assert improvement["status"] == "ok"
    assert improvement["recommended_ticket_id"] == "ticket-350"
    assert improvement["draft_count"] == 1
    assert improvement["pending"] is True


def test_autocycle_cycle_reports_not_run_improvement_when_artifacts_missing(
    tmp_path: Path,
) -> None:
    _seed_done_only_queue(tmp_path)
    clean = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    evaluation = evaluate_autocycle_cycle(root=tmp_path, working_tree=clean)
    improvement = evaluation["autonomous_loop_improvement_status"]

    assert improvement["status"] == "not_run"
    assert improvement["recommended_ticket_id"] is None
    assert improvement["draft_count"] == 0


def test_run_autocycle_payload_includes_autonomous_loop_improvement_status(
    tmp_path: Path,
) -> None:
    _seed_done_only_queue(tmp_path)
    artifact_dir = tmp_path / "data" / "reports" / "operator_autonomous_loop"
    _write_loop_improvement_artifacts(artifact_dir, recommended_id="ticket-350")

    payload = run_autocycle(mode="plan", max_cycles=1, root=tmp_path)
    improvement = payload["autonomous_loop_improvement_status"]

    assert improvement["status"] == "ok"
    assert improvement["recommended_ticket_id"] == "ticket-350"
    assert improvement["draft_count"] == 1
    assert payload["cycles"][0]["autonomous_loop_improvement_status"] == improvement
