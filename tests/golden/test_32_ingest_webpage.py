"""Golden Test 32: webpage ingest pipeline (fixture HTML; no network)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_FIXTURE = REPO_ROOT / "fixtures" / "sources" / "web_article_creativity_fixture.html"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "ingest_webpage_golden.sqlite"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def test_ingest_webpage_fixture_pipeline_writes_webpage_source_and_claims(
    temp_db: Path,
) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    assert (
        main(
            [
                "ingest-webpage",
                "--html",
                str(WEB_FIXTURE),
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
        source_row = conn.execute(
            "SELECT id, source_type, domain_metadata_json FROM sources"
        ).fetchone()
        assert source_row is not None
        assert source_row["source_type"] == "webpage"
        metadata = json.loads(source_row["domain_metadata_json"])
        assert metadata["acquisition_status"] == "clean_text_ready"
        assert metadata["source_adapter"] == "web_source_adapter"

        chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        accepted_count = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE status = 'accepted'"
        ).fetchone()[0]
        assert chunk_count >= 1
        assert accepted_count >= 1
    finally:
        conn.close()
