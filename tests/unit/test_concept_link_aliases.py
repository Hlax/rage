"""Unit tests for concept-link alias resolution (ticket-087)."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pytest

from rge.modules.concept_linker import (
    allowed_concept_labels_for_pack,
    link_rejection_diagnostic,
    normalize_proposed_concept_links,
    resolve_concept_label,
    validate_concept_links,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "alias_linking.sqlite"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def test_allowed_concept_labels_include_alias_phrases() -> None:
    labels = allowed_concept_labels_for_pack("creativity")
    assert "AI assistance" in labels
    assert "AI-assisted brainstorming" in labels
    assert "idea diversity" in labels


def test_resolve_concept_label_maps_pack_alias_to_canonical() -> None:
    assert resolve_concept_label("creativity", "AI-assisted brainstorming") == "AI assistance"
    assert resolve_concept_label("creativity", "idea diversity") == "semantic diversity"


def test_normalize_proposed_concept_links_rewrites_aliases() -> None:
    links = [
        {
            "claim_id": "claim_1",
            "concept_label": "AI-assisted brainstorming",
            "confidence": 0.8,
        },
        {
            "claim_id": "claim_1",
            "concept_label": "ideation",
            "confidence": 0.75,
        },
    ]
    normalized = normalize_proposed_concept_links(links, "creativity")
    assert normalized[0]["concept_label"] == "AI assistance"
    assert normalized[1]["concept_label"] == "ideation"


def test_validate_concept_links_accepts_normalized_alias_batch() -> None:
    links = normalize_proposed_concept_links(
        [
            {
                "claim_id": "claim_1",
                "concept_label": "AI-assisted brainstorming",
                "confidence": 0.8,
            },
            {
                "claim_id": "claim_1",
                "concept_label": "ideation",
                "confidence": 0.75,
            },
        ],
        "creativity",
    )
    validated = validate_concept_links(links)
    assert len(validated["accepted"]) == 2
    assert validated["accepted"][0]["concept_label"] == "AI assistance"


def test_link_rejection_diagnostic_accepts_alias_in_allowed_pack_labels() -> None:
    diagnostic = link_rejection_diagnostic(
        {
            "claim_id": "claim_1",
            "concept_label": "AI-assisted brainstorming",
            "confidence": 0.8,
        },
        domain_pack="creativity",
    )
    assert "not in the domain ontology" not in diagnostic


def test_alias_links_persist_against_canonical_concepts(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ClaimConceptRepository, ConceptRepository
    from rge.modules.concept_linker import propose_concept_links

    assert (
        main(
            [
                "ingest",
                str(FIXTURE_SOURCE),
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    conn = connect(temp_db)
    try:
        source_id = conn.execute("SELECT id FROM sources").fetchone()[0]
    finally:
        conn.close()

    assert main(["extract-claims", "--source", source_id, "--db", str(temp_db)]) == 0

    conn = connect(temp_db)
    try:
        claims = conn.execute(
            "SELECT id, claim_text, subject, object, domain FROM claims WHERE status = 'accepted'"
        ).fetchall()
        claim_dicts = [
            {
                "id": row[0],
                "claim_text": row[1],
                "subject": row[2],
                "object": row[3],
                "domain": row[4],
            }
            for row in claims
        ]
        ConceptRepository(conn).ensure_domain_concepts("creativity")
        proposed = propose_concept_links(claim_dicts, "creativity", diversity_heuristic=True)
        proposed[0] = {
            **proposed[0],
            "concept_label": "AI-assisted brainstorming",
        }
        proposed = normalize_proposed_concept_links(proposed, "creativity")
        validated = validate_concept_links(proposed)
        assert any(
            link["concept_label"] == "AI assistance" for link in validated["accepted"]
        )

        concept = ConceptRepository(conn).get_by_label("creativity", "AI assistance")
        assert concept is not None
    finally:
        conn.close()

    assert main(["link-concepts", "--source", source_id, "--db", str(temp_db)]) == 0

    conn = sqlite3.connect(temp_db)
    conn.row_factory = sqlite3.Row
    try:
        links = ClaimConceptRepository(conn).list_for_source(source_id)
        linked_labels = {link["concept_label"] for link in links}
        assert "AI assistance" in linked_labels
    finally:
        conn.close()


def test_golden_concept_linking_fixture_still_maps_expected_labels(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ClaimConceptRepository, ClaimRepository

    assert (
        main(
            [
                "ingest",
                str(FIXTURE_SOURCE),
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    conn = connect(temp_db)
    try:
        source_id = conn.execute("SELECT id FROM sources").fetchone()[0]
    finally:
        conn.close()
    assert main(["extract-claims", "--source", source_id, "--db", str(temp_db)]) == 0
    assert main(["link-concepts", "--source", source_id, "--db", str(temp_db)]) == 0

    conn = connect(temp_db)
    try:
        diversity_claims = [
            claim
            for claim in ClaimRepository(conn).list_for_source(source_id, status="accepted")
            if "reduced semantic diversity" in claim.claim_text
        ]
        assert len(diversity_claims) == 1
        diversity_claim_id = diversity_claims[0].id
        links = ClaimConceptRepository(conn).list_for_source(source_id)
        diversity_links = [link for link in links if link["claim_id"] == diversity_claim_id]
        linked_labels = {link["concept_label"] for link in diversity_links}
        assert {
            "AI assistance",
            "brainstorming",
            "semantic diversity",
            "ideation",
            "creativity",
        }.issubset(linked_labels)
    finally:
        conn.close()
