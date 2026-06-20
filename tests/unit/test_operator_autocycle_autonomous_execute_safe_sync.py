"""Operator autocycle execute-safe scratch status sync (ticket-346)."""

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
| 345 | ticket-345 | done | prev | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "tickets" / "ticket-345.json").write_text(
        json.dumps({"id": "ticket-345", "status": "done", "risk_level": "low"}),
        encoding="utf-8",
    )
    (
        tmp_path
        / "agent_reports"
        / "2026-06-18_principal-audit-post-ticket-343.md"
    ).write_text("# audit", encoding="utf-8")
    from tests.unit.operator_loop_helpers import seed_public_site_preview_paths
    seed_public_site_preview_paths(tmp_path, include_source_health=True)


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


def test_autocycle_execute_safe_syncs_scratch_from_execution_on_pass(
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
    execution_scratch = cycle["execution"]["autonomous_loop_scratch_status"]
    cycle_scratch = cycle["autonomous_loop_scratch_status"]
    summary_scratch = payload["autonomous_loop_scratch_status"]

    assert payload["status"] == "completed"
    assert cycle["execution"]["execution_status"] == "pass"
    assert execution_scratch["status"] == "ok"
    assert execution_scratch["research_quality_verdict"] is not None
    assert execution_scratch["weakest_dimension"] is not None
    assert cycle_scratch == execution_scratch
    assert summary_scratch == execution_scratch


def test_autocycle_execute_safe_failed_keeps_pre_run_scratch_status(
    tmp_path: Path,
) -> None:
    _seed_done_only_queue(tmp_path)
    artifact_dir = tmp_path / "data" / "reports" / "operator_autonomous_loop"
    _write_loop_report(
        artifact_dir,
        verdict="PARTIAL",
        weakest="weak_claim_extraction",
        weakest_score=55,
    )
    clean = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    def failing_runner(root=None, **kwargs: object) -> dict:
        payload = execute_safe_checks(root=root, working_tree=clean, **kwargs)
        payload["execution_status"] = "fail"
        payload["autonomous_loop_scratch_status"] = {
            "status": "ok",
            "research_quality_verdict": "GO",
            "weakest_dimension": "weak_run_lineage",
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
    scratch = cycle["autonomous_loop_scratch_status"]

    assert payload["status"] == "stopped"
    assert payload["stop_reason"] == "verification_failed"
    assert scratch["status"] == "ok"
    assert scratch["research_quality_verdict"] == "PARTIAL"
    assert scratch["weakest_dimension"] == "weak_claim_extraction"
    assert scratch["weakest_dimension_score"] == 55
