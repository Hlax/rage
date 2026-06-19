"""Golden Test 1: source ingestion creates durable source records."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "ingestion_test.sqlite"


def test_migration_harness_creates_schema(temp_db: Path) -> None:
    from rge.db.connection import apply_migrations, connect

    conn = connect(temp_db)
    try:
        applied = apply_migrations(conn)
        assert applied == [
            "0001_initial",
            "0002_relationship_evidence",
            "0003_candidate_sources_research_queue",
            "0004_cluster_reports",
            "0005_theory_candidates",
            "0006_ontology_proposals",
            "0007_domain_proposals",
            "0008_candidate_sources_url_candidates",
            "0009_purpose_evidence_atoms",
        ]
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert "sources" in tables
        assert "chunks" in tables
        assert "claims" in tables
        assert "claim_quotes" in tables
        assert "relationship_evidence" in tables
        assert "evidence_atoms" in tables
        assert "candidate_sources" in tables
        assert "research_queue" in tables
        contract_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(research_contracts)")
        }
        assert "purpose_metadata_json" in contract_columns
        assert "claims_staged" not in tables
        assert "claims_accepted" not in tables
        assert "claim_rejections" not in tables
    finally:
        conn.close()


def test_ingest_persists_source_and_chunks(temp_db: Path) -> None:
    from rge.cli import main

    exit_code = main(
        [
            "ingest",
            str(FIXTURE_SOURCE),
            "--domain",
            "creativity",
            "--db",
            str(temp_db),
        ]
    )
    assert exit_code == 0

    conn = sqlite3.connect(temp_db)
    conn.row_factory = sqlite3.Row
    try:
        source = conn.execute("SELECT * FROM sources").fetchone()
        assert source is not None
        assert source["id"].startswith("src_")
        assert source["title"] == FIXTURE_SOURCE.name
        assert source["source_type"] == "fixture"
        assert source["domain"] == "creativity"
        assert source["status"] == "ingested"
        assert source["raw_text_checksum"]
        assert source["created_at"]
        assert source["updated_at"]
        assert source["local_path"]

        chunks = conn.execute(
            "SELECT * FROM chunks WHERE source_id = ? ORDER BY chunk_index",
            (source["id"],),
        ).fetchall()
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk["id"].startswith("chk_")
            assert chunk["text_checksum"]
            assert chunk["chunk_text"]
            assert chunk["created_at"]
    finally:
        conn.close()


def test_source_survives_process_restart(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ChunkRepository, SourceRepository

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
        sources = conn.execute("SELECT id FROM sources").fetchall()
        assert len(sources) == 1
        source_id = sources[0][0]
    finally:
        conn.close()

    conn2 = connect(temp_db)
    try:
        source = SourceRepository(conn2).get_by_id(source_id)
        assert source is not None
        assert source.status == "ingested"
        chunks = ChunkRepository(conn2).list_for_source(source_id)
        assert len(chunks) >= 1
    finally:
        conn2.close()


def test_reingest_same_content_is_idempotent(temp_db: Path) -> None:
    from rge.cli import main

    args = [
        "ingest",
        str(FIXTURE_SOURCE),
        "--domain",
        "creativity",
        "--db",
        str(temp_db),
    ]
    assert main(args) == 0
    assert main(args) == 0

    conn = sqlite3.connect(temp_db)
    try:
        count = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        assert count == 1
    finally:
        conn.close()


def test_ingest_cli_emits_machine_readable_json(
    temp_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    exit_code = main(
        [
            "ingest",
            str(FIXTURE_SOURCE),
            "--domain",
            "creativity",
            "--db",
            str(temp_db),
        ]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["status"] in {"ingested", "already_ingested"}
    assert payload["command"] == "ingest"
    assert payload["source"]["status"] == "ingested"
    assert payload["chunk_count"] >= 1
