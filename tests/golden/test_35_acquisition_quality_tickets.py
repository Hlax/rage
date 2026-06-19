"""Golden Test 35: acquisition quality summary seeds improvement tickets."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.cli import main
from rge.modules.failure_recommender import (
    PACKET_QUALITY_GATES,
    recommend_from_run_report,
)
from rge.modules.ticket_writer import validate_builder_ticket, write_improvement_tickets

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_acquisition_summary_seeds_improvement_tickets() -> None:
    run_report = {
        "run_id": "run_gt35_acquisition",
        "top_failure_modes": [],
        "acquisition_quality_summary": {
            "sources_with_metadata": 2,
            "acquisition_status_counts": {"dirty_text": 2, "parse_failed": 1},
            "source_type_counts": {"webpage": 1, "selective_fulltext": 1},
            "parser_backend_counts": {"html_to_text": 1, "pdf_unavailable": 1},
        },
    }
    tickets = write_improvement_tickets(run_report)
    reasons = {ticket["failure_reason"] for ticket in tickets}
    assert "blocked_by_quality_gate" in reasons
    assert "parse_failed" in reasons
    assert "webpage_dirty_text" in reasons
    assert "pdf_parser_unavailable" in reasons
    for ticket in tickets:
        assert validate_builder_ticket(ticket) == []


def test_recommend_improvement_packet_cli_run_report_with_acquisition_summary(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report_path = tmp_path / "run_report_gt35.json"
    report_path.write_text(
        json.dumps(
            {
                "claims_accepted": 0,
                "claims_rejected": 0,
                "top_failure_modes": [],
                "acquisition_quality_summary": {
                    "acquisition_status_counts": {"dirty_text": 2},
                    "source_type_counts": {"selective_fulltext": 2},
                },
            }
        ),
        encoding="utf-8",
    )
    os.environ["RGE_LLM_MODE"] = "mock"
    exit_code = main(
        [
            "recommend-improvement-packet",
            "--run-report",
            str(report_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["input"] == "run_report"
    assert payload["recommended_packet"] == PACKET_QUALITY_GATES
    assert payload["source_run"] == "run_report"


def test_recommend_from_run_report_matches_cli_input_shape() -> None:
    run_report = {
        "claims_accepted": 0,
        "claims_rejected": 0,
        "top_failure_modes": [],
        "acquisition_quality_summary": {
            "acquisition_status_counts": {"dirty_text": 2},
            "source_type_counts": {"selective_fulltext": 2},
        },
    }
    result = recommend_from_run_report(run_report)
    assert result["status"] == "ok"
    assert result["recommended_packet"] == PACKET_QUALITY_GATES
