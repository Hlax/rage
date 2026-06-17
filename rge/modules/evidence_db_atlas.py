"""Evidence DB atlas population: run lineage and claim-backed card projection (ticket-294).

Operator-private helpers for non-fixture manual_text research on evidence DBs.
Fixture-mode golden MVP paths remain unchanged.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from rge.db.repositories import (
    ClusterReportRepository,
    PublicCardRepository,
    ResearchContractRepository,
    ResearchQueueRepository,
    ResearchRunRepository,
    RelationshipEvidenceRepository,
    RelationshipRepository,
    RunReportRepository,
    sha256_hex,
)
from rge.modules.domain_pack_loader import load_domain_pack, source_strategy_from_search_templates
from rge.modules.manual_source_fixtures import manual_text_lacks_extract_fixture


def _evidence_lineage_ids(topic: str) -> tuple[str, str, str]:
    digest = sha256_hex(topic.strip().casefold())[:16]
    return (
        f"contract_evidence_{digest}",
        f"rq_evidence_{digest}",
        f"run_evidence_{digest}",
    )


def _confidence_label(value: float | None) -> str:
    if value is None:
        return "medium"
    if value >= 0.75:
        return "high"
    if value >= 0.5:
        return "medium"
    return "low"


def _claim_card_id(claim_id: str) -> str:
    suffix = claim_id.removeprefix("clm_")[:16]
    return f"card_claim_{suffix}"


def _claim_card_title(claim_text: str, subject: str | None, predicate: str | None) -> str:
    if subject and predicate:
        candidate = f"{subject} {predicate}".strip()
        if len(candidate) <= 80:
            return candidate
    text = claim_text.strip()
    if len(text) <= 80:
        return text
    return text[:77].rstrip() + "..."


def db_has_non_fixture_manual_claims(conn: sqlite3.Connection) -> bool:
    """True when accepted claims exist from manual_text sources outside the fixture map."""
    rows = conn.execute(
        """
        SELECT s.id, s.source_type, s.raw_text_checksum
        FROM claims c
        JOIN sources s ON s.id = c.source_id
        WHERE c.status = 'accepted'
        """
    ).fetchall()
    for row in rows:
        if row["source_type"] != "manual_text":
            continue
        source = type("Source", (), dict(row))()
        if manual_text_lacks_extract_fixture(source):
            return True
    return False


def ensure_evidence_research_run_lineage(
    conn: sqlite3.Connection,
    *,
    topic: str,
    domain_pack: str = "creativity",
) -> dict[str, Any]:
    """Ensure contract, queue question row, and research_run for evidence DB atlas lineage."""
    contract_id, question_id, run_id = _evidence_lineage_ids(topic)
    run_repo = ResearchRunRepository(conn)
    existing_run = run_repo.get_by_id(run_id)
    if existing_run is not None:
        return {
            "status": "already_present",
            "contract_id": contract_id,
            "research_question_id": question_id,
            "run_id": run_id,
        }

    contract_repo = ResearchContractRepository(conn)
    if contract_repo.get_by_id(contract_id) is None:
        pack = load_domain_pack(domain_pack)
        allowed = [concept.label for concept in pack.concepts[:8]]
        adjacent = list(pack.domain_identity.overlap_domains[:4])
        contract_repo.insert(
            {
                "id": contract_id,
                "root_topic": topic,
                "primary_question": topic,
                "domain_pack": domain_pack,
                "allowed_concepts": allowed,
                "adjacent_concepts": adjacent,
                "out_of_scope_concepts": [],
                "source_strategy": source_strategy_from_search_templates(pack),
                "status": "active",
            }
        )

    queue_repo = ResearchQueueRepository(conn)
    if queue_repo.get_followup(contract_id, topic) is None:
        queue_repo.insert_followup(
            contract_id=contract_id,
            question_text=topic,
            priority_score=1.0,
            reason="evidence_db_atlas_lineage",
            status="active",
            research_question_id=question_id,
        )

    run_repo.ensure(
        run_id=run_id,
        topic=topic,
        domain_pack=domain_pack,
        contract_id=contract_id,
        mode="live_evidence",
        status="completed",
    )
    return {
        "status": "created",
        "contract_id": contract_id,
        "research_question_id": question_id,
        "run_id": run_id,
    }


def _linked_concept_labels(conn: sqlite3.Connection, claim_id: str) -> list[str]:
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
    labels = [str(row["label"]).strip() for row in rows if row["label"]]
    return labels


def ensure_claim_backed_public_cards(conn: sqlite3.Connection) -> list[str]:
    """Seed public cards from accepted non-fixture manual claims when none exist yet."""
    repo = PublicCardRepository(conn)
    if not db_has_non_fixture_manual_claims(conn):
        return []

    existing = repo.list_public_safe(limit=100)
    if existing:
        if all(record.id.startswith("card_golden_") for record in existing):
            for record in existing:
                conn.execute("DELETE FROM public_cards WHERE id = ?", (record.id,))
            conn.commit()
        else:
            return []

    rows = conn.execute(
        """
        SELECT c.id, c.claim_text, c.subject, c.predicate, c.confidence,
               c.evidence_type, c.source_id, s.title AS source_title,
               s.source_type, s.raw_text_checksum
        FROM claims c
        JOIN sources s ON s.id = c.source_id
        WHERE c.status = 'accepted'
        ORDER BY c.id
        """
    ).fetchall()

    seeded: list[str] = []
    source_ids: set[str] = set()
    for row in rows:
        source = type("Source", (), {"source_type": row["source_type"], "raw_text_checksum": row["raw_text_checksum"]})()
        if not manual_text_lacks_extract_fixture(source):
            continue

        claim_id = str(row["id"])
        card_id = _claim_card_id(claim_id)
        concepts = _linked_concept_labels(conn, claim_id)
        if not concepts:
            concepts = ["creativity"]

        source_ids.add(str(row["source_id"]))
        repo.insert(
            card_id=card_id,
            card_type="claim_card",
            title=_claim_card_title(
                str(row["claim_text"] or ""),
                row["subject"],
                row["predicate"],
            ),
            summary=str(row["claim_text"] or "").strip(),
            confidence=_confidence_label(
                float(row["confidence"]) if row["confidence"] is not None else None
            ),
            concepts=concepts,
            source_count=1,
            claim_ids=[claim_id],
            public_detail_level="standard",
            is_public_safe=True,
            private_fields={
                "evidence_type": row["evidence_type"],
                "source_title": row["source_title"],
                "source_type": row["source_type"],
            },
        )
        seeded.append(card_id)

    if seeded:
        for card_id in seeded:
            record = repo.get_by_id(card_id)
            if record is None:
                continue
            claim_ids = json.loads(record.claim_ids_json or "[]")
            conn.execute(
                """
                UPDATE public_cards
                SET source_count = ?
                WHERE id = ?
                """,
                (len(source_ids), card_id),
            )
        conn.commit()

    return seeded


def claim_backed_card_extras(conn: sqlite3.Connection, record: Any) -> dict[str, Any]:
    """Build atlas export extras for claim-backed cards at projection time."""
    if not str(record.id).startswith("card_claim_"):
        return {}
    private = json.loads(record.private_fields_json or "{}")
    claim_ids = json.loads(record.claim_ids_json or "[]")
    extras: dict[str, Any] = {
        "public_caveats": [
            "Evidence from operator live or arbitrary manual_text extraction.",
        ],
        "public_source_metadata": [
            {
                "title": str(private.get("source_title") or "Manual research note"),
                "source_type": str(private.get("source_type") or "manual_text"),
            }
        ],
    }
    if private.get("evidence_type"):
        extras["evidence_type"] = private["evidence_type"]
    if claim_ids:
        row = conn.execute(
            "SELECT created_at FROM claims WHERE id = ?",
            (claim_ids[0],),
        ).fetchone()
        if row and row["created_at"]:
            extras["public_run_timestamp"] = row["created_at"]
    return extras


def ensure_evidence_run_report(
    conn: sqlite3.Connection,
    *,
    topic: str,
    domain_pack: str = "creativity",
) -> dict[str, Any]:
    """Persist an evidence DB run report row for atlas reports[] projection."""
    if not db_has_non_fixture_manual_claims(conn):
        return {"status": "skipped", "reason": "no_non_fixture_manual_claims"}

    contract_id, _question_id, run_id = _evidence_lineage_ids(topic)
    ensure_evidence_research_run_lineage(conn, topic=topic, domain_pack=domain_pack)

    report_repo = RunReportRepository(conn)
    existing = report_repo.get_by_run_id(run_id)
    if existing is not None:
        return {
            "status": "already_present",
            "run_id": run_id,
            "report_id": existing.id,
        }

    from rge.modules.run_evaluator import build_run_report

    report = build_run_report(
        conn,
        run_id=run_id,
        topic=topic,
        domain_pack=domain_pack,
        contract_id=contract_id,
    )
    record = report_repo.insert(
        run_id=run_id,
        topic=topic,
        domain_pack=domain_pack,
        report=report,
    )
    return {
        "status": "created",
        "run_id": run_id,
        "report_id": record.id,
    }


def _evidence_claim_ids(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT c.id, s.source_type, s.raw_text_checksum
        FROM claims c
        JOIN sources s ON s.id = c.source_id
        WHERE c.status = 'accepted'
        ORDER BY c.id
        """
    ).fetchall()
    claim_ids: list[str] = []
    for row in rows:
        if row["source_type"] != "manual_text":
            continue
        source = type("Source", (), dict(row))()
        if manual_text_lacks_extract_fixture(source):
            claim_ids.append(str(row["id"]))
    return claim_ids


def _concepts_for_claims(conn: sqlite3.Connection, claim_ids: list[str]) -> list[str]:
    if not claim_ids:
        return []
    placeholders = ",".join("?" for _ in claim_ids)
    rows = conn.execute(
        f"""
        SELECT DISTINCT c.label
        FROM claim_concepts cc
        JOIN concepts c ON c.id = cc.concept_id
        WHERE cc.claim_id IN ({placeholders})
        ORDER BY c.label
        """,
        tuple(claim_ids),
    ).fetchall()
    return [str(row["label"]).strip() for row in rows if row["label"]]


def _evidence_cluster_label(concepts: list[str]) -> str:
    if len(concepts) >= 2:
        return f"{concepts[0]} and {concepts[1]}"
    if concepts:
        return concepts[0]
    return "Evidence cluster summary"


def ensure_evidence_cluster_summary(
    conn: sqlite3.Connection,
    *,
    topic: str,
    domain_pack: str = "creativity",
) -> dict[str, Any]:
    """Persist a minimal cluster_reports row for evidence DB atlas clusters[] projection."""
    if not db_has_non_fixture_manual_claims(conn):
        return {"status": "skipped", "reason": "no_non_fixture_manual_claims"}

    claim_ids = _evidence_claim_ids(conn)
    if not claim_ids:
        return {"status": "skipped", "reason": "no_evidence_claim_ids"}

    _contract_id, _question_id, run_id = _evidence_lineage_ids(topic)
    ensure_evidence_research_run_lineage(conn, topic=topic, domain_pack=domain_pack)

    existing = conn.execute(
        "SELECT id FROM cluster_reports WHERE run_id = ? ORDER BY created_at DESC LIMIT 1",
        (run_id,),
    ).fetchone()
    if existing is not None:
        return {
            "status": "already_present",
            "run_id": run_id,
            "cluster_report_id": str(existing["id"]),
        }

    digest = sha256_hex(topic.strip().casefold())[:12]
    cluster_id = f"cluster_evidence_{digest}"
    included_concepts = _concepts_for_claims(conn, claim_ids)
    if not included_concepts:
        included_concepts = [domain_pack]
    cluster_label = _evidence_cluster_label(included_concepts)

    relationships = RelationshipRepository(conn).list_active()
    strongest = sorted(
        relationships,
        key=lambda rel: float(rel.get("confidence") or 0.0),
        reverse=True,
    )[:3]

    source_rows = conn.execute(
        f"""
        SELECT DISTINCT s.id, s.title
        FROM sources s
        JOIN claims c ON c.source_id = s.id
        WHERE c.id IN ({",".join("?" for _ in claim_ids)})
        ORDER BY s.id
        """,
        tuple(claim_ids),
    ).fetchall()

    evidence_packet = {
        "cluster_id": cluster_id,
        "top_supporting_claims": claim_ids[:5],
        "top_contradicting_claims": [],
        "top_qualifying_claims": [],
        "highest_quality_sources": [
            {"source_id": row["id"], "title": row["title"]} for row in source_rows[:3]
        ],
        "newest_claims": claim_ids[-3:],
        "highest_score_change_events": [],
        "bridge_concepts": included_concepts[:2],
        "open_gaps": [],
    }

    report = {
        "report_type": "cluster_report",
        "cluster_id": cluster_id,
        "cluster_label": cluster_label,
        "included_concepts": included_concepts,
        "supporting_claims": claim_ids,
        "contradicting_claims": [],
        "qualifying_claims": [],
        "strongest_relationships": [rel["id"] for rel in strongest],
        "linked_claim_ids": claim_ids,
        "formula_version": "evidence_summary_v0.1.0",
        "relationship_count": len(relationships),
        "evidence_packet": evidence_packet,
    }

    record = ClusterReportRepository(conn).insert(
        cluster_id=cluster_id,
        cluster_label=cluster_label,
        included_concepts=included_concepts,
        evidence_packet=evidence_packet,
        report=report,
        prose_summary=(
            f"Evidence cluster summary for {len(claim_ids)} claim(s) "
            f"linked to {len(included_concepts)} concept(s)."
        ),
        run_id=run_id,
    )
    return {
        "status": "created",
        "run_id": run_id,
        "cluster_report_id": record.id,
        "cluster_label": cluster_label,
    }


_ROLE_PRIORITY: dict[str, int] = {
    "method": 0,
    "subject": 1,
    "object": 2,
    "context": 3,
}


def _claim_concept_links(
    conn: sqlite3.Connection, claim_id: str
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT cc.concept_id, cc.role, cc.confidence, c.label
        FROM claim_concepts cc
        JOIN concepts c ON c.id = cc.concept_id
        WHERE cc.claim_id = ?
        ORDER BY cc.concept_id
        """,
        (claim_id,),
    ).fetchall()
    return [
        {
            "concept_id": str(row["concept_id"]),
            "role": str(row["role"] or "context"),
            "confidence": float(row["confidence"] or 0.5),
            "label": str(row["label"] or ""),
        }
        for row in rows
    ]


def _ordered_concept_pair(
    links: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    if len(links) < 2:
        return None
    ordered = sorted(
        links,
        key=lambda item: (
            _ROLE_PRIORITY.get(str(item["role"]), 99),
            -float(item["confidence"]),
            str(item["concept_id"]),
        ),
    )
    return ordered[0], ordered[1]


def _predicate_for_link_pair(subject_role: str, object_role: str) -> str:
    if subject_role == "method":
        return "may_influence"
    if object_role == "object":
        return "relates_to"
    return "relates_to"


def _evidence_relationships_exist(
    conn: sqlite3.Connection, claim_ids: list[str]
) -> bool:
    if not claim_ids:
        return False
    placeholders = ",".join("?" for _ in claim_ids)
    row = conn.execute(
        f"""
        SELECT COUNT(DISTINCT r.id)
        FROM relationships r
        JOIN relationship_evidence re ON re.relationship_id = r.id
        WHERE r.status = 'active' AND re.claim_id IN ({placeholders})
        """,
        tuple(claim_ids),
    ).fetchone()
    return int(row[0]) > 0 if row else False


def ensure_evidence_relationship_edges(
    conn: sqlite3.Connection,
    *,
    topic: str,
    domain_pack: str = "creativity",
) -> dict[str, Any]:
    """Seed active relationships from claim-concept links for evidence DB atlas edges[]."""
    if not db_has_non_fixture_manual_claims(conn):
        return {"status": "skipped", "reason": "no_non_fixture_manual_claims"}

    claim_ids = _evidence_claim_ids(conn)
    if not claim_ids:
        return {"status": "skipped", "reason": "no_evidence_claim_ids"}

    if _evidence_relationships_exist(conn, claim_ids):
        return {
            "status": "already_present",
            "relationship_ids": [],
        }

    rel_repo = RelationshipRepository(conn)
    evidence_repo = RelationshipEvidenceRepository(conn)
    created_ids: list[str] = []

    for claim_id in claim_ids:
        links = _claim_concept_links(conn, claim_id)
        pair = _ordered_concept_pair(links)
        if pair is None:
            continue
        subject, obj = pair
        if subject["concept_id"] == obj["concept_id"]:
            continue

        scope_row = conn.execute(
            "SELECT scope FROM claims WHERE id = ?",
            (claim_id,),
        ).fetchone()
        scope = str(scope_row["scope"]).strip() if scope_row and scope_row["scope"] else "evidence summary"
        predicate = _predicate_for_link_pair(str(subject["role"]), str(obj["role"]))
        confidence = min(float(subject["confidence"]), float(obj["confidence"]))

        relationship = rel_repo.insert(
            subject_concept_id=subject["concept_id"],
            predicate=predicate,
            object_concept_id=obj["concept_id"],
            scope=scope,
            confidence=confidence,
            domain=domain_pack,
            status="active",
            evidence_strength=confidence,
            domain_metadata={"evidence_db_atlas": True, "claim_id": claim_id},
        )
        evidence_repo.insert(
            relationship_id=relationship["id"],
            claim_id=claim_id,
            stance="supports",
            relevance_score=confidence,
        )
        created_ids.append(relationship["id"])

    if not created_ids:
        return {"status": "skipped", "reason": "no_concept_pairs_for_edges"}

    return {
        "status": "created",
        "relationship_ids": created_ids,
    }
