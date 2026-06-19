"""Operator autocycle execute-safe recommended action reason sync (ticket-357)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from rge.modules.operator_autocycle import run_autocycle
from rge.modules.operator_loop import (
    WorkingTreeStatus,
    _AUTONOMOUS_LOOP_BASE_REASON,
    execute_safe_checks,
)


def _seed_done_only_queue(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "agent_reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        """
| 356 | ticket-356 | done | prev | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "tickets" / "ticket-356.json").write_text(
        json.dumps({"id": "ticket-356", "status": "done", "risk_level": "low"}),
        encoding="utf-8",
    )
    (
        tmp_path
        / "agent_reports"
        / "2026-06-18_principal-audit-post-ticket-356.md"
    ).write_text("# audit", encoding="utf-8")


def _write_pre_run_loop_artifacts(
    artifact_dir: Path,
    *,
    recommended_id: str = "ticket-old",
    weakness: str = "weak_concept_mapping",
    verdict: str = "PARTIAL",
    weakest: str = "weak_claim_extraction",
) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    ticket_dir = artifact_dir / "tickets"
    ticket_dir.mkdir(parents=True, exist_ok=True)
    improvement_path = ticket_dir / "improvement_ticket_latest.json"
    recommended_path = artifact_dir / "recommended_improvement_ticket.json"
    improvement_path.write_text(
        json.dumps(
            [
                {
                    "title": "Old draft",
                    "status": "draft",
                    "failure_reason": weakness,
                    "risk_level": "low",
                    "problem": "Old problem.",
                    "acceptance_criteria": ["Old criterion."],
                }
            ]
        ),
        encoding="utf-8",
    )
    recommended_path.write_text(
        json.dumps(
            {
                "id": recommended_id,
                "title": "Old recommendation",
                "status": "proposed",
                "source_weakness": weakness,
            }
        ),
        encoding="utf-8",
    )
    (artifact_dir / "autonomous_loop_report.json").write_text(
        json.dumps(
            {
                "status": "completed",
                "research_path": "fixture_mode",
                "research_quality": {
                    "research_quality_verdict": verdict,
                    "weakest_dimension": weakest,
                    "weakest_dimension_score": 55,
                },
                "artifacts": {
                    "improvement_tickets": str(improvement_path),
                    "recommended_improvement_ticket": str(recommended_path),
                },
                "run_summary": {"quality_driven_ticket_ids": ["old_id"]},
            }
        ),
        encoding="utf-8",
    )


def test_autocycle_execute_safe_syncs_reason_from_execution_on_pass(
    tmp_path: Path,
) -> None:
    _seed_done_only_queue(tmp_path)
    clean = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    with patch(
        "rge.modules.operator_autocycle.inspect_working_tree",
        lambda root=None: clean,
    ), patch(
        "rge.modules.operator_loop.safe_verification_commands",
        return_value=[],
    ):
        payload = run_autocycle(mode="execute-safe", max_cycles=1, root=tmp_path)

    cycle = payload["cycles"][0]
    execution_reason = cycle["execution"]["next_recommended_action"]["reason"]
    cycle_reason = cycle["recommended_action"]["reason"]
    summary_reason = payload["recommended_action"]["reason"]

    assert payload["status"] == "completed"
    assert cycle["execution"]["execution_status"] == "pass"
    assert "Last scratch loop quality" in execution_reason
    assert "Last loop improvement" in execution_reason
    assert cycle_reason == execution_reason
    assert summary_reason == execution_reason
    assert execution_reason != _AUTONOMOUS_LOOP_BASE_REASON


def test_autocycle_execute_safe_failed_keeps_pre_run_reason(tmp_path: Path) -> None:
    _seed_done_only_queue(tmp_path)
    artifact_dir = tmp_path / "data" / "reports" / "operator_autonomous_loop"
    _write_pre_run_loop_artifacts(
        artifact_dir,
        recommended_id="ticket-old",
        weakness="weak_concept_mapping",
        verdict="PARTIAL",
        weakest="weak_claim_extraction",
    )
    clean = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    def failing_runner(root=None, **kwargs: object) -> dict:
        payload = execute_safe_checks(root=root, working_tree=clean, **kwargs)
        payload["execution_status"] = "fail"
        payload["next_recommended_action"] = {
            **payload.get("next_recommended_action", {}),
            "reason": (
                f"{_AUTONOMOUS_LOOP_BASE_REASON} Last scratch loop quality: GO; "
                "weakest dimension weak_run_lineage. Last loop improvement: "
                "recommended ticket-new; source weakness weak_ticket_generation."
            ),
        }
        return payload

    with patch(
        "rge.modules.operator_autocycle.inspect_working_tree",
        lambda root=None: clean,
    ), patch(
        "rge.modules.operator_loop.safe_verification_commands",
        return_value=[],
    ):
        payload = run_autocycle(
            mode="execute-safe",
            max_cycles=1,
            root=tmp_path,
            execute_runner=failing_runner,
        )

    cycle = payload["cycles"][0]
    reason = cycle["recommended_action"]["reason"]

    assert payload["status"] == "stopped"
    assert payload["stop_reason"] == "verification_failed"
    assert "ticket-old" in reason
    assert "weak_concept_mapping" in reason
    assert "PARTIAL" in reason
    assert "weak_claim_extraction" in reason
    assert "ticket-new" not in reason
    assert "weak_run_lineage" not in reason
