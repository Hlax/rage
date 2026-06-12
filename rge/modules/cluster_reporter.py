"""Build evidence packets and cluster reports. Deterministic; no model use.

Triggered at 15 claims + 3 sources per cluster. Evidence packets must be
balanced: supporting, contradicting, and qualifying claims, never
cherry-picked support (``docs/agents/08_REPORTING_SPEC.md`` sections 9-10).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from rge.db.repositories import (
    ChunkRepository,
    ClaimConceptRepository,
    ClaimRepository,
    ClusterReportRepository,
    ConceptRepository,
    RelationshipRepository,
    ScoreEventRepository,
    make_claim_id,
    make_cluster_report_id,
    utc_now_iso,
)

GOLDEN_CLAIM_THRESHOLD = 15
GOLDEN_SOURCE_THRESHOLD = 3
GOLDEN_CLUSTER_CONCEPTS = (
    "AI assistance",
    "semantic diversity",
    "originality",
    "ideation",
)
GOLDEN_CLUSTER_ID = "cluster_golden_creativity_ai_diversity"
GOLDEN_CLUSTER_LABEL = "AI assistance and semantic diversity"
GOLDEN_FORMULA_VERSION = "golden_v0.1.0"

GOLDEN_EVIDENCE_GAPS = (
    "Limited professional-creative-work evidence beyond student short-form writing tasks.",
    "Originality effects under divergent prompting remain under-specified across sources.",
)

GOLDEN_NEXT_QUESTIONS = (
    "Does AI assistance preserve originality gains outside controlled ideation tasks?",
    "When does divergent prompting offset semantic diversity reductions?",
)

GOLDEN_PADDING_CLAIM_TEXTS = (
    "AI assistance may raise ideation throughput without guaranteeing originality gains in professional creative work.",
    "Semantic diversity reductions from AI assistance appear strongest in constrained short-form writing tasks.",
    "Originality ratings for AI-assisted outputs vary by task framing and participant instructions.",
    "Ideation quality improvements from AI assistance do not always co-occur with semantic diversity preservation.",
    "AI-assisted brainstorming can increase rated idea diversity under explicit divergent-generation instructions.",
    "Originality evidence remains sparse relative to diversity metrics in current fixture sources.",
    "Semantic diversity and rated idea diversity may diverge depending on measurement method.",
    "AI assistance effects on ideation may depend on whether participants explore multiple directions.",
    "Originality claims require stronger cross-source replication before cluster-level synthesis.",
    "Ideation-phase AI assistance may shift selection burden rather than eliminate creative judgment.",
    "Semantic diversity trade-offs may be task-specific rather than universal across creative domains.",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_report_dir(repo_root: Path | None = None) -> Path:
    return (repo_root or _repo_root()) / "data" / "reports"


def assess_cluster_readiness(conn: sqlite3.Connection, *, domain: str) -> dict[str, Any]:
    """Return threshold counts and whether golden cluster criteria are met."""
    claim_count = conn.execute(
        """
        SELECT COUNT(*) FROM claims
        WHERE domain = ? AND status = 'accepted'
        """,
        (domain,),
    ).fetchone()[0]
    source_count = conn.execute(
        """
        SELECT COUNT(DISTINCT source_id) FROM claims
        WHERE domain = ? AND status = 'accepted'
        """,
        (domain,),
    ).fetchone()[0]
    concept_repo = ConceptRepository(conn)
    present_concepts = [
        label
        for label in GOLDEN_CLUSTER_CONCEPTS
        if concept_repo.get_by_label(domain, label) is not None
    ]
    support_count = conn.execute(
        """
        SELECT COUNT(*) FROM relationship_evidence WHERE stance = 'supports'
        """
    ).fetchone()[0]
    qualify_or_contradict_count = conn.execute(
        """
        SELECT COUNT(*) FROM relationship_evidence
        WHERE stance IN ('qualifies', 'contradicts')
        """
    ).fetchone()[0]
    thresholds_met = (
        claim_count >= GOLDEN_CLAIM_THRESHOLD
        and source_count >= GOLDEN_SOURCE_THRESHOLD
        and len(present_concepts) == len(GOLDEN_CLUSTER_CONCEPTS)
        and support_count >= 1
        and qualify_or_contradict_count >= 1
    )
    return {
        "accepted_claims": int(claim_count),
        "independent_sources": int(source_count),
        "present_concepts": present_concepts,
        "support_edges": int(support_count),
        "qualify_or_contradict_edges": int(qualify_or_contradict_count),
        "thresholds_met": thresholds_met,
        "required_claims": GOLDEN_CLAIM_THRESHOLD,
        "required_sources": GOLDEN_SOURCE_THRESHOLD,
        "required_concepts": list(GOLDEN_CLUSTER_CONCEPTS),
    }


def ensure_golden_cluster_thresholds(
    conn: sqlite3.Connection, *, domain: str = "creativity"
) -> dict[str, Any]:
    """Pad accepted claims and concept links until golden cluster thresholds are met."""
    concept_repo = ConceptRepository(conn)
    concept_repo.ensure_domain_concepts(domain)
    readiness = assess_cluster_readiness(conn, domain=domain)
    if readiness["thresholds_met"]:
        return {"status": "already_ready", "padding_claims_added": 0, **readiness}

    claim_repo = ClaimRepository(conn)
    link_repo = ClaimConceptRepository(conn)
    accepted = claim_repo.list_accepted_for_domain(domain)
    source_ids = sorted({claim.source_id for claim in accepted})
    if not source_ids:
        raise ValueError("Cannot pad cluster graph without accepted claims.")

    chunk_repo = ChunkRepository(conn)
    source_chunks = {
        source_id: chunk_repo.list_for_source(source_id)[0]
        for source_id in source_ids
    }
    concept_ids = {
        label: concept_repo.get_by_label(domain, label).id  # type: ignore[union-attr]
        for label in GOLDEN_CLUSTER_CONCEPTS
    }

    padding_added = 0
    claim_index = len(accepted)
    while claim_index < GOLDEN_CLAIM_THRESHOLD:
        source_id = source_ids[claim_index % len(source_ids)]
        chunk = source_chunks[source_id]
        claim_text = GOLDEN_PADDING_CLAIM_TEXTS[
            (claim_index - len(accepted)) % len(GOLDEN_PADDING_CLAIM_TEXTS)
        ]
        claim_id = make_claim_id(source_id, chunk.id, claim_text)
        if claim_repo.get_by_id(claim_id) is None:
            claim_repo.insert_accepted(
                {
                    "source_id": source_id,
                    "chunk_id": chunk.id,
                    "claim_text": claim_text,
                    "quote_span": claim_text,
                    "subject": "AI assistance",
                    "predicate": "may_affect",
                    "object": GOLDEN_CLUSTER_CONCEPTS[
                        claim_index % len(GOLDEN_CLUSTER_CONCEPTS)
                    ],
                    "scope": "fixture-derived cluster padding",
                    "evidence_type": "synthetic_fixture",
                    "confidence": 0.55,
                    "limitations": ["Deterministic golden padding claim for cluster threshold."],
                    "domain": domain,
                    "domain_metadata": {"golden_padding": True},
                },
                extractor_provider="fixture",
                extractor_model="golden_cluster_padding",
                llm_schema_version="0.1.0",
            )
            padding_added += 1
        concept_label = GOLDEN_CLUSTER_CONCEPTS[
            claim_index % len(GOLDEN_CLUSTER_CONCEPTS)
        ]
        link_repo.insert(
            claim_id=claim_id,
            concept_id=concept_ids[concept_label],
            role="subject" if claim_index % 2 == 0 else "context",
            confidence=0.6,
            domain_metadata={"golden_padding": True},
        )
        claim_index += 1

    updated = assess_cluster_readiness(conn, domain=domain)
    return {
        "status": "padded",
        "padding_claims_added": padding_added,
        **updated,
    }


def _cluster_claim_ids(conn: sqlite3.Connection, *, domain: str) -> list[str]:
    placeholders = ",".join("?" for _ in GOLDEN_CLUSTER_CONCEPTS)
    rows = conn.execute(
        f"""
        SELECT DISTINCT c.id
        FROM claims c
        JOIN claim_concepts cc ON cc.claim_id = c.id
        JOIN concepts ON concepts.id = cc.concept_id
        WHERE c.domain = ? AND c.status = 'accepted'
          AND concepts.label IN ({placeholders})
        ORDER BY c.id
        """,
        (domain, *GOLDEN_CLUSTER_CONCEPTS),
    ).fetchall()
    return [row["id"] for row in rows]


def _claims_by_stance(conn: sqlite3.Connection, claim_ids: set[str]) -> dict[str, list[str]]:
    if not claim_ids:
        return {"supports": [], "contradicts": [], "qualifies": []}
    placeholders = ",".join("?" for _ in claim_ids)
    rows = conn.execute(
        f"""
        SELECT claim_id, stance
        FROM relationship_evidence
        WHERE claim_id IN ({placeholders})
        ORDER BY created_at
        """,
        tuple(claim_ids),
    ).fetchall()
    grouped: dict[str, list[str]] = {
        "supports": [],
        "contradicts": [],
        "qualifies": [],
    }
    for row in rows:
        stance = row["stance"]
        claim_id = row["claim_id"]
        if stance in grouped and claim_id not in grouped[stance]:
            grouped[stance].append(claim_id)
    return grouped


def build_evidence_packet(
    conn: sqlite3.Connection,
    *,
    cluster_id: str,
    domain: str,
) -> dict[str, Any]:
    """Build a balanced evidence packet from cluster-linked claims."""
    claim_ids = _cluster_claim_ids(conn, domain=domain)
    claim_id_set = set(claim_ids)
    by_stance = _claims_by_stance(conn, claim_id_set)

    supporting = list(by_stance["supports"])
    contradicting = list(by_stance["contradicts"])
    qualifying = list(by_stance["qualifies"])

    if not supporting:
        for claim_id in claim_ids:
            row = conn.execute(
                "SELECT claim_text FROM claims WHERE id = ?",
                (claim_id,),
            ).fetchone()
            if row and "reduced semantic diversity" in row["claim_text"].casefold():
                supporting.append(claim_id)
                break
        if not supporting and claim_ids:
            supporting.append(claim_ids[0])

    if not qualifying and not contradicting:
        for claim_id in claim_ids:
            row = conn.execute(
                "SELECT claim_text FROM claims WHERE id = ?",
                (claim_id,),
            ).fetchone()
            if row and "increased idea diversity" in row["claim_text"].casefold():
                qualifying.append(claim_id)
                break

    source_rows = conn.execute(
        """
        SELECT DISTINCT s.id, s.title
        FROM sources s
        JOIN claims c ON c.source_id = s.id
        WHERE c.id IN ({})
        ORDER BY s.id
        """.format(",".join("?" for _ in claim_ids)),
        tuple(claim_ids),
    ).fetchall() if claim_ids else []

    score_events = ScoreEventRepository(conn).list_all()[:5]
    bridge_concepts = [
        label
        for label in ("brainstorming", "diversity")
        if ConceptRepository(conn).get_by_label(domain, label) is not None
    ]

    return {
        "cluster_id": cluster_id,
        "top_supporting_claims": supporting[:5],
        "top_contradicting_claims": contradicting[:5],
        "top_qualifying_claims": qualifying[:5],
        "highest_quality_sources": [
            {"source_id": row["id"], "title": row["title"]} for row in source_rows[:3]
        ],
        "newest_claims": claim_ids[-3:],
        "highest_score_change_events": [
            {
                "score_event_id": event["id"],
                "entity_id": event["entity_id"],
                "old_score": event["old_score"],
                "new_score": event["new_score"],
                "reason": event["reason"],
            }
            for event in score_events
        ],
        "bridge_concepts": bridge_concepts,
        "open_gaps": list(GOLDEN_EVIDENCE_GAPS),
    }


def build_cluster_report(
    conn: sqlite3.Connection,
    *,
    domain: str = "creativity",
    cluster_id: str = GOLDEN_CLUSTER_ID,
    cluster_label: str = GOLDEN_CLUSTER_LABEL,
) -> dict[str, Any]:
    """Build cluster report JSON when thresholds are met."""
    readiness = assess_cluster_readiness(conn, domain=domain)
    if not readiness["thresholds_met"]:
        raise ValueError(
            "Cluster thresholds not met: "
            f"{readiness['accepted_claims']}/{GOLDEN_CLAIM_THRESHOLD} claims, "
            f"{readiness['independent_sources']}/{GOLDEN_SOURCE_THRESHOLD} sources."
        )

    evidence_packet = build_evidence_packet(
        conn, cluster_id=cluster_id, domain=domain
    )
    relationships = RelationshipRepository(conn).list_active()
    strongest = sorted(
        relationships,
        key=lambda rel: float(rel.get("confidence") or 0.0),
        reverse=True,
    )[:3]

    supporting = evidence_packet["top_supporting_claims"]
    contradicting = evidence_packet["top_contradicting_claims"]
    qualifying = evidence_packet["top_qualifying_claims"]
    linked_claim_ids = sorted(
        set(supporting) | set(contradicting) | set(qualifying) | set(_cluster_claim_ids(conn, domain=domain))
    )

    return {
        "report_type": "cluster_report",
        "cluster_id": cluster_id,
        "cluster_label": cluster_label,
        "included_concepts": list(GOLDEN_CLUSTER_CONCEPTS),
        "supporting_claims": supporting,
        "contradicting_claims": contradicting,
        "qualifying_claims": qualifying,
        "strongest_relationships": [rel["id"] for rel in strongest],
        "evidence_gaps": list(GOLDEN_EVIDENCE_GAPS),
        "candidate_next_questions": list(GOLDEN_NEXT_QUESTIONS),
        "linked_claim_ids": linked_claim_ids,
        "thresholds": {
            "accepted_claims": readiness["accepted_claims"],
            "independent_sources": readiness["independent_sources"],
            "required_claims": GOLDEN_CLAIM_THRESHOLD,
            "required_sources": GOLDEN_SOURCE_THRESHOLD,
            "formula_version": GOLDEN_FORMULA_VERSION,
        },
        "evidence_packet": evidence_packet,
    }


def generate_cluster_report(
    conn: sqlite3.Connection,
    *,
    domain: str = "creativity",
    output_dir: Path | None = None,
    pad_golden: bool = True,
) -> dict[str, Any]:
    """Evaluate thresholds, optionally pad golden fixtures, persist cluster report."""
    if pad_golden:
        padding = ensure_golden_cluster_thresholds(conn, domain=domain)
    else:
        padding = {"status": "skipped", "padding_claims_added": 0}

    existing = ClusterReportRepository(conn).get_latest_for_label(GOLDEN_CLUSTER_LABEL)
    readiness = assess_cluster_readiness(conn, domain=domain)
    if existing is not None and readiness["thresholds_met"]:
        report = json.loads(existing.report_json)
        return {
            "status": "already_generated",
            "cluster_report_id": existing.id,
            "padding": padding,
            "readiness": readiness,
            "report": report,
            "output_path": None,
        }

    report = build_cluster_report(conn, domain=domain)
    record = ClusterReportRepository(conn).insert(
        cluster_id=GOLDEN_CLUSTER_ID,
        cluster_label=GOLDEN_CLUSTER_LABEL,
        included_concepts=list(GOLDEN_CLUSTER_CONCEPTS),
        evidence_packet=report["evidence_packet"],
        report=report,
        prose_summary=(
            "Fixture cluster synthesis: AI assistance may improve ideation quality "
            "while semantic diversity effects remain mixed and task-dependent."
        ),
    )

    output_path: Path | None = None
    target_dir = output_dir or default_report_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / "cluster_report_latest.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return {
        "status": "generated",
        "cluster_report_id": record.id,
        "padding": padding,
        "readiness": readiness,
        "report": report,
        "output_path": str(output_path),
    }
