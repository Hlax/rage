"""Evidence card export and atlas-safe preview tests."""

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
from rge.modules.evidence_card_exporter import (
    assert_atlas_safe_preview_bundle,
    derive_atlas_safe_evidence_preview,
    export_evidence_cards,
    list_top_evidence_cards,
)
from rge.modules.evidence_atoms import build_evidence_card_for_claim


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
                title="Evidence card export fixture source",
                source_type="paper",
                domain="creativity",
                local_path="fixtures/sources/packet_5.txt",
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
            extractor_model="packet_5_test",
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


def test_derive_atlas_safe_evidence_preview_omits_quote_and_private_keys() -> None:
    preview = derive_atlas_safe_evidence_preview(
        {
            "card_type": "evidence_claim",
            "claim": "AI-assisted brainstorming reduced semantic diversity in short-form writing tasks.",
            "quote": "AI-assisted brainstorming reduced semantic diversity in short-form writing tasks",
            "source": {
                "title": "Fixture source",
                "source_type": "paper",
            },
            "stance": "supports",
            "evidence_type": "empirical",
            "scope": "short-form writing tasks",
            "concepts": ["semantic diversity"],
            "confidence": "medium",
            "limitations": ["Fixture only."],
            "asset_tags": ["reasoning_training_candidate"],
            "evidence_maturity": "seed",
        }
    )

    assert "quote" not in preview
    assert "claim_id" not in preview
    assert preview["summary"]
    assert preview["source_type"] == "paper"
    assert preview["evidence_maturity"] == "seed"
    assert assert_atlas_safe_preview_bundle([preview]) == []


def test_export_evidence_cards_writes_operator_private_bundle(tmp_path: Path) -> None:
    db_path = tmp_path / "evidence_cards.sqlite"
    claim_id = _seed_claim_graph(db_path)
    conn = ensure_database(db_path)
    try:
        output_dir = tmp_path / "exports"
        result = export_evidence_cards(
            conn,
            domain="creativity",
            output_dir=output_dir,
            limit=10,
            generated_at="2026-06-19T12:00:00Z",
        )
        assert result["status"] == "success"
        assert result["card_count"] == 1
        bundle_path = output_dir / "evidence_cards.json"
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        assert bundle["schema_version"] == "evidence_card_export_v0.1.0"
        assert bundle["evidence_cards"][0]["schema_version"] == "evidence_card_v0.1.0"
        assert bundle["atlas_safe_previews"][0]["summary"]
        assert "quote" not in bundle["atlas_safe_previews"][0]
    finally:
        conn.close()


def test_list_top_evidence_cards_returns_quote_backed_cards(tmp_path: Path) -> None:
    db_path = tmp_path / "top_cards.sqlite"
    claim_id = _seed_claim_graph(db_path)
    conn = ensure_database(db_path)
    try:
        cards = list_top_evidence_cards(conn, claim_ids=[claim_id], limit=3)
        assert len(cards) == 1
        assert cards[0]["quote"]
        card = build_evidence_card_for_claim(conn, claim_id)
        assert cards[0]["claim"] == card.claim
    finally:
        conn.close()
