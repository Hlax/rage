"""Multi-claim evidence atom clustering for synthesis readiness (mock-safe).

Fixture/network-free proof that cross-source claims cluster into multi-claim,
source-diverse atoms with an explicit synthesis-ready threshold. Paid/OpenAI
synthesis remains blocked until readiness passes.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

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
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.atlas_trace import build_graph_connection_metrics
from rge.modules.evidence_atoms import cluster_compatible_evidence_atoms
from rge.modules.principal_audit_gate import repo_root
from rge.modules.relationship_density_proof import ensure_purpose_gated_relationship_density_proof

PACKET_ID = "multi-claim-atom-clustering"
CLUSTERING_SCHEMA_VERSION = "atlas_multi_claim_atom_clustering_v0.1.0"
CLUSTERING_ARTIFACT_NAME = "atlas_multi_claim_atom_clustering_latest.json"
CLUSTERING_RUN_ID = "run_multi_claim_atom_clustering"

DEFAULT_QUESTION = (
    "What originality and style patterns recur in AI-assisted design?"
)

NEXT_RECOMMENDED_PACKET = {
    "id": "openai-synthesis-adapter-spec",
    "title": "OpenAI Synthesis Adapter Spec (ticket-059; evidence-packet input only)",
}

# Honest synthesis readiness gates (Atlas graph summary).
SYNTHESIS_READY_THRESHOLDS = {
    "multi_claim_atom_count_min": 1,
    "source_diverse_atom_count_min": 1,
    "synthesis_ready_cluster_count_min": 1,
    "weak_atom_share_max": 0.5,
}


class MultiClaimAtomClusteringGateError(RuntimeError):
    """Raised when operator env gates for clustering proof are missing."""


def assert_multi_claim_atom_clustering_env() -> dict[str, str]:
    allow = os.environ.get("RGE_ALLOW_MULTI_CLAIM_ATOM_CLUSTERING", "0").strip().casefold()
    if allow not in {"1", "true", "yes"}:
        raise MultiClaimAtomClusteringGateError(
            "Multi-claim atom clustering requires "
            "RGE_ALLOW_MULTI_CLAIM_ATOM_CLUSTERING=1."
        )
    os.environ.setdefault("RGE_LLM_MODE", "mock")
    return {
        "RGE_ALLOW_MULTI_CLAIM_ATOM_CLUSTERING": allow,
        "RGE_LLM_MODE": os.environ.get("RGE_LLM_MODE", "mock"),
    }


def required_env_setup_commands() -> list[str]:
    return [
        '$env:RGE_ALLOW_MULTI_CLAIM_ATOM_CLUSTERING = "1"',
        '$env:RGE_LLM_MODE = "mock"',
        "python scripts/run_multi_claim_atom_clustering.py --sync-public",
    ]


def _seed_source(conn: sqlite3.Connection, *, source_key: str) -> tuple[str, str]:
    now = utc_now_iso()
    raw_text = (
        f"{source_key}: AI assistance, originality, and semantic diversity "
        "appear in quote-backed fixture evidence for clustering proof."
    )
    checksum = sha256_hex(raw_text)
    source_id = f"src_{checksum[:16]}"
    SourceRepository(conn).insert(
        SourceRecord(
            id=source_id,
            title=f"Clustering proof source {source_key}",
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
                token_count=20,
            )
        ]
    )
    return source_id, chunk_id


def _seed_claim(
    conn: sqlite3.Connection,
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
            "quote_span": claim_text[:80],
            "subject": "AI assistance",
            "predicate": "may_affect",
            "object": concepts[-1],
            "scope": scope,
            "evidence_type": "empirical",
            "confidence": 0.7,
            "limitations": [],
            "domain": "creativity",
        },
        extractor_provider="fixture",
        extractor_model="multi_claim_clustering",
        llm_schema_version="0.1.0",
    )
    ConceptRepository(conn).ensure_domain_concepts("creativity")
    link_repo = ClaimConceptRepository(conn)
    for index, label in enumerate(concepts):
        concept = ConceptRepository(conn).get_by_label("creativity", label)
        assert concept is not None
        link_repo.insert(
            claim_id=claim.id,
            concept_id=concept.id,
            role="object" if index else "method",
            confidence=0.8,
            domain_metadata={},
        )
    return claim.id


def _seed_cluster_report(conn: sqlite3.Connection, claim_ids: list[str]) -> None:
    evidence_packet = {
        "cluster_id": "cluster_multi_claim_fixture_001",
        "top_supporting_claims": claim_ids[:2],
        "top_contradicting_claims": [],
        "top_qualifying_claims": claim_ids[2:3],
        "newest_claims": claim_ids,
    }
    report = {
        "report_type": "cluster_report",
        "cluster_id": "cluster_multi_claim_fixture_001",
        "cluster_label": "Multi-claim fixture cluster",
        "linked_claim_ids": claim_ids,
        "supporting_claims": claim_ids[:2],
        "contradicting_claims": [],
        "qualifying_claims": claim_ids[2:3],
        "strongest_relationships": [],
    }
    ClusterReportRepository(conn).insert(
        cluster_id="cluster_multi_claim_fixture_001",
        cluster_label="Multi-claim fixture cluster",
        included_concepts=["AI assistance", "originality"],
        evidence_packet=evidence_packet,
        report=report,
        prose_summary="Fixture multi-claim clustering proof cluster.",
    )


def run_multi_claim_atom_clustering_proof(
    conn: sqlite3.Connection,
    *,
    domain: str = "creativity",
    question: str = DEFAULT_QUESTION,
) -> dict[str, Any]:
    """Seed cross-source claims, cluster atoms, and return before/after metrics."""
    before = build_graph_connection_metrics(
        conn,
        domain_pack=domain,
        question=question,
    )["totals"]

    claim_ids = [
        _seed_claim(
            conn,
            source_key=f"cluster_src_{idx}",
            claim_text=(
                f"AI assistance changed originality in visual design task {idx} "
                "with measurable semantic diversity effects."
            ),
            scope="visual design tasks",
            concepts=["AI assistance", "originality"],
        )
        for idx in range(3)
    ]
    _seed_cluster_report(conn, claim_ids)
    ensure_purpose_gated_relationship_density_proof(
        conn,
        domain=domain,
        question=question,
        claim_ids=claim_ids,
    )
    cluster_result = cluster_compatible_evidence_atoms(
        conn,
        domain=domain,
        claim_ids=claim_ids,
    )
    after = build_graph_connection_metrics(
        conn,
        domain_pack=domain,
        question=question,
    )["totals"]

    return {
        "before": before,
        "after": after,
        "cluster_result": cluster_result,
        "claim_ids": claim_ids,
    }


def evaluate_synthesis_readiness(totals: dict[str, Any]) -> dict[str, Any]:
    """Evaluate graph totals against synthesis-ready thresholds."""
    multi_claim = int(totals.get("multi_claim_atom_count") or 0)
    source_diverse = int(totals.get("source_diverse_atom_count") or 0)
    synthesis_ready = int(totals.get("synthesis_ready_cluster_count") or 0)
    weak = int(totals.get("weak_atom_count") or 0)
    atom_total = max(
        1,
        multi_claim
        + int(totals.get("single_claim_atom_count") or 0)
        + int(totals.get("clustered_atom_count") or 0),
    )
    weak_share = weak / atom_total
    thresholds = SYNTHESIS_READY_THRESHOLDS
    checks = {
        "multi_claim_atoms": multi_claim >= thresholds["multi_claim_atom_count_min"],
        "source_diverse_atoms": source_diverse
        >= thresholds["source_diverse_atom_count_min"],
        "synthesis_ready_clusters": synthesis_ready
        >= thresholds["synthesis_ready_cluster_count_min"],
        "weak_atom_share": weak_share <= thresholds["weak_atom_share_max"],
    }
    passed = all(checks.values())
    return {
        "thresholds": thresholds,
        "checks": checks,
        "synthesis_readiness_passed": passed,
        "openai_synthesis_blocked": not passed,
        "openai_block_reason": (
            None
            if passed
            else "Synthesis readiness thresholds not met; paid synthesis remains blocked."
        ),
    }


def classify_clustering_verdict(
    proof: dict[str, Any],
    readiness: dict[str, Any],
) -> tuple[str, str]:
    after = proof.get("after") or {}
    multi_claim = int(after.get("multi_claim_atom_count") or 0)
    source_diverse = int(after.get("source_diverse_atom_count") or 0)
    if readiness.get("synthesis_readiness_passed"):
        return (
            "GO",
            f"Multi-claim ({multi_claim}) and source-diverse ({source_diverse}) "
            "atoms meet synthesis-ready thresholds on fixture proof.",
        )
    if multi_claim >= 1 and source_diverse >= 1:
        return (
            "PARTIAL",
            "Multi-claim and source-diverse atoms exist but synthesis-ready "
            "cluster threshold is not fully met.",
        )
    return "NO-GO", "Clustering proof did not produce multi-claim atoms."


def build_atlas_safe_clustering_artifact(
    *,
    proof: dict[str, Any],
    readiness: dict[str, Any],
    verdict: str,
    rationale: str,
    question: str = DEFAULT_QUESTION,
) -> dict[str, Any]:
    after = proof.get("after") or {}
    artifact: dict[str, Any] = {
        "schema_version": CLUSTERING_SCHEMA_VERSION,
        "status": "completed",
        "packet_id": PACKET_ID,
        "run_id": CLUSTERING_RUN_ID,
        "research_question": question,
        "clustering_verdict": verdict,
        "clustering_rationale": rationale,
        "mock_only": True,
        "no_paid_apis": True,
        "graph_summary": {
            "multi_claim_atom_count": int(after.get("multi_claim_atom_count") or 0),
            "source_diverse_atom_count": int(after.get("source_diverse_atom_count") or 0),
            "clustered_atom_count": int(after.get("clustered_atom_count") or 0),
            "synthesis_ready_cluster_count": int(
                after.get("synthesis_ready_cluster_count") or 0
            ),
            "weak_atom_count": int(after.get("weak_atom_count") or 0),
            "frontend_ready_trace_count": int(
                after.get("frontend_ready_trace_count") or 0
            ),
        },
        "before_after_delta": {
            "multi_claim_atom_delta": int(after.get("multi_claim_atom_count") or 0)
            - int((proof.get("before") or {}).get("multi_claim_atom_count") or 0),
            "clustered_atom_delta": int(after.get("clustered_atom_count") or 0)
            - int((proof.get("before") or {}).get("clustered_atom_count") or 0),
        },
        "synthesis_readiness": readiness,
        "next_recommended_packet": NEXT_RECOMMENDED_PACKET,
    }
    violations = assert_no_private_fields({"artifact": artifact})
    if violations:
        raise ValueError(
            "Clustering artifact blocked by private-field policy: "
            + "; ".join(violations[:5])
        )
    return artifact


def sync_clustering_artifact_to_public_site(
    artifact: dict[str, Any],
    *,
    public_path: Path,
) -> Path:
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return public_path


def run_multi_claim_atom_clustering_with_fresh_db(
    *,
    output_dir: Path | None = None,
    question: str = DEFAULT_QUESTION,
    sync_public: bool = False,
    root: Path | None = None,
) -> dict[str, Any]:
    """Operator entry: fresh DB clustering proof with optional public sync."""
    project_root = root or repo_root()
    gates = assert_multi_claim_atom_clustering_env()
    export_dir = output_dir or (project_root / "data/exports/multi_claim_atom_clustering")
    if not export_dir.is_absolute():
        export_dir = project_root / export_dir
    export_dir.mkdir(parents=True, exist_ok=True)

    db_path = export_dir / "clustering_proof.sqlite"
    conn = ensure_database(db_path)
    try:
        proof = run_multi_claim_atom_clustering_proof(conn, question=question)
        readiness = evaluate_synthesis_readiness(proof["after"])
        verdict, rationale = classify_clustering_verdict(proof, readiness)
        artifact = build_atlas_safe_clustering_artifact(
            proof=proof,
            readiness=readiness,
            verdict=verdict,
            rationale=rationale,
            question=question,
        )
    finally:
        conn.close()

    artifact_path = export_dir / CLUSTERING_ARTIFACT_NAME
    artifact_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    public_path: Path | None = None
    if sync_public:
        public_path = (
            project_root
            / "apps/public-site/public/data"
            / CLUSTERING_ARTIFACT_NAME
        )
        sync_clustering_artifact_to_public_site(artifact, public_path=public_path)

    return {
        "status": "completed",
        "packet_id": PACKET_ID,
        "clustering_verdict": verdict,
        "clustering_rationale": rationale,
        "gates": gates,
        "artifact_path": str(artifact_path),
        "public_artifact_path": str(public_path) if public_path else None,
        "atlas_safe_artifact": artifact,
        "synthesis_readiness_passed": readiness["synthesis_readiness_passed"],
        "openai_synthesis_blocked": readiness["openai_synthesis_blocked"],
    }
