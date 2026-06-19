"""Unit tests for failure-to-packet recommender (MVP-P4)."""

from __future__ import annotations

import json

import pytest

from rge.cli import main
from rge.modules.failure_recommender import (
    PACKET_PDF_PARSER,
    PACKET_QUALITY_GATES,
    PACKET_SOURCE_RESOLVER,
    PACKET_FIELD_MAP,
    PACKET_WEB_ADAPTER,
    REJECTION_UNSUPPORTED_WALL,
    classify_dominant_bottleneck,
    recommend_improvement_packet,
    recommend_from_abstract_evidence_run,
    recommend_from_run_report,
)
from rge.modules.source_resolver.status import METADATA_ONLY, PARSE_FAILED


def test_unsupported_claim_wall_recommends_pdf_parser_packet() -> None:
    result = recommend_improvement_packet(
        rejection_reasons=["unsupported_claim"] * 9,
        run_metrics={"claims_accepted": 1, "claims_rejected": 9},
    )

    assert result["dominant_signal"] == REJECTION_UNSUPPORTED_WALL
    assert result["recommended_packet"] == PACKET_PDF_PARSER


def test_metadata_only_sources_recommend_resolver_packet() -> None:
    result = recommend_improvement_packet(
        source_statuses=[METADATA_ONLY, METADATA_ONLY, METADATA_ONLY],
        run_metrics={"claims_accepted": 0, "claims_rejected": 0},
    )

    assert result["dominant_signal"] == METADATA_ONLY
    assert result["recommended_packet"] == PACKET_SOURCE_RESOLVER


def test_parse_failed_recommends_pdf_parser() -> None:
    classification = classify_dominant_bottleneck(
        source_statuses=[PARSE_FAILED, PARSE_FAILED],
        rejection_reasons=["unsupported_claim"],
    )
    result = recommend_improvement_packet(
        source_statuses=[PARSE_FAILED, PARSE_FAILED],
        run_metrics={"claims_accepted": 0, "claims_rejected": 4},
    )

    assert classification["dominant_signal"] == PARSE_FAILED
    assert result["recommended_packet"] == PACKET_PDF_PARSER


def test_weak_synthesis_recommends_field_map_when_claims_accepted() -> None:
    result = recommend_improvement_packet(
        run_metrics={"claims_accepted": 8, "claims_rejected": 0},
    )

    assert result["dominant_signal"] == "weak_synthesis"
    assert result["recommended_packet"] == PACKET_FIELD_MAP


def test_recommend_from_abstract_evidence_fixture_shape() -> None:
    evidence = {
        "accepted_claims_total": 2,
        "rejected_claims_total": 0,
        "cards": [{"status": "completed", "rejected_claims": []}],
    }
    result = recommend_from_abstract_evidence_run(
        evidence,
        source_statuses=["abstract_available", "metadata_only"],
    )

    assert result["recommended_packet"]
    assert result["source_run"] == "abstract_evidence"


def test_recommend_improvement_packet_cli_fixture_mode(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["recommend-improvement-packet", "--fixture-mode"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["recommended_packet"].startswith("MVP-P")


def test_recommend_from_run_report_quality_gate_blocks() -> None:
    run_report = {
        "claims_accepted": 0,
        "claims_rejected": 0,
        "top_failure_modes": [],
        "acquisition_quality_summary": {
            "acquisition_status_counts": {"dirty_text": 3},
            "source_type_counts": {"selective_fulltext": 3},
            "parser_backend_counts": {"pymupdf": 3},
        },
    }
    result = recommend_from_run_report(run_report)

    assert result["source_run"] == "run_report"
    assert result["recommended_packet"] == PACKET_QUALITY_GATES
    assert result["dominant_signal"] == "blocked_by_quality_gate"


def test_recommend_from_run_report_webpage_dirty_text() -> None:
    run_report = {
        "claims_accepted": 0,
        "claims_rejected": 0,
        "top_failure_modes": [],
        "acquisition_quality_summary": {
            "acquisition_status_counts": {"dirty_text": 1},
            "source_type_counts": {"webpage": 1},
            "parser_backend_counts": {"html_to_text": 1},
        },
    }
    result = recommend_from_run_report(run_report)

    assert result["recommended_packet"] in {PACKET_WEB_ADAPTER, PACKET_QUALITY_GATES}
    assert result["source_run"] == "run_report"
