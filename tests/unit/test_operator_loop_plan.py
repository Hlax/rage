"""Unit tests for operator loop plan runtime config surfacing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.config import DEFAULT_STAGED_RANK2_SCAN_MAX
from rge.modules.operator_loop import WorkingTreeStatus, build_operator_plan
from rge.modules.operator_proof_bundle import COMMAND, PIPELINE_MODE


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


def test_plan_includes_default_staged_rank2_scan_max(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_STAGED_RANK2_SCAN_MAX", raising=False)
    _seed_minimal_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)

    assert plan["staged_rank2_scan_max"] == DEFAULT_STAGED_RANK2_SCAN_MAX


def test_plan_honors_staged_rank2_scan_max_env_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_STAGED_RANK2_SCAN_MAX", "20")
    _seed_minimal_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)

    assert plan["staged_rank2_scan_max"] == 20


def test_plan_includes_arbitrary_source_proof_bundle_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_STAGED_RANK2_SCAN_MAX", raising=False)
    _seed_minimal_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    status = plan["arbitrary_source_proof_bundle_status"]

    assert status["command"] == COMMAND
    assert status["pipeline_mode"] == PIPELINE_MODE
    assert status["mock_llm_only"] is True
    assert status["requires_temp_db"] is True
    assert "prove-arbitrary-source-bundle" in status["operator_commands"]["proof_bundle"]
    assert status["proof_artifact"] == "operator_proof_bundle.json"


def test_proof_bundle_recommended_action_when_product_drift_and_no_open_ticket(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_done_only_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    monkeypatch.setattr(
        "rge.modules.operator_loop.checkpoint_status",
        lambda **kwargs: {
            "cadence_status": "satisfied",
            "implementation_gate": "satisfied",
            "drift_warning": [
                "No product-risk or live-research proof advanced in the last 3 completed tickets."
            ],
        },
    )

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    action = plan["next_recommended_action"]

    assert plan["arbitrary_source_proof_bundle_status"]["proof_bundle_recommended"] is True
    assert action["action_id"] == "run_arbitrary_source_proof_bundle"
    assert "prove-arbitrary-source-bundle" in action["commands"][0]["shell"]


def test_proof_bundle_action_deferred_when_open_ticket_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_minimal_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    monkeypatch.setattr(
        "rge.modules.operator_loop.checkpoint_status",
        lambda **kwargs: {
            "cadence_status": "satisfied",
            "implementation_gate": "satisfied",
            "drift_warning": [
                "No product-risk or live-research proof advanced in the last 3 completed tickets."
            ],
        },
    )

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)

    assert plan["arbitrary_source_proof_bundle_status"]["proof_bundle_recommended"] is True
    assert plan["next_recommended_action"]["action_id"] == "begin_ticket_implementation"
