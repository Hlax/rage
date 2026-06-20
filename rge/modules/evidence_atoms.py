"""Build stable evidence atoms and canonical evidence cards from accepted claims."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from rge.contracts.evidence_atom_v0 import (
    EvidenceAtom_v0_1,
    EvidenceCard_v0_1,
    validate_evidence_atom,
    validate_evidence_card,
)
from rge.db.repositories import sha256_hex

DEFAULT_ATOM_ASSET_TAGS = ["reasoning_training_candidate", "argument_map_candidate"]
MAX_CARD_QUOTE_CHARS = 600
MIN_CLAIMS_FOR_CLUSTERED_MATURITY = 3
MIN_SOURCES_FOR_PROMISING_MATURITY = 2


def atom_maturity_for_stance(
    *,
    support_count: int,
    contradiction_count: int,
    qualifying_count: int = 0,
    linked_claim_count: int = 1,
    source_count: int = 1,
) -> tuple[str, str]:
    """Return conservative evidence_maturity and training_suitability for an atom."""
    if linked_claim_count <= 0:
        return "seed", "not_ready"
    if support_count == 0 and contradiction_count == 0 and qualifying_count == 0:
        if linked_claim_count >= 2 or source_count >= MIN_SOURCES_FOR_PROMISING_MATURITY:
            return "promising", "not_ready"
        return "weak", "not_ready"
    if (
        linked_claim_count >= MIN_CLAIMS_FOR_CLUSTERED_MATURITY
        and source_count >= MIN_SOURCES_FOR_PROMISING_MATURITY
        and (support_count >= 2 or contradiction_count > 0 or qualifying_count > 0)
    ):
        return "clustered", "needs_human_review"
    if support_count >= 2 or linked_claim_count >= 2 or source_count >= MIN_SOURCES_FOR_PROMISING_MATURITY:
        return "promising", "not_ready"
    return "weak", "not_ready"


def make_evidence_atom_id(canonical_text: str, scope: str) -> str:
    digest = sha256_hex(f"{canonical_text.strip().casefold()}:{scope.strip().casefold()}")
    return f"atom_{digest[:16]}"


def confidence_label(value: float | None) -> str:
    if value is None:
        return "low"
    if value >= 0.75:
        return "high"
    if value >= 0.5:
        return "medium"
    return "low"


def _claim_row(conn: sqlite3.Connection, claim_id: str) -> sqlite3.Row:
    row = conn.execute(
        """
        SELECT id, source_id, chunk_id, claim_text, scope, evidence_type, confidence,
               limitations_json, status
        FROM claims
        WHERE id = ?
        """,
        (claim_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Claim not found: {claim_id}")
    if row["status"] != "accepted":
        raise ValueError(f"Evidence atoms require accepted claims: {claim_id}")
    return row


def _quote_rows(conn: sqlite3.Connection, claim_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT id, quote_text
        FROM claim_quotes
        WHERE claim_id = ?
        ORDER BY is_primary DESC, created_at
        """,
        (claim_id,),
    ).fetchall()


def _concept_labels(conn: sqlite3.Connection, claim_id: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT DISTINCT concepts.label
        FROM claim_concepts
        JOIN concepts ON concepts.id = claim_concepts.concept_id
        WHERE claim_concepts.claim_id = ?
        ORDER BY concepts.label
        """,
        (claim_id,),
    ).fetchall()
    return [str(row["label"]) for row in rows]


def _stance_profile(conn: sqlite3.Connection, claim_id: str) -> dict[str, int]:
    rows = conn.execute(
        """
        SELECT stance, COUNT(*) AS count
        FROM relationship_evidence
        WHERE claim_id = ?
        GROUP BY stance
        """,
        (claim_id,),
    ).fetchall()
    profile = {"supports": 0, "contradicts": 0, "qualifies": 0}
    for row in rows:
        stance = str(row["stance"])
        if stance in profile:
            profile[stance] = int(row["count"])
    return profile


def _claim_rows_for_clustering(
    conn: sqlite3.Connection,
    *,
    domain: str,
    claim_ids: list[str] | None = None,
) -> list[sqlite3.Row]:
    if claim_ids:
        placeholders = ",".join("?" for _ in claim_ids)
        return conn.execute(
            f"""
            SELECT id, source_id, claim_text, scope, evidence_type, confidence
            FROM claims
            WHERE domain = ? AND status = 'accepted' AND id IN ({placeholders})
            ORDER BY id
            """,
            (domain, *claim_ids),
        ).fetchall()
    return conn.execute(
        """
        SELECT id, source_id, claim_text, scope, evidence_type, confidence
        FROM claims
        WHERE domain = ? AND status = 'accepted'
        ORDER BY id
        """,
        (domain,),
    ).fetchall()


def _quote_ids_for_claim(conn: sqlite3.Connection, claim_id: str) -> list[str]:
    return [str(row["id"]) for row in _quote_rows(conn, claim_id)]


def _cluster_concept_signature(concepts: list[str]) -> tuple[str, ...]:
    ignored = {"ai assistance", "creativity", "ideation", "brainstorming"}
    selected = [
        concept.strip().casefold()
        for concept in concepts
        if concept.strip() and concept.strip().casefold() not in ignored
    ]
    if not selected:
        selected = [concept.strip().casefold() for concept in concepts if concept.strip()]
    return tuple(sorted(set(selected)))


def _scope_signature(scope: str) -> str:
    return " ".join(scope.strip().casefold().split())


def _cluster_atom_id(scope_signature: str, concept_signature: tuple[str, ...]) -> str:
    digest = sha256_hex(f"{scope_signature}:{'|'.join(concept_signature)}")
    return f"atom_cluster_{digest[:16]}"


def _source_count_for_claims(conn: sqlite3.Connection, claim_ids: list[str]) -> int:
    if not claim_ids:
        return 0
    placeholders = ",".join("?" for _ in claim_ids)
    row = conn.execute(
        f"""
        SELECT COUNT(DISTINCT source_id)
        FROM claims
        WHERE id IN ({placeholders})
        """,
        tuple(claim_ids),
    ).fetchone()
    return int(row[0]) if row else 0


def _delete_merged_single_claim_atoms(
    conn: sqlite3.Connection,
    *,
    keep_atom_id: str,
    claim_ids: list[str],
) -> int:
    rows = conn.execute(
        "SELECT id, source_claim_ids_json FROM evidence_atoms"
    ).fetchall()
    deleted = 0
    claim_set = set(claim_ids)
    for row in rows:
        atom_id = str(row["id"])
        if atom_id == keep_atom_id:
            continue
        atom_claims = set(json.loads(row["source_claim_ids_json"] or "[]"))
        if atom_claims and atom_claims <= claim_set:
            conn.execute("DELETE FROM evidence_atoms WHERE id = ?", (atom_id,))
            deleted += 1
    if deleted:
        conn.commit()
    return deleted


def cluster_compatible_evidence_atoms(
    conn: sqlite3.Connection,
    *,
    domain: str,
    claim_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Group compatible quote-backed accepted claims into shared evidence atoms."""
    rows = _claim_rows_for_clustering(conn, domain=domain, claim_ids=claim_ids)
    groups: dict[tuple[str, tuple[str, ...]], list[sqlite3.Row]] = {}
    separate_claims: list[str] = []
    for row in rows:
        concepts = _concept_labels(conn, str(row["id"]))
        signature = _cluster_concept_signature(concepts)
        if not signature:
            separate_claims.append(str(row["id"]))
            continue
        groups.setdefault((_scope_signature(str(row["scope"] or "")), signature), []).append(row)

    clustered_atoms: list[dict[str, Any]] = []
    duplicate_merged_count = 0
    for (scope_sig, concept_sig), group in groups.items():
        if len(group) < 2:
            separate_claims.extend(str(row["id"]) for row in group)
            continue
        group_claim_ids = [str(row["id"]) for row in group]
        source_quote_ids: list[str] = []
        concepts: list[str] = []
        stance_profile = {"supports": 0, "contradicts": 0, "qualifies": 0}
        confidence_values: list[float] = []
        for row in group:
            claim_id = str(row["id"])
            source_quote_ids.extend(_quote_ids_for_claim(conn, claim_id))
            for concept in _concept_labels(conn, claim_id):
                if concept not in concepts:
                    concepts.append(concept)
            profile = _stance_profile(conn, claim_id)
            for key in stance_profile:
                stance_profile[key] += int(profile.get(key, 0))
            if row["confidence"] is not None:
                confidence_values.append(float(row["confidence"]))
        source_count = len({str(row["source_id"]) for row in group})
        maturity, suitability = atom_maturity_for_stance(
            support_count=stance_profile["supports"],
            contradiction_count=stance_profile["contradicts"],
            qualifying_count=stance_profile["qualifies"],
            linked_claim_count=len(group_claim_ids),
            source_count=source_count,
        )
        atom_id = _cluster_atom_id(scope_sig, concept_sig)
        canonical = (
            f"Clustered evidence atom linking {len(group_claim_ids)} compatible "
            f"claims about {', '.join(concept_sig)} within scope: {group[0]['scope']}."
        )
        payload = {
            "atom_id": atom_id,
            "atom_type": "claim",
            "canonical_text": canonical,
            "source_claim_ids": group_claim_ids,
            "source_quote_ids": list(dict.fromkeys(source_quote_ids)),
            "concepts": sorted(concepts),
            "stance_profile": stance_profile,
            "support_count": stance_profile["supports"],
            "contradiction_count": stance_profile["contradicts"],
            "scope": str(group[0]["scope"] or "shared scope"),
            "evidence_type": str(group[0]["evidence_type"] or "unknown"),
            "asset_tags": list(DEFAULT_ATOM_ASSET_TAGS),
            "evidence_maturity": maturity,
            "training_suitability": suitability,
            "confidence": confidence_label(
                sum(confidence_values) / len(confidence_values)
                if confidence_values
                else None
            ),
        }
        atom = validate_evidence_atom(payload)
        persisted = persist_evidence_atom(conn, atom)
        duplicate_merged_count += _delete_merged_single_claim_atoms(
            conn,
            keep_atom_id=atom_id,
            claim_ids=group_claim_ids,
        )
        common_concepts = set(_concept_labels(conn, group_claim_ids[0]))
        for claim_id in group_claim_ids[1:]:
            common_concepts &= set(_concept_labels(conn, claim_id))
        clustered_atoms.append(
            {
                **persisted,
                "source_count": source_count,
                "source_diverse": source_count >= MIN_SOURCES_FOR_PROMISING_MATURITY,
                "concept_overlap_count": len(common_concepts),
                "scope_compatible": True,
                "qualification_count": stance_profile["qualifies"],
                "why_clustered": (
                    f"{len(group_claim_ids)} claims share compatible scope, "
                    f"{len(common_concepts)} overlapping concept(s), and {source_count} source(s)."
                ),
            }
        )

    return {
        "status": "completed",
        "domain": domain,
        "candidate_claim_count": len(rows),
        "clustered_atom_count": len(clustered_atoms),
        "duplicate_merged_atom_count": duplicate_merged_count,
        "separate_claim_count": len(separate_claims),
        "separate_claim_ids": sorted(set(separate_claims)),
        "clustered_atoms": clustered_atoms,
    }


def build_evidence_atom_for_claim(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    asset_tags: list[str] | None = None,
    evidence_maturity: str = "seed",
    training_suitability: str = "not_ready",
) -> EvidenceAtom_v0_1:
    """Promote one accepted quote-backed claim into a validated atom object."""
    claim = _claim_row(conn, claim_id)
    quotes = _quote_rows(conn, claim_id)
    if not quotes:
        raise ValueError(f"Evidence atom requires at least one quote-backed claim: {claim_id}")
    profile = _stance_profile(conn, claim_id)
    payload = {
        "atom_id": make_evidence_atom_id(claim["claim_text"], claim["scope"]),
        "atom_type": "claim",
        "canonical_text": claim["claim_text"],
        "source_claim_ids": [claim_id],
        "source_quote_ids": [str(row["id"]) for row in quotes],
        "concepts": _concept_labels(conn, claim_id),
        "stance_profile": profile,
        "support_count": profile["supports"],
        "contradiction_count": profile["contradicts"],
        "scope": claim["scope"],
        "evidence_type": claim["evidence_type"],
        "asset_tags": asset_tags or list(DEFAULT_ATOM_ASSET_TAGS),
        "evidence_maturity": evidence_maturity,
        "training_suitability": training_suitability,
        "confidence": confidence_label(float(claim["confidence"] or 0.0)),
    }
    return validate_evidence_atom(payload)


def _load_atom_row(conn: sqlite3.Connection, atom_id: str) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT id, atom_type, canonical_text, source_claim_ids_json,
               source_quote_ids_json, concepts_json, stance_profile_json,
               support_count, contradiction_count, scope, evidence_type,
               asset_tags_json, evidence_maturity, training_suitability, confidence
        FROM evidence_atoms
        WHERE id = ?
        """,
        (atom_id,),
    ).fetchone()


def _merge_atom_payload(existing: sqlite3.Row, incoming: EvidenceAtom_v0_1) -> EvidenceAtom_v0_1:
    existing_claim_ids = json.loads(existing["source_claim_ids_json"] or "[]")
    existing_quote_ids = json.loads(existing["source_quote_ids_json"] or "[]")
    existing_concepts = json.loads(existing["concepts_json"] or "[]")
    existing_profile = json.loads(existing["stance_profile_json"] or "{}")
    incoming_payload = incoming.model_dump(mode="json")

    merged_claim_ids = list(dict.fromkeys(existing_claim_ids + incoming_payload["source_claim_ids"]))
    merged_quote_ids = list(dict.fromkeys(existing_quote_ids + incoming_payload["source_quote_ids"]))
    merged_concepts = list(dict.fromkeys(existing_concepts + incoming_payload["concepts"]))
    merged_profile = {
        "supports": int(existing_profile.get("supports", 0)) + int(incoming.stance_profile.get("supports", 0)),
        "contradicts": int(existing_profile.get("contradicts", 0))
        + int(incoming.stance_profile.get("contradicts", 0)),
        "qualifies": int(existing_profile.get("qualifies", 0))
        + int(incoming.stance_profile.get("qualifies", 0)),
    }
    maturity, suitability = atom_maturity_for_stance(
        support_count=merged_profile["supports"],
        contradiction_count=merged_profile["contradicts"],
        qualifying_count=merged_profile["qualifies"],
        linked_claim_count=len(merged_claim_ids),
    )
    merged_payload = {
        **incoming_payload,
        "atom_id": existing["id"],
        "source_claim_ids": merged_claim_ids,
        "source_quote_ids": merged_quote_ids,
        "concepts": merged_concepts,
        "stance_profile": merged_profile,
        "support_count": merged_profile["supports"],
        "contradiction_count": merged_profile["contradicts"],
        "evidence_maturity": maturity,
        "training_suitability": suitability,
    }
    return validate_evidence_atom(merged_payload)


def persist_evidence_atom(conn: sqlite3.Connection, atom: EvidenceAtom_v0_1) -> dict[str, Any]:
    """Persist a validated atom in the operator-private evidence_atoms table."""
    from rge.db.repositories import utc_now_iso

    existing = _load_atom_row(conn, atom.atom_id)
    if existing is not None:
        atom = _merge_atom_payload(existing, atom)

    now = utc_now_iso()
    payload = atom.model_dump(mode="json")
    conn.execute(
        """
        INSERT INTO evidence_atoms (
            id, atom_type, canonical_text, source_claim_ids_json,
            source_quote_ids_json, concepts_json, stance_profile_json,
            support_count, contradiction_count, scope, evidence_type,
            asset_tags_json, evidence_maturity, training_suitability,
            confidence, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            source_claim_ids_json = excluded.source_claim_ids_json,
            source_quote_ids_json = excluded.source_quote_ids_json,
            concepts_json = excluded.concepts_json,
            stance_profile_json = excluded.stance_profile_json,
            support_count = excluded.support_count,
            contradiction_count = excluded.contradiction_count,
            asset_tags_json = excluded.asset_tags_json,
            evidence_maturity = excluded.evidence_maturity,
            training_suitability = excluded.training_suitability,
            confidence = excluded.confidence,
            updated_at = excluded.updated_at
        """,
        (
            atom.atom_id,
            atom.atom_type,
            atom.canonical_text,
            json.dumps(payload["source_claim_ids"]),
            json.dumps(payload["source_quote_ids"]),
            json.dumps(payload["concepts"]),
            json.dumps(payload["stance_profile"]),
            atom.support_count,
            atom.contradiction_count,
            atom.scope,
            atom.evidence_type,
            json.dumps(payload["asset_tags"]),
            atom.evidence_maturity,
            atom.training_suitability,
            atom.confidence,
            now,
            now,
        ),
    )
    conn.commit()
    return payload


def promote_claim_to_evidence_atom(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    asset_tags: list[str] | None = None,
    evidence_maturity: str | None = None,
    training_suitability: str | None = None,
) -> dict[str, Any]:
    """Build and persist one accepted claim-backed evidence atom."""
    profile = _stance_profile(conn, claim_id)
    maturity, suitability = atom_maturity_for_stance(
        support_count=profile["supports"],
        contradiction_count=profile["contradicts"],
        qualifying_count=profile["qualifies"],
        linked_claim_count=1,
    )
    atom = build_evidence_atom_for_claim(
        conn,
        claim_id,
        asset_tags=asset_tags,
        evidence_maturity=evidence_maturity or maturity,
        training_suitability=training_suitability or suitability,
    )
    return persist_evidence_atom(conn, atom)


def promote_accepted_claims_for_domain(
    conn: sqlite3.Connection,
    *,
    domain: str,
    claim_ids: list[str] | None = None,
    asset_tags: list[str] | None = None,
) -> dict[str, Any]:
    """Promote accepted quote-backed claims in a domain into evidence atoms."""
    if claim_ids is None:
        rows = conn.execute(
            """
            SELECT id FROM claims
            WHERE domain = ? AND status = 'accepted'
            ORDER BY created_at
            """,
            (domain,),
        ).fetchall()
        claim_ids = [str(row["id"]) for row in rows]

    promoted: list[str] = []
    skipped: list[dict[str, str]] = []
    for claim_id in claim_ids:
        try:
            atom = promote_claim_to_evidence_atom(
                conn,
                claim_id,
                asset_tags=asset_tags,
            )
            promoted.append(str(atom["atom_id"]))
        except ValueError as exc:
            skipped.append({"claim_id": claim_id, "reason": str(exc)})

    return {
        "status": "completed",
        "domain": domain,
        "promoted_count": len(promoted),
        "skipped_count": len(skipped),
        "atom_ids": promoted,
        "skipped": skipped,
    }


def promote_cluster_evidence_atoms(
    conn: sqlite3.Connection,
    *,
    domain: str,
    claim_ids: list[str],
) -> dict[str, Any]:
    """Promote atoms for cluster-linked accepted claims before report synthesis."""
    if not claim_ids:
        return {
            "status": "skipped",
            "domain": domain,
            "promoted_count": 0,
            "skipped_count": 0,
            "atom_ids": [],
            "skipped": [],
        }
    accepted_ids = [
        str(row["id"])
        for row in conn.execute(
            f"""
            SELECT id FROM claims
            WHERE domain = ? AND status = 'accepted'
              AND id IN ({",".join("?" for _ in claim_ids)})
            """,
            (domain, *claim_ids),
        ).fetchall()
    ]
    return promote_accepted_claims_for_domain(
        conn,
        domain=domain,
        claim_ids=accepted_ids,
    )


def list_top_evidence_atoms(
    conn: sqlite3.Connection,
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Return compact atom projections for reports."""
    rows = conn.execute(
        """
        SELECT id, canonical_text, source_claim_ids_json, source_quote_ids_json,
               concepts_json, support_count, contradiction_count, scope,
               evidence_type, asset_tags_json, evidence_maturity,
               training_suitability, confidence
        FROM evidence_atoms
        ORDER BY support_count DESC, contradiction_count DESC, updated_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    atoms: list[dict[str, Any]] = []
    for row in rows:
        atoms.append(
            {
                "atom_id": row["id"],
                "canonical_text": row["canonical_text"],
                "source_claim_ids": json.loads(row["source_claim_ids_json"] or "[]"),
                "source_quote_ids": json.loads(row["source_quote_ids_json"] or "[]"),
                "concepts": json.loads(row["concepts_json"] or "[]"),
                "support_count": int(row["support_count"] or 0),
                "contradiction_count": int(row["contradiction_count"] or 0),
                "scope": row["scope"],
                "evidence_type": row["evidence_type"],
                "asset_tags": json.loads(row["asset_tags_json"] or "[]"),
                "evidence_maturity": row["evidence_maturity"],
                "training_suitability": row["training_suitability"],
                "confidence": row["confidence"],
            }
        )
    return atoms


def build_evidence_card_for_claim(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    stance: str = "supports",
    asset_tags: list[str] | None = None,
    evidence_maturity: str = "seed",
) -> EvidenceCard_v0_1:
    """Build a canonical operator-private evidence card from an accepted claim."""
    claim = _claim_row(conn, claim_id)
    quotes = _quote_rows(conn, claim_id)
    if not quotes:
        raise ValueError(f"Evidence card requires a quote-backed claim: {claim_id}")
    source = conn.execute(
        """
        SELECT title, authors_json, year, url, source_type
        FROM sources
        WHERE id = ?
        """,
        (claim["source_id"],),
    ).fetchone()
    if source is None:
        raise ValueError(f"Source not found for claim: {claim_id}")
    limitations = json.loads(claim["limitations_json"] or "[]")
    quote = str(quotes[0]["quote_text"])
    payload = {
        "card_type": "evidence_claim",
        "claim": claim["claim_text"],
        "quote": quote[:MAX_CARD_QUOTE_CHARS],
        "source": {
            "title": source["title"],
            "authors": json.loads(source["authors_json"] or "[]"),
            "year": source["year"],
            "url": source["url"],
            "source_type": source["source_type"] or "unknown",
        },
        "stance": stance,
        "evidence_type": claim["evidence_type"],
        "scope": claim["scope"],
        "concepts": _concept_labels(conn, claim_id),
        "confidence": confidence_label(float(claim["confidence"] or 0.0)),
        "limitations": limitations,
        "asset_tags": asset_tags or list(DEFAULT_ATOM_ASSET_TAGS),
        "evidence_maturity": evidence_maturity,
    }
    return validate_evidence_card(payload)
