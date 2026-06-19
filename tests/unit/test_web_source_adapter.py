"""Web source adapter tests (fixture HTML only; no live network)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from rge.modules.web_source_adapter import (
    ACQUISITION_CLEAN,
    acquire_webpage_from_path,
    ingest_webpage_artifact_to_db,
    normalize_webpage_artifact,
    run_ingest_webpage_pipeline,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_FIXTURE = REPO_ROOT / "fixtures" / "sources" / "web_article_creativity_fixture.html"


def test_acquire_webpage_from_fixture_produces_clean_text_ready_artifact() -> None:
    artifact = acquire_webpage_from_path(WEB_FIXTURE)

    assert artifact["source_type"] == "webpage"
    assert artifact["acquisition_status"] == ACQUISITION_CLEAN
    assert "AI-assisted brainstorming increased average idea quality" in artifact["clean_text"]
    assert artifact["quality_metrics"]["extractable"] is True
    assert artifact["quality_metrics"]["quoteable_span_count"] >= 1


def test_normalize_webpage_artifact_marks_dirty_when_unextractable() -> None:
    artifact = normalize_webpage_artifact(
        html="<html><body>bad</body></html>",
        url="https://example.com/empty",
        title="Empty page",
    )

    assert artifact["acquisition_status"] == "dirty_text"
    assert artifact["quality_metrics"]["extractable"] is False


def test_ingest_webpage_artifact_to_db_persists_webpage_source_and_chunks(
    tmp_path: Path,
) -> None:
    from rge.db.connection import connect, ensure_database

    os.environ["RGE_LLM_MODE"] = "mock"
    artifact = acquire_webpage_from_path(WEB_FIXTURE)
    db_path = tmp_path / "web_ingest.sqlite"
    conn = ensure_database(db_path)
    try:
        result = ingest_webpage_artifact_to_db(
            conn,
            artifact,
            domain="creativity",
            staging_dir=tmp_path / "staging",
        )
        assert result["status"] == "ingested"
        row = conn.execute(
            "SELECT source_type, domain_metadata_json FROM sources WHERE id = ?",
            (result["source_id"],),
        ).fetchone()
        metadata = json.loads(row["domain_metadata_json"])
        assert row["source_type"] == "webpage"
        assert metadata["parser_backend"] == "html_to_text"
        chunk_count = conn.execute(
            "SELECT COUNT(*) FROM chunks WHERE source_id = ?",
            (result["source_id"],),
        ).fetchone()[0]
        assert chunk_count >= 1
    finally:
        conn.close()


def test_run_ingest_webpage_pipeline_extracts_quote_backed_claims(
    tmp_path: Path,
) -> None:
    from rge.db.connection import ensure_database

    os.environ["RGE_LLM_MODE"] = "mock"
    artifact = acquire_webpage_from_path(WEB_FIXTURE)
    conn = ensure_database(tmp_path / "web_pipeline.sqlite")
    try:
        result = run_ingest_webpage_pipeline(
            conn,
            artifact,
            domain="creativity",
            staging_dir=tmp_path / "staging",
        )
        assert result["status"] == "completed"
        assert result["extract"]["accepted_count"] >= 1
    finally:
        conn.close()
