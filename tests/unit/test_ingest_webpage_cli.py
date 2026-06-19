"""ingest-webpage CLI pipeline tests (fixture HTML only; no live network)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.cli import main

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_FIXTURE = REPO_ROOT / "fixtures" / "sources" / "web_article_creativity_fixture.html"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "ingest_webpage.sqlite"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def test_ingest_webpage_cli_ingests_and_extracts_fixture_html(
    temp_db: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    staging_dir = tmp_path / "web_staging"
    exit_code = main(
        [
            "ingest-webpage",
            "--html",
            str(WEB_FIXTURE),
            "--domain",
            "creativity",
            "--db",
            str(temp_db),
            "--staging-dir",
            str(staging_dir),
        ]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["command"] == "ingest-webpage"
    assert payload["ingest"]["status"] in {"ingested", "already_ingested"}
    assert payload["ingest"]["acquisition_status"] == "clean_text_ready"
    assert payload["extract"]["status"] == "completed"
    assert payload["extract"]["accepted_count"] >= 1

    from rge.db.connection import connect

    conn = connect(temp_db)
    try:
        row = conn.execute(
            "SELECT source_type, domain_metadata_json FROM sources WHERE id = ?",
            (payload["source_id"],),
        ).fetchone()
        metadata = json.loads(row["domain_metadata_json"])
        assert row["source_type"] == "webpage"
        assert metadata["acquisition_status"] == "clean_text_ready"
        assert metadata["parser_backend"] == "html_to_text"
        claim_count = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ? AND status = 'accepted'",
            (payload["source_id"],),
        ).fetchone()[0]
        assert claim_count >= 1
    finally:
        conn.close()


def test_ingest_webpage_cli_no_extract_flag_skips_claims(
    temp_db: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "ingest-webpage",
            "--html",
            str(WEB_FIXTURE),
            "--domain",
            "creativity",
            "--db",
            str(temp_db),
            "--no-extract",
        ]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["extract"] is None

    from rge.db.connection import connect

    conn = connect(temp_db)
    try:
        claim_count = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
        assert claim_count == 0
    finally:
        conn.close()


def test_ingest_webpage_cli_blocks_dirty_html(
    temp_db: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dirty_path = tmp_path / "dirty.html"
    dirty_path.write_text("<html><body>bad</body></html>", encoding="utf-8")
    exit_code = main(
        [
            "ingest-webpage",
            "--html",
            str(dirty_path),
            "--domain",
            "creativity",
            "--db",
            str(temp_db),
        ]
    )
    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ingest"]["status"] == "blocked_dirty_text"
