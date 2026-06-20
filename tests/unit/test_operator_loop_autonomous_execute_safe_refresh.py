"""Execute-safe autonomous loop scratch status refresh (ticket-343)."""

from __future__ import annotations

import pytest
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from rge.modules.operator_loop import (
    WorkingTreeStatus,
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
| 342 | ticket-342 | done | prev | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "tickets" / "ticket-342.json").write_text(
        json.dumps({"id": "ticket-342", "status": "done", "risk_level": "low"}),
        encoding="utf-8",
    )
    (
        tmp_path
        / "agent_reports"
        / "2026-06-18_phase-3_ticket-340_principal-audit-post-ticket-338.md"
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


def test_execute_safe_refresh_scratch_status_after_real_loop_proof(
    tmp_path: Path,
) -> None:
    _seed_done_only_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    with patch(
        "rge.modules.operator_loop.safe_verification_commands",
        return_value=[],
    ):
        result = execute_safe_checks(root=tmp_path, working_tree=clean_tree)

    scratch = result["autonomous_loop_scratch_status"]

    assert result["execution_status"] == "pass"
    assert scratch["status"] == "ok"
    assert scratch["research_quality_verdict"] is not None
    assert scratch["weakest_dimension"] is not None
    assert scratch["research_path"] == "fixture_mode"
    artifact = tmp_path / "data" / "reports" / "operator_autonomous_loop" / "autonomous_loop_report.json"
    assert artifact.is_file()


def test_execute_safe_failed_loop_keeps_pre_run_scratch_status(tmp_path: Path) -> None:
    _seed_done_only_queue(tmp_path)
    artifact_dir = tmp_path / "data" / "reports" / "operator_autonomous_loop"
    _write_loop_report(
        artifact_dir,
        verdict="PARTIAL",
        weakest="weak_claim_extraction",
        weakest_score=55,
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

    scratch = result["autonomous_loop_scratch_status"]

    assert result["execution_status"] == "fail"
    assert scratch["status"] == "ok"
    assert scratch["research_quality_verdict"] == "PARTIAL"
    assert scratch["weakest_dimension"] == "weak_claim_extraction"
    assert scratch["weakest_dimension_score"] == 55


def test_execute_safe_blocked_keeps_pre_run_scratch_status(tmp_path: Path) -> None:
    _seed_done_only_queue(tmp_path)
    dirty_tree = WorkingTreeStatus(clean=False, branch="main", dirty_paths=[" M x"])

    result = execute_safe_checks(root=tmp_path, working_tree=dirty_tree)
    scratch = result["autonomous_loop_scratch_status"]

    assert result["execution_status"] == "blocked"
    assert scratch["status"] == "not_run"
    assert scratch["research_quality_verdict"] is None
