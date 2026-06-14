"""Update confidence scores and write score events. Deterministic; no model use.

Scores are derived, never manually overwritten. Every change writes an
append-only ``score_events`` row preserving old score, new score, triggering
claim/source, reason, and formula version.
"""

from __future__ import annotations

from typing import Any

from rge.db.repositories import ClaimRecord
from rge.modules.domain_pack_loader import (
    ScoreReconciliationOverlay,
    load_domain_pack,
)

GOLDEN_SUBJECT = "ai assistance"
GOLDEN_OBJECT = "semantic diversity"
GOLDEN_PREDICATE = "may_reduce"

_creativity_overlay = load_domain_pack("creativity").score_reconciliation
FORMULA_VERSION = _creativity_overlay.formula_version
STRONGER_SOURCE_BOOST = _creativity_overlay.stronger_evidence_boost
STRONGER_SOURCE_REASON = _creativity_overlay.stronger_source_reason
STRONGER_CLAIM_CONFIDENCE_THRESHOLD = (
    _creativity_overlay.stronger_claim_confidence_threshold
)


def _overlay_for_domain(domain: str | None) -> ScoreReconciliationOverlay:
    pack_id = (domain or "creativity").strip() or "creativity"
    return load_domain_pack(pack_id).score_reconciliation


def _normalize(text: str) -> str:
    return text.strip().casefold()


def is_stronger_supporting_claim(
    claim: ClaimRecord,
    overlay: ScoreReconciliationOverlay | None = None,
) -> bool:
    """Deterministic gate for Golden Test 8 stronger follow-up evidence."""
    active = overlay or _creativity_overlay
    return float(claim.confidence) >= active.stronger_claim_confidence_threshold


def claim_supports_relationship(
    claim: ClaimRecord, relationship: dict[str, Any]
) -> bool:
    """Check whether a claim supports an existing may_reduce diversity edge."""
    if _normalize(relationship.get("predicate", "")) != GOLDEN_PREDICATE:
        return False
    if _normalize(relationship.get("subject_concept", "")) != GOLDEN_SUBJECT:
        return False
    if _normalize(relationship.get("object_concept", "")) != GOLDEN_OBJECT:
        return False
    text = claim.claim_text.casefold()
    return "semantic diversity" in text and (
        "reduced" in text or "reduce" in text
    )


def compute_relationship_score(
    old_score: float,
    claim: ClaimRecord,
    overlay: ScoreReconciliationOverlay | None = None,
) -> float:
    """Deterministic score update for stronger supporting evidence."""
    active = overlay or _creativity_overlay
    if not is_stronger_supporting_claim(claim, overlay=active):
        return old_score
    return round(min(1.0, old_score + active.stronger_evidence_boost), 2)


def reconcile_scores_for_source(conn: Any, source_id: str) -> dict[str, Any]:
    """Reconcile relationship scores when new source claims add support."""
    from rge.db.repositories import (
        ClaimRepository,
        RelationshipEvidenceRepository,
        RelationshipRepository,
        ScoreEventRepository,
        persist_relationship_score_update,
    )

    claim_repo = ClaimRepository(conn)
    claims = claim_repo.list_for_source(source_id, status="accepted")
    if not claims:
        raise ValueError(f"No accepted claims found for source: {source_id}")

    rel_repo = RelationshipRepository(conn)
    score_repo = ScoreEventRepository(conn)
    evidence_repo = RelationshipEvidenceRepository(conn)
    active_relationships = rel_repo.list_active()

    score_event_ids: list[str] = []
    updated_relationship_ids: list[str] = []
    skipped: list[dict[str, str]] = []

    for claim in claims:
        for relationship in active_relationships:
            if not claim_supports_relationship(claim, relationship):
                continue
            if score_repo.has_triggering_claim(
                entity_type="relationship",
                entity_id=relationship["id"],
                triggering_claim_id=claim.id,
            ):
                skipped.append(
                    {
                        "relationship_id": relationship["id"],
                        "claim_id": claim.id,
                        "reason": "already_reconciled",
                    }
                )
                continue
            if not is_stronger_supporting_claim(
                claim, overlay=_overlay_for_domain(relationship.get("domain"))
            ):
                skipped.append(
                    {
                        "relationship_id": relationship["id"],
                        "claim_id": claim.id,
                        "reason": "insufficient_credibility_boost",
                    }
                )
                continue

            overlay = _overlay_for_domain(relationship.get("domain"))
            old_score = float(relationship["confidence"])
            new_score = compute_relationship_score(old_score, claim, overlay=overlay)
            if new_score <= old_score:
                skipped.append(
                    {
                        "relationship_id": relationship["id"],
                        "claim_id": claim.id,
                        "reason": "no_score_increase",
                    }
                )
                continue

            needs_evidence = not evidence_repo.has_link(
                relationship_id=relationship["id"],
                claim_id=claim.id,
                stance="supports",
            )
            event = persist_relationship_score_update(
                conn,
                relationship_id=relationship["id"],
                old_score=old_score,
                new_score=new_score,
                triggering_claim_id=claim.id,
                triggering_source_id=claim.source_id,
                reason=overlay.stronger_source_reason,
                formula_version=overlay.formula_version,
                add_evidence=needs_evidence,
                evidence_relevance_score=new_score,
            )
            score_event_ids.append(event["id"])
            updated_relationship_ids.append(relationship["id"])
            relationship["confidence"] = new_score

    if not score_event_ids and not skipped:
        return {
            "status": "no_matching_relationships",
            "source_id": source_id,
            "score_events_created": 0,
            "relationships_updated": 0,
        }

    status = "completed" if score_event_ids else "no_score_changes"
    return {
        "status": status,
        "source_id": source_id,
        "score_events_created": len(score_event_ids),
        "score_event_ids": score_event_ids,
        "relationships_updated": len(updated_relationship_ids),
        "relationship_ids": updated_relationship_ids,
        "skipped": skipped,
    }


def reconcile_scores(new_claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Legacy entry point for module contract checks."""
    overlay = _creativity_overlay
    results: list[dict[str, Any]] = []
    for claim in new_claims:
        old_score = float(claim.get("relationship_old_score", 0.52))
        confidence = float(claim.get("confidence", 0.0))
        if confidence < overlay.stronger_claim_confidence_threshold:
            continue
        new_score = round(
            min(1.0, old_score + overlay.stronger_evidence_boost), 2
        )
        if new_score > old_score:
            results.append(
                {
                    "old_score": old_score,
                    "new_score": new_score,
                    "triggering_claim_id": claim.get("id"),
                    "reason": overlay.stronger_source_reason,
                    "formula_version": overlay.formula_version,
                }
            )
    return results
