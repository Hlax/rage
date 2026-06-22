"""Operator loop autonomous loop improvement artifact inspection (ticket-348)."""

from __future__ import annotations

import pytest
import json
from pathlib import Path

from rge.modules.operator_loop import (
    WorkingTreeStatus,
    _autonomous_loop_recommended_reason,
    build_operator_plan,
    inspect_autonomous_loop_improvement_artifact,
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
| 347 | ticket-347 | done | prev | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "tickets" / "ticket-347.json").write_text(
        json.dumps({"id": "ticket-347", "status": "done", "risk_level": "low"}),
        encoding="utf-8",
    )
    (
        tmp_path
        / "agent_reports"
        / "2026-06-18_principal-audit-post-ticket-352.md"
    ).write_text("# audit", encoding="utf-8")
    from tests.unit.operator_loop_helpers import (
        seed_public_site_preview_paths,
        seed_synthesis_human_review_neutral_artifact,
    )
    seed_public_site_preview_paths(tmp_path, include_source_health=True)
    seed_synthesis_human_review_neutral_artifact(tmp_path)


def _write_loop_improvement_artifacts(
    artifact_dir: Path,
    *,
    recommended_id: str = "ticket-349",
    weakness: str = "weak_ticket_generation",
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
                    "failure_reason": weakness,
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
                "source_weakness": weakness,
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


def test_improvement_inspection_not_run_when_loop_report_missing(tmp_path: Path) -> None:
    status = inspect_autonomous_loop_improvement_artifact(root=tmp_path)

    assert status["status"] == "not_run"
    assert status["loop_report_exists"] is False
    assert status["draft_count"] == 0
    assert "not found" in (status["error"] or "")


def test_improvement_inspection_surfaces_drafts_when_loop_report_exists(
    tmp_path: Path,
) -> None:
    artifact_dir = tmp_path / "data" / "reports" / "operator_autonomous_loop"
    _write_loop_improvement_artifacts(artifact_dir, recommended_id="ticket-349")

    status = inspect_autonomous_loop_improvement_artifact(root=tmp_path)

    assert status["status"] == "ok"
    assert status["improvement_tickets_exists"] is True
    assert status["recommended_improvement_ticket_exists"] is True
    assert status["recommended_ticket_id"] == "ticket-349"
    assert status["source_weakness"] == "weak_ticket_generation"
    assert status["quality_driven_ticket_ids"] == ["improvement_quality_001"]
    assert status["draft_count"] == 1
    assert status["pending"] is True
    assert status["draft_tickets"][0]["failure_reason"] == "weak_ticket_generation"


def test_plan_includes_improvement_status_without_failing(tmp_path: Path) -> None:
    _seed_done_only_queue(tmp_path)
    artifact_dir = tmp_path / "data" / "reports" / "operator_autonomous_loop"
    _write_loop_improvement_artifacts(artifact_dir)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    improvement = plan["autonomous_loop_improvement_status"]

    assert plan["report_type"] == "operator_loop_status"
    assert improvement["status"] == "ok"
    assert improvement["recommended_ticket_title"] == "Follow-on from autonomous loop"
    assert plan["autonomous_loop_scratch_status"]["status"] == "ok"


def test_plan_includes_not_run_improvement_status_when_artifacts_missing(
    tmp_path: Path,
) -> None:
    _seed_done_only_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    improvement = plan["autonomous_loop_improvement_status"]

    assert improvement["status"] == "not_run"
    assert improvement["recommended_ticket_id"] is None
    assert plan["next_recommended_action"]["gate"] == "safe_autonomous"


def test_recommended_action_reason_includes_improvement_when_ok(tmp_path: Path) -> None:
    _seed_done_only_queue(tmp_path)
    artifact_dir = tmp_path / "data" / "reports" / "operator_autonomous_loop"
    _write_loop_improvement_artifacts(
        artifact_dir,
        recommended_id="ticket-354",
        weakness="weak_concept_mapping",
    )
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    reason = plan["next_recommended_action"]["reason"]

    assert plan["autonomous_loop_improvement_status"]["status"] == "ok"
    assert "ticket-354" in reason
    assert "weak_concept_mapping" in reason
    assert "Last loop improvement" in reason


def test_recommended_action_reason_unchanged_when_improvement_not_run(
    tmp_path: Path,
) -> None:
    _seed_done_only_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    improvement = plan["autonomous_loop_improvement_status"]

    assert improvement["status"] == "not_run"
    expected = _autonomous_loop_recommended_reason(
        plan["autonomous_loop_scratch_status"],
        None,
    )
    assert plan["next_recommended_action"]["reason"] == expected
    assert "Last loop improvement" not in plan["next_recommended_action"]["reason"]
