"""Evidence atom clustering + purpose-gated retrieval tests."""

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
    RelationshipEvidenceRepository,
    RelationshipRepository,
    SourceRecord,
    SourceRepository,
    make_chunk_id,
    sha256_hex,
    utc_now_iso,
)
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.atlas_trace import (
    build_atlas_trace_export,
    build_atlas_trace_preview,
    build_graph_connection_metrics,
)
from rge.modules.evidence_atoms import (
    cluster_compatible_evidence_atoms,
    promote_accepted_claims_for_domain,
)
from rge.modules.failure_recommender import (
    PACKET_ATOM_CLUSTERING,
    PACKET_PURPOSE_GATING,
    recommend_from_run_report,
)
from rge.modules.purpose_gating import evaluate_claim_purpose_fit


def _seed_source(conn, *, source_key: str) -> tuple[str, str]:
    now = utc_now_iso()
    raw_text = (
        f"Source {source_key}: AI-assisted work affected creative evidence. "
        "The source contains quote-backed research claims for testing."
    )
    checksum = sha256_hex(raw_text)
    source_id = f"src_{checksum[:16]}"
    SourceRepository(conn).insert(
        SourceRecord(
            id=source_id,
            title=f"Atom clustering source {source_key}",
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
                token_count=16,
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
    stance: str | None = None,
    relationship_concepts: tuple[str, str] | None = None,
) -> str:
    source_id, chunk_id = _seed_source(conn, source_key=source_key)
    claim = ClaimRepository(conn).insert_accepted(
        {
            "source_id": source_id,
            "chunk_id": chunk_id,
            "claim_text": claim_text,
            "quote_span": claim_text[:80],
            "subject": "AI-assisted creative work",
            "predicate": "affected",
            "object": "creative evidence",
            "scope": scope,
            "evidence_type": "empirical",
            "confidence": 0.72,
            "limitations": [],
            "domain": "creativity",
        },
        extractor_provider="fixture",
        extractor_model="purpose_gating_test",
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
    if stance and relationship_concepts:
        rel_ids = _concept_ids(conn, list(relationship_concepts))
        relationship = RelationshipRepository(conn).insert(
            subject_concept_id=rel_ids[relationship_concepts[0]],
            predicate="relates_to",
            object_concept_id=rel_ids[relationship_concepts[1]],
            scope=scope,
            confidence=0.65,
            evidence_strength=0.65,
            domain="creativity",
            status="active",
        )
        RelationshipEvidenceRepository(conn).insert(
            relationship_id=relationship["id"],
            claim_id=claim.id,
            stance=stance,
            relevance_score=0.8,
        )
    return claim.id


def _seed_cluster_report(conn, claim_ids: list[str]) -> None:
    evidence_packet = {
        "cluster_id": "cluster_atom_purpose_fixture",
        "top_supporting_claims": claim_ids[:1],
        "top_contradicting_claims": [],
        "top_qualifying_claims": [],
        "newest_claims": claim_ids,
    }
    report = {
        "report_type": "cluster_report",
        "cluster_id": "cluster_atom_purpose_fixture",
        "cluster_label": "Atom purpose fixture",
        "linked_claim_ids": claim_ids,
        "supporting_claims": claim_ids[:1],
        "contradicting_claims": [],
        "qualifying_claims": [],
        "strongest_relationships": [],
    }
    ClusterReportRepository(conn).insert(
        cluster_id="cluster_atom_purpose_fixture",
        cluster_label="Atom purpose fixture",
        included_concepts=["AI assistance", "semantic diversity", "originality"],
        evidence_packet=evidence_packet,
        report=report,
        prose_summary="Atom purpose fixture.",
    )


def test_compatible_claims_cluster_into_one_atom(tmp_path: Path) -> None:
    conn = ensure_database(tmp_path / "cluster_compatible.sqlite")
    try:
        claim_ids = [
            _seed_claim(
                conn,
                source_key=f"compatible_{idx}",
                claim_text=f"AI assistance reduced semantic diversity in writing task {idx}.",
                scope="short-form writing tasks",
                concepts=["AI assistance", "semantic diversity"],
                stance="supports",
                relationship_concepts=("AI assistance", "semantic diversity"),
            )
            for idx in range(3)
        ]
        promote_accepted_claims_for_domain(conn, domain="creativity", claim_ids=claim_ids)
        result = cluster_compatible_evidence_atoms(conn, domain="creativity", claim_ids=claim_ids)
        assert result["clustered_atom_count"] == 1
        assert result["duplicate_merged_atom_count"] == 3
        atom = result["clustered_atoms"][0]
        assert sorted(atom["source_claim_ids"]) == sorted(claim_ids)
        assert atom["source_count"] == 3
        assert atom["concept_overlap_count"] >= 2
    finally:
        conn.close()


def test_incompatible_scope_claims_stay_separate(tmp_path: Path) -> None:
    conn = ensure_database(tmp_path / "cluster_scope.sqlite")
    try:
        claim_ids = [
            _seed_claim(
                conn,
                source_key="scope_short",
                claim_text="AI assistance reduced semantic diversity in short writing.",
                scope="short-form writing tasks",
                concepts=["AI assistance", "semantic diversity"],
            ),
            _seed_claim(
                conn,
                source_key="scope_film",
                claim_text="AI assistance affected semantic diversity in film production.",
                scope="feature film production",
                concepts=["AI assistance", "semantic diversity"],
            ),
        ]
        result = cluster_compatible_evidence_atoms(conn, domain="creativity", claim_ids=claim_ids)
        assert result["clustered_atom_count"] == 0
        assert result["separate_claim_count"] == 2
    finally:
        conn.close()


def test_contradiction_and_qualification_counts_on_clustered_atoms(tmp_path: Path) -> None:
    conn = ensure_database(tmp_path / "cluster_stances.sqlite")
    try:
        claim_ids = [
            _seed_claim(
                conn,
                source_key="stance_support",
                claim_text="AI assistance reduced semantic diversity in writing.",
                scope="short-form writing tasks",
                concepts=["AI assistance", "semantic diversity"],
                stance="supports",
                relationship_concepts=("AI assistance", "semantic diversity"),
            ),
            _seed_claim(
                conn,
                source_key="stance_contradict",
                claim_text="AI assistance increased semantic diversity in writing.",
                scope="short-form writing tasks",
                concepts=["AI assistance", "semantic diversity"],
                stance="contradicts",
                relationship_concepts=("AI assistance", "semantic diversity"),
            ),
            _seed_claim(
                conn,
                source_key="stance_qualify",
                claim_text="AI assistance qualified semantic diversity effects in writing.",
                scope="short-form writing tasks",
                concepts=["AI assistance", "semantic diversity"],
                stance="qualifies",
                relationship_concepts=("AI assistance", "semantic diversity"),
            ),
        ]
        result = cluster_compatible_evidence_atoms(conn, domain="creativity", claim_ids=claim_ids)
        atom = result["clustered_atoms"][0]
        assert atom["support_count"] == 1
        assert atom["contradiction_count"] == 1
        assert atom["qualification_count"] == 1
        assert atom["evidence_maturity"] == "clustered"
    finally:
        conn.close()


def test_atom_maturity_promotes_with_claim_and_source_diversity(tmp_path: Path) -> None:
    conn = ensure_database(tmp_path / "cluster_maturity.sqlite")
    try:
        claim_ids = [
            _seed_claim(
                conn,
                source_key=f"maturity_{idx}",
                claim_text=f"AI assistance reduced semantic diversity replicate {idx}.",
                scope="short-form writing tasks",
                concepts=["AI assistance", "semantic diversity"],
                stance="supports",
                relationship_concepts=("AI assistance", "semantic diversity"),
            )
            for idx in range(3)
        ]
        result = cluster_compatible_evidence_atoms(conn, domain="creativity", claim_ids=claim_ids)
        assert result["clustered_atoms"][0]["evidence_maturity"] == "clustered"
        assert result["clustered_atoms"][0]["training_suitability"] == "needs_human_review"
    finally:
        conn.close()


def test_style_question_rejects_generic_ai_diversity_evidence(tmp_path: Path) -> None:
    conn = ensure_database(tmp_path / "style_gate.sqlite")
    try:
        claim_id = _seed_claim(
            conn,
            source_key="style_generic",
            claim_text="AI assistance reduced semantic diversity in writing.",
            scope="short-form writing tasks",
            concepts=["AI assistance", "semantic diversity"],
        )
        fit = evaluate_claim_purpose_fit(
            conn,
            claim_id,
            question="What visual style patterns recur in AI-assisted product design?",
            domain_pack="creativity",
        )
        assert fit["purpose_match_status"] == "mismatch"
        assert fit["decision"] == "rejected"
    finally:
        conn.close()


def test_agency_question_rejects_unrelated_diversity_evidence(tmp_path: Path) -> None:
    conn = ensure_database(tmp_path / "agency_gate.sqlite")
    try:
        claim_id = _seed_claim(
            conn,
            source_key="agency_generic",
            claim_text="AI assistance reduced semantic diversity in writing.",
            scope="short-form writing tasks",
            concepts=["AI assistance", "semantic diversity"],
        )
        fit = evaluate_claim_purpose_fit(
            conn,
            claim_id,
            question="How does AI co-creation affect human agency and control?",
            domain_pack="creativity",
        )
        assert fit["purpose_match_status"] == "mismatch"
        assert fit["decision"] == "rejected"
    finally:
        conn.close()


def test_purpose_matched_evidence_passes(tmp_path: Path) -> None:
    conn = ensure_database(tmp_path / "purpose_match.sqlite")
    try:
        claim_id = _seed_claim(
            conn,
            source_key="style_match",
            claim_text="AI assistance changed originality and novelty in visual design.",
            scope="visual design tasks",
            concepts=["AI assistance", "originality", "novelty"],
        )
        fit = evaluate_claim_purpose_fit(
            conn,
            claim_id,
            question="What originality and style patterns recur in AI-assisted design?",
            domain_pack="creativity",
        )
        assert fit["purpose_match_status"] == "match"
        assert fit["decision"] == "accepted"
    finally:
        conn.close()


def test_atlas_trace_includes_maturity_and_purpose_fields(tmp_path: Path) -> None:
    conn = ensure_database(tmp_path / "trace_purpose.sqlite")
    try:
        claim_ids = [
            _seed_claim(
                conn,
                source_key=f"trace_{idx}",
                claim_text=f"AI assistance changed originality in design task {idx}.",
                scope="visual design tasks",
                concepts=["AI assistance", "originality", "novelty"],
                stance="supports",
                relationship_concepts=("AI assistance", "originality"),
            )
            for idx in range(3)
        ]
        _seed_cluster_report(conn, claim_ids)
        cluster_compatible_evidence_atoms(conn, domain="creativity", claim_ids=claim_ids)
        traces = build_atlas_trace_export(
            conn,
            domain_pack="creativity",
            question="What originality and style patterns recur in AI-assisted design?",
        )
        trace = traces[0]
        assert trace["atom_cluster_maturity"] == "clustered"
        assert trace["purpose_match_status"] == "match"
        assert trace["why_clustered"]
        assert trace["evidence_decision"] == "accepted"
    finally:
        conn.close()


def test_public_safe_trace_preview_strips_private_fields_and_keeps_purpose_status(
    tmp_path: Path,
) -> None:
    conn = ensure_database(tmp_path / "preview_purpose.sqlite")
    try:
        claim_id = _seed_claim(
            conn,
            source_key="preview_match",
            claim_text="AI assistance changed originality in visual design.",
            scope="visual design tasks",
            concepts=["AI assistance", "originality"],
        )
        cluster_compatible_evidence_atoms(conn, domain="creativity", claim_ids=[claim_id])
        previews = build_atlas_trace_preview(
            build_atlas_trace_export(
                conn,
                domain_pack="creativity",
                question="What originality and style patterns recur in AI-assisted design?",
            )
        )
        assert previews[0]["purpose_match_status"] == "match"
        assert assert_no_private_fields({"atlas_trace_preview": previews}) == []
        payload = json.dumps(previews)
        assert "claim_id" not in payload
        assert "source_id" not in payload
        assert "quote_id" not in payload
    finally:
        conn.close()


def test_graph_readiness_metrics_include_atom_and_purpose_counts(tmp_path: Path) -> None:
    conn = ensure_database(tmp_path / "readiness_metrics.sqlite")
    try:
        claim_ids = [
            _seed_claim(
                conn,
                source_key=f"metrics_{idx}",
                claim_text=f"AI assistance changed originality in design task {idx}.",
                scope="visual design tasks",
                concepts=["AI assistance", "originality"],
                stance="supports",
                relationship_concepts=("AI assistance", "originality"),
            )
            for idx in range(3)
        ]
        _seed_cluster_report(conn, claim_ids)
        cluster_compatible_evidence_atoms(conn, domain="creativity", claim_ids=claim_ids)
        metrics = build_graph_connection_metrics(
            conn,
            domain_pack="creativity",
            question="What originality and style patterns recur in AI-assisted design?",
        )
        assert metrics["totals"]["multi_claim_atom_count"] == 1
        assert metrics["totals"]["source_diverse_atom_count"] == 1
        assert metrics["totals"]["clustered_atom_count"] == 1
        assert metrics["totals"]["frontend_ready_trace_count"] >= 3
    finally:
        conn.close()


def test_recommender_chooses_purpose_gating_or_atom_clustering() -> None:
    purpose_result = recommend_from_run_report(
        {
            "claims_accepted": 5,
            "claims_rejected": 0,
            "top_failure_modes": [],
            "acquisition_quality_summary": {},
            "graph_connection_metrics": {
                "totals": {
                    "purpose_mismatch_count": 4,
                    "weak_atom_count": 0,
                    "multi_claim_atom_count": 2,
                }
            },
        }
    )
    assert purpose_result["recommended_packet"] == PACKET_PURPOSE_GATING

    atom_result = recommend_from_run_report(
        {
            "claims_accepted": 6,
            "claims_rejected": 0,
            "top_failure_modes": [],
            "acquisition_quality_summary": {},
            "graph_connection_metrics": {
                "totals": {
                    "purpose_mismatch_count": 0,
                    "weak_atom_count": 5,
                    "multi_claim_atom_count": 0,
                }
            },
        }
    )
    assert atom_result["recommended_packet"] == PACKET_ATOM_CLUSTERING
