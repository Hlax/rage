"""Unit tests for principal audit checkpoint status helper."""

from __future__ import annotations

from pathlib import Path

from rge.modules.principal_audit_gate import checkpoint_status, parse_queue_rows


def test_parse_queue_rows_reads_done_tickets() -> None:
    sample = """
| 39 | ticket-039 | done | Title | branch | report |
| 40 | ticket-040 | proposed | Next | | |
"""
    rows = parse_queue_rows(sample)
    assert len(rows) == 2
    assert rows[0].ticket_id == "ticket-039"
    assert rows[0].status == "done"


def test_checkpoint_status_not_overdue_after_pre_ticket_audit(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir()
    (tmp_path / "agent_reports").mkdir()
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        """
| 39 | ticket-039 | done | t | | |
| 40 | ticket-040 | proposed | n | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "agent_reports" / "2026-06-12_pre-ticket-039_round-trip-readiness-audit.md").write_text(
        "# audit", encoding="utf-8"
    )
    (tmp_path / "tickets" / "ticket-040.json").write_text(
        '{"id":"ticket-040","risk_level":"medium"}', encoding="utf-8"
    )

    report = checkpoint_status(root=tmp_path, next_ticket_id="ticket-040")
    assert report["cadence_status"] == "satisfied"
    assert report["done_tickets_since_latest_checkpoint"] == 0
    assert report["implementation_gate"] == "blocked_missing_pre_ticket_audit"
    assert report["status"] == "blocked"


def test_checkpoint_status_overdue_without_recent_audit(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir()
    (tmp_path / "agent_reports").mkdir()
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        """
| 33 | ticket-033 | done | audit | | |
| 34 | ticket-034 | done | a | | |
| 35 | ticket-035 | done | b | | |
| 36 | ticket-036 | done | c | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "agent_reports" / "2026-06-01_pre-phase-2_principal-audit.md").write_text(
        "# old", encoding="utf-8"
    )

    report = checkpoint_status(root=tmp_path)
    assert report["cadence_status"] == "overdue"
    assert report["done_tickets_since_latest_checkpoint"] >= 3
