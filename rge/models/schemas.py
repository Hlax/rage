"""Domain-neutral core entity schemas.

Domain-specific fields live in ``domain_metadata`` JSON, never as core columns
or core model fields. The structured research claim contract is private and
candidate-only until deterministic validation approves it.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict

STRUCTURED_RESEARCH_CLAIM_VERSION = "0.1.0"


class ClaimKind(str, Enum):
    EMPIRICAL_RESULT = "empirical_result"
    METHOD = "method"
    BACKGROUND = "background"
    HYPOTHESIS = "hypothesis"
    INTERPRETATION = "interpretation"
    SPECULATION = "speculation"


class StudyDesign(str, Enum):
    RANDOMIZED_CONTROLLED_TRIAL = "randomized_controlled_trial"
    CONTROLLED_TRIAL = "controlled_trial"
    EXPERIMENT = "experiment"
    COHORT = "cohort"
    CASE_CONTROL = "case_control"
    CROSS_SECTIONAL = "cross_sectional"
    LONGITUDINAL = "longitudinal"
    OBSERVATIONAL = "observational"
    QUALITATIVE = "qualitative"
    MIXED_METHODS = "mixed_methods"
    CASE_STUDY = "case_study"
    REVIEW = "review"
    META_ANALYSIS = "meta_analysis"
    SIMULATION = "simulation"
    OTHER = "other"


class EffectDirection(str, Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    NO_EFFECT = "no_effect"
    MIXED = "mixed"
    ASSOCIATION = "association"


class ClaimSectionType(str, Enum):
    TITLE_METADATA = "title_metadata"
    ABSTRACT = "abstract"
    INTRODUCTION_BACKGROUND = "introduction_background"
    METHODS = "methods"
    RESULTS = "results"
    DISCUSSION = "discussion"
    LIMITATIONS = "limitations"
    REFERENCES = "references"
    ACKNOWLEDGEMENTS = "acknowledgements"
    NAVIGATION = "navigation"
    BOILERPLATE = "boilerplate"
    UNKNOWN = "unknown"


class ClaimSectionProvenance_v0_1(BaseModel):
    """Exact persisted chunk provenance claimed by a candidate."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    section_type: ClaimSectionType
    section_title: str | None
    page: str | None
    char_start: int
    char_end: int


class StructuredResearchClaim_v0_1(BaseModel):
    """Explicit scientific context nested under a legacy candidate envelope.

    Every key is required even where ``null`` is allowed. This makes absence
    explicit and prevents the engine from fabricating unknown values.
    """

    model_config = ConfigDict(extra="forbid")

    contract_version: Literal["0.1.0"]
    claim_kind: ClaimKind
    study_design: StudyDesign | None
    population_or_sample: str | None
    intervention_or_exposure: str | None
    comparator: str | None
    outcome: str | None
    effect_direction: EffectDirection | None
    statistical_context: str | None
    limitations: list[str]
    section_provenance: ClaimSectionProvenance_v0_1 | None
