"""Unit tests for concept-link rejection diagnostics (ticket-062)."""

from __future__ import annotations

from rge.modules.concept_linker import (
    REJECTION_WEAK_CONCEPT_MAPPING,
    link_rejection_diagnostic,
    validate_concept_links,
)


def test_link_rejection_diagnostic_missing_claim_id() -> None:
    diagnostic = link_rejection_diagnostic(
        {"concept_label": "brainstorming", "confidence": 0.8},
        rejection_reason=REJECTION_WEAK_CONCEPT_MAPPING,
    )
    assert "claim_id" in diagnostic


def test_link_rejection_diagnostic_generic_only_batch() -> None:
    links = [
        {
            "claim_id": "claim_1",
            "concept_label": "creativity",
            "confidence": 0.7,
        }
    ]
    validated = validate_concept_links(links)
    assert not validated["accepted"]
    assert validated["rejected"][0]["rejection_reason"] == REJECTION_WEAK_CONCEPT_MAPPING
    diagnostic = link_rejection_diagnostic(
        validated["rejected"][0],
        rejection_reason=REJECTION_WEAK_CONCEPT_MAPPING,
    )
    assert "specific concept labels" in diagnostic


def test_validate_concept_links_still_requires_two_specific_labels() -> None:
    links = [
        {
            "claim_id": "claim_1",
            "concept_label": "brainstorming",
            "confidence": 0.8,
        },
        {
            "claim_id": "claim_1",
            "concept_label": "AI assistance",
            "confidence": 0.85,
        },
    ]
    validated = validate_concept_links(links)
    assert len(validated["accepted"]) == 2
    assert not validated["rejected"]


def test_validate_concept_links_rejects_missing_confidence() -> None:
    links = [
        {
            "claim_id": "claim_1",
            "concept_label": "brainstorming",
            "confidence": 0.8,
        },
        {
            "claim_id": "claim_1",
            "concept_label": "ideation",
        },
    ]
    validated = validate_concept_links(links)
    assert len(validated["accepted"]) == 1
    assert validated["rejected"][0]["rejection_reason"] == REJECTION_WEAK_CONCEPT_MAPPING
