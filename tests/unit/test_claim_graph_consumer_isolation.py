"""Accepted-only graph and projection isolation tests (ticket-417)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from rge.db.connection import ensure_database
from rge.db.repositories import (
    ChunkRecord,
    ChunkRepository,
    ClaimConceptRepository,
    ClaimRepository,
    ConceptRepository,
    RelationshipEvidenceRepository,
    RelationshipRepository,
    SourceRecord,
    SourceRepository,
    make_claim_concept_link_id,
    make_relationship_evidence_id,
    utc_now_iso,
)
from rge.modules.atlas_snapshot_builder import _build_relationship_edges
from rge.modules.card_exporter import ensure_golden_public_cards
from rge.modules.evidence_atoms import build_evidence_atom_for_claim
from rge.modules.run_evaluator import aggregate_run_metrics
from rge.modules.synthesis_packet_runner import collect_db_throughput_snapshot


def _seed_source(conn: sqlite3.Connection) -> tuple[str, str]:
    now = utc_now_iso()
    source_id = "src_consumer_isolation"
    chunk_id = "chk_consumer_isolation_0"
    SourceRepository(conn).insert(
        SourceRecord(
            id=source_id,
            title="Consumer isolation fixture",
            source_type="manual_text",
            domain="creativity",
            local_path="",
            raw_text_checksum="consumer-isolation-checksum",
            status="ingested",
            created_at=now,
            updated_at=now,
        )
    )
    ChunkRepository(conn).insert_many(
        [
            ChunkRecord(
                id=chunk_id,
                source_id=source_id,
                chunk_index=0,
                chunk_text="Accepted evidence remains bounded and private candidates stay isolated.",
                text_checksum="consumer-chunk-checksum",
                created_at=now,
            )
        ]
    )
    return source_id, chunk_id


def _candidate(source_id: str, chunk_id: str, label: str) -> dict:
    claim_text = f"{label} evidence remains bounded."
    return {
        "source_id": source_id,
        "chunk_id": chunk_id,
        "claim_text": claim_text,
        "quote_span": claim_text,
        "subject": label,
        "predicate": "remains",
        "object": "bounded",
        "scope": "consumer isolation fixture",
        "evidence_type": "empirical",
        "confidence": 0.6,
        "limitations": [],
        "domain": "creativity",
        "domain_metadata": {},
    }


def _seed_lifecycle_claims(
    conn: sqlite3.Connection,
) -> tuple[dict[str, str], dict[str, dict]]:
    source_id, chunk_id = _seed_source(conn)
    repo = ClaimRepository(conn)
    candidates = {
        state: _candidate(source_id, chunk_id, state)
        for state in ("accepted", "proposed", "needs_review", "rejected")
    }
    ids: dict[str, str] = {}
    for state, candidate in candidates.items():
        proposed = repo.insert_proposed(
            candidate,
            extractor_provider="mock",
            extractor_model="isolation-fixture",
            llm_schema_version="0.1.0",
        )
        ids[state] = proposed.id
        if state == "accepted":
            repo.transition_status(
                proposed.id,
                "accepted",
                actor_type="python_validator",
                reason_code="fixture_accept",
                claim=candidate,
            )
        elif state == "needs_review":
            repo.transition_status(
                proposed.id,
                "needs_review",
                actor_type="python_validator",
                reason_code="fixture_review",
            )
        elif state == "rejected":
            repo.transition_status(
                proposed.id,
                "rejected",
                actor_type="python_validator",
                reason_code="fixture_reject",
                rejection_reason="fixture_reject",
            )
    return ids, candidates


def test_graph_repositories_reject_new_nonaccepted_links_and_hide_stale_rows(
    tmp_path: Path,
) -> None:
    conn = ensure_database(tmp_path / "graph-isolation.sqlite")
    try:
        ids, _ = _seed_lifecycle_claims(conn)
        concepts = ConceptRepository(conn).ensure_domain_concepts("creativity")
        assert len(concepts) >= 3
        link_repo = ClaimConceptRepository(conn)

        link_repo.insert(
            claim_id=ids["accepted"],
            concept_id=concepts[0].id,
            role="subject",
            confidence=0.8,
            domain_metadata={},
        )
        for state in ("proposed", "needs_review", "rejected"):
            with pytest.raises(ValueError, match="accepted claim"):
                link_repo.insert(
                    claim_id=ids[state],
                    concept_id=concepts[0].id,
                    role="subject",
                    confidence=0.8,
                    domain_metadata={},
                )
            conn.execute(
                """
                INSERT INTO claim_concepts (
                    id, claim_id, concept_id, role, confidence,
                    domain_metadata_json, created_at
                ) VALUES (?, ?, ?, 'subject', 0.8, '{}', ?)
                """,
                (
                    make_claim_concept_link_id(ids[state], concepts[0].id, "subject"),
                    ids[state],
                    concepts[0].id,
                    utc_now_iso(),
                ),
            )
        conn.commit()

        assert link_repo.count_for_source("src_consumer_isolation") == 1
        assert [row["claim_id"] for row in link_repo.list_for_source("src_consumer_isolation")] == [
            ids["accepted"]
        ]

        accepted_relationship = RelationshipRepository(conn).insert(
            subject_concept_id=concepts[0].id,
            predicate="supports",
            object_concept_id=concepts[1].id,
            scope="accepted fixture",
            confidence=0.7,
            domain="creativity",
            status="active",
        )
        private_relationship = RelationshipRepository(conn).insert(
            subject_concept_id=concepts[1].id,
            predicate="qualifies",
            object_concept_id=concepts[2].id,
            scope="private fixture",
            confidence=0.5,
            domain="creativity",
            status="active",
        )
        evidence_repo = RelationshipEvidenceRepository(conn)
        evidence_repo.insert(
            relationship_id=accepted_relationship["id"],
            claim_id=ids["accepted"],
            stance="supports",
        )
        with pytest.raises(ValueError, match="accepted claim"):
            evidence_repo.insert(
                relationship_id=private_relationship["id"],
                claim_id=ids["proposed"],
                stance="qualifies",
            )
        conn.execute(
            """
            INSERT INTO relationship_evidence (
                id, relationship_id, claim_id, stance, relevance_score, created_at
            ) VALUES (?, ?, ?, 'qualifies', 0.5, ?)
            """,
            (
                make_relationship_evidence_id(
                    private_relationship["id"], ids["proposed"], "qualifies"
                ),
                private_relationship["id"],
                ids["proposed"],
                utc_now_iso(),
            ),
        )
        conn.commit()

        assert evidence_repo.list_for_relationship(private_relationship["id"]) == []
        assert RelationshipRepository(conn).count_for_source("src_consumer_isolation") == 1
        assert [
            row["id"]
            for row in RelationshipRepository(conn).list_for_source(
                "src_consumer_isolation"
            )
        ] == [accepted_relationship["id"]]
        assert [edge["id"] for edge in _build_relationship_edges(conn, "creativity")] == [
            accepted_relationship["id"]
        ]
    finally:
        conn.close()


def test_reports_synthesis_atoms_and_public_cards_use_accepted_claims_only(
    tmp_path: Path,
) -> None:
    conn = ensure_database(tmp_path / "projection-isolation.sqlite")
    try:
        ids, _ = _seed_lifecycle_claims(conn)

        throughput = collect_db_throughput_snapshot(conn)
        assert throughput["claim_count"] == 1
        metrics = aggregate_run_metrics(conn)
        assert metrics["claims_accepted"] == 1
        assert metrics["claims_rejected"] == 1
        assert metrics["claims_extracted"] == 2

        accepted_atom = build_evidence_atom_for_claim(conn, ids["accepted"])
        assert accepted_atom.source_claim_ids == [ids["accepted"]]
        for state in ("proposed", "needs_review", "rejected"):
            with pytest.raises(ValueError, match="accepted claims"):
                build_evidence_atom_for_claim(conn, ids[state])

        seeded = ensure_golden_public_cards(conn)
        assert seeded
        rows = conn.execute(
            "SELECT claim_ids_json FROM public_cards ORDER BY id"
        ).fetchall()
        assert rows
        for row in rows:
            assert set(json.loads(row["claim_ids_json"])) <= {ids["accepted"]}
    finally:
        conn.close()
