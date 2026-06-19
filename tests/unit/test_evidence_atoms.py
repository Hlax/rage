"""Packet 1 evidence atom and canonical evidence card tests."""

from __future__ import annotations

import json
from pathlib import Path

from rge.db.connection import ensure_database
from rge.db.repositories import (
    ChunkRecord,
    ChunkRepository,
    ClaimConceptRepository,
    ClaimRepository,
    ConceptRepository,
    SourceRecord,
    SourceRepository,
    make_chunk_id,
    sha256_hex,
    utc_now_iso,
)
from rge.modules.evidence_atoms import (
    build_evidence_card_for_claim,
    promote_accepted_claims_for_domain,
    promote_claim_to_evidence_atom,
)


def _seed_claim_graph(db_path: Path) -> str:
    conn = ensure_database(db_path)
    try:
        now = utc_now_iso()
        raw_text = (
            "AI-assisted brainstorming reduced semantic diversity in short-form "
            "writing tasks while improving average idea quality."
        )
        checksum = sha256_hex(raw_text)
        source_id = f"src_{checksum[:16]}"
        SourceRepository(conn).insert(
            SourceRecord(
                id=source_id,
                title="Packet 1 fixture source",
                source_type="paper",
                domain="creativity",
                local_path="fixtures/sources/packet_1.txt",
                raw_text_checksum=checksum,
                status="ingested",
                created_at=now,
                updated_at=now,
                authors_json=json.dumps(["Fixture Author"]),
            )
        )
        chunk_checksum = sha256_hex(raw_text)
        chunk_id = make_chunk_id(source_id, 0, chunk_checksum)
        ChunkRepository(conn).insert_many(
            [
                ChunkRecord(
                    id=chunk_id,
                    source_id=source_id,
                    chunk_index=0,
                    chunk_text=raw_text,
                    text_checksum=chunk_checksum,
                    created_at=now,
                    token_count=12,
                )
            ]
        )
        claim = ClaimRepository(conn).insert_accepted(
            {
                "source_id": source_id,
                "chunk_id": chunk_id,
                "claim_text": (
                    "AI-assisted brainstorming reduced semantic diversity in "
                    "short-form writing tasks."
                ),
                "quote_span": (
                    "AI-assisted brainstorming reduced semantic diversity in "
                    "short-form writing tasks"
                ),
                "subject": "AI-assisted brainstorming",
                "predicate": "reduced",
                "object": "semantic diversity",
                "scope": "short-form writing tasks",
                "evidence_type": "empirical",
                "confidence": 0.72,
                "limitations": ["Fixture source only."],
                "domain": "creativity",
            },
            extractor_provider="fixture",
            extractor_model="packet_1_test",
            llm_schema_version="0.1.0",
        )
        concepts = ConceptRepository(conn)
        concepts.ensure_domain_concepts("creativity")
        concept = concepts.get_by_label("creativity", "semantic diversity")
        assert concept is not None
        ClaimConceptRepository(conn).insert(
            claim_id=claim.id,
            concept_id=concept.id,
            role="object",
            confidence=0.8,
            domain_metadata={},
        )
        return claim.id
    finally:
        conn.close()


def test_promote_claim_to_evidence_atom_preserves_quote_claim_and_maturity(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "evidence_atoms.sqlite"
    claim_id = _seed_claim_graph(db_path)
    conn = ensure_database(db_path)
    try:
        atom = promote_claim_to_evidence_atom(
            conn,
            claim_id,
            evidence_maturity="promising",
            training_suitability="not_ready",
        )

        assert atom["atom_id"].startswith("atom_")
        assert atom["source_claim_ids"] == [claim_id]
        assert atom["source_quote_ids"][0].startswith("qt_")
        assert "semantic diversity" in atom["concepts"]
        assert atom["support_count"] == 0
        assert atom["contradiction_count"] == 0
        assert atom["evidence_maturity"] == "promising"
        assert atom["training_suitability"] == "not_ready"

        persisted = conn.execute("SELECT COUNT(*) FROM evidence_atoms").fetchone()[0]
        assert persisted == 1
    finally:
        conn.close()


def test_promote_accepted_claims_for_domain_is_idempotent_merge(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "evidence_atoms_merge.sqlite"
    claim_id = _seed_claim_graph(db_path)
    conn = ensure_database(db_path)
    try:
        first = promote_accepted_claims_for_domain(conn, domain="creativity")
        second = promote_accepted_claims_for_domain(conn, domain="creativity")
        assert first["promoted_count"] == 1
        assert second["promoted_count"] == 1
        count = conn.execute("SELECT COUNT(*) FROM evidence_atoms").fetchone()[0]
        assert count == 1
    finally:
        conn.close()


def test_build_evidence_card_for_claim_uses_operator_private_canonical_shape(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "evidence_card.sqlite"
    claim_id = _seed_claim_graph(db_path)
    conn = ensure_database(db_path)
    try:
        card = build_evidence_card_for_claim(conn, claim_id)
        payload = card.model_dump(mode="json")

        assert payload["schema_version"] == "evidence_card_v0.1.0"
        assert payload["card_type"] == "evidence_claim"
        assert (
            payload["quote"]
            == "AI-assisted brainstorming reduced semantic diversity in short-form writing tasks"
        )
        assert payload["source"]["title"] == "Packet 1 fixture source"
        assert payload["source"]["source_type"] == "paper"
        assert "semantic diversity" in payload["concepts"]
        assert payload["evidence_maturity"] == "seed"
        assert "reasoning_training_candidate" in payload["asset_tags"]
    finally:
        conn.close()
