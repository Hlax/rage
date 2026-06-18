"""Operator loop autonomous loop scratch artifact inspection (ticket-339)."""

from __future__ import annotations

import json
from pathlib import Path

from rge.modules.operator_loop import (
    WorkingTreeStatus,
    _AUTONOMOUS_LOOP_BASE_REASON,
    build_operator_plan,
    inspect_autonomous_loop_scratch_artifact,
)


def _seed_done_only_queue(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "agent_reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        """
| 340 | ticket-340 | done | audit | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "tickets" / "ticket-340.json").write_text(
        json.dumps({"id": "ticket-340", "status": "done", "risk_level": "low"}),
        encoding="utf-8",
    )
    (tmp_path / "agent_reports" / "2026-06-18_phase-3_ticket-340_principal-audit-post-ticket-338.md").write_text(
        "# audit",
        encoding="utf-8",
    )


def _write_loop_report(
    artifact_dir: Path,
    *,
    run_status: str = "completed",
    verdict: str = "GO",
    weakest: str = "weak_claim_extraction",
    weakest_score: int = 90,
) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    report_path = artifact_dir / "autonomous_loop_report.json"
    report_path.write_text(
        json.dumps(
            {
                "status": run_status,
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
    return report_path


def test_scratch_inspection_not_run_when_report_missing(tmp_path: Path) -> None:
    status = inspect_autonomous_loop_scratch_artifact(root=tmp_path)

    assert status["status"] == "not_run"
    assert status["loop_report_exists"] is False
    assert status["research_quality_verdict"] is None
    assert status["weakest_dimension"] is None
    assert "not found" in (status["error"] or "")


def test_scratch_inspection_surfaces_quality_verdict(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "data" / "reports" / "operator_autonomous_loop"
    _write_loop_report(artifact_dir, verdict="GO", weakest="weak_run_lineage", weakest_score=85)

    status = inspect_autonomous_loop_scratch_artifact(root=tmp_path)

    assert status["status"] == "ok"
    assert status["loop_report_exists"] is True
    assert status["research_quality_verdict"] == "GO"
    assert status["weakest_dimension"] == "weak_run_lineage"
    assert status["weakest_dimension_score"] == 85
    assert status["evaluated_after_ticket_seeding"] is True
    assert status["research_path"] == "fixture_mode"


def test_scratch_inspection_invalid_json(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "data" / "reports" / "operator_autonomous_loop"
    artifact_dir.mkdir(parents=True)
    (artifact_dir / "autonomous_loop_report.json").write_text("{bad", encoding="utf-8")

    status = inspect_autonomous_loop_scratch_artifact(root=tmp_path)

    assert status["status"] == "invalid"
    assert status["error"]


def test_plan_includes_scratch_status_when_report_exists(tmp_path: Path) -> None:
    _seed_done_only_queue(tmp_path)
    artifact_dir = tmp_path / "data" / "reports" / "operator_autonomous_loop"
    _write_loop_report(artifact_dir, verdict="PARTIAL", weakest="weak_ticket_generation", weakest_score=70)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    scratch = plan["autonomous_loop_scratch_status"]

    assert scratch["status"] == "ok"
    assert scratch["research_quality_verdict"] == "PARTIAL"
    assert scratch["weakest_dimension"] == "weak_ticket_generation"
    assert plan["next_recommended_action"]["action_id"] == "run_autonomous_researcher_loop"
    reason = plan["next_recommended_action"]["reason"]
    assert "PARTIAL" in reason
    assert "weak_ticket_generation" in reason
    assert "Last scratch loop quality" in reason


def test_recommended_action_reason_unchanged_when_scratch_not_run(tmp_path: Path) -> None:
    _seed_done_only_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)

    assert plan["next_recommended_action"]["reason"] == _AUTONOMOUS_LOOP_BASE_REASON
    assert "Last scratch loop quality" not in plan["next_recommended_action"]["reason"]


def test_plan_includes_not_run_scratch_status_without_failing(tmp_path: Path) -> None:
    _seed_done_only_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    scratch = plan["autonomous_loop_scratch_status"]

    assert scratch["status"] == "not_run"
    assert scratch["research_quality_verdict"] is None
    assert plan["report_type"] == "operator_loop_status"
    assert plan["next_recommended_action"]["gate"] == "safe_autonomous"
