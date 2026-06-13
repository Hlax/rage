"""Unit tests for claim extraction from manual_text sources (ticket-088)."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pytest

from rge.modules.claim_extractor import _default_fixture_for_source_chunk

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNTHNOTE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "manual_synthnote.txt"
SYNTHNOTE_CHECKSUM = "2c53bfdfdf3c68530f89e24f4f6c88e4ba95574f76484aa5664be9b0ff0c04e4"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "manual_claim_extraction.sqlite"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def _ingest_manual_synthnote(db_path: Path) -> str:
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
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT id, raw_text_checksum FROM sources").fetchone()
        assert row is not None
        assert row[1] == SYNTHNOTE_CHECKSUM
        return row[0]
    finally:
        conn.close()


def test_manual_source_fixture_map_resolves_synthnote_checksum() -> None:
    class _Source:
        source_type = "manual_text"
        raw_text_checksum = SYNTHNOTE_CHECKSUM

    fixture = _default_fixture_for_source_chunk(_Source(), {"chunk_text": "x"})
    assert fixture == "claim_extraction_manual_synthnote.json"


def test_extract_claims_on_manual_synthnote_produces_accepted_and_rejected(
    temp_db: Path,
) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ClaimRepository

    source_id = _ingest_manual_synthnote(temp_db)
    assert main(["extract-claims", "--source", source_id, "--db", str(temp_db)]) == 0

    conn = connect(temp_db)
    try:
        claim_repo = ClaimRepository(conn)
        accepted = claim_repo.list_for_source(source_id, status="accepted")
        rejected = claim_repo.list_for_source(source_id, status="rejected")
        assert len(accepted) >= 1
        assert len(rejected) >= 1
        assert any(
            "narrowed the range of themes" in claim.claim_text for claim in accepted
        )
        assert rejected[0].rejection_reason == "missing_quote_span"

        for claim in accepted:
            quotes = claim_repo.list_quotes_for_claim(claim.id)
            assert quotes
            primary = next(q for q in quotes if q["is_primary"] == 1)
            assert primary["char_start"] is not None
            assert primary["char_end"] > primary["char_start"]
    finally:
        conn.close()


def test_extract_claims_manual_synthnote_is_idempotent(temp_db: Path) -> None:
    from rge.cli import main

    source_id = _ingest_manual_synthnote(temp_db)
    assert main(["extract-claims", "--source", source_id, "--db", str(temp_db)]) == 0
    assert main(["extract-claims", "--source", source_id, "--db", str(temp_db)]) == 0

    conn = sqlite3.connect(temp_db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 3
    finally:
        conn.close()


def test_extract_claims_cli_json_for_manual_synthnote(
    temp_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    source_id = _ingest_manual_synthnote(temp_db)
    capsys.readouterr()
    assert main(["extract-claims", "--source", source_id, "--db", str(temp_db)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["accepted_count"] >= 1
    assert payload["rejected_count"] >= 1


def test_fixture_source_still_uses_diversity_heuristic_not_manual_map(
    temp_db: Path,
) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ChunkRepository, SourceRepository

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
        source = SourceRepository(conn).get_by_checksum(
            conn.execute("SELECT raw_text_checksum FROM sources").fetchone()[0]
        )
        assert source is not None
        assert source.source_type == "fixture"
        chunk = ChunkRepository(conn).list_for_source(source.id)[0]
        resolved = _default_fixture_for_source_chunk(
            source,
            {"chunk_text": chunk.chunk_text},
        )
        assert resolved == "claim_extraction_creativity_scoped.json"
    finally:
        conn.close()
