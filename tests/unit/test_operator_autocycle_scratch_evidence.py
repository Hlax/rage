"""Unit tests for operator autocycle scratch evidence review gate (ticket-252)."""

from __future__ import annotations

import json
from pathlib import Path

from rge.modules.live_probe_scratch import (
    build_scratch_record,
    ensure_scratch_database,
    insert_reviewed_report,
)
from rge.modules.operator_autocycle import evaluate_autocycle_cycle, run_autocycle
from rge.modules.operator_loop import WorkingTreeStatus

REPO_ROOT = Path(__file__).resolve().parents[2]
_SAMPLE_REPORT = (
    REPO_ROOT / "tests" / "fixtures" / "probes" / "reviewed_mini_run_report_sample.json"
)


def _seed_queue(tmp_path: Path, body: str) -> None:
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "agent_reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(body, encoding="utf-8")


def _seed_audit_report(tmp_path: Path) -> None:
    (
        tmp_path
        / "agent_reports"
        / "2026-06-16_pre-ticket-251_rank-2-staged-candidate-heuristic-scan-audit.md"
    ).write_text("# pre-ticket audit", encoding="utf-8")


def _sample_scratch_record(**overrides: object) -> dict:
    report = json.loads(_SAMPLE_REPORT.read_text(encoding="utf-8"))
    record = build_scratch_record(
        report,
        report_rel_path="tests/fixtures/probes/reviewed_mini_run_report_sample.json",
        operator_note="reviewed",
        reviewed_at="2026-06-12T22:01:00+00:00",
    )
    record.update(overrides)
    return record


def _seed_scratch_db(db_path: Path, records: list[dict]) -> None:
    conn = ensure_scratch_database(db_path)
    try:
        for record in records:
            insert_reviewed_report(conn, record)
    finally:
        conn.close()


def test_autocycle_recommends_scratch_evidence_review_when_ready(tmp_path: Path) -> None:
    _seed_queue(
        tmp_path,
        """
| 251 | ticket-251 | done | Rank-2 heuristic scan | | |
""",
    )
    _seed_audit_report(tmp_path)
    scratch_db = tmp_path / "data" / "db" / "live_probe_scratch.sqlite"
    _seed_scratch_db(scratch_db, [_sample_scratch_record()])

    clean = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    evaluation = evaluate_autocycle_cycle(root=tmp_path, working_tree=clean)

    assert evaluation["scratch_evidence_status"]["evidence_review_ready"] is True
    assert evaluation["scratch_evidence_review_recommended"] is True
    assert evaluation["status"] == "stopped"
    assert evaluation["stop_reason"] == (
        "operator_action_blocked_automation: run_scratch_evidence_review"
    )
    assert evaluation["recommended_action"]["action_id"] == "run_scratch_evidence_review"
    assert "probe-scratch-evidence-review" in evaluation["next_command"]


def test_autocycle_scratch_review_precedes_drift_warning(tmp_path: Path, monkeypatch) -> None:
    _seed_queue(
        tmp_path,
        """
| 251 | ticket-251 | done | Rank-2 heuristic scan | | |
""",
    )
    _seed_audit_report(tmp_path)
    scratch_db = tmp_path / "data" / "db" / "live_probe_scratch.sqlite"
    _seed_scratch_db(scratch_db, [_sample_scratch_record()])

    monkeypatch.setattr(
        "rge.modules.principal_audit_gate.checkpoint_status",
        lambda **kwargs: {
            "status": "satisfied",
            "cadence_status": "satisfied",
            "implementation_gate": "satisfied",
            "drift_warning": [
                "No product-risk or live-research proof advanced in the last 3 completed tickets."
            ],
        },
    )

    clean = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    evaluation = evaluate_autocycle_cycle(root=tmp_path, working_tree=clean)

    assert evaluation["scratch_evidence_review_recommended"] is True
    assert "drift_warning_active" not in (evaluation["stop_reason"] or "")


def test_autocycle_defers_scratch_when_proposed_ticket_blocks(tmp_path: Path) -> None:
    _seed_queue(
        tmp_path,
        """
| 251 | ticket-251 | done | Rank-2 heuristic scan | | |
| 252 | ticket-252 | proposed | Scratch autocycle gate | | |
""",
    )
    _seed_audit_report(tmp_path)
    (tmp_path / "tickets" / "ticket-252.json").write_text(
        json.dumps(
            {
                "id": "ticket-252",
                "title": "Scratch autocycle gate",
                "risk_level": "low",
                "status": "proposed",
            }
        ),
        encoding="utf-8",
    )
    scratch_db = tmp_path / "data" / "db" / "live_probe_scratch.sqlite"
    _seed_scratch_db(scratch_db, [_sample_scratch_record()])

    clean = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    evaluation = evaluate_autocycle_cycle(root=tmp_path, working_tree=clean)

    assert evaluation["scratch_evidence_review_recommended"] is False
    assert evaluation["run_next_ticket_allowed"] is True
    assert "ticket_implementation_requires_agent" in evaluation["stop_reason"]


def test_run_autocycle_payload_includes_scratch_evidence_status(tmp_path: Path) -> None:
    _seed_queue(tmp_path, "| 251 | ticket-251 | done | Rank-2 heuristic scan | | |\n")
    _seed_audit_report(tmp_path)
    scratch_db = tmp_path / "data" / "db" / "live_probe_scratch.sqlite"
    _seed_scratch_db(scratch_db, [_sample_scratch_record()])

    payload = run_autocycle(mode="plan", max_cycles=1, root=tmp_path)

    assert "scratch_evidence_status" in payload
    assert payload["scratch_evidence_status"]["evidence_review_ready"] is True
    assert payload["scratch_evidence_review_recommended"] is True
