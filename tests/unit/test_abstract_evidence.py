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
)
from rge.modules.source_resolver import load_manual_fixture_records

REPO_ROOT = Path(__file__).resolve().parents[2]


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
