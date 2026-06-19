"""Deterministic research-purpose and asset-affordance classifier."""

from __future__ import annotations

from typing import Any

from rge.contracts.evidence_atom_v0 import validate_research_purpose

DEFAULT_ACCEPTABLE_SOURCE_TYPES = [
    "paper",
    "abstract",
    "essay",
    "book",
    "interview",
    "webpage",
]
DEFAULT_OUTPUT_TARGETS = ["cluster_report", "evidence_cards", "atlas_map"]


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _append_unique(values: list[str], additions: list[str]) -> None:
    for addition in additions:
        if addition not in values:
            values.append(addition)


def classify_research_purpose(
    question: str,
    *,
    domain: str,
    question_id: str = "rq_unspecified",
) -> dict[str, Any]:
    """Classify a question into stable purpose metadata without an LLM."""
    normalized = question.casefold()
    research_intent: list[str] = []
    asset_affordance: list[str] = []
    evidence_need = "full_text_preferred"

    if _contains_any(normalized, ("benchmark", "evaluation", "eval", "test set", "rubric")):
        _append_unique(research_intent, ["benchmark_design", "eval_design", "evidence_review"])
        _append_unique(
            asset_affordance,
            ["eval_question_candidate", "dataset_curation_candidate"],
        )
        evidence_need = "empirical_required"

    if _contains_any(
        normalized,
        ("art", "product design", "graphic design", "visual", "style", "image", "aesthetic"),
    ):
        _append_unique(research_intent, ["style_taxonomy", "visual_descriptor_mining"])
        _append_unique(
            asset_affordance,
            ["visual_descriptor_candidate", "style_vocabulary_candidate"],
        )
        evidence_need = "visual_examples_required"

    if _contains_any(normalized, ("contradict", "trade-off", "tradeoff", "tension")):
        _append_unique(research_intent, ["contradiction_mapping", "evidence_review"])
        _append_unique(asset_affordance, ["contradiction_map_candidate"])

    if _contains_any(normalized, ("ai", "creativ", "originality", "diversity", "ideation")):
        _append_unique(research_intent, ["theory_building", "evidence_review"])
        _append_unique(
            asset_affordance,
            [
                "reasoning_training_candidate",
                "argument_map_candidate",
                "concept_ontology_candidate",
            ],
        )
        if evidence_need == "full_text_preferred":
            evidence_need = "mixed_empirical_theory"

    if _contains_any(normalized, ("ontology", "concept", "taxonomy", "field map", "map the field")):
        _append_unique(research_intent, ["concept_ontology_building", "field_mapping"])
        _append_unique(asset_affordance, ["concept_ontology_candidate"])

    if not research_intent:
        research_intent = ["field_mapping"]
    if not asset_affordance:
        asset_affordance = ["memo_candidate"]

    payload = {
        "question_id": question_id,
        "question": question,
        "domain": domain,
        "research_intent": research_intent,
        "asset_affordance": asset_affordance,
        "evidence_need": evidence_need,
        "acceptable_source_types": list(DEFAULT_ACCEPTABLE_SOURCE_TYPES),
        "output_targets": list(DEFAULT_OUTPUT_TARGETS),
        "evidence_maturity": "seed",
        "training_suitability": "not_ready",
    }
    return validate_research_purpose(payload).model_dump(mode="json")


def conservative_maturity_profile(
    *,
    accepted_claim_count: int,
    source_count: int,
    has_disagreement: bool = False,
) -> dict[str, str]:
    """Return conservative maturity/training labels for operator reports."""
    if accepted_claim_count <= 0 or source_count <= 0:
        return {"evidence_maturity": "seed", "training_suitability": "not_ready"}
    if accepted_claim_count < 3 or source_count < 2:
        return {"evidence_maturity": "weak", "training_suitability": "not_ready"}
    if accepted_claim_count >= 15 and source_count >= 3:
        suitability = "needs_human_review" if has_disagreement else "candidate"
        return {"evidence_maturity": "clustered", "training_suitability": suitability}
    return {"evidence_maturity": "promising", "training_suitability": "not_ready"}
