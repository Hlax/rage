"""Improvement tickets seeded from acquisition_quality_summary."""

from __future__ import annotations

from rge.modules.ticket_writer import (
    ACQUISITION_FAILURE_TEMPLATES,
    validate_builder_ticket,
    write_improvement_tickets,
)


def test_write_improvement_tickets_from_acquisition_summary_only() -> None:
    run_report = {
        "run_id": "run_acq_quality_only",
        "top_failure_modes": [],
        "acquisition_quality_summary": {
            "sources_with_metadata": 2,
            "acquisition_status_counts": {"dirty_text": 2},
            "source_type_counts": {"webpage": 1, "selective_fulltext": 1},
            "parser_backend_counts": {"html_to_text": 1, "pymupdf": 1},
        },
    }
    tickets = write_improvement_tickets(run_report)
    reasons = {ticket["failure_reason"] for ticket in tickets}
    assert "blocked_by_quality_gate" in reasons
    assert "webpage_dirty_text" in reasons
    for ticket in tickets:
        assert validate_builder_ticket(ticket) == []
        assert any(
            item.startswith("acquisition_quality:run_acq_quality_only:")
            for item in ticket["evidence"]
        )


def test_acquisition_failure_templates_are_builder_consumable() -> None:
    run_report = {
        "run_id": "run_acq_template_check",
        "top_failure_modes": [],
        "acquisition_quality_summary": {
            "sources_with_metadata": 3,
            "acquisition_status_counts": {
                "dirty_text": 1,
                "parse_failed": 1,
            },
            "source_type_counts": {"webpage": 1, "selective_fulltext": 2},
            "parser_backend_counts": {"pdf_unavailable": 1},
        },
    }
    tickets = write_improvement_tickets(run_report)
    expected = set(ACQUISITION_FAILURE_TEMPLATES)
    assert expected.issubset({ticket["failure_reason"] for ticket in tickets})
    for ticket in tickets:
        if ticket["failure_reason"] in expected:
            assert validate_builder_ticket(ticket) == []
