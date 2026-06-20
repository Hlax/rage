"""Purpose-gated evidence acceptance for retrieval and Atlas readiness."""

from __future__ import annotations

import sqlite3
from typing import Any

from rge.modules.research_purpose import classify_research_purpose

STYLE_ORIGINALITY_CONCEPTS = {
    "style",
    "originality",
    "aesthetic",
    "design",
    "novelty",
    "visual language",
    "visual-language",
    "visual",
}
AGENCY_COCREATION_CONCEPTS = {
    "agency",
    "control",
    "collaboration",
    "autonomy",
    "co-creation",
    "co creation",
    "authorship",
    "human control",
    "ownership",
}
GENERIC_AI_DIVERSITY_CONCEPTS = {
    "ai assistance",
    "semantic diversity",
    "diversity",
    "creativity",
    "ideation",
    "brainstorming",
}


def _contains_any(text: str, terms: set[str]) -> bool:
    return any(term in text for term in terms)


def _normalize_text_terms(text: str) -> set[str]:
    normalized = text.casefold().replace("-", " ")
    terms: set[str] = set()
    for family in (
        STYLE_ORIGINALITY_CONCEPTS,
        AGENCY_COCREATION_CONCEPTS,
        GENERIC_AI_DIVERSITY_CONCEPTS,
    ):
        for term in family:
            if term.replace("-", " ") in normalized:
                terms.add(term.casefold())
    return terms


def required_concept_family_for_question(
    question: str,
    *,
    domain_pack: str,
) -> dict[str, Any]:
    """Return purpose-specific concept requirements for a question."""
    purpose = classify_research_purpose(
        question or "Unspecified research question",
        domain=domain_pack,
        question_id="purpose_gate",
    )
    normalized = question.casefold()
    families: list[dict[str, Any]] = []
    if (
        _contains_any(normalized, STYLE_ORIGINALITY_CONCEPTS)
        or "style_taxonomy" in purpose.get("research_intent", [])
        or "visual_descriptor_candidate" in purpose.get("asset_affordance", [])
    ):
        families.append(
            {
                "family": "style_originality",
                "required_concepts": sorted(STYLE_ORIGINALITY_CONCEPTS),
                "reason": "style/originality purpose requires visual, aesthetic, originality, design, or novelty evidence",
            }
        )
    if _contains_any(normalized, AGENCY_COCREATION_CONCEPTS):
        families.append(
            {
                "family": "agency_cocreation",
                "required_concepts": sorted(AGENCY_COCREATION_CONCEPTS),
                "reason": "agency/co-creation purpose requires agency, control, collaboration, autonomy, co-creation, authorship, or ownership evidence",
            }
        )
    return {
        "purpose": purpose,
        "families": families,
    }


def _claim_concepts(conn: sqlite3.Connection, claim_id: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT c.label
        FROM claim_concepts cc
        JOIN concepts c ON c.id = cc.concept_id
        WHERE cc.claim_id = ?
        ORDER BY c.label
        """,
        (claim_id,),
    ).fetchall()
    return [str(row["label"]).strip() for row in rows if row["label"]]


def evaluate_text_purpose_fit(
    text: str,
    *,
    question: str,
    domain_pack: str,
    evidence_ref: str | None = None,
) -> dict[str, Any]:
    """Evaluate purpose fit before DB concept links exist."""
    requirement = required_concept_family_for_question(
        question,
        domain_pack=domain_pack,
    )
    text_terms = _normalize_text_terms(text)
    if not requirement["families"]:
        return {
            "evidence_ref": evidence_ref,
            "purpose_match_status": "match",
            "decision": "accepted",
            "matched_concepts": sorted(text_terms),
            "required_concept_families": [],
            "why_purpose_match": "No purpose-specific concept gate was required.",
            "why_evidence_downgraded_or_rejected": "",
        }

    matched: list[str] = []
    missing_families: list[str] = []
    for family in requirement["families"]:
        required = {str(item).casefold() for item in family["required_concepts"]}
        required_normalized = {item.replace("-", " ") for item in required}
        family_matches = sorted(
            term
            for term in text_terms
            if term in required or term.replace("-", " ") in required_normalized
        )
        if family_matches:
            matched.extend(family_matches)
        else:
            missing_families.append(str(family["family"]))

    if not missing_families:
        return {
            "evidence_ref": evidence_ref,
            "purpose_match_status": "match",
            "decision": "accepted",
            "matched_concepts": sorted(set(matched)),
            "required_concept_families": [
                family["family"] for family in requirement["families"]
            ],
            "why_purpose_match": "Evidence text satisfies the question purpose gate.",
            "why_evidence_downgraded_or_rejected": "",
        }

    generic_only = bool(text_terms) and text_terms <= GENERIC_AI_DIVERSITY_CONCEPTS
    decision = "rejected" if generic_only else "downgraded"
    return {
        "evidence_ref": evidence_ref,
        "purpose_match_status": "mismatch",
        "decision": decision,
        "matched_concepts": sorted(set(matched)),
        "required_concept_families": [
            family["family"] for family in requirement["families"]
        ],
        "missing_concept_families": missing_families,
        "why_purpose_match": "",
        "why_evidence_downgraded_or_rejected": (
            "Generic AI/diversity evidence cannot satisfy this purpose-specific question."
            if generic_only
            else "Evidence lacks at least one required purpose-specific concept family."
        ),
    }


def evaluate_claim_purpose_fit(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    question: str,
    domain_pack: str,
) -> dict[str, Any]:
    """Evaluate whether a claim can satisfy a purpose-specific question."""
    requirement = required_concept_family_for_question(
        question,
        domain_pack=domain_pack,
    )
    concepts = _claim_concepts(conn, claim_id)
    normalized_concepts = {concept.casefold() for concept in concepts}
    if not requirement["families"]:
        return {
            "claim_id": claim_id,
            "purpose_match_status": "match",
            "decision": "accepted",
            "matched_concepts": concepts,
            "required_concept_families": [],
            "why_purpose_match": "No purpose-specific concept gate was required.",
            "why_evidence_downgraded_or_rejected": "",
        }

    matched: list[str] = []
    missing_families: list[str] = []
    for family in requirement["families"]:
        required = {str(item).casefold() for item in family["required_concepts"]}
        family_matches = sorted(normalized_concepts & required)
        if family_matches:
            matched.extend(family_matches)
        else:
            missing_families.append(str(family["family"]))

    if not missing_families:
        return {
            "claim_id": claim_id,
            "purpose_match_status": "match",
            "decision": "accepted",
            "matched_concepts": sorted(set(matched)),
            "required_concept_families": [
                family["family"] for family in requirement["families"]
            ],
            "why_purpose_match": "Claim concepts satisfy the question purpose gate.",
            "why_evidence_downgraded_or_rejected": "",
        }

    generic_only = bool(normalized_concepts) and normalized_concepts <= GENERIC_AI_DIVERSITY_CONCEPTS
    decision = "rejected" if generic_only else "downgraded"
    return {
        "claim_id": claim_id,
        "purpose_match_status": "mismatch",
        "decision": decision,
        "matched_concepts": sorted(set(matched)),
        "required_concept_families": [
            family["family"] for family in requirement["families"]
        ],
        "missing_concept_families": missing_families,
        "why_purpose_match": "",
        "why_evidence_downgraded_or_rejected": (
            "Generic AI/diversity evidence cannot satisfy this purpose-specific question."
            if generic_only
            else "Evidence lacks at least one required purpose-specific concept family."
        ),
    }


def purpose_decision_allows_graph_promotion(decision: dict[str, Any]) -> bool:
    """Only purpose-accepted evidence may promote into graph objects."""
    return (
        decision.get("purpose_match_status") == "match"
        and decision.get("decision") == "accepted"
    )


def purpose_gate_claim_ids(
    conn: sqlite3.Connection,
    claim_ids: list[str],
    *,
    question: str,
    domain_pack: str,
) -> dict[str, Any]:
    """Split claims into graph-promotable and gated sets."""
    decisions = [
        evaluate_claim_purpose_fit(
            conn,
            claim_id,
            question=question,
            domain_pack=domain_pack,
        )
        for claim_id in claim_ids
    ]
    promotable = [
        str(item["claim_id"])
        for item in decisions
        if purpose_decision_allows_graph_promotion(item)
    ]
    gated = [
        {
            "claim_id": str(item["claim_id"]),
            "decision": str(item["decision"]),
            "purpose_match_status": str(item["purpose_match_status"]),
            "reason": str(item.get("why_evidence_downgraded_or_rejected") or ""),
        }
        for item in decisions
        if not purpose_decision_allows_graph_promotion(item)
    ]
    return {
        "promotable_claim_ids": promotable,
        "gated_claims": gated,
        "purpose_match_count": len(promotable),
        "purpose_mismatch_count": len(gated),
        "decisions": decisions,
    }


def evaluate_claims_for_purpose(
    conn: sqlite3.Connection,
    claim_ids: list[str],
    *,
    question: str,
    domain_pack: str,
) -> dict[str, Any]:
    decisions = [
        evaluate_claim_purpose_fit(
            conn,
            claim_id,
            question=question,
            domain_pack=domain_pack,
        )
        for claim_id in claim_ids
    ]
    return {
        "purpose_match_count": sum(1 for item in decisions if item["purpose_match_status"] == "match"),
        "purpose_mismatch_count": sum(1 for item in decisions if item["purpose_match_status"] == "mismatch"),
        "accepted_count": sum(1 for item in decisions if item["decision"] == "accepted"),
        "downgraded_count": sum(1 for item in decisions if item["decision"] == "downgraded"),
        "rejected_count": sum(1 for item in decisions if item["decision"] == "rejected"),
        "decisions": decisions,
    }
