"""Connection layer + Atlas trace contract tests."""

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
from rge.modules.acquisition_quality import persist_source_acquisition_status
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.atlas_trace import (
    build_atlas_trace_export,
    build_atlas_trace_preview,
    build_graph_connection_metrics,
)
from rge.modules.evidence_atoms import promote_accepted_claims_for_domain
from rge.modules.failure_recommender import (
    PACKET_PDF_PARSER,
    PACKET_QUALITY_GATES,
    recommend_from_run_report,
)
from rge.modules.run_evaluator import build_run_report
from rge.modules.web_source_adapter import (
    ingest_webpage_artifact_to_db,
    normalize_webpage_artifact,
)


def _seed_connection_graph(db_path: Path, *, claim_count: int = 3) -> list[str]:
    conn = ensure_database(db_path)
    try:
        now = utc_now_iso()
        raw_text = (
            "AI-assisted brainstorming reduced semantic diversity in short-form writing tasks. "
            "Human curation qualified those effects when divergent directions were required."
        )
        checksum = sha256_hex(raw_text)
        source_id = f"src_{checksum[:16]}"
        SourceRepository(conn).insert(
            SourceRecord(
                id=source_id,
                title="Connection layer fixture",
                source_type="paper",
                domain="creativity",
                local_path="fixtures/sources/connection_layer.txt",
                raw_text_checksum=checksum,
                status="ingested",
                created_at=now,
                updated_at=now,
                authors_json=json.dumps(["Fixture Author"]),
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

        concept_repo = ConceptRepository(conn)
        concept_repo.ensure_domain_concepts("creativity")
        ai = concept_repo.get_by_label("creativity", "AI assistance")
        diversity = concept_repo.get_by_label("creativity", "semantic diversity")
        assert ai is not None
        assert diversity is not None

        claim_ids: list[str] = []
        claim_repo = ClaimRepository(conn)
        link_repo = ClaimConceptRepository(conn)
        for index in range(claim_count):
            claim = claim_repo.insert_accepted(
                {
                    "source_id": source_id,
                    "chunk_id": chunk_id,
                    "claim_text": (
                        f"AI-assisted brainstorming connection claim {index} reduced "
                        "semantic diversity in short-form writing tasks."
                    ),
                    "quote_span": "AI-assisted brainstorming reduced semantic diversity",
                    "subject": "AI-assisted brainstorming",
                    "predicate": "reduced",
                    "object": "semantic diversity",
                    "scope": "short-form writing tasks",
                    "evidence_type": "empirical",
                    "confidence": 0.7,
                    "limitations": [],
                    "domain": "creativity",
                },
                extractor_provider="fixture",
                extractor_model="connection_layer_test",
                llm_schema_version="0.1.0",
            )
            claim_ids.append(claim.id)
            link_repo.insert(
                claim_id=claim.id,
                concept_id=ai.id,
                role="method",
                confidence=0.8,
                domain_metadata={},
            )
            link_repo.insert(
                claim_id=claim.id,
                concept_id=diversity.id,
                role="object",
                confidence=0.8,
                domain_metadata={},
            )

        relationship = RelationshipRepository(conn).insert(
            subject_concept_id=ai.id,
            predicate="may_reduce",
            object_concept_id=diversity.id,
            scope="short-form writing tasks",
            confidence=0.7,
            evidence_strength=0.7,
            domain="creativity",
            status="active",
        )
        RelationshipEvidenceRepository(conn).insert(
            relationship_id=relationship["id"],
            claim_id=claim_ids[0],
            stance="supports",
            relevance_score=0.8,
        )
        promote_accepted_claims_for_domain(conn, domain="creativity", claim_ids=claim_ids)

        evidence_packet = {
            "cluster_id": "cluster_connection_fixture",
            "top_supporting_claims": [claim_ids[0]],
            "top_contradicting_claims": [],
            "top_qualifying_claims": [],
            "newest_claims": claim_ids,
        }
        report = {
            "report_type": "cluster_report",
            "cluster_id": "cluster_connection_fixture",
            "cluster_label": "Connection fixture",
            "linked_claim_ids": claim_ids,
            "supporting_claims": [claim_ids[0]],
            "contradicting_claims": [],
            "qualifying_claims": [],
            "strongest_relationships": [relationship["id"]],
        }
        ClusterReportRepository(conn).insert(
            cluster_id="cluster_connection_fixture",
            cluster_label="Connection fixture",
            included_concepts=["AI assistance", "semantic diversity"],
            evidence_packet=evidence_packet,
            report=report,
            prose_summary="Connection fixture.",
        )
        return claim_ids
    finally:
        conn.close()


def test_db_backed_run_report_includes_acquisition_status_counts(tmp_path: Path) -> None:
    db_path = tmp_path / "run_report_acquisition.sqlite"
    conn = ensure_database(db_path)
    try:
        persist_source_acquisition_status(
            conn,
            source_id="src_failed_parser",
            title="Failed parser source",
            domain="creativity",
            source_type="selective_fulltext",
            raw_text_checksum="checksum_failed_parser",
            status="failed",
            metadata={
                "source_status": "parse_failed",
                "acquisition_status": "full_text_parse_failed",
                "parser_backend": "pdf_unavailable",
                "source_type": "selective_fulltext",
                "quality_gate_status": "parse_failed",
                "extractable": False,
                "failure_reason": "fixture_document_missing",
                "resolver_source": "openalex",
                "is_oa": True,
                "pdf_url": "https://example.test/paper.pdf",
            },
        )
        report = build_run_report(
            conn,
            run_id="run_acq_counts",
            topic="Connection layer acquisition counts",
            domain_pack="creativity",
        )
        summary = report["acquisition_quality_summary"]
        assert summary["acquisition_status_counts"]["full_text_parse_failed"] == 1
        assert summary["source_status_counts"]["parse_failed"] == 1
        assert summary["parser_backend_counts"]["pdf_unavailable"] == 1
        assert summary["failure_reason_counts"]["fixture_document_missing"] == 1
        assert summary["availability_counts"]["pdf_available"] == 1
    finally:
        conn.close()


def test_dirty_failed_web_source_persists_durable_acquisition_row(tmp_path: Path) -> None:
    conn = ensure_database(tmp_path / "dirty_web.sqlite")
    try:
        artifact = normalize_webpage_artifact(
            html="<html><title>Dirty</title><body>Too short.</body></html>",
            url="https://example.test/dirty",
            title="Dirty source",
            source_id="src_dirty_web",
        )
        result = ingest_webpage_artifact_to_db(conn, artifact, domain="creativity")
        row = conn.execute(
            "SELECT status, source_type, domain_metadata_json FROM sources WHERE id = ?",
            ("src_dirty_web",),
        ).fetchone()
        assert result["status"] == "blocked_dirty_text"
        assert row is not None
        metadata = json.loads(row["domain_metadata_json"])
        assert row["status"] == "failed"
        assert row["source_type"] == "webpage"
        assert metadata["acquisition_status"] == "dirty_text"
        assert metadata["extractable"] is False
    finally:
        conn.close()


def test_recommender_prefers_acquisition_blocker_over_missing_quote_span() -> None:
    result = recommend_from_run_report(
        {
            "claims_accepted": 0,
            "claims_rejected": 8,
            "top_failure_modes": [{"reason": "missing_quote_span", "count": 8}],
            "acquisition_quality_summary": {
                "source_status_counts": {"parse_failed": 1},
                "acquisition_status_counts": {"full_text_parse_failed": 1},
                "parser_backend_counts": {"pdf_unavailable": 1},
            },
        }
    )
    assert result["recommended_packet"] == PACKET_PDF_PARSER
    assert result["signal_kind"] == "acquisition_status"


def test_missing_quote_span_maps_to_quoteability_packet() -> None:
    result = recommend_from_run_report(
        {
            "claims_accepted": 0,
            "claims_rejected": 3,
            "top_failure_modes": [{"reason": "missing_quote_span", "count": 3}],
            "acquisition_quality_summary": {"sources_with_metadata": 1},
        }
    )
    assert result["recommended_packet"] == PACKET_QUALITY_GATES
    assert result["dominant_signal"] in {"missing_quote_span", "zero_quoteable_spans"}


def test_atlas_trace_export_connects_source_quote_claim_atom_concept_cluster(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "trace.sqlite"
    claim_ids = _seed_connection_graph(db_path, claim_count=1)
    conn = ensure_database(db_path)
    try:
        traces = build_atlas_trace_export(conn, domain_pack="creativity")
        trace = next(item for item in traces if item["claim_id"] == claim_ids[0])
        assert trace["question_id"]
        assert trace["cluster_id"] == "cluster_connection_fixture"
        assert trace["atom_id"].startswith("atom_")
        assert trace["claim_id"] == claim_ids[0]
        assert trace["quote_id"].startswith("qt_")
        assert trace["source_id"].startswith("src_")
        assert len(trace["concept_ids"]) == 2
        assert len(trace["relationship_ids"]) == 1
        assert trace["connection_type"] == "source_quote_claim_atom_concept_cluster"
    finally:
        conn.close()


def test_public_safe_trace_preview_strips_private_fields(tmp_path: Path) -> None:
    db_path = tmp_path / "trace_preview.sqlite"
    _seed_connection_graph(db_path, claim_count=1)
    conn = ensure_database(db_path)
    try:
        preview = build_atlas_trace_preview(
            build_atlas_trace_export(conn, domain_pack="creativity")
        )
        assert preview
        assert assert_no_private_fields({"atlas_trace_preview": preview}) == []
        joined = json.dumps(preview)
        assert "claim_id" not in joined
        assert "source_id" not in joined
        assert "quote_id" not in joined
    finally:
        conn.close()


def test_graph_health_metrics_expose_low_relationship_density(tmp_path: Path) -> None:
    db_path = tmp_path / "graph_metrics.sqlite"
    _seed_connection_graph(db_path, claim_count=3)
    conn = ensure_database(db_path)
    try:
        metrics = build_graph_connection_metrics(conn, domain_pack="creativity")
        cluster = metrics["clusters"][0]
        assert cluster["claims_per_cluster"] == 3
        assert cluster["atoms_per_cluster"] == 3
        assert cluster["relationships_per_cluster"] == 1
        assert cluster["sources_per_cluster"] == 1
        assert cluster["orphan_claims"] == 2
        assert cluster["orphan_atoms"] == 2
        assert cluster["low_relationship_density"] is True
    finally:
        conn.close()
