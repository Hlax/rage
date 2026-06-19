"""Asset export candidate derivation tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

from rge.db.connection import ensure_database
from rge.modules.asset_export_candidates import derive_asset_candidate, export_asset_candidates
from rge.modules.evidence_atoms import promote_claim_to_evidence_atom
from tests.unit.test_evidence_atoms import _seed_claim_graph


def test_derive_asset_candidate_stays_conservative_for_seed_atoms() -> None:
    candidate = derive_asset_candidate(
        {
            "atom_id": "atom_seed",
            "canonical_text": "AI-assisted brainstorming reduced semantic diversity in short-form writing tasks.",
            "scope": "short-form writing tasks",
            "evidence_type": "empirical",
            "evidence_maturity": "seed",
            "training_suitability": "not_ready",
            "asset_tags": ["reasoning_training_candidate"],
            "concepts": ["semantic diversity"],
        }
    )

    assert candidate["export_category"] == "do_not_export"
    assert candidate["human_review_required"] is False
    assert candidate["review_status"] == "not_applicable"
    assert "quote" not in candidate


def test_promising_maturity_does_not_promote_qa_eval_candidate() -> None:
    candidate = derive_asset_candidate(
        {
            "atom_id": "atom_promising",
            "canonical_text": "AI-assisted brainstorming reduced semantic diversity in short-form writing tasks.",
            "scope": "short-form writing tasks",
            "evidence_type": "empirical",
            "evidence_maturity": "promising",
            "training_suitability": "not_ready",
            "asset_tags": ["reasoning_training_candidate"],
            "concepts": ["semantic diversity"],
        }
    )

    assert candidate["export_category"] == "do_not_export"
    assert candidate["human_review_required"] is False


def test_clustered_maturity_promotes_qa_eval_with_human_review_gate() -> None:
    candidate = derive_asset_candidate(
        {
            "atom_id": "atom_clustered",
            "canonical_text": "AI-assisted brainstorming reduced semantic diversity in short-form writing tasks.",
            "scope": "short-form writing tasks",
            "evidence_type": "empirical",
            "evidence_maturity": "clustered",
            "training_suitability": "needs_human_review",
            "asset_tags": ["reasoning_training_candidate"],
            "concepts": ["semantic diversity"],
        }
    )

    assert candidate["export_category"] == "qa_eval_candidate"
    assert candidate["human_review_required"] is True
    assert candidate["review_status"] == "pending"


def test_clustered_rubric_tag_exports_rubric_candidate() -> None:
    candidate = derive_asset_candidate(
        {
            "atom_id": "atom_rubric",
            "canonical_text": "Semantic diversity trade-offs may be task-specific rather than universal.",
            "scope": "fixture-derived cluster padding",
            "evidence_type": "synthetic_fixture",
            "evidence_maturity": "clustered",
            "training_suitability": "needs_human_review",
            "asset_tags": ["rubric_candidate"],
            "concepts": ["semantic diversity"],
        }
    )

    assert candidate["export_category"] == "rubric_candidate"
    assert candidate["human_review_required"] is True


def test_export_asset_candidates_groups_by_category(tmp_path: Path) -> None:
    db_path = tmp_path / "asset_export.sqlite"
    claim_id = _seed_claim_graph(db_path)
    conn = ensure_database(db_path)
    try:
        promote_claim_to_evidence_atom(conn, claim_id, evidence_maturity="clustered")
        bundle = export_asset_candidates(conn, domain="creativity", limit=10)
        assert bundle["atom_count"] == 1
        assert bundle["qa_eval_candidate_count"] == 1
        assert bundle["human_review_required_count"] == 1
        assert bundle["candidates"][0]["atom_id"].startswith("atom_")
        assert bundle["candidates"][0]["export_category"] == "qa_eval_candidate"
        assert bundle["qa_eval_candidates"][0]["review_status"] == "pending"
        assert "qa_eval_candidate" in bundle["candidates_by_category"]
    finally:
        conn.close()


def test_export_asset_candidates_from_promising_atom_is_not_exportable(tmp_path: Path) -> None:
    db_path = tmp_path / "asset_export_promising.sqlite"
    claim_id = _seed_claim_graph(db_path)
    conn = ensure_database(db_path)
    try:
        promote_claim_to_evidence_atom(conn, claim_id, evidence_maturity="promising")
        bundle = export_asset_candidates(conn, domain="creativity", limit=10)
        assert bundle["candidate_count"] == 0
        assert bundle["qa_eval_candidate_count"] == 0
    finally:
        conn.close()
