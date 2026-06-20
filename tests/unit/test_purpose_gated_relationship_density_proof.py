"""Purpose-gated relationship density proof tests."""

from __future__ import annotations

import json
from pathlib import Path

from rge.db.connection import ensure_database
from rge.db.repositories import (
    ChunkRecord,
    ChunkRepository,
    ClaimConceptRepository,
    ClaimRepository,
    ClusterReportRepository,
    ConceptRepository,
    SourceRecord,
    SourceRepository,
    make_chunk_id,
    sha256_hex,
    utc_now_iso,
)
from rge.modules.abstract_evidence import generate_abstract_evidence_cards
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.atlas_trace import (
    build_atlas_trace_export,
    build_atlas_trace_preview,
    build_graph_connection_metrics,
)
from rge.modules.failure_recommender import (
    PACKET_PURPOSE_GATING,
    PACKET_RELATIONSHIP_DENSITY,
    recommend_from_run_report,
)
from rge.modules.relationship_density_proof import (
    CORE_DENSITY_QUESTION,
    ensure_purpose_gated_relationship_density_proof,
)
from rge.modules.research_queue import score_discovered_candidate


def _seed_source(conn, *, source_key: str) -> tuple[str, str]:
    now = utc_now_iso()
    raw_text = (
        f"{source_key}: AI assistance, semantic diversity, originality, and ideation "
        "are discussed in quote-backed fixture evidence."
    )
    checksum = sha256_hex(raw_text)
    source_id = f"src_{checksum[:16]}"
    SourceRepository(conn).insert(
        SourceRecord(
            id=source_id,
            title=f"Density proof source {source_key}",
            source_type="paper",
            domain="creativity",
            local_path=f"fixtures/sources/{source_key}.txt",
            raw_text_checksum=checksum,
            status="ingested",
            created_at=now,
            updated_at=now,
            authors_json=json.dumps([f"Author {source_key}"]),
        )
    )
    chunk_id = make_chunk_id(source_id, 0, checksum)
    ChunkRepository(conn).insert_many(
        [
            ChunkRecord(
                id=chunk_id,
                source_id=source_id,
                chunk_index=0,
                chunk_text=raw_text,
                text_checksum=checksum,
                created_at=now,
                token_count=18,
            )
        ]
    )
    return source_id, chunk_id


def _concept_ids(conn, labels: list[str]) -> dict[str, str]:
    repo = ConceptRepository(conn)
    repo.ensure_domain_concepts("creativity")
    ids: dict[str, str] = {}
    for label in labels:
        concept = repo.get_by_label("creativity", label)
        assert concept is not None, label
        ids[label] = concept.id
    return ids


def _seed_claim(
    conn,
    *,
    source_key: str,
    claim_text: str,
    scope: str,
    concepts: list[str],
) -> str:
    source_id, chunk_id = _seed_source(conn, source_key=source_key)
    claim = ClaimRepository(conn).insert_accepted(
        {
            "source_id": source_id,
            "chunk_id": chunk_id,
            "claim_text": claim_text,
            "quote_span": claim_text[:100],
            "subject": "AI assistance",
            "predicate": "may_affect",
            "object": concepts[-1],
            "scope": scope,
            "evidence_type": "empirical",
            "confidence": 0.72,
            "limitations": [],
            "domain": "creativity",
        },
        extractor_provider="fixture",
        extractor_model="density_proof_test",
        llm_schema_version="0.1.0",
    )
    ids = _concept_ids(conn, concepts)
    link_repo = ClaimConceptRepository(conn)
    for index, concept_id in enumerate(ids.values()):
        link_repo.insert(
            claim_id=claim.id,
            concept_id=concept_id,
            role="object" if index else "method",
            confidence=0.82,
            domain_metadata={},
        )
    return claim.id


def _seed_density_claims(conn, count: int = 9) -> list[str]:
    concept_groups = [
        ["AI assistance", "semantic diversity"],
        ["AI assistance", "originality"],
        ["AI assistance", "ideation"],
    ]
    claim_ids: list[str] = []
    for index in range(count):
        group = concept_groups[index % len(concept_groups)]
        claim_ids.append(
            _seed_claim(
                conn,
                source_key=f"density_{index}",
                claim_text=(
                    f"AI assistance density claim {index} connects "
                    f"{group[-1]} to idea quality or diversity."
                ),
                scope="shared fixture density scope",
                concepts=group,
            )
        )
    return claim_ids


def _seed_cluster_report(conn, claim_ids: list[str]) -> None:
    report = {
        "report_type": "cluster_report",
        "cluster_id": "cluster_density_proof",
        "cluster_label": "Density proof cluster",
        "linked_claim_ids": claim_ids,
        "supporting_claims": claim_ids[:3],
        "contradicting_claims": claim_ids[3:4],
        "qualifying_claims": claim_ids[4:6],
        "strongest_relationships": [],
    }
    packet = {
        "cluster_id": "cluster_density_proof",
        "top_supporting_claims": claim_ids[:3],
        "top_contradicting_claims": claim_ids[3:4],
        "top_qualifying_claims": claim_ids[4:6],
        "newest_claims": claim_ids,
    }
    ClusterReportRepository(conn).insert(
        cluster_id="cluster_density_proof",
        cluster_label="Density proof cluster",
        included_concepts=["AI assistance", "semantic diversity", "originality"],
        evidence_packet=packet,
        report=report,
        prose_summary="Density proof cluster.",
    )


def test_purpose_mismatch_rejected_before_atom_promotion(tmp_path: Path) -> None:
    conn = ensure_database(tmp_path / "purpose_mismatch.sqlite")
    try:
        claim_id = _seed_claim(
            conn,
            source_key="mismatch",
            claim_text="AI assistance reduced semantic diversity in writing tasks.",
            scope="short-form writing tasks",
            concepts=["AI assistance", "semantic diversity"],
        )
        result = ensure_purpose_gated_relationship_density_proof(
            conn,
            domain="creativity",
            question="What visual style patterns recur in AI-assisted product design?",
            claim_ids=[claim_id],
        )
        assert result["purpose_mismatch_count"] == 1
        assert result["relationship_count"] == 0
        assert result["atom_result"]["promoted_count"] == 0
        assert conn.execute("SELECT COUNT(*) FROM evidence_atoms").fetchone()[0] == 0
    finally:
        conn.close()


def test_density_proof_creates_clustered_atoms_and_typed_edges(tmp_path: Path) -> None:
    conn = ensure_database(tmp_path / "density.sqlite")
    try:
        claim_ids = _seed_density_claims(conn, count=9)
        _seed_cluster_report(conn, claim_ids)
        result = ensure_purpose_gated_relationship_density_proof(
            conn,
            domain="creativity",
            question=CORE_DENSITY_QUESTION,
            claim_ids=claim_ids,
        )
        metrics = build_graph_connection_metrics(
            conn,
            domain_pack="creativity",
            question=CORE_DENSITY_QUESTION,
        )
        totals = metrics["totals"]
        cluster = metrics["clusters"][0]
        assert result["relationship_count"] >= 8
        assert totals["multi_claim_atom_count"] >= 3
        assert totals["clustered_atom_count"] >= 2
        assert cluster["relationship_density"] >= 0.5
        assert cluster["orphan_claim_count"] < 5
        assert cluster["orphan_atom_count"] < 5
        assert totals["contradiction_edge_count"] >= 1
        assert totals["qualification_edge_count"] >= 1
        assert totals["synthesis_ready_cluster_count"] >= 1
    finally:
        conn.close()


def test_atlas_trace_preview_shows_connection_reasons_and_relationship_type(
    tmp_path: Path,
) -> None:
    conn = ensure_database(tmp_path / "trace.sqlite")
    try:
        claim_ids = _seed_density_claims(conn, count=3)
        _seed_cluster_report(conn, claim_ids)
        ensure_purpose_gated_relationship_density_proof(
            conn,
            domain="creativity",
            question=CORE_DENSITY_QUESTION,
            claim_ids=claim_ids,
        )
        traces = build_atlas_trace_export(
            conn,
            domain_pack="creativity",
            question=CORE_DENSITY_QUESTION,
        )
        preview = build_atlas_trace_preview(traces)
        assert preview
        assert any(item["relationship_type"] for item in preview)
        assert any(item["why_connected"] for item in preview)
        assert all(item["purpose_match_status"] == "match" for item in preview)
        assert assert_no_private_fields({"atlas_trace_preview": preview}) == []
        joined = json.dumps(preview)
        assert "claim_id" not in joined
        assert "source_id" not in joined
        assert "quote_id" not in joined
    finally:
        conn.close()


def test_source_ranking_rejects_purpose_mismatch() -> None:
    scored = score_discovered_candidate(
        {
            "provider_id": "generic-diversity",
            "title": "AI assistance and semantic diversity in writing",
            "abstract": "AI assistance reduced semantic diversity during brainstorming.",
            "work_type": "article",
            "doi": "10.123/example",
            "year": 2024,
        },
        query="What visual style patterns recur in AI-assisted product design?",
        domain_pack="creativity",
        reference_year=2026,
    )
    assert scored["status"] == "rejected"
    assert scored["purpose_match_status"] == "mismatch"
    assert scored["purpose_gate_decision"] == "rejected"


def test_abstract_evidence_skips_purpose_mismatched_record() -> None:
    result = generate_abstract_evidence_cards(
        [
            {
                "source_id": "src_abstract_mismatch",
                "title": "AI assistance and semantic diversity",
                "abstract_text": "AI assistance reduced semantic diversity during brainstorming.",
                "source_status": "abstract_available",
            }
        ],
        domain_pack="creativity",
        question="How does AI co-creation affect human agency and control?",
    )
    assert result["purpose_mismatch_count"] == 1
    assert result["cards"][0]["status"] == "skipped"
    assert result["cards"][0]["skip_reason"] == "purpose_mismatch"


def test_recommender_chooses_density_or_purpose_gate_when_dominant() -> None:
    density = recommend_from_run_report(
        {
            "claims_accepted": 9,
            "claims_rejected": 0,
            "top_failure_modes": [],
            "acquisition_quality_summary": {},
            "graph_connection_metrics": {
                "totals": {
                    "claims": 9,
                    "relationships": 2,
                    "weak_atom_count": 0,
                    "multi_claim_atom_count": 3,
                    "purpose_mismatch_count": 0,
                }
            },
        }
    )
    purpose = recommend_from_run_report(
        {
            "claims_accepted": 4,
            "claims_rejected": 0,
            "top_failure_modes": [],
            "acquisition_quality_summary": {},
            "graph_connection_metrics": {
                "totals": {
                    "claims": 4,
                    "relationships": 4,
                    "weak_atom_count": 1,
                    "multi_claim_atom_count": 2,
                    "purpose_mismatch_count": 2,
                }
            },
        }
    )
    assert density["recommended_packet"] == PACKET_RELATIONSHIP_DENSITY
    assert purpose["recommended_packet"] == PACKET_PURPOSE_GATING
