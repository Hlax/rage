"""Unit tests for multi-claim atom clustering packet."""

from __future__ import annotations

import os

import pytest

from rge.db.connection import ensure_database
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.multi_claim_atom_clustering import (
    MultiClaimAtomClusteringGateError,
    assert_multi_claim_atom_clustering_env,
    build_atlas_safe_clustering_artifact,
    evaluate_synthesis_readiness,
    run_multi_claim_atom_clustering_proof,
    run_multi_claim_atom_clustering_with_fresh_db,
)


def test_clustering_env_gate_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RGE_ALLOW_MULTI_CLAIM_ATOM_CLUSTERING", raising=False)
    with pytest.raises(MultiClaimAtomClusteringGateError):
        assert_multi_claim_atom_clustering_env()


def test_multi_claim_atoms_from_fixture_proof(tmp_path) -> None:
    conn = ensure_database(tmp_path / "cluster.sqlite")
    try:
        proof = run_multi_claim_atom_clustering_proof(conn)
        after = proof["after"]
        assert int(after["multi_claim_atom_count"]) >= 1
        assert int(after["source_diverse_atom_count"]) >= 1
        readiness = evaluate_synthesis_readiness(after)
        assert readiness["openai_synthesis_blocked"] is (
            not readiness["synthesis_readiness_passed"]
        )
    finally:
        conn.close()


def test_clustering_artifact_is_public_safe(tmp_path) -> None:
    conn = ensure_database(tmp_path / "artifact.sqlite")
    try:
        proof = run_multi_claim_atom_clustering_proof(conn)
        readiness = evaluate_synthesis_readiness(proof["after"])
        artifact = build_atlas_safe_clustering_artifact(
            proof=proof,
            readiness=readiness,
            verdict="GO",
            rationale="fixture proof",
        )
        assert assert_no_private_fields({"artifact": artifact}) == []
        assert artifact["graph_summary"]["multi_claim_atom_count"] >= 1
    finally:
        conn.close()


def test_run_clustering_with_fresh_db(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_MULTI_CLAIM_ATOM_CLUSTERING", "1")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    result = run_multi_claim_atom_clustering_with_fresh_db(
        output_dir=tmp_path / "export",
        root=tmp_path,
    )
    assert result["status"] == "completed"
    assert result["openai_synthesis_blocked"] in {True, False}
