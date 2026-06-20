"""Operator autocycle execute-safe improvement status sync (ticket-351)."""

from __future__ import annotations

import pytest
import json
from pathlib import Path
from unittest.mock import patch

from rge.modules.operator_autocycle import run_autocycle
from rge.modules.operator_loop import WorkingTreeStatus, execute_safe_checks




@pytest.fixture(autouse=True)
def _operator_autonomous_live_smoke_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    from tests.unit.operator_loop_helpers import apply_live_smoke_env_gates
    apply_live_smoke_env_gates(monkeypatch)

def _seed_done_only_queue(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "agent_reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        """
| 350 | ticket-350 | done | prev | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "tickets" / "ticket-350.json").write_text(
        json.dumps({"id": "ticket-350", "status": "done", "risk_level": "low"}),
        encoding="utf-8",
    )
    (
        tmp_path
        / "agent_reports"
        / "2026-06-18_principal-audit-post-ticket-349.md"
    ).write_text("# audit", encoding="utf-8")
    from tests.unit.operator_loop_helpers import seed_public_site_preview_paths
    seed_public_site_preview_paths(tmp_path, include_source_health=True)


def _write_pre_run_improvement_report(
    artifact_dir: Path,
    *,
    recommended_id: str = "ticket-old",
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
                    "failure_reason": "weak_concept_mapping",
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
                "source_weakness": "weak_concept_mapping",
            }
        ),
        encoding="utf-8",
    )
    (artifact_dir / "autonomous_loop_report.json").write_text(
        json.dumps(
            {
                "status": "completed",
                "artifacts": {
                    "improvement_tickets": str(improvement_path),
                    "recommended_improvement_ticket": str(recommended_path),
                },
                "run_summary": {"quality_driven_ticket_ids": ["old_id"]},
            }
        ),
        encoding="utf-8",
    )


def test_autocycle_execute_safe_syncs_improvement_from_execution_on_pass(
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
    execution_improvement = cycle["execution"]["autonomous_loop_improvement_status"]
    cycle_improvement = cycle["autonomous_loop_improvement_status"]
    summary_improvement = payload["autonomous_loop_improvement_status"]

    assert payload["status"] == "completed"
    assert cycle["execution"]["execution_status"] == "pass"
    assert execution_improvement["status"] == "ok"
    assert execution_improvement["recommended_ticket_id"] is not None
    assert execution_improvement["draft_count"] >= 1
    assert cycle_improvement == execution_improvement
    assert summary_improvement == execution_improvement


def test_autocycle_execute_safe_failed_keeps_pre_run_improvement_status(
    tmp_path: Path,
) -> None:
    _seed_done_only_queue(tmp_path)
    artifact_dir = tmp_path / "data" / "reports" / "operator_autonomous_loop"
    _write_pre_run_improvement_report(artifact_dir, recommended_id="ticket-old")
    clean = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    def failing_runner(root=None, **kwargs: object) -> dict:
        payload = execute_safe_checks(root=root, working_tree=clean, **kwargs)
        payload["execution_status"] = "fail"
        payload["autonomous_loop_improvement_status"] = {
            "status": "ok",
            "recommended_ticket_id": "ticket-new",
            "draft_count": 2,
            "source_weakness": "weak_ticket_generation",
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
    improvement = cycle["autonomous_loop_improvement_status"]

    assert payload["status"] == "stopped"
    assert payload["stop_reason"] == "verification_failed"
    assert improvement["status"] == "ok"
    assert improvement["recommended_ticket_id"] == "ticket-old"
    assert improvement["source_weakness"] == "weak_concept_mapping"
    assert improvement["draft_count"] == 1
