"""Golden Test 5: concept linking maps claims to domain concepts."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"

EXPECTED_CONCEPT_LABELS = {
    "AI assistance",
    "brainstorming",
    "semantic diversity",
    "ideation",
    "creativity",
}

EXPECTED_DOMAIN_METADATA = {
    "creative_phase": "ideation",
    "measured_dimension": "diversity",
    "track": "human-AI",
}

DIVERSITY_CLAIM_FRAGMENT = "reduced semantic diversity"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "concept_linking_test.sqlite"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def _prepare_source_with_claims(db_path: Path) -> str:
    from rge.cli import main

    assert (
        main(
            [
                "ingest",
                str(FIXTURE_SOURCE),
                "--domain",
                "creativity",
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    from rge.db.connection import connect

    conn = connect(db_path)
    try:
        source_id = conn.execute("SELECT id FROM sources").fetchone()[0]
    finally:
        conn.close()
    assert (
        main(["extract-claims", "--source", source_id, "--db", str(db_path)]) == 0
    )
    return source_id


def test_link_concepts_maps_diversity_claim_to_expected_concepts(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ClaimConceptRepository, ClaimRepository

    source_id = _prepare_source_with_claims(temp_db)
    assert (
        main(["link-concepts", "--source", source_id, "--db", str(temp_db)]) == 0
    )

    conn = connect(temp_db)
    try:
        claim_repo = ClaimRepository(conn)
        diversity_claims = [
            claim
            for claim in claim_repo.list_for_source(source_id, status="accepted")
            if DIVERSITY_CLAIM_FRAGMENT in claim.claim_text
        ]
        assert len(diversity_claims) == 1
        diversity_claim_id = diversity_claims[0].id

        link_repo = ClaimConceptRepository(conn)
        links = link_repo.list_for_source(source_id)
        assert len(links) >= 5

        diversity_links = [
            link for link in links if link["claim_id"] == diversity_claim_id
        ]
        linked_labels = {link["concept_label"] for link in diversity_links}
        assert EXPECTED_CONCEPT_LABELS.issubset(linked_labels)

        for link in diversity_links:
            assert link["role"]
            assert link["confidence"] is not None
            metadata = link["domain_metadata"]
            for key, value in EXPECTED_DOMAIN_METADATA.items():
                assert metadata.get(key) == value
    finally:
        conn.close()


def test_concept_links_survive_process_restart(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ClaimConceptRepository

    source_id = _prepare_source_with_claims(temp_db)
    assert (
        main(["link-concepts", "--source", source_id, "--db", str(temp_db)]) == 0
    )

    conn = connect(temp_db)
    try:
        count = ClaimConceptRepository(conn).count_for_source(source_id)
        assert count >= 5
    finally:
        conn.close()

    conn2 = connect(temp_db)
    try:
        links = ClaimConceptRepository(conn2).list_for_source(source_id)
        assert len(links) >= 5
    finally:
        conn2.close()


def test_link_concepts_cli_emits_machine_readable_json(
    temp_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    source_id = _prepare_source_with_claims(temp_db)
    capsys.readouterr()
    exit_code = main(["link-concepts", "--source", source_id, "--db", str(temp_db)])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] in {"completed", "already_linked"}
    assert payload["command"] == "link-concepts"
    assert payload["link_count"] >= 5
    assert len(payload["links"]) >= 5
