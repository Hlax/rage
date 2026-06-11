"""Detect and preserve contradictions between evidence edges.

Model-assisted, validated. Reads active relationships and accepted claims
across the domain so a contradiction source can qualify an earlier edge
without deleting or flattening opposing claims.
"""

from __future__ import annotations

import os
from typing import Any

from rge.config import load_config
from rge.llm.registry import get_model_client
from rge.modules.relationship_builder import VALID_STANCES

OPPOSING_CLAIM_FRAGMENT = "reduced semantic diversity"
QUALIFYING_CLAIM_FRAGMENT = "increased idea diversity"
VALID_CLASSIFICATIONS = frozenset(
    {"qualifies", "apparent_contradiction_metric_or_condition_difference"}
)


def _normalize(text: str) -> str:
    return text.strip().casefold()


def _resolve_qualifying_claim_id(
    source_claims: list[Any],
    candidate: dict[str, Any],
) -> str | None:
    proposed = candidate.get("qualifying_claim_id")
    claim_ids = {claim.id for claim in source_claims}
    if proposed and proposed in claim_ids:
        return proposed
    for claim in source_claims:
        if QUALIFYING_CLAIM_FRAGMENT in claim.claim_text.casefold():
            return claim.id
    return source_claims[0].id if source_claims else None


def _resolve_opposing_claim_id(
    domain_claims: list[Any],
    candidate: dict[str, Any],
) -> str | None:
    proposed = candidate.get("opposing_claim_id")
    claim_ids = {claim.id for claim in domain_claims}
    if proposed and proposed in claim_ids:
        return proposed
    for claim in domain_claims:
        if OPPOSING_CLAIM_FRAGMENT in claim.claim_text.casefold():
            return claim.id
    return None


def validate_contradiction_candidates(
    candidates: list[dict[str, Any]],
    *,
    source_claims: list[Any],
    domain_claims: list[Any],
    base_relationship: dict[str, Any] | None,
    new_relationship: dict[str, Any] | None,
) -> dict[str, list[dict[str, Any]]]:
    """Validate proposed contradiction links before persistence."""
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for candidate in candidates:
        stance = (candidate.get("qualification_stance") or "").strip().casefold()
        classification = (
            candidate.get("contradiction_classification") or ""
        ).strip()
        if base_relationship is None:
            rejected.append(
                {**candidate, "rejection_reason": "missing_base_relationship"}
            )
            continue
        if new_relationship is None:
            rejected.append(
                {**candidate, "rejection_reason": "missing_new_relationship"}
            )
            continue
        if stance not in VALID_STANCES:
            rejected.append({**candidate, "rejection_reason": "invalid_stance"})
            continue
        if classification not in VALID_CLASSIFICATIONS:
            rejected.append(
                {**candidate, "rejection_reason": "invalid_classification"}
            )
            continue

        qualifying_claim_id = _resolve_qualifying_claim_id(source_claims, candidate)
        opposing_claim_id = _resolve_opposing_claim_id(domain_claims, candidate)
        if qualifying_claim_id is None:
            rejected.append(
                {**candidate, "rejection_reason": "missing_qualifying_claim"}
            )
            continue
        if opposing_claim_id is None:
            rejected.append({**candidate, "rejection_reason": "missing_opposing_claim"})
            continue
        if qualifying_claim_id == opposing_claim_id:
            rejected.append({**candidate, "rejection_reason": "same_claim_pair"})
            continue

        accepted.append(
            {
                **candidate,
                "qualification_stance": stance,
                "qualifying_claim_id": qualifying_claim_id,
                "opposing_claim_id": opposing_claim_id,
                "base_relationship_id": base_relationship["id"],
                "new_relationship_id": new_relationship["id"],
            }
        )

    return {"accepted": accepted, "rejected": rejected}


def propose_contradictions(
    claim_dicts: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    domain_pack: str,
    *,
    fixture_name: str | None = None,
) -> list[dict[str, Any]]:
    """Propose contradiction/qualification links via the mock model client."""
    prior_mode = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    try:
        config = load_config()
        client = get_model_client(config)
        batch = client.detect_contradictions(
            claims=claim_dicts,
            relationships=relationships,
            domain_pack=domain_pack,
            schema_version=config.llm_schema_version,
            fixture_name=fixture_name
            or "contradiction_detection_creativity_diversity.json",
        )
    finally:
        if prior_mode is None:
            os.environ.pop("RGE_LLM_MODE", None)
        else:
            os.environ["RGE_LLM_MODE"] = prior_mode

    return [item.model_dump() for item in batch.items]


def detect_contradictions_for_source(
    conn: Any,
    source_id: str,
    *,
    fixture_name: str | None = None,
) -> dict[str, Any]:
    """Detect contradictions for a source against existing graph edges."""
    from rge.db.repositories import (
        ClaimRepository,
        RelationshipEvidenceRepository,
        RelationshipRepository,
    )

    claim_repo = ClaimRepository(conn)
    source_claims = claim_repo.list_for_source(source_id, status="accepted")
    if not source_claims:
        raise ValueError(f"No accepted claims found for source: {source_id}")

    domain_pack = source_claims[0].domain
    relationship_repo = RelationshipRepository(conn)
    evidence_repo = RelationshipEvidenceRepository(conn)
    domain_claims = claim_repo.list_accepted_for_domain(domain_pack)
    active_relationships = relationship_repo.list_active()

    existing_qualifications = evidence_repo.list_for_source(source_id)
    if any(row["stance"] == "qualifies" for row in existing_qualifications):
        return {
            "status": "already_detected",
            "source_id": source_id,
            "qualification_count": len(existing_qualifications),
        }

    claim_dicts = [
        {
            "id": claim.id,
            "claim_text": claim.claim_text,
            "source_id": claim.source_id,
            "domain": claim.domain,
        }
        for claim in domain_claims
    ]
    proposed = propose_contradictions(
        claim_dicts,
        active_relationships,
        domain_pack,
        fixture_name=fixture_name,
    )

    base_relationship = None
    new_relationship = None
    if proposed:
        first = proposed[0]
        base_relationship = relationship_repo.find_active_by_triple(
            subject_concept=first["base_subject_concept"],
            predicate=first["base_predicate"],
            object_concept=first["base_object_concept"],
        )
        new_relationship = relationship_repo.find_active_by_triple(
            subject_concept=first["new_subject_concept"],
            predicate=first["new_predicate"],
            object_concept=first["new_object_concept"],
        )

    validated = validate_contradiction_candidates(
        proposed,
        source_claims=source_claims,
        domain_claims=domain_claims,
        base_relationship=base_relationship,
        new_relationship=new_relationship,
    )

    qualification_ids: list[str] = []
    for candidate in validated["accepted"]:
        classification = candidate["contradiction_classification"]
        metadata_patch = {
            "contradiction_classification": classification,
            "qualifies_relationship_id": candidate["new_relationship_id"],
        }
        relationship_repo.merge_domain_metadata(
            candidate["base_relationship_id"],
            metadata_patch,
        )
        relationship_repo.merge_domain_metadata(
            candidate["new_relationship_id"],
            {
                "contradiction_classification": classification,
                "qualifies_relationship_id": candidate["base_relationship_id"],
            },
        )
        evidence = evidence_repo.insert(
            relationship_id=candidate["base_relationship_id"],
            claim_id=candidate["qualifying_claim_id"],
            stance=candidate["qualification_stance"],
            relevance_score=0.75,
        )
        qualification_ids.append(evidence["id"])

    return {
        "status": "completed" if qualification_ids else "no_qualifications",
        "source_id": source_id,
        "qualification_count": len(qualification_ids),
        "qualification_ids": qualification_ids,
        "rejected_count": len(validated["rejected"]),
        "rejected": validated["rejected"],
    }


def detect_contradictions(
    claims: list[dict[str, Any]], relationships: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Legacy entry point for module contract checks."""
    proposed = propose_contradictions(claims, relationships, "creativity")
    base = next(
        (
            rel
            for rel in relationships
            if _normalize(rel.get("predicate", "")) == "may_reduce"
        ),
        None,
    )
    new = next(
        (
            rel
            for rel in relationships
            if _normalize(rel.get("predicate", "")) == "may_increase"
        ),
        None,
    )
    source_claims = [type("Claim", (), claim)() for claim in claims]
    domain_claims = source_claims
    validated = validate_contradiction_candidates(
        proposed,
        source_claims=source_claims,
        domain_claims=domain_claims,
        base_relationship=base,
        new_relationship=new,
    )
    return validated["accepted"]
