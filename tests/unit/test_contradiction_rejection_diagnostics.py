"""Unit tests for contradiction rejection diagnostics (ticket-064)."""

from __future__ import annotations

from rge.modules.contradiction_detector import (
    REJECTION_INVALID_CLASSIFICATION,
    REJECTION_MISSING_BASE_RELATIONSHIP,
    contradiction_rejection_diagnostic,
    validate_contradiction_probe_batch,
    claim_dicts_as_objects,
)


def test_contradiction_rejection_diagnostic_missing_base_relationship() -> None:
    diagnostic = contradiction_rejection_diagnostic(
        {
            "base_subject_concept": "AI assistance",
            "base_predicate": "unknown_predicate",
            "base_object_concept": "semantic diversity",
        },
        rejection_reason=REJECTION_MISSING_BASE_RELATIONSHIP,
        relationship_triples={
            ("AI assistance", "may_reduce", "semantic diversity"),
        },
    )
    assert "base relationship triple" in diagnostic
    assert "may_reduce" in diagnostic


def test_validate_contradiction_probe_batch_accepts_valid_link() -> None:
    source_claims = claim_dicts_as_objects(
        [
            {
                "id": "claim_live_probe_qualify_001",
                "claim_text": "AI-assisted brainstorming increased idea diversity when participants were instructed to generate multiple divergent directions.",
            }
        ]
    )
    domain_claims = claim_dicts_as_objects(
        [
            {
                "id": "claim_live_probe_qualify_001",
                "claim_text": "AI-assisted brainstorming increased idea diversity when participants were instructed to generate multiple divergent directions.",
            },
            {
                "id": "claim_live_probe_oppose_001",
                "claim_text": "AI-assisted brainstorming reduced semantic diversity across submitted ideas.",
            },
        ]
    )
    relationships = [
        {
            "id": "rel_live_probe_base_001",
            "subject_concept": "AI assistance",
            "predicate": "may_reduce",
            "object_concept": "semantic diversity",
        },
        {
            "id": "rel_live_probe_new_001",
            "subject_concept": "AI assistance",
            "predicate": "may_increase",
            "object_concept": "diversity",
        },
    ]
    candidates = [
        {
            "base_subject_concept": "AI assistance",
            "base_predicate": "may_reduce",
            "base_object_concept": "semantic diversity",
            "new_subject_concept": "AI assistance",
            "new_predicate": "may_increase",
            "new_object_concept": "diversity",
            "qualification_stance": "qualifies",
            "contradiction_classification": (
                "apparent_contradiction_metric_or_condition_difference"
            ),
        }
    ]
    validated = validate_contradiction_probe_batch(
        candidates,
        source_claims=source_claims,
        domain_claims=domain_claims,
        relationships=relationships,
    )
    assert len(validated["accepted"]) == 1
    assert not validated["rejected"]


def test_validate_contradiction_probe_batch_rejects_invalid_classification() -> None:
    source_claims = claim_dicts_as_objects(
        [{"id": "claim_live_probe_qualify_001", "claim_text": "increased idea diversity"}]
    )
    domain_claims = claim_dicts_as_objects(
        [
            {"id": "claim_live_probe_qualify_001", "claim_text": "increased idea diversity"},
            {
                "id": "claim_live_probe_oppose_001",
                "claim_text": "reduced semantic diversity",
            },
        ]
    )
    relationships = [
        {
            "id": "rel_live_probe_base_001",
            "subject_concept": "AI assistance",
            "predicate": "may_reduce",
            "object_concept": "semantic diversity",
        },
        {
            "id": "rel_live_probe_new_001",
            "subject_concept": "AI assistance",
            "predicate": "may_increase",
            "object_concept": "diversity",
        },
    ]
    candidates = [
        {
            "base_subject_concept": "AI assistance",
            "base_predicate": "may_reduce",
            "base_object_concept": "semantic diversity",
            "new_subject_concept": "AI assistance",
            "new_predicate": "may_increase",
            "new_object_concept": "diversity",
            "qualification_stance": "qualifies",
            "contradiction_classification": "resolved_contradiction",
        }
    ]
    validated = validate_contradiction_probe_batch(
        candidates,
        source_claims=source_claims,
        domain_claims=domain_claims,
        relationships=relationships,
    )
    assert not validated["accepted"]
    assert validated["rejected"][0]["rejection_reason"] == REJECTION_INVALID_CLASSIFICATION
    diagnostic = contradiction_rejection_diagnostic(
        validated["rejected"][0],
        rejection_reason=REJECTION_INVALID_CLASSIFICATION,
    )
    assert "apparent_contradiction_metric_or_condition_difference" in diagnostic
