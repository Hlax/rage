"""Golden Test 6: relationship builder creates support edges."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
MIGRATIONS_DIR = REPO_ROOT / "rge" / "db" / "migrations"

DIVERSITY_CLAIM_FRAGMENT = "reduced semantic diversity"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "relationship_builder_test.sqlite"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def _prepare_source_with_links(db_path: Path) -> str:
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
    assert main(["link-concepts", "--source", source_id, "--db", str(db_path)]) == 0
    return source_id


def test_build_relationships_creates_golden_test_6_edge(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import (
        ClaimRepository,
        RelationshipEvidenceRepository,
        RelationshipRepository,
    )

    source_id = _prepare_source_with_links(temp_db)
    assert (
        main(
            ["build-relationships", "--source", source_id, "--db", str(temp_db)]
        )
        == 0
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

        rel_repo = RelationshipRepository(conn)
        relationships = rel_repo.list_for_source(source_id)
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
        assert match["scope"] == "short-form writing tasks"
        assert match["status"] == "active"
        assert match["confidence"] == pytest.approx(0.5)

        evidence_repo = RelationshipEvidenceRepository(conn)
        evidence = evidence_repo.list_for_source(source_id)
        assert len(evidence) >= 1
        support = next(
            (
                row
                for row in evidence
                if row["relationship_id"] == match["id"]
                and row["stance"] == "supports"
                and row["claim_id"] == diversity_claim_id
            ),
            None,
        )
        assert support is not None
    finally:
        conn.close()


def test_relationships_survive_process_restart(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import RelationshipEvidenceRepository, RelationshipRepository

    source_id = _prepare_source_with_links(temp_db)
    assert (
        main(
            ["build-relationships", "--source", source_id, "--db", str(temp_db)]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        rel_count = RelationshipRepository(conn).count_for_source(source_id)
        evidence_count = len(
            RelationshipEvidenceRepository(conn).list_for_source(source_id)
        )
        assert rel_count >= 1
        assert evidence_count >= 1
    finally:
        conn.close()

    conn2 = connect(temp_db)
    try:
        rel_count = RelationshipRepository(conn2).count_for_source(source_id)
        evidence_count = len(
            RelationshipEvidenceRepository(conn2).list_for_source(source_id)
        )
        assert rel_count >= 1
        assert evidence_count >= 1
    finally:
        conn2.close()


def test_invalid_relationship_candidate_is_rejected_with_reason(
    temp_db: Path,
) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import RelationshipRepository

    source_id = _prepare_source_with_links(temp_db)
    assert (
        main(
            [
                "build-relationships",
                "--source",
                source_id,
                "--db",
                str(temp_db),
                "--fixture",
                "relationship_drafting_unknown_concept.json",
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        assert RelationshipRepository(conn).count_for_source(source_id) == 0
    finally:
        conn.close()


def test_relationship_evidence_migration_applies_after_0001(tmp_path: Path) -> None:
    from rge.db.connection import connect, ensure_database

    db_path = tmp_path / "partial_0001.sqlite"
    conn = connect(db_path)
    migration_0001 = (MIGRATIONS_DIR / "0001_initial.sql").read_text(encoding="utf-8")
    conn.executescript(migration_0001)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        INSERT INTO schema_migrations (version, applied_at)
        VALUES (?, datetime('now'))
        """,
        ("0001_initial",),
    )
    conn.commit()
    tables_before = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "relationships" in tables_before
    assert "relationship_evidence" not in tables_before
    conn.close()

    conn2 = ensure_database(db_path)
    try:
        assert conn2.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='relationship_evidence'"
        ).fetchone()
        tables_after = {
            row[0]
            for row in conn2.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "relationship_evidence" in tables_after
    finally:
        conn2.close()


def test_build_relationships_cli_emits_machine_readable_json(
    temp_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    source_id = _prepare_source_with_links(temp_db)
    capsys.readouterr()
    exit_code = main(
        ["build-relationships", "--source", source_id, "--db", str(temp_db)]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] in {"completed", "already_built"}
    assert payload["command"] == "build-relationships"
    assert payload["relationship_count"] >= 1
    assert payload["evidence_count"] >= 1
    assert payload["relationships"][0]["predicate"] == "may_reduce"
