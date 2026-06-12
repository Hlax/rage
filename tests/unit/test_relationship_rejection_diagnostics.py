"""Unit tests for relationship rejection diagnostics (ticket-063)."""

from __future__ import annotations

from rge.modules.relationship_builder import (
    REJECTION_INVALID_CONFIDENCE,
    REJECTION_MISSING_EVIDENCE,
    REJECTION_MISSING_SCOPE,
    relationship_rejection_diagnostic,
    validate_relationship_candidates,
)


def test_relationship_rejection_diagnostic_missing_scope() -> None:
    diagnostic = relationship_rejection_diagnostic(
        {"subject_concept": "AI assistance", "object_concept": "ideation"},
        rejection_reason=REJECTION_MISSING_SCOPE,
    )
    assert "scope" in diagnostic


def test_validate_relationship_candidates_accepts_valid_edge() -> None:
    candidates = [
        {
            "subject_concept": "AI assistance",
            "predicate": "supports",
            "object_concept": "ideation",
            "stance": "supports",
            "scope": "short-form writing tasks",
            "confidence": "medium",
            "supporting_claim_ids": ["claim_live_probe_link_001"],
        }
    ]
    validated = validate_relationship_candidates(
        candidates,
        accepted_claim_ids={"claim_live_probe_link_001"},
        concept_labels={"AI assistance", "ideation", "brainstorming"},
    )
    assert len(validated["accepted"]) == 1
    assert not validated["rejected"]


def test_validate_relationship_candidates_rejects_invalid_confidence() -> None:
    candidates = [
        {
            "subject_concept": "AI assistance",
            "predicate": "supports",
            "object_concept": "ideation",
            "stance": "supports",
            "scope": "short-form writing tasks",
            "confidence": "0.8",
            "supporting_claim_ids": ["claim_live_probe_link_001"],
        }
    ]
    validated = validate_relationship_candidates(
        candidates,
        accepted_claim_ids={"claim_live_probe_link_001"},
        concept_labels={"AI assistance", "ideation"},
    )
    assert not validated["accepted"]
    assert validated["rejected"][0]["rejection_reason"] == REJECTION_INVALID_CONFIDENCE
    diagnostic = relationship_rejection_diagnostic(
        validated["rejected"][0],
        rejection_reason=REJECTION_INVALID_CONFIDENCE,
    )
    assert "low, medium, or high" in diagnostic


def test_validate_relationship_candidates_rejects_missing_evidence_claim() -> None:
    candidates = [
        {
            "subject_concept": "AI assistance",
            "predicate": "supports",
            "object_concept": "ideation",
            "stance": "supports",
            "scope": "short-form writing tasks",
            "confidence": "medium",
            "supporting_claim_ids": ["unknown_claim"],
        }
    ]
    validated = validate_relationship_candidates(
        candidates,
        accepted_claim_ids={"claim_live_probe_link_001"},
        concept_labels={"AI assistance", "ideation"},
    )
    assert validated["rejected"][0]["rejection_reason"] == REJECTION_MISSING_EVIDENCE
    diagnostic = relationship_rejection_diagnostic(
        validated["rejected"][0],
        rejection_reason=REJECTION_MISSING_EVIDENCE,
        accepted_claim_ids={"claim_live_probe_link_001"},
    )
    assert "claim_live_probe_link_001" in diagnostic
