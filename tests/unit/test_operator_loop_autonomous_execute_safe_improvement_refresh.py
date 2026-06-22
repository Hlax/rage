"""Execute-safe autonomous loop improvement status refresh (ticket-350)."""

from __future__ import annotations

import pytest
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from rge.modules.operator_loop import (
    WorkingTreeStatus,
    _AUTONOMOUS_LOOP_BASE_REASON,
    execute_safe_checks,
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
| 349 | ticket-349 | done | prev | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "tickets" / "ticket-349.json").write_text(
        json.dumps({"id": "ticket-349", "status": "done", "risk_level": "low"}),
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


def test_execute_safe_refresh_improvement_status_after_real_loop_proof(
    tmp_path: Path,
) -> None:
    _seed_done_only_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    with patch(
        "rge.modules.operator_loop.safe_verification_commands",
        return_value=[],
    ):
        result = execute_safe_checks(root=tmp_path, working_tree=clean_tree)

    improvement = result["autonomous_loop_improvement_status"]

    assert result["execution_status"] == "pass"
    assert improvement["status"] == "ok"
    assert improvement["recommended_ticket_id"] is not None
    assert improvement["draft_count"] >= 1
    assert improvement["pending"] is True
    assert improvement["source_weakness"] is not None


def test_execute_safe_failed_loop_keeps_pre_run_improvement_status(
    tmp_path: Path,
) -> None:
    _seed_done_only_queue(tmp_path)
    artifact_dir = tmp_path / "data" / "reports" / "operator_autonomous_loop"
    _write_pre_run_improvement_report(artifact_dir, recommended_id="ticket-old")
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    def failing_runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "autonomous-researcher-loop" in " ".join(argv):
            return subprocess.CompletedProcess(argv, 1, stdout="", stderr="loop failed")
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    with patch(
        "rge.modules.operator_loop.safe_verification_commands",
        return_value=[],
    ):
        result = execute_safe_checks(
            root=tmp_path,
            working_tree=clean_tree,
            command_runner=failing_runner,
        )

    improvement = result["autonomous_loop_improvement_status"]

    assert result["execution_status"] == "fail"
    assert improvement["status"] == "ok"
    assert improvement["recommended_ticket_id"] == "ticket-old"
    assert improvement["source_weakness"] == "weak_concept_mapping"
    assert improvement["draft_tickets"][0]["failure_reason"] == "weak_concept_mapping"


def test_execute_safe_blocked_keeps_pre_run_improvement_status(tmp_path: Path) -> None:
    _seed_done_only_queue(tmp_path)
    dirty_tree = WorkingTreeStatus(clean=False, branch="main", dirty_paths=[" M x"])

    result = execute_safe_checks(root=tmp_path, working_tree=dirty_tree)
    improvement = result["autonomous_loop_improvement_status"]

    assert result["execution_status"] == "blocked"
    assert improvement["status"] == "not_run"
    assert improvement["recommended_ticket_id"] is None


def test_execute_safe_refresh_reason_after_real_loop_proof(tmp_path: Path) -> None:
    _seed_done_only_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    with patch(
        "rge.modules.operator_loop.safe_verification_commands",
        return_value=[],
    ):
        result = execute_safe_checks(root=tmp_path, working_tree=clean_tree)

    reason = result["next_recommended_action"]["reason"]

    assert result["execution_status"] == "pass"
    assert "Last scratch loop quality" in reason
    assert "Last loop improvement" in reason
    assert reason != _AUTONOMOUS_LOOP_BASE_REASON


def test_execute_safe_failed_loop_keeps_pre_run_reason(tmp_path: Path) -> None:
    _seed_done_only_queue(tmp_path)
    artifact_dir = tmp_path / "data" / "reports" / "operator_autonomous_loop"
    _write_pre_run_improvement_report(artifact_dir, recommended_id="ticket-old")
    (artifact_dir / "autonomous_loop_report.json").write_text(
        json.dumps(
            {
                "status": "completed",
                "research_path": "fixture_mode",
                "research_quality": {
                    "research_quality_verdict": "PARTIAL",
                    "weakest_dimension": "weak_claim_extraction",
                    "weakest_dimension_score": 55,
                },
                "artifacts": {
                    "improvement_tickets": str(
                        artifact_dir / "tickets" / "improvement_ticket_latest.json"
                    ),
                    "recommended_improvement_ticket": str(
                        artifact_dir / "recommended_improvement_ticket.json"
                    ),
                },
                "run_summary": {"quality_driven_ticket_ids": ["old_id"]},
            }
        ),
        encoding="utf-8",
    )
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    def failing_runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "autonomous-researcher-loop" in " ".join(argv):
            return subprocess.CompletedProcess(argv, 1, stdout="", stderr="loop failed")
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    with patch(
        "rge.modules.operator_loop.safe_verification_commands",
        return_value=[],
    ):
        result = execute_safe_checks(
            root=tmp_path,
            working_tree=clean_tree,
            command_runner=failing_runner,
        )

    reason = result["next_recommended_action"]["reason"]

    assert result["execution_status"] == "fail"
    assert "ticket-old" in reason
    assert "weak_concept_mapping" in reason
    assert "PARTIAL" in reason
    assert "weak_claim_extraction" in reason
