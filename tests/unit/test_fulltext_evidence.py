"""Unit tests for full-text evidence extraction."""

from __future__ import annotations

from rge.modules.fulltext_evidence import (
    FULLTEXT_EVIDENCE_BASIS,
    extract_fulltext_evidence_card,
    generate_fulltext_evidence_cards,
)
from rge.modules.selective_fulltext import FULL_TEXT_CLEAN_TEXT_READY, acquire_full_text
from rge.modules.source_resolver import load_manual_fixture_records


def test_extract_fulltext_evidence_card_from_fixture_acquisition() -> None:
    records = load_manual_fixture_records(domain_pack="creativity")
    tei_record = next(record for record in records if record.get("tei_url"))
    acquisition = acquire_full_text(tei_record, fixture_mode=True, force=True)

    assert acquisition["acquisition_status"] == FULL_TEXT_CLEAN_TEXT_READY
    card = extract_fulltext_evidence_card(acquisition, domain_pack="creativity")

    assert card["status"] == "completed"
    assert card["evidence_basis"] == FULLTEXT_EVIDENCE_BASIS
    assert card["accepted_count"] >= 1
    quote = card["accepted_claims"][0]["quote_span"]
    assert quote in acquisition["clean_text"]


def test_generate_fulltext_evidence_cards_counts() -> None:
    records = load_manual_fixture_records(domain_pack="creativity")
    acquisitions = [
        acquire_full_text(record, fixture_mode=True, force=True)
        for record in records
        if record.get("tei_url") or record.get("pdf_url")
    ]
    result = generate_fulltext_evidence_cards(acquisitions, domain_pack="creativity")

    assert result["completed_count"] >= 1
    assert result["accepted_claims_total"] >= 1
