"""Unit tests for claim rejection diagnostics (ticket-061)."""

from __future__ import annotations

from rge.modules.claim_validator import (
    REJECTION_OVERGENERALIZED,
    rejection_diagnostic,
    validate_candidate_claim,
)


def test_rejection_diagnostic_scope_must_appear_in_claim_text() -> None:
    candidate = {
        "claim_text": "AI-assisted brainstorming increased average idea quality across submitted ideas.",
        "source_id": "src_1",
        "chunk_id": "chk_1",
        "quote_span": "AI-assisted brainstorming increased average idea quality across submitted ideas.",
        "scope": "short-form writing tasks",
        "subject": "AI-assisted brainstorming",
        "predicate": "increased",
        "object": "average idea quality",
        "evidence_type": "empirical",
        "confidence": 0.5,
        "limitations": [],
        "domain": "creativity",
    }
    chunk_text = candidate["quote_span"]
    status, _, reason = validate_candidate_claim(candidate, chunk_text=chunk_text)
    assert status == "rejected"
    assert reason == REJECTION_OVERGENERALIZED
    diagnostic = rejection_diagnostic(
        candidate, chunk_text=chunk_text, rejection_reason=reason
    )
    assert "verbatim" in diagnostic


def test_scoped_claim_with_scope_in_text_is_accepted() -> None:
    candidate = {
        "claim_text": "AI-assisted brainstorming increased average idea quality in short-form writing tasks.",
        "source_id": "src_1",
        "chunk_id": "chk_1",
        "quote_span": "AI-assisted brainstorming increased average idea quality across submitted ideas",
        "subject": "AI-assisted brainstorming",
        "predicate": "increased",
        "object": "average idea quality",
        "scope": "short-form writing tasks",
        "evidence_type": "empirical",
        "confidence": 0.7,
        "limitations": ["Only tested short-form writing tasks."],
        "domain": "creativity",
    }
    chunk_text = (
        "In a controlled study of short-form writing tasks, we found that "
        "AI-assisted brainstorming increased average idea quality across submitted ideas."
    )
    status, _, reason = validate_candidate_claim(candidate, chunk_text=chunk_text)
    assert status == "accepted"
    assert reason is None


def test_overgeneralized_pattern_still_rejected() -> None:
    candidate = {
        "claim_text": "AI reduces creativity in short-form writing tasks.",
        "source_id": "src_1",
        "chunk_id": "chk_1",
        "quote_span": "AI-assisted brainstorming reduced semantic diversity across submitted ideas.",
        "subject": "AI",
        "predicate": "reduces",
        "object": "creativity",
        "scope": "short-form writing tasks",
        "evidence_type": "empirical",
        "confidence": 0.9,
        "limitations": [],
        "domain": "creativity",
    }
    chunk_text = candidate["quote_span"]
    status, _, reason = validate_candidate_claim(candidate, chunk_text=chunk_text)
    assert status == "rejected"
    assert reason == REJECTION_OVERGENERALIZED
