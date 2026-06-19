"""Unit tests for selective full-text acquisition (MVP-P5)."""

from __future__ import annotations

import json

import pytest

from rge.modules.selective_fulltext import (
    FULL_TEXT_CLEAN_TEXT_READY,
    FULL_TEXT_NOT_NEEDED,
    acquire_full_text,
    acquire_selective_fulltext,
    resolve_fulltext_location,
    should_request_full_text,
)
from rge.modules.source_resolver import load_manual_fixture_records


def test_resolve_fulltext_location_prefers_tei() -> None:
    record = {
        "tei_url": "https://example.org/paper.tei.xml",
        "pdf_url": "https://example.org/paper.pdf",
    }
    location = resolve_fulltext_location(record)

    assert location is not None
    assert location["kind"] == "tei"


def test_should_request_full_text_when_zero_abstract_claims() -> None:
    record = {"pdf_url": "https://example.org/paper.pdf", "source_id": "x:1"}
    requested, reason = should_request_full_text(
        record,
        abstract_card={"accepted_count": 0, "status": "completed"},
    )

    assert requested is True
    assert reason == "zero_abstract_claims"


def test_should_skip_full_text_when_abstract_sufficient() -> None:
    record = {"pdf_url": "https://example.org/paper.pdf", "source_id": "x:1"}
    requested, reason = should_request_full_text(
        record,
        abstract_card={"accepted_count": 2, "status": "completed"},
    )

    assert requested is False
    assert reason == "abstract_sufficient"


def test_acquire_full_text_fixture_tei_record() -> None:
    records = load_manual_fixture_records(domain_pack="creativity")
    tei_record = next(record for record in records if record.get("tei_url"))
    result = acquire_full_text(
        tei_record,
        fixture_mode=True,
        force=True,
    )

    assert result["acquisition_status"] == FULL_TEXT_CLEAN_TEXT_READY
    assert "Human-AI co-creativity" in str(result.get("clean_text") or "")


def test_acquire_full_text_fixture_pdf_simulation() -> None:
    records = load_manual_fixture_records(domain_pack="creativity")
    pdf_record = next(record for record in records if record.get("pdf_url"))
    result = acquire_full_text(
        pdf_record,
        fixture_mode=True,
        force=True,
    )

    assert result["acquisition_status"] == FULL_TEXT_CLEAN_TEXT_READY


def test_acquire_selective_fulltext_fixture_mode() -> None:
    records = load_manual_fixture_records(domain_pack="creativity")
    abstract_evidence = {
        "cards": [
            {
                "source_id": record["source_id"],
                "accepted_count": 0 if not record.get("abstract_text") else 1,
                "status": "completed",
            }
            for record in records
        ]
    }
    result = acquire_selective_fulltext(
        records,
        abstract_evidence=abstract_evidence,
        top_n=2,
        fixture_mode=True,
    )

    assert result["acquisition_count"] == 2
    assert FULL_TEXT_NOT_NEEDED in result["status_counts"] or FULL_TEXT_CLEAN_TEXT_READY in result["status_counts"]
