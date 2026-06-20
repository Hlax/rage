"""Unit tests for abstract-first evidence cards (MVP-P2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.cli import main
from rge.modules.abstract_evidence import (
    ABSTRACT_EVIDENCE_BASIS,
    build_abstract_chunk,
    extract_abstract_evidence_card,
    generate_abstract_evidence_cards,
    propose_quote_grounded_claim_from_abstract,
    select_quote_span_from_abstract,
)
from rge.modules.source_resolver import load_manual_fixture_records

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_select_quote_span_from_realistic_abstract() -> None:
    abstract = (
        "Recent studies show that generative AI tools can assist creative writing workflows. "
        "However, empirical evidence on semantic diversity remains limited."
    )
    quote = select_quote_span_from_abstract(abstract)
    assert quote
    assert quote in abstract


def test_propose_quote_grounded_claim_from_abstract_is_validator_ready() -> None:
    abstract = (
        "This paper examines how AI-assisted brainstorming affects rated idea diversity "
        "under explicit divergent-generation instructions in creative tasks."
    )
    claim = propose_quote_grounded_claim_from_abstract(
        abstract,
        source_id="openalex:W123",
        chunk_id="abstract_openalex_W123",
        domain_pack="creativity",
    )
    assert claim is not None
    assert claim["quote_span"] in abstract


def test_extract_live_abstract_evidence_accepts_quote_grounded_claim() -> None:
    abstract = (
        "This study investigates human-AI co-creativity in songwriting workflows and "
        "reports measurable changes in lyrical originality under assisted drafting."
    )
    record = {
        "source_id": "openalex:W_live_abstract_test",
        "source_status": "abstract_available",
        "abstract_text": abstract,
        "title": "Human-AI co-creativity in songwriting",
        "source_kind": "openalex",
    }
    card = extract_abstract_evidence_card(
        record,
        domain_pack="creativity",
        live_abstract_mode=True,
    )
    assert card["status"] == "completed"
    assert card["extraction_mode"] == "live_deterministic_quote"
    assert card["accepted_count"] >= 1
    assert card["accepted_claims"][0]["quote_span"] in abstract


def test_build_abstract_chunk_from_manual_fixture() -> None:
    records = load_manual_fixture_records(domain_pack="creativity")
    abstract_record = next(
        record for record in records if record.get("abstract_text")
    )
    chunk = build_abstract_chunk(abstract_record)

    assert chunk is not None
    assert chunk["chunk_text"] == abstract_record["abstract_text"]
    assert chunk["source_id"] == abstract_record["source_id"]


def test_extract_abstract_evidence_card_accepts_quote_grounded_claim() -> None:
    records = load_manual_fixture_records(domain_pack="creativity")
    abstract_record = next(
        record
        for record in records
        if "idea diversity" in str(record.get("abstract_text") or "")
    )
    card = extract_abstract_evidence_card(abstract_record, domain_pack="creativity")

    assert card["status"] == "completed"
    assert card["evidence_basis"] == ABSTRACT_EVIDENCE_BASIS
    assert card["accepted_count"] >= 1
    claim = card["accepted_claims"][0]
    assert claim["quote_span"] in abstract_record["abstract_text"]


def test_metadata_only_record_is_skipped_without_llm() -> None:
    records = load_manual_fixture_records(domain_pack="creativity")
    metadata_record = next(
        record for record in records if not str(record.get("abstract_text") or "").strip()
    )
    card = extract_abstract_evidence_card(metadata_record, domain_pack="creativity")

    assert card["status"] == "skipped"
    assert card["accepted_claims"] == []
    assert card["skip_reason"] == "abstract_missing_or_not_extractable"


def test_generate_abstract_evidence_cards_fixture_mode() -> None:
    records = load_manual_fixture_records(domain_pack="creativity")
    result = generate_abstract_evidence_cards(records, domain_pack="creativity")

    assert result["evidence_basis"] == ABSTRACT_EVIDENCE_BASIS
    assert result["completed_count"] >= 1
    assert result["accepted_claims_total"] >= 1


def test_generate_abstract_evidence_cli_fixture_mode(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["generate-abstract-evidence", "--fixture-mode"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["accepted_claims_total"] >= 1
    assert payload["cards"][0]["evidence_basis"] in {ABSTRACT_EVIDENCE_BASIS, None}
