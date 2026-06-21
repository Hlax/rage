"""Unit tests for graph maturity / evidence atom upgrade."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

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
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.graph_maturity_evidence_atom_upgrade import (
    GraphMaturityGateError,
    assert_live_graph_maturity_evidence_atom_upgrade_env,
    build_atlas_safe_graph_maturity_artifact,
    classify_graph_maturity_verdict,
    explain_cluster_maturity,
    seed_deterministic_concepts_for_claims,
    snapshot_graph_maturity_metrics,
    upgrade_graph_evidence_atom_maturity,
)


def _insert_accepted_claim(
    conn,
    *,
    claim_id: str,
    source_id: str,
    claim_text: str,
    scope: str,
    quote_text: str,
) -> None:
    now = utc_now_iso()
    chunk_text = f"{claim_text} Source excerpt with {quote_text}."
    checksum = sha256_hex(chunk_text)
    SourceRepository(conn).insert(
        SourceRecord(
            id=source_id,
            title=f"Fixture {source_id}",
            source_type="paper",
            domain="creativity",
            local_path=f"fixtures/sources/{source_id}.txt",
            raw_text_checksum=checksum,
            status="ingested",
            created_at=now,
            updated_at=now,
            authors_json="[]",
        )
    )
    chunk_id = make_chunk_id(source_id, 0, checksum)
    ChunkRepository(conn).insert_many(
        [
            ChunkRecord(
                id=chunk_id,
                source_id=source_id,
                chunk_index=0,
                chunk_text=chunk_text,
                text_checksum=checksum,
                created_at=now,
                token_count=20,
            )
        ]
    )
    claim = ClaimRepository(conn).insert_accepted(
        {
            "id": claim_id,
            "source_id": source_id,
            "chunk_id": chunk_id,
            "claim_text": claim_text,
            "quote_span": quote_text,
            "subject": "AI assistance",
            "predicate": "reports",
            "object": "evidence",
            "scope": scope,
            "evidence_type": "empirical",
            "confidence": 0.6,
            "limitations": ["Fixture limitation."],
            "domain": "creativity",
            "domain_metadata": {},
        },
        extractor_provider="fixture",
        extractor_model="graph_maturity_test",
        llm_schema_version="0.1.0",
    )
    return str(claim.id)


def test_missing_graph_maturity_gate_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_MULTI_QUESTION_ABSTRACT_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_EXPANSION_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("RGE_ALLOW_LIVE_GRAPH_MATURITY_EVIDENCE_ATOM_UPGRADE", raising=False)
    with pytest.raises(
        GraphMaturityGateError,
        match="RGE_ALLOW_LIVE_GRAPH_MATURITY_EVIDENCE_ATOM_UPGRADE",
    ):
        assert_live_graph_maturity_evidence_atom_upgrade_env()


def test_seed_deterministic_concepts_links_keywords(tmp_path: Path) -> None:
    conn = ensure_database(tmp_path / "seed.sqlite")
    ConceptRepository(conn).ensure_domain_concepts("creativity")
    claim_id = _insert_accepted_claim(
        conn,
        claim_id="claim_seed_1",
        source_id="source_a",
        claim_text="AI assistance may reduce semantic diversity in brainstorming.",
        scope="brainstorming tasks",
        quote_text="semantic diversity",
    )
    result = seed_deterministic_concepts_for_claims(
        conn,
        domain_pack="creativity",
        claim_ids=[claim_id],
        question="Does AI assistance reduce semantic diversity?",
    )
    assert result["seeded_link_count"] >= 1
    links = ClaimConceptRepository(conn).list_for_source("source_a")
    assert links
    labels = {link["concept_label"] for link in links}
    assert "semantic diversity" in labels or "AI assistance" in labels


def test_upgrade_graph_maturity_clusters_compatible_claims(tmp_path: Path) -> None:
    conn = ensure_database(tmp_path / "upgrade.sqlite")
    ConceptRepository(conn).ensure_domain_concepts("creativity")
    for index, source_id in enumerate(("source_a", "source_b"), start=1):
        _insert_accepted_claim(
            conn,
            claim_id=f"claim_cluster_{index}",
            source_id=source_id,
            claim_text=(
                "AI assistance may reduce semantic diversity in short-form writing tasks."
            ),
            scope="short-form writing tasks",
            quote_text="semantic diversity",
        )
    seed_deterministic_concepts_for_claims(
        conn,
        domain_pack="creativity",
        question="Does AI assistance reduce semantic diversity?",
    )
    upgrade = upgrade_graph_evidence_atom_maturity(
        conn,
        domain_pack="creativity",
        question="Does AI assistance reduce semantic diversity?",
    )
    after = upgrade["after"]
    assert int(after.get("multi_claim_atom_count") or 0) >= 1
    assert int(upgrade["cluster_result"]["clustered_atom_count"] or 0) >= 1
    assert upgrade["cluster_explanations"]
    verdict, _ = classify_graph_maturity_verdict(
        upgrade,
        question_ingest_rows=[{"accepted_claim_count": 2}],
    )
    assert verdict in {"GO", "PARTIAL"}


def test_explain_cluster_maturity_and_public_artifact() -> None:
    explanation = explain_cluster_maturity(
        {
            "cluster_id": "cluster_preview_001",
            "relationship_density": 0.25,
            "relationships_per_cluster": 1,
            "orphan_claim_count": 1,
            "low_relationship_density": True,
            "contradiction_edges": 0,
            "qualification_edges": 0,
            "atoms_per_cluster": 1,
        }
    )
    assert explanation["maturity_label"] == "weak"
    assert explanation["reasons"]

    artifact = build_atlas_safe_graph_maturity_artifact(
        upgrade={
            "before": {"single_claim_atom_count": 3, "clustered_atom_count": 0},
            "after": {"single_claim_atom_count": 1, "clustered_atom_count": 1},
            "delta": {"single_claim_atom_delta": -2, "clustered_atom_delta": 1},
            "concept_seed": {"seeded_link_count": 4},
            "cluster_result": {"clustered_atom_count": 1},
            "cluster_explanations": [explanation],
        },
        question_ingest_rows=[
            {"question_id": "mq_test", "gate_mode": "open", "accepted_claim_count": 2}
        ],
        verdict="PARTIAL",
        rationale="Thin but improved.",
    )
    assert artifact["schema_version"].startswith("atlas_graph_maturity")
    assert assert_no_private_fields({"artifact": artifact}) == []


def test_sync_graph_maturity_artifact_to_public_site(tmp_path: Path) -> None:
    from rge.modules.graph_maturity_evidence_atom_upgrade import (
        sync_graph_maturity_artifact_to_public_site,
    )

    artifact = build_atlas_safe_graph_maturity_artifact(
        upgrade={
            "before": {"single_claim_atom_count": 2, "clustered_atom_count": 0},
            "after": {"single_claim_atom_count": 1, "clustered_atom_count": 1},
            "delta": {"single_claim_atom_delta": -1, "clustered_atom_delta": 1},
            "concept_seed": {"seeded_link_count": 2},
            "cluster_result": {"clustered_atom_count": 1},
            "cluster_explanations": [],
        },
        question_ingest_rows=[
            {
                "question_id": "mq_test",
                "gate_mode": "open",
                "live_source_count": 2,
                "accepted_claim_count": 2,
                "relationship_count": 1,
            }
        ],
        verdict="PARTIAL",
        rationale="Clustering improved with thin multi-claim consolidation.",
    )
    public_path = tmp_path / "atlas_graph_maturity_evidence_atom_upgrade_latest.json"
    result = sync_graph_maturity_artifact_to_public_site(
        artifact,
        public_path=public_path,
    )
    assert result["status"] == "completed"
    loaded = json.loads(public_path.read_text(encoding="utf-8"))
    assert loaded["graph_maturity_verdict"] == "PARTIAL"


def test_snapshot_includes_single_claim_atom_count(tmp_path: Path) -> None:
    conn = ensure_database(tmp_path / "snapshot.sqlite")
    ConceptRepository(conn).ensure_domain_concepts("creativity")
    claim_id = _insert_accepted_claim(
        conn,
        claim_id="claim_single",
        source_id="source_single",
        claim_text="Generative AI tools assist creative writing workflows.",
        scope="creative writing workflows",
        quote_text="creative writing workflows",
    )
    from rge.modules.evidence_atoms import promote_claim_to_evidence_atom

    promote_claim_to_evidence_atom(conn, claim_id)
    metrics = snapshot_graph_maturity_metrics(conn, domain_pack="creativity")
    assert metrics["single_claim_atom_count"] == 1
