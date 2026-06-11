"""Versioned Pydantic schemas for candidate model outputs.

Every structured model output declares ``task_name`` and ``schema_version``.
Parsers fail closed on schema-version mismatch. Backward-incompatible changes
must increment the schema version and ship updated fixtures and golden tests.

These are CANDIDATE objects. Nothing here is trusted or accepted until the
deterministic validators in ``rge/modules`` approve it.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SCHEMA_VERSION_0_1_0 = "0.1.0"


class SchemaVersionError(Exception):
    """Raised when a model output declares an unexpected schema version."""


def validate_schema_version(declared: str, expected: str) -> None:
    """Fail closed when a model output's schema version does not match."""
    if declared != expected:
        raise SchemaVersionError(
            f"Model output declared schema_version={declared!r} but the parser "
            f"expects {expected!r}. Refusing to parse (fail closed)."
        )


class CandidateClaim_v0_1(BaseModel):
    """One candidate claim proposed by a model. Untrusted until validated."""

    claim_text: str
    source_id: str | None = None
    chunk_id: str | None = None
    quote_span: str | None = None  # missing quote spans get rejected downstream
    subject: str | None = None
    predicate: str | None = None
    object: str | None = None
    scope: str | None = None
    evidence_type: str | None = None
    confidence: float | None = None
    limitations: list[str] = Field(default_factory=list)
    domain: str | None = None
    domain_metadata: dict[str, str] = Field(default_factory=dict)


class CandidateClaimBatch_v0_1(BaseModel):
    task_name: Literal["claim_extraction"] = "claim_extraction"
    schema_version: str = SCHEMA_VERSION_0_1_0
    items: list[CandidateClaim_v0_1] = Field(default_factory=list)


class CandidateConceptLink_v0_1(BaseModel):
    claim_id: str
    concept_label: str
    role: str | None = None
    confidence: float | None = None
    domain_metadata: dict[str, str] = Field(default_factory=dict)


class CandidateConceptLinkBatch_v0_1(BaseModel):
    task_name: Literal["concept_linking"] = "concept_linking"
    schema_version: str = SCHEMA_VERSION_0_1_0
    items: list[CandidateConceptLink_v0_1] = Field(default_factory=list)


class CandidateRelationship_v0_1(BaseModel):
    subject_concept: str
    predicate: str
    object_concept: str
    stance: str | None = None  # supports, contradicts, qualifies
    scope: str | None = None
    confidence: str | None = None
    supporting_claim_ids: list[str] = Field(default_factory=list)


class CandidateRelationshipBatch_v0_1(BaseModel):
    task_name: Literal["relationship_drafting"] = "relationship_drafting"
    schema_version: str = SCHEMA_VERSION_0_1_0
    items: list[CandidateRelationship_v0_1] = Field(default_factory=list)


class CandidateContradiction_v0_1(BaseModel):
    """One candidate contradiction/qualification link. Untrusted until validated."""

    base_subject_concept: str
    base_predicate: str
    base_object_concept: str
    new_subject_concept: str
    new_predicate: str
    new_object_concept: str
    qualifying_claim_id: str | None = None
    opposing_claim_id: str | None = None
    qualification_stance: str = "qualifies"
    contradiction_classification: str = (
        "apparent_contradiction_metric_or_condition_difference"
    )


class CandidateContradictionBatch_v0_1(BaseModel):
    task_name: Literal["contradiction_detection"] = "contradiction_detection"
    schema_version: str = SCHEMA_VERSION_0_1_0
    items: list[CandidateContradiction_v0_1] = Field(default_factory=list)


class CandidateRunSummary_v0_1(BaseModel):
    task_name: Literal["run_summary"] = "run_summary"
    schema_version: str = SCHEMA_VERSION_0_1_0
    summary_text: str = ""
    top_failure_modes: list[str] = Field(default_factory=list)


class CandidateImprovementTicket_v0_1(BaseModel):
    task_name: Literal["ticket_drafting"] = "ticket_drafting"
    schema_version: str = SCHEMA_VERSION_0_1_0
    title: str = ""
    problem: str = ""
    evidence: list[str] = Field(default_factory=list)
    affected_modules: list[str] = Field(default_factory=list)
    expected_files: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    test_plan: list[str] = Field(default_factory=list)
    non_goals: list[str] = Field(default_factory=list)
    risk_level: str = "low"
    rollback_plan: str = ""
