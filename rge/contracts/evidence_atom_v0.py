"""Purpose metadata, evidence atom, and evidence card contracts v0.1.0.

These contracts are operator-private foundations for the research-to-asset
layer. Public export surfaces must opt in separately through safety allowlists.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

PURPOSE_SCHEMA_VERSION = "purpose_metadata_v0.1.0"
EVIDENCE_ATOM_SCHEMA_VERSION = "evidence_atom_v0.1.0"
EVIDENCE_CARD_SCHEMA_VERSION = "evidence_card_v0.1.0"

ResearchIntent = Literal[
    "evidence_review",
    "theory_building",
    "contradiction_mapping",
    "style_taxonomy",
    "visual_descriptor_mining",
    "product_strategy",
    "benchmark_design",
    "training_data_mining",
    "eval_design",
    "concept_ontology_building",
    "field_mapping",
    "historical_context",
]

AssetAffordance = Literal[
    "reasoning_training_candidate",
    "visual_descriptor_candidate",
    "eval_question_candidate",
    "concept_ontology_candidate",
    "prompt_pattern_candidate",
    "public_card_candidate",
    "memo_candidate",
    "argument_map_candidate",
    "contradiction_map_candidate",
    "dataset_curation_candidate",
    "style_vocabulary_candidate",
    "product_principle_candidate",
]

EvidenceNeed = Literal[
    "abstract_only_ok",
    "full_text_preferred",
    "full_text_required",
    "empirical_required",
    "theory_ok",
    "mixed_empirical_theory",
    "visual_examples_required",
    "historical_sources_required",
]

EvidenceMaturity = Literal[
    "seed",
    "weak",
    "promising",
    "clustered",
    "synthesis_ready",
    "eval_ready",
    "training_ready",
    "rejected",
]

TrainingSuitability = Literal[
    "not_ready",
    "candidate",
    "needs_human_review",
    "eval_ready",
    "training_ready",
    "do_not_train",
]

EvidenceAtomType = Literal[
    "claim",
    "definition",
    "distinction",
    "mechanism",
    "method",
    "statistic",
    "limitation",
    "contradiction",
    "design_principle",
    "visual_descriptor",
    "evaluation_rubric",
    "open_question",
]

EvidenceCardType = Literal[
    "evidence_claim",
    "evidence_cluster",
    "source_summary",
    "concept_definition",
]

Stance = Literal[
    "supports",
    "contradicts",
    "qualifies",
    "defines",
    "contextualizes",
    "extends",
]

ConfidenceLabel = Literal["low", "medium", "high"]


class EvidenceContractValidationError(ValueError):
    """Raised when a purpose/evidence payload fails contract validation."""


class ResearchPurposeMetadata_v0_1(BaseModel):
    schema_version: Literal["purpose_metadata_v0.1.0"] = PURPOSE_SCHEMA_VERSION
    question_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    research_intent: list[ResearchIntent] = Field(min_length=1)
    asset_affordance: list[AssetAffordance] = Field(min_length=1)
    evidence_need: EvidenceNeed
    acceptable_source_types: list[str] = Field(default_factory=list)
    output_targets: list[str] = Field(default_factory=list)
    evidence_maturity: EvidenceMaturity = "seed"
    training_suitability: TrainingSuitability = "not_ready"
    classifier_version: str = "purpose_classifier_v0.1.0"


class EvidenceAtom_v0_1(BaseModel):
    schema_version: Literal["evidence_atom_v0.1.0"] = EVIDENCE_ATOM_SCHEMA_VERSION
    atom_id: str = Field(min_length=1)
    atom_type: EvidenceAtomType = "claim"
    canonical_text: str = Field(min_length=1, max_length=1200)
    source_claim_ids: list[str] = Field(min_length=1)
    source_quote_ids: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    stance_profile: dict[str, int] = Field(default_factory=dict)
    support_count: int = Field(ge=0)
    contradiction_count: int = Field(ge=0)
    scope: str = Field(min_length=1, max_length=800)
    evidence_type: str = Field(min_length=1)
    asset_tags: list[AssetAffordance] = Field(default_factory=list)
    evidence_maturity: EvidenceMaturity = "seed"
    training_suitability: TrainingSuitability = "not_ready"
    confidence: ConfidenceLabel = "low"

    @field_validator("source_claim_ids")
    @classmethod
    def _source_claims_are_claim_ids(cls, value: list[str]) -> list[str]:
        if any(not item.startswith("clm_") for item in value):
            raise ValueError("source_claim_ids must contain stable clm_ identifiers")
        return value

    @field_validator("source_quote_ids")
    @classmethod
    def _source_quotes_are_quote_ids(cls, value: list[str]) -> list[str]:
        if any(not (item.startswith("qt_") or item.startswith("quote_")) for item in value):
            raise ValueError("source_quote_ids must contain stable quote identifiers")
        return value


class EvidenceCardSource_v0_1(BaseModel):
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    url: str | None = None
    source_type: str = Field(min_length=1)


class EvidenceCard_v0_1(BaseModel):
    schema_version: Literal["evidence_card_v0.1.0"] = EVIDENCE_CARD_SCHEMA_VERSION
    card_type: EvidenceCardType = "evidence_claim"
    claim: str = Field(min_length=1, max_length=1200)
    quote: str = Field(min_length=1, max_length=600)
    source: EvidenceCardSource_v0_1
    stance: Stance
    evidence_type: str = Field(min_length=1)
    scope: str = Field(min_length=1, max_length=800)
    concepts: list[str] = Field(default_factory=list)
    confidence: ConfidenceLabel
    limitations: list[str] = Field(default_factory=list)
    asset_tags: list[AssetAffordance] = Field(default_factory=list)
    evidence_maturity: EvidenceMaturity = "seed"


def validate_research_purpose(payload: dict[str, Any]) -> ResearchPurposeMetadata_v0_1:
    """Validate deterministic research-purpose metadata."""
    try:
        return ResearchPurposeMetadata_v0_1.model_validate(payload)
    except ValidationError as exc:
        raise EvidenceContractValidationError(str(exc)) from exc


def validate_evidence_atom(payload: dict[str, Any]) -> EvidenceAtom_v0_1:
    """Validate an evidence atom candidate."""
    try:
        return EvidenceAtom_v0_1.model_validate(payload)
    except ValidationError as exc:
        raise EvidenceContractValidationError(str(exc)) from exc


def validate_evidence_card(payload: dict[str, Any]) -> EvidenceCard_v0_1:
    """Validate a canonical operator-private evidence card."""
    try:
        return EvidenceCard_v0_1.model_validate(payload)
    except ValidationError as exc:
        raise EvidenceContractValidationError(str(exc)) from exc
