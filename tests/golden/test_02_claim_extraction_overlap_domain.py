"""Golden Test 2 extension: overlap-domain claim labels accepted in mock extraction."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.modules.claim_extractor import extract_and_validate_for_chunk

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
OVERLAP_FIXTURE = "claim_extraction_overlap_domain_art.json"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "overlap_domain_claim_test.sqlite"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def _ingest_fixture(db_path: Path) -> str:
    from rge.cli import main

    exit_code = main(
        [
            "ingest",
            str(FIXTURE_SOURCE),
            "--domain",
            "creativity",
            "--db",
            str(db_path),
        ]
    )
    assert exit_code == 0
    from rge.db.connection import connect

    conn = connect(db_path)
    try:
        row = conn.execute("SELECT id FROM sources").fetchone()
        assert row is not None
        return row[0]
    finally:
        conn.close()


def _chunk_dict_for_source(db_path: Path, source_id: str) -> dict[str, object]:
    from rge.db.connection import connect
    from rge.db.repositories import ChunkRepository

    conn = connect(db_path)
    try:
        chunks = ChunkRepository(conn).list_for_source(source_id)
        assert len(chunks) == 1
        chunk = chunks[0]
        return {
            "id": chunk.id,
            "source_id": chunk.source_id,
            "chunk_index": chunk.chunk_index,
            "chunk_text": chunk.chunk_text,
        }
    finally:
        conn.close()


def test_overlap_domain_claim_accepted_via_extract_and_validate(temp_db: Path) -> None:
    source_id = _ingest_fixture(temp_db)
    chunk = _chunk_dict_for_source(temp_db, source_id)

    result = extract_and_validate_for_chunk(
        chunk,
        domain_pack="creativity",
        fixture_name=OVERLAP_FIXTURE,
    )

    accepted = result["accepted"]
    rejected = result["rejected"]
    assert len(rejected) == 0
    assert len(accepted) == 1
    claim = accepted[0]
    assert claim["domain"] == "art"
    assert "film and music" in claim["object"]
    assert claim["scope"] == "short-form writing tasks"


def test_overlap_domain_claim_persisted_via_extract_claims_cli(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ClaimRepository

    source_id = _ingest_fixture(temp_db)
    assert (
        main(
            [
                "extract-claims",
                "--source",
                source_id,
                "--db",
                str(temp_db),
                "--fixture",
                OVERLAP_FIXTURE,
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        claim_repo = ClaimRepository(conn)
        accepted = claim_repo.list_for_source(source_id, status="accepted")
        rejected = claim_repo.list_for_source(source_id, status="rejected")
        assert len(rejected) == 0
        assert len(accepted) == 1
        claim = accepted[0]
        assert claim.domain == "art"
        assert claim.scope == "short-form writing tasks"
        assert claim.evidence_type == "empirical"
        assert json.loads(claim.limitations_json) is not None
    finally:
        conn.close()
