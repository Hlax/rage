"""Build support/contradict/qualify edges between concepts.

Model-assisted, validated. Contradictions are assets: preserve disagreement
and distinguish real contradictions from metric/scope differences. Every
relationship needs evidence links with stance, confidence, and scope.
"""

from __future__ import annotations

from typing import Any

from rge.config import load_config
from rge.llm.mock_client import MockModelClient
from rge.llm.mode import effective_llm_mode
from rge.llm.registry import get_model_client
from rge.modules.manual_source_fixtures import relationship_fixture_for_manual_source

CONFIDENCE_LABEL_TO_REAL: dict[str, float] = {
    "low": 0.25,
    "medium": 0.5,
    "high": 0.75,
}

VALID_STANCES = frozenset({"supports", "contradicts", "qualifies"})

REJECTION_UNKNOWN_CONCEPT = "unknown_concept_label"
REJECTION_MISSING_SCOPE = "missing_scope"
REJECTION_INVALID_STANCE = "invalid_stance"
REJECTION_MISSING_PREDICATE = "missing_predicate"
REJECTION_MISSING_EVIDENCE = "missing_evidence_claim"
REJECTION_INVALID_CONFIDENCE = "invalid_confidence_label"

DIVERSITY_CLAIM_FRAGMENT = "reduced semantic diversity"


def confidence_label_to_real(label: str | None) -> float | None:
    """Map public confidence labels to stored REAL scores."""
    if label is None:
        return None
    normalized = label.strip().casefold()
    return CONFIDENCE_LABEL_TO_REAL.get(normalized)


def _resolve_diversity_claim_id(claim_dicts: list[dict[str, Any]]) -> str | None:
    for claim in claim_dicts:
        if DIVERSITY_CLAIM_FRAGMENT in claim.get("claim_text", ""):
            return claim["id"]
    return claim_dicts[0]["id"] if claim_dicts else None


def _default_claim_id(claim_dicts: list[dict[str, Any]], *, diversity_fallback: bool) -> str | None:
    if diversity_fallback:
        return _resolve_diversity_claim_id(claim_dicts)
    return claim_dicts[0]["id"] if claim_dicts else None


def _resolve_supporting_claim_ids(
    candidate: dict[str, Any],
    accepted_claim_ids: set[str],
    claim_dicts: list[dict[str, Any]],
    *,
    diversity_fallback: bool = True,
) -> list[str]:
    """Resolve fixture claim IDs against accepted claims for the source."""
    supporting = [
        claim_id
        for claim_id in candidate.get("supporting_claim_ids") or []
        if claim_id in accepted_claim_ids
    ]
    if supporting:
        return supporting
    raw_ids = candidate.get("supporting_claim_ids") or []
    if raw_ids and raw_ids != ["placeholder"]:
        return []
    fallback = _default_claim_id(claim_dicts, diversity_fallback=diversity_fallback)
    return [fallback] if fallback else []


def relationship_rejection_diagnostic(
    candidate: dict[str, Any],
    *,
    rejection_reason: str | None = None,
    concept_labels: set[str] | None = None,
    accepted_claim_ids: set[str] | None = None,
) -> str:
    """Human-readable note for a rejected relationship (probe reporting only)."""
    reason = rejection_reason or REJECTION_UNKNOWN_CONCEPT
    allowed = {label.casefold() for label in concept_labels} if concept_labels else set()
    claim_ids = accepted_claim_ids or set()

    if reason == REJECTION_UNKNOWN_CONCEPT:
        subject = (candidate.get("subject_concept") or "").strip()
        obj = (candidate.get("object_concept") or "").strip()
        for label, field in ((subject, "subject_concept"), (obj, "object_concept")):
            if label and allowed and label.casefold() not in allowed:
                return (
                    f"{field} {label!r} is not in the allowed concept label set "
                    "for this probe"
                )
        return "subject_concept or object_concept is not an allowed concept label"
    if reason == REJECTION_MISSING_SCOPE:
        return "scope is missing or empty"
    if reason == REJECTION_INVALID_STANCE:
        return "stance must be one of supports, contradicts, or qualifies"
    if reason == REJECTION_MISSING_PREDICATE:
        return "predicate is missing or empty"
    if reason == REJECTION_MISSING_EVIDENCE:
        raw = candidate.get("supporting_claim_ids") or []
        if not raw:
            return "supporting_claim_ids is missing or empty"
        return (
            "supporting_claim_ids must reference a probe-local claim id "
            f"from {sorted(claim_ids)}"
        )
    if reason == REJECTION_INVALID_CONFIDENCE:
        return "confidence must be low, medium, or high"
    return f"rejected with reason {reason!r}"


def validate_relationship_candidates(
    candidates: list[dict[str, Any]],
    *,
    accepted_claim_ids: set[str],
    concept_labels: set[str],
) -> dict[str, list[dict[str, Any]]]:
    """Validate proposed relationships before persistence."""
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for candidate in candidates:
        subject = (candidate.get("subject_concept") or "").strip()
        obj = (candidate.get("object_concept") or "").strip()
        scope = (candidate.get("scope") or "").strip()
        stance = (candidate.get("stance") or "").strip().casefold()
        predicate = (candidate.get("predicate") or "").strip()

        if subject.casefold() not in {label.casefold() for label in concept_labels}:
            rejected.append({**candidate, "rejection_reason": "unknown_concept_label"})
            continue
        if obj.casefold() not in {label.casefold() for label in concept_labels}:
            rejected.append({**candidate, "rejection_reason": "unknown_concept_label"})
            continue
        if not scope:
            rejected.append({**candidate, "rejection_reason": "missing_scope"})
            continue
        if stance not in VALID_STANCES:
            rejected.append({**candidate, "rejection_reason": "invalid_stance"})
            continue
        if not predicate:
            rejected.append({**candidate, "rejection_reason": "missing_predicate"})
            continue

        supporting = [
            claim_id
            for claim_id in candidate.get("supporting_claim_ids") or []
            if claim_id in accepted_claim_ids
        ]
        if not supporting:
            rejected.append({**candidate, "rejection_reason": "missing_evidence_claim"})
            continue

        confidence_real = confidence_label_to_real(candidate.get("confidence"))
        if confidence_real is None:
            rejected.append({**candidate, "rejection_reason": "invalid_confidence_label"})
            continue

        accepted.append(
            {
                **candidate,
                "stance": stance,
                "confidence_real": confidence_real,
                "supporting_claim_ids": supporting,
            }
        )

    return {"accepted": accepted, "rejected": rejected}


def _pipeline_model_client(config=None):
    cfg = config if config is not None else load_config()
    return get_model_client(cfg, mode=effective_llm_mode(cfg))


def propose_relationship_drafts(
    claim_dicts: list[dict[str, Any]],
    concept_dicts: list[dict[str, Any]],
    domain_pack: str,
    *,
    client: Any | None = None,
    fixture_name: str | None = None,
    diversity_fallback: bool = True,
    source: Any | None = None,
) -> list[dict[str, Any]]:
    """Propose relationship drafts via the model client without persistence."""
    config = load_config()
    model_client = client if client is not None else _pipeline_model_client(config)
    draft_kwargs: dict[str, Any] = {
        "claims": claim_dicts,
        "concepts": concept_dicts,
        "domain_pack": domain_pack,
        "schema_version": config.llm_schema_version,
    }
    if isinstance(model_client, MockModelClient):
        resolved_fixture = fixture_name or relationship_fixture_for_manual_source(source)
        draft_kwargs["fixture_name"] = (
            resolved_fixture or "relationship_drafting_creativity_diversity.json"
        )
    batch = model_client.draft_relationships(**draft_kwargs)

    accepted_claim_ids = {claim["id"] for claim in claim_dicts if claim.get("id")}
    drafts: list[dict[str, Any]] = []
    for item in batch.items:
        draft = item.model_dump()
        draft["supporting_claim_ids"] = _resolve_supporting_claim_ids(
            draft,
            accepted_claim_ids,
            claim_dicts,
            diversity_fallback=diversity_fallback,
        )
        drafts.append(draft)
    return drafts


def draft_relationships_for_source(
    claim_dicts: list[dict[str, Any]],
    concept_dicts: list[dict[str, Any]],
    domain_pack: str,
    *,
    fixture_name: str | None = None,
    source: Any | None = None,
) -> list[dict[str, Any]]:
    """Propose relationship drafts via the configured model client."""
    return propose_relationship_drafts(
        claim_dicts,
        concept_dicts,
        domain_pack,
        fixture_name=fixture_name,
        diversity_fallback=True,
        source=source,
    )


def build_relationships_for_source(
    conn: Any,
    source_id: str,
    *,
    fixture_name: str | None = None,
) -> dict[str, Any]:
    """Build evidence relationships for a source and persist active edges."""
    from rge.db.repositories import (
        ClaimRepository,
        ConceptRepository,
        RelationshipEvidenceRepository,
        RelationshipRepository,
        SourceRepository,
    )

    claim_repo = ClaimRepository(conn)
    source_claims = claim_repo.list_for_source(source_id, status="accepted")
    if not source_claims:
        raise ValueError(f"No accepted claims found for source: {source_id}")

    source_record = SourceRepository(conn).get_by_id(source_id)
    domain_pack = source_claims[0].domain
    concept_repo = ConceptRepository(conn)
    concept_repo.ensure_domain_concepts(domain_pack)

    relationship_repo = RelationshipRepository(conn)
    if relationship_repo.count_for_source(source_id) > 0:
        existing = relationship_repo.list_for_source(source_id)
        return {
            "status": "already_built",
            "source_id": source_id,
            "relationship_count": len(existing),
            "relationship_ids": [rel["id"] for rel in existing],
        }

    claim_dicts = [
        {
            "id": claim.id,
            "claim_text": claim.claim_text,
            "subject": claim.subject,
            "object": claim.object,
            "scope": claim.scope,
            "domain": claim.domain,
        }
        for claim in source_claims
    ]
    concept_dicts = [
        {"id": concept.id, "label": concept.label}
        for concept in concept_repo.list_for_domain(domain_pack)
    ]
    concept_labels = {concept["label"] for concept in concept_dicts}
    accepted_claim_ids = {claim["id"] for claim in claim_dicts}

    proposed = draft_relationships_for_source(
        claim_dicts,
        concept_dicts,
        domain_pack,
        fixture_name=fixture_name,
        source=source_record,
    )
    validated = validate_relationship_candidates(
        proposed,
        accepted_claim_ids=accepted_claim_ids,
        concept_labels=concept_labels,
    )

    evidence_repo = RelationshipEvidenceRepository(conn)
    relationship_ids: list[str] = []
    for candidate in validated["accepted"]:
        subject = concept_repo.get_by_label(domain_pack, candidate["subject_concept"])
        obj = concept_repo.get_by_label(domain_pack, candidate["object_concept"])
        if subject is None or obj is None:
            continue

        relationship = relationship_repo.insert(
            subject_concept_id=subject.id,
            predicate=candidate["predicate"],
            object_concept_id=obj.id,
            scope=candidate["scope"],
            confidence=float(candidate["confidence_real"]),
            domain=domain_pack,
            status="active",
        )
        relationship_ids.append(relationship["id"])

        for claim_id in candidate["supporting_claim_ids"]:
            evidence_repo.insert(
                relationship_id=relationship["id"],
                claim_id=claim_id,
                stance=candidate["stance"],
                relevance_score=float(candidate["confidence_real"]),
            )

    return {
        "status": "completed",
        "source_id": source_id,
        "relationship_count": len(relationship_ids),
        "relationship_ids": relationship_ids,
        "rejected_relationship_count": len(validated["rejected"]),
        "rejected_relationships": validated["rejected"],
    }


def build_relationships(
    claims: list[dict[str, Any]], domain_pack: str
) -> list[dict[str, Any]]:
    """Legacy entry point retained for module contract tests."""
    concept_dicts: list[dict[str, Any]] = []
    drafts = draft_relationships_for_source(
        claims, concept_dicts, domain_pack
    )
    accepted_claim_ids = {claim.get("id", "") for claim in claims}
    concept_labels = {
        draft.get("subject_concept", "")
        for draft in drafts
    } | {draft.get("object_concept", "") for draft in drafts}
    validated = validate_relationship_candidates(
        drafts,
        accepted_claim_ids=accepted_claim_ids,
        concept_labels=concept_labels,
    )
    return validated["accepted"]
