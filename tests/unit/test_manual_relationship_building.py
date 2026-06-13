"""Unit tests for relationship building on manual_text sources (ticket-090)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.modules.manual_source_fixtures import relationship_fixture_for_manual_source

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNTHNOTE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "manual_synthnote.txt"
SYNTHNOTE_CHECKSUM = "2c53bfdfdf3c68530f89e24f4f6c88e4ba95574f76484aa5664be9b0ff0c04e4"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "manual_relationship_building.sqlite"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def _prepare_manual_synthnote_with_links(db_path: Path) -> str:
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
    assert main(["link-concepts", "--source", source_id, "--db", str(db_path)]) == 0
    return source_id


def test_relationship_fixture_map_resolves_synthnote_checksum() -> None:
    class _Source:
        source_type = "manual_text"
        raw_text_checksum = SYNTHNOTE_CHECKSUM

    assert (
        relationship_fixture_for_manual_source(_Source())
        == "relationship_drafting_manual_synthnote.json"
    )


def test_build_relationships_on_manual_synthnote_persists_edges(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import (
        RelationshipEvidenceRepository,
        RelationshipRepository,
    )

    source_id = _prepare_manual_synthnote_with_links(temp_db)
    assert (
        main(["build-relationships", "--source", source_id, "--db", str(temp_db)]) == 0
    )

    conn = connect(temp_db)
    try:
        relationships = RelationshipRepository(conn).list_for_source(source_id)
        assert len(relationships) >= 1
        match = next(
            (
                rel
                for rel in relationships
                if rel["subject_concept"] == "AI assistance"
                and rel["object_concept"] == "semantic diversity"
                and rel["predicate"] == "may_reduce"
            ),
            None,
        )
        assert match is not None
        assert match["scope"] == "synthetic brainstorming"
        assert match["status"] == "active"

        evidence = RelationshipEvidenceRepository(conn).list_for_source(source_id)
        assert len(evidence) >= 1
        assert any(row["stance"] == "supports" for row in evidence)
    finally:
        conn.close()


def test_build_relationships_manual_synthnote_is_idempotent(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import RelationshipRepository

    source_id = _prepare_manual_synthnote_with_links(temp_db)
    assert (
        main(["build-relationships", "--source", source_id, "--db", str(temp_db)]) == 0
    )

    conn = connect(temp_db)
    try:
        first_count = RelationshipRepository(conn).count_for_source(source_id)
        assert first_count >= 1
    finally:
        conn.close()

    assert (
        main(["build-relationships", "--source", source_id, "--db", str(temp_db)]) == 0
    )

    conn = connect(temp_db)
    try:
        second_count = RelationshipRepository(conn).count_for_source(source_id)
        assert second_count == first_count
    finally:
        conn.close()


def test_build_relationships_cli_json_for_manual_synthnote(
    temp_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    source_id = _prepare_manual_synthnote_with_links(temp_db)
    capsys.readouterr()
    assert (
        main(["build-relationships", "--source", source_id, "--db", str(temp_db)]) == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["relationship_count"] >= 1
    assert payload["evidence_count"] >= 1


def test_golden_fixture_source_still_uses_diversity_relationship_fixture(
    temp_db: Path,
) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import RelationshipRepository

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
    assert (
        main(["build-relationships", "--source", source_id, "--db", str(temp_db)]) == 0
    )

    conn = connect(temp_db)
    try:
        relationships = RelationshipRepository(conn).list_for_source(source_id)
        assert any(rel["predicate"] == "may_reduce" for rel in relationships)
    finally:
        conn.close()
