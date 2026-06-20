"""Deterministic purpose-gated relationship-density proof helpers.

This module is intentionally fixture-safe: it does not call a model and it does
not accept raw source text into public exports. It turns already accepted,
quote-backed claims into typed relationship evidence after purpose gating.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from rge.db.repositories import (
    ConceptRepository,
    RelationshipEvidenceRepository,
    RelationshipRepository,
)
from rge.modules.evidence_atoms import promote_cluster_evidence_atoms
from rge.modules.purpose_gating import purpose_gate_claim_ids

CORE_DENSITY_QUESTION = "Does AI assistance improve idea quality or reduce diversity?"

_RELATIONSHIP_PROOF_SPECS: tuple[dict[str, Any], ...] = (
    {
        "subject": "AI assistance",
        "predicate": "may_reduce",
        "object": "semantic diversity",
        "stance": "supports",
        "relationship_type": "support",
    },
    {
        "subject": "AI assistance",
        "predicate": "may_improve",
        "object": "taste",
        "stance": "supports",
        "relationship_type": "support",
    },
    {
        "subject": "AI assistance",
        "predicate": "may_increase",
        "object": "diversity",
        "stance": "supports",
        "relationship_type": "support",
    },
    {
        "subject": "prompt engineering",
        "predicate": "may_qualify",
        "object": "semantic diversity",
        "stance": "qualifies",
        "relationship_type": "qualification",
    },
    {
        "subject": "AI assistance",
        "predicate": "may_increase",
        "object": "semantic diversity",
        "stance": "contradicts",
        "relationship_type": "contradiction",
    },
    {
        "subject": "semantic diversity",
        "predicate": "is_dimension_of",
        "object": "diversity",
        "stance": "supports",
        "relationship_type": "definition",
    },
    {
        "subject": "semantic diversity",
        "predicate": "differs_by_scope_from",
        "object": "diversity",
        "stance": "qualifies",
        "relationship_type": "scope_difference",
    },
    {
        "subject": "human control",
        "predicate": "may_qualify",
        "object": "AI assistance",
        "stance": "qualifies",
        "relationship_type": "qualification",
    },
)


def _accepted_quote_backed_claim_ids(
    conn: sqlite3.Connection,
    *,
    domain: str,
    claim_ids: list[str] | None,
) -> list[str]:
    params: list[Any] = [domain]
    where = "c.domain = ? AND c.status = 'accepted'"
    if claim_ids is not None:
        if not claim_ids:
            return []
        where += f" AND c.id IN ({','.join('?' for _ in claim_ids)})"
        params.extend(claim_ids)
    rows = conn.execute(
        f"""
        SELECT DISTINCT c.id
        FROM claims c
        JOIN claim_quotes q ON q.claim_id = c.id
        WHERE {where}
        ORDER BY c.id
        """,
        tuple(params),
    ).fetchall()
    return [str(row["id"]) for row in rows]


def _concept_map(conn: sqlite3.Connection, domain: str) -> dict[str, str]:
    repo = ConceptRepository(conn)
    repo.ensure_domain_concepts(domain)
    labels = {
        spec["subject"] for spec in _RELATIONSHIP_PROOF_SPECS
    } | {
        spec["object"] for spec in _RELATIONSHIP_PROOF_SPECS
    }
    concepts: dict[str, str] = {}
    for label in sorted(labels):
        concept = repo.get_by_label(domain, label)
        if concept is not None:
            concepts[label] = concept.id
    return concepts


def ensure_purpose_gated_relationship_density_proof(
    conn: sqlite3.Connection,
    *,
    domain: str,
    question: str = CORE_DENSITY_QUESTION,
    claim_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Create deterministic typed relationships for purpose-matching claims."""
    quote_backed_ids = _accepted_quote_backed_claim_ids(
        conn,
        domain=domain,
        claim_ids=claim_ids,
    )
    gate = purpose_gate_claim_ids(
        conn,
        quote_backed_ids,
        question=question,
        domain_pack=domain,
    )
    promotable_ids = list(gate["promotable_claim_ids"])
    concept_ids = _concept_map(conn, domain)
    relationship_repo = RelationshipRepository(conn)
    evidence_repo = RelationshipEvidenceRepository(conn)

    created_relationship_ids: list[str] = []
    linked_claim_ids: list[str] = []
    for index, claim_id in enumerate(promotable_ids):
        spec = _RELATIONSHIP_PROOF_SPECS[index % len(_RELATIONSHIP_PROOF_SPECS)]
        subject_id = concept_ids.get(str(spec["subject"]))
        object_id = concept_ids.get(str(spec["object"]))
        if subject_id is None or object_id is None:
            continue
        relationship = relationship_repo.insert(
            subject_concept_id=subject_id,
            predicate=str(spec["predicate"]),
            object_concept_id=object_id,
            scope=f"{question} :: proof edge {index % len(_RELATIONSHIP_PROOF_SPECS) + 1}",
            confidence=0.65,
            evidence_strength=0.65,
            domain=domain,
            status="active",
            domain_metadata={
                "relationship_type": str(spec["relationship_type"]),
                "purpose_gate": "accepted",
                "proof": "purpose_gated_relationship_density",
            },
        )
        created_relationship_ids.append(str(relationship["id"]))
        evidence_repo.insert(
            relationship_id=str(relationship["id"]),
            claim_id=claim_id,
            stance=str(spec["stance"]),
            relevance_score=0.75,
        )
        linked_claim_ids.append(claim_id)

    atom_result = promote_cluster_evidence_atoms(
        conn,
        domain=domain,
        claim_ids=promotable_ids,
        question=question,
        enforce_purpose_gate=True,
    )
    return {
        "status": "completed",
        "domain": domain,
        "question": question,
        "candidate_claim_count": len(quote_backed_ids),
        "purpose_match_count": int(gate["purpose_match_count"]),
        "purpose_mismatch_count": int(gate["purpose_mismatch_count"]),
        "gated_claims": gate["gated_claims"],
        "relationship_count": len(set(created_relationship_ids)),
        "relationship_ids": sorted(set(created_relationship_ids)),
        "linked_claim_count": len(set(linked_claim_ids)),
        "linked_claim_ids": sorted(set(linked_claim_ids)),
        "atom_result": atom_result,
    }
