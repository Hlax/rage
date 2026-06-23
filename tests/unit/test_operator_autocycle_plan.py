"""Unit tests for operator autocycle plan runtime config surfacing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.config import DEFAULT_STAGED_RANK2_SCAN_MAX
from rge.modules.operator_autocycle import evaluate_autocycle_cycle, run_autocycle
from rge.modules.operator_loop import WorkingTreeStatus
from rge.modules.operator_proof_bundle import COMMAND, PIPELINE_MODE


def _seed_satisfied_proof_bundle(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "data" / "reports" / "operator_proof_bundle"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "operator_proof_bundle.json").write_text(
        json.dumps(
            {
                "status": "completed",
                "usable_output": True,
                "pipeline_mode": PIPELINE_MODE,
            }
        ),
        encoding="utf-8",
    )


def _seed_minimal_queue(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "agent_reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        """
| 40 | ticket-040 | done | prev | | |
| 41 | ticket-041 | proposed | Next | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "tickets" / "ticket-041.json").write_text(
        json.dumps(
            {
                "id": "ticket-041",
                "title": "Next",
                "risk_level": "low",
                "status": "proposed",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "agent_reports" / "2026-06-16_principal-audit-post-ticket-254.md").write_text(
        "# audit",
        encoding="utf-8",
    )


def test_autocycle_plan_includes_default_staged_rank2_scan_max(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_STAGED_RANK2_SCAN_MAX", raising=False)
    _seed_minimal_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    monkeypatch.setattr(
        "rge.modules.operator_autocycle.inspect_working_tree",
        lambda root=None: clean_tree,
    )

    payload = run_autocycle(mode="plan", max_cycles=1, root=tmp_path)

    assert payload["staged_rank2_scan_max"] == DEFAULT_STAGED_RANK2_SCAN_MAX
    assert payload["cycles"][0]["staged_rank2_scan_max"] == DEFAULT_STAGED_RANK2_SCAN_MAX


def test_autocycle_plan_honors_staged_rank2_scan_max_env_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_STAGED_RANK2_SCAN_MAX", "20")
    _seed_minimal_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    monkeypatch.setattr(
        "rge.modules.operator_autocycle.inspect_working_tree",
        lambda root=None: clean_tree,
    )

    payload = run_autocycle(mode="plan", max_cycles=1, root=tmp_path)

    assert payload["staged_rank2_scan_max"] == 20
    assert payload["cycles"][0]["staged_rank2_scan_max"] == 20


def _seed_done_only_queue(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "agent_reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        """
| 40 | ticket-040 | done | prev | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "tickets" / "ticket-040.json").write_text(
        json.dumps(
            {
                "id": "ticket-040",
                "title": "Done",
                "risk_level": "low",
                "status": "done",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "agent_reports" / "2026-06-16_principal-audit-post-ticket-254.md").write_text(
        "# audit",
        encoding="utf-8",
    )


def test_autocycle_plan_includes_arbitrary_source_proof_bundle_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_minimal_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    monkeypatch.setattr(
        "rge.modules.operator_autocycle.inspect_working_tree",
        lambda root=None: clean_tree,
    )

    payload = run_autocycle(mode="plan", max_cycles=1, root=tmp_path)
    status = payload["arbitrary_source_proof_bundle_status"]
    cycle_status = payload["cycles"][0]["arbitrary_source_proof_bundle_status"]

    assert status["command"] == COMMAND
    assert status["pipeline_mode"] == PIPELINE_MODE
    assert cycle_status == status
    assert "prove-arbitrary-source-bundle" in status["operator_commands"]["proof_bundle"]


def test_autocycle_proof_bundle_recommended_when_product_drift_and_no_open_ticket(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_done_only_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    monkeypatch.setattr(
        "rge.modules.operator_autocycle.inspect_working_tree",
        lambda root=None: clean_tree,
    )
    monkeypatch.setattr(
        "rge.modules.operator_loop.checkpoint_status",
        lambda **kwargs: {
            "status": "satisfied",
            "cadence_status": "satisfied",
            "implementation_gate": "satisfied",
            "drift_warning": [
                "No product-risk or live-research proof advanced in the last 3 completed tickets."
            ],
        },
    )
    monkeypatch.setattr(
        "rge.modules.operator_autocycle.checkpoint_status",
        lambda **kwargs: {
            "status": "satisfied",
            "cadence_status": "satisfied",
            "implementation_gate": "satisfied",
            "drift_warning": None,
        },
    )

    payload = run_autocycle(mode="plan", max_cycles=1, root=tmp_path)
    cycle = payload["cycles"][0]

    assert cycle["arbitrary_source_proof_bundle_status"]["proof_bundle_recommended"] is True
    assert cycle["proof_bundle_recommended"] is True
    assert cycle["status"] == "stopped"
    assert cycle["stop_reason"] == (
        "operator_action_blocked_automation: run_arbitrary_source_proof_bundle"
    )
    assert "prove-arbitrary-source-bundle" in cycle["next_command"]


def test_autocycle_product_drift_cleared_when_proof_bundle_artifact_satisfied(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_minimal_queue(tmp_path)
    _seed_satisfied_proof_bundle(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    monkeypatch.setattr(
        "rge.modules.operator_autocycle.inspect_working_tree",
        lambda root=None: clean_tree,
    )
    drift_warning = [
        "No product-risk or live-research proof advanced in the last 3 completed tickets."
    ]
    monkeypatch.setattr(
        "rge.modules.operator_loop.checkpoint_status",
        lambda **kwargs: {
            "cadence_status": "satisfied",
            "implementation_gate": "satisfied",
            "drift_warning": drift_warning,
        },
    )
    monkeypatch.setattr(
        "rge.modules.operator_autocycle.checkpoint_status",
        lambda **kwargs: {
            "status": "satisfied",
            "cadence_status": "satisfied",
            "implementation_gate": "satisfied",
            "drift_warning": drift_warning,
        },
    )

    evaluation = evaluate_autocycle_cycle(root=tmp_path, working_tree=clean_tree)

    assert (
        evaluation["arbitrary_source_proof_bundle_status"]["proof_artifact_satisfied"]
        is True
    )
    assert evaluation["arbitrary_source_proof_bundle_status"]["proof_bundle_recommended"] is False
    assert "drift_warning_active" not in (evaluation["stop_reason"] or "")
    assert evaluation["run_next_ticket_allowed"] is True
