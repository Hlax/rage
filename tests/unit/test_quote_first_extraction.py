"""Quote-first extraction hardening tests."""

from __future__ import annotations

from rge.modules.claim_extractor import extract_and_validate_for_chunk
from rge.modules.claim_validator import (
    REJECTION_OVERGENERALIZED,
    REJECTION_ZERO_QUOTEABLE,
    validate_candidate_claim,
)


def test_extract_and_validate_returns_zero_quoteable_for_dirty_chunk() -> None:
    result = extract_and_validate_for_chunk(
        {
            "id": "chk_dirty",
            "source_id": "src_dirty",
            "chunk_text": "bad",
        },
        domain_pack="creativity",
    )

    assert result["accepted"] == []
    assert len(result["rejected"]) == 1
    assert result["rejected"][0]["rejection_reason"] == REJECTION_ZERO_QUOTEABLE


def test_validate_rejects_scope_not_entailed_by_quote() -> None:
    chunk_text = (
        "AI-assisted brainstorming reduced semantic diversity in short-form writing tasks."
    )
    candidate = {
        "source_id": "src_1",
        "chunk_id": "chk_1",
        "claim_text": (
            "AI-assisted brainstorming reduced semantic diversity in ideation studies."
        ),
        "quote_span": (
            "AI-assisted brainstorming reduced semantic diversity in short-form writing tasks"
        ),
        "subject": "AI-assisted brainstorming",
        "predicate": "reduced",
        "object": "semantic diversity",
        "scope": "ideation studies",
        "evidence_type": "empirical",
        "confidence": 0.7,
        "limitations": [],
        "domain": "creativity",
    }

    status, _, reason = validate_candidate_claim(candidate, chunk_text=chunk_text)

    assert status == "rejected"
    assert reason == REJECTION_OVERGENERALIZED


def test_fixture_mode_still_extracts_scoped_claims_from_golden_chunk() -> None:
    chunk_text = (
        "In a controlled study of short-form writing tasks, we found that "
        "AI-assisted brainstorming increased average idea quality across submitted ideas. "
        "AI-assisted brainstorming reduced semantic diversity across submitted ideas."
    )
    result = extract_and_validate_for_chunk(
        {
            "id": "chk_fixture",
            "source_id": "src_fixture",
            "chunk_text": chunk_text,
        },
        domain_pack="creativity",
        fixture_name="claim_extraction_creativity_scoped.json",
        skip_quoteability_gate=True,
    )

    assert result["accepted"]
    assert all(claim["quote_span"] for claim in result["accepted"])
