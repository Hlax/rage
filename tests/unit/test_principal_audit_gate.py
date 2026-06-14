"""Unit tests for principal audit checkpoint status helper."""

from __future__ import annotations

from pathlib import Path

from rge.modules.principal_audit_gate import (
    checkpoint_status,
    classify_ticket_value,
    evaluate_value_drift,
    parse_queue_rows,
)


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


def test_post_ticket_principal_audit_satisfies_cadence(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir()
    (tmp_path / "agent_reports").mkdir()
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        """
| 42 | ticket-042 | done | prev | | |
| 43 | ticket-043 | done | latest | | |
| 44 | ticket-044 | proposed | next | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "agent_reports" / "2026-06-12_principal-audit-post-ticket-042.md").write_text(
        "# principal audit after ticket-042", encoding="utf-8"
    )

    report = checkpoint_status(root=tmp_path, next_ticket_id="ticket-044")
    assert report["latest_checkpoint_ticket_number"] == 42
    assert report["cadence_status"] == "satisfied"
    assert report["done_tickets_since_latest_checkpoint"] == 1
    assert report["done_ticket_ids_since_latest_checkpoint"] == ["ticket-043"]
    assert report["status"] == "satisfied"


def test_three_done_tickets_after_checkpoint_becomes_overdue(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir()
    (tmp_path / "agent_reports").mkdir()
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        """
| 39 | ticket-039 | done | t | | |
| 40 | ticket-040 | done | a | | |
| 41 | ticket-041 | done | b | | |
| 42 | ticket-042 | done | c | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "agent_reports" / "2026-06-12_pre-ticket-039_round-trip-readiness-audit.md").write_text(
        "# audit", encoding="utf-8"
    )

    report = checkpoint_status(root=tmp_path)
    assert report["cadence_status"] == "overdue"
    assert report["done_tickets_since_latest_checkpoint"] == 3
    assert report["done_ticket_ids_since_latest_checkpoint"] == [
        "ticket-040",
        "ticket-041",
        "ticket-042",
    ]


def test_premature_post_ticket_principal_audit_is_ignored(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir()
    (tmp_path / "agent_reports").mkdir()
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        """
| 33 | ticket-033 | done | phase audit | | |
| 42 | ticket-042 | done | prev | | |
| 43 | ticket-043 | proposed | next | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "agent_reports" / "2026-06-01_pre-phase-2_principal-audit.md").write_text(
        "# phase boundary", encoding="utf-8"
    )
    (tmp_path / "agent_reports" / "2026-06-12_principal-audit-post-ticket-043.md").write_text(
        "# premature", encoding="utf-8"
    )

    report = checkpoint_status(root=tmp_path)
    assert "pre-phase-2" in report["latest_checkpoint_report"]
    assert report["latest_checkpoint_ticket_number"] == 33


def test_medium_risk_ticket_without_pre_audit_remains_blocked(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir()
    (tmp_path / "agent_reports").mkdir()
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        """
| 43 | ticket-043 | done | prev | | |
| 44 | ticket-044 | proposed | next | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "agent_reports" / "2026-06-12_principal-audit-post-ticket-043.md").write_text(
        "# audit", encoding="utf-8"
    )
    (tmp_path / "tickets" / "ticket-044.json").write_text(
        '{"id":"ticket-044","risk_level":"medium"}', encoding="utf-8"
    )

    report = checkpoint_status(root=tmp_path, next_ticket_id="ticket-044")
    assert report["cadence_status"] == "satisfied"
    assert report["implementation_gate"] == "blocked_missing_pre_ticket_audit"
    assert report["status"] == "blocked"


def test_classify_ticket_value_detects_doc_crosslink() -> None:
    assert classify_ticket_value("README manual synthnote pipeline proof test cross-link") == "docs_crosslink"


def test_classify_ticket_value_detects_product_work() -> None:
    assert classify_ticket_value("Real manual source ingestion (Level-1)") == "product_risk_reduction"


def test_historical_doc_crosslink_pattern_emits_drift_warning(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir()
    (tmp_path / "agent_reports").mkdir()
    rows = "\n".join(
        f"| {num} | ticket-{num:03d} | done | README manual synthnote cross-link | b | r |"
        for num in range(94, 112)
    )
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(rows, encoding="utf-8")
    (tmp_path / "agent_reports" / "2026-06-14_principal-audit-post-ticket-110.md").write_text(
        "# audit", encoding="utf-8"
    )
    (tmp_path / "tickets" / "ticket-111.json").write_text(
        '{"id":"ticket-111","title":"README manual synthnote pipeline proof test cross-link","risk_level":"low"}',
        encoding="utf-8",
    )

    report = checkpoint_status(root=tmp_path, next_ticket_id="ticket-111")
    assert report["drift_warning"] is not None
    assert report["next_ticket_value_class"] == "docs_crosslink"
    assert report["recommended_override"] is not None


def test_product_risk_ticket_reduces_drift_pressure() -> None:
    crosslink_rows = [
        type("Row", (), {"ticket_id": f"ticket-{n:03d}", "title": title, "status": "done"})()
        for n, title in (
            (108, "Operating protocol manual synthnote pipeline proof test cross-link"),
            (109, "Cursor build loop manual synthnote pipeline proof test cross-link"),
            (110, "Runtime config manual synthnote pipeline proof test cross-link"),
        )
    ]
    drift = evaluate_value_drift(crosslink_rows)
    assert drift["drift_warning"] is not None

    with_product = crosslink_rows + [
        type(
            "Row",
            (),
            {
                "ticket_id": "ticket-086",
                "title": "Real manual source ingestion (Level-1)",
                "status": "done",
            },
        )()
    ]
    reduced = evaluate_value_drift(with_product)
    assert reduced["drift_warning"] is None
    assert any(
        item["value_class"] == "product_risk_reduction"
        for item in reduced["recent_ticket_classifications"]
    )
