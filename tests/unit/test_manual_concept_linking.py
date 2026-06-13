"""Unit tests for concept linking on manual_text sources (ticket-089)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.modules.manual_source_fixtures import link_fixture_for_manual_source

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNTHNOTE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "manual_synthnote.txt"
SYNTHNOTE_CHECKSUM = "2c53bfdfdf3c68530f89e24f4f6c88e4ba95574f76484aa5664be9b0ff0c04e4"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "manual_concept_linking.sqlite"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def _prepare_manual_synthnote_with_claims(db_path: Path) -> str:
    from rge.cli import main

    assert (
        main(
            [
                "ingest",
                str(SYNTHNOTE_SOURCE),
                "--domain",
                "creativity",
                "--source-type",
                "manual_text",
                "--source-title",
                "Synthetic Source Note: AI-Assisted Ideation and Semantic Diversity",
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
    assert main(["extract-claims", "--source", source_id, "--db", str(db_path)]) == 0
    return source_id


def test_link_fixture_map_resolves_synthnote_checksum() -> None:
    class _Source:
        source_type = "manual_text"
        raw_text_checksum = SYNTHNOTE_CHECKSUM

    assert (
        link_fixture_for_manual_source(_Source())
        == "concept_linking_manual_synthnote.json"
    )


def test_link_concepts_on_manual_synthnote_persists_canonical_labels(
    temp_db: Path,
) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ClaimConceptRepository

    source_id = _prepare_manual_synthnote_with_claims(temp_db)
    assert main(["link-concepts", "--source", source_id, "--db", str(temp_db)]) == 0

    conn = connect(temp_db)
    try:
        links = ClaimConceptRepository(conn).list_for_source(source_id)
        assert len(links) >= 3
        linked_labels = {link["concept_label"] for link in links}
        assert "AI assistance" in linked_labels
        assert "semantic diversity" in linked_labels
        assert "ideation" in linked_labels
        assert "AI-assisted brainstorming" not in linked_labels
    finally:
        conn.close()


def test_link_concepts_manual_synthnote_is_idempotent(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ClaimConceptRepository

    source_id = _prepare_manual_synthnote_with_claims(temp_db)
    assert main(["link-concepts", "--source", source_id, "--db", str(temp_db)]) == 0

    conn = connect(temp_db)
    try:
        first_count = ClaimConceptRepository(conn).count_for_source(source_id)
        assert first_count >= 3
    finally:
        conn.close()

    assert main(["link-concepts", "--source", source_id, "--db", str(temp_db)]) == 0

    conn = connect(temp_db)
    try:
        second_count = ClaimConceptRepository(conn).count_for_source(source_id)
        assert second_count == first_count
    finally:
        conn.close()


def test_link_concepts_cli_json_for_manual_synthnote(
    temp_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    source_id = _prepare_manual_synthnote_with_claims(temp_db)
    capsys.readouterr()
    assert main(["link-concepts", "--source", source_id, "--db", str(temp_db)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["link_count"] >= 3
    assert len(payload["links"]) >= 3


def test_golden_fixture_source_still_uses_diversity_link_fixture(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ClaimConceptRepository, ClaimRepository

    fixture_path = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
    assert (
        main(
            [
                "ingest",
                str(fixture_path),
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
        links = ClaimConceptRepository(conn).list_for_source(source_id)
        linked_labels = {link["concept_label"] for link in links}
        assert "brainstorming" in linked_labels
        diversity_claims = [
            claim
            for claim in ClaimRepository(conn).list_for_source(source_id, status="accepted")
            if "reduced semantic diversity" in claim.claim_text
        ]
        assert len(diversity_claims) == 1
    finally:
        conn.close()
