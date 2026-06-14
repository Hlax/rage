"""Unit tests for staged artifact ingest (ticket-143)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.cli import main
from rge.db.connection import ensure_database
from rge.modules.fetcher import (
    OK_EXIT_CODE,
    artifact_bytes_to_text,
    html_to_text,
    ingest_staged_artifact,
    resolve_staged_artifact_path,
    run_ingest_staged_command,
    sha256_bytes,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
TEST_QUESTION_ID = "rq_ingest_staged_test"
CANDIDATE_ID = "disc_openalex_W2741809807"
REFERENCE_YEAR = 2026
SAMPLE_HTML = (
    b"<html><body><p>Human-AI co-creativity supports diverse songwriting outputs.</p></body></html>"
)


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "ingest_staged.sqlite"


@pytest.fixture()
def staging_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "staged"
    directory.mkdir()
    artifact = directory / f"{CANDIDATE_ID}.html"
    artifact.write_bytes(SAMPLE_HTML)
    return directory


@pytest.fixture()
def staged_db_with_candidate(temp_db: Path) -> Path:
    import io

    from rge.modules.research_queue import (
        enqueue_discovered_candidates,
        rank_discovered_candidates,
    )
    from rge.modules.source_providers.openalex import OpenAlexProvider

    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text())
    provider = OpenAlexProvider(
        urlopen=lambda request, timeout=30: io.BytesIO(  # noqa: ARG005
            json.dumps(fixture_payload).encode("utf-8")
        )
    )
    candidates = provider.discover("human AI creativity", "creativity", 10)
    ranked = rank_discovered_candidates(
        candidates,
        query="human AI creativity",
        reference_year=REFERENCE_YEAR,
    )
    conn = ensure_database(temp_db)
    try:
        enqueue_discovered_candidates(
            conn,
            ranked,
            provider_id="openalex",
            research_question_id=TEST_QUESTION_ID,
        )
    finally:
        conn.close()
    return temp_db


def test_html_to_text_strips_tags() -> None:
    assert "Human-AI co-creativity" in html_to_text("<html><body>Human-AI co-creativity</body></html>")


def test_resolve_staged_artifact_path_by_candidate(staging_dir: Path) -> None:
    path = resolve_staged_artifact_path(
        candidate_id=CANDIDATE_ID,
        staging_dir=staging_dir,
    )
    assert path.name == f"{CANDIDATE_ID}.html"


def test_ingest_staged_artifact_persists_source_and_chunks(
    temp_db: Path,
    staging_dir: Path,
) -> None:
    conn = ensure_database(temp_db)
    try:
        result = ingest_staged_artifact(
            conn,
            domain="creativity",
            candidate_id=CANDIDATE_ID,
            staging_dir=staging_dir,
            expected_checksum=sha256_bytes(SAMPLE_HTML),
        )
        assert result["status"] == "ingested"
        assert result["artifact_checksum"] == sha256_bytes(SAMPLE_HTML)

        source_count = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        claims_count = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
        assert source_count == 1
        assert chunk_count >= 1
        assert claims_count == 0
    finally:
        conn.close()


def test_ingest_staged_artifact_checksum_mismatch(
    temp_db: Path,
    staging_dir: Path,
) -> None:
    conn = ensure_database(temp_db)
    try:
        from rge.modules.fetcher import FetchError

        with pytest.raises(FetchError, match="Checksum mismatch"):
            ingest_staged_artifact(
                conn,
                domain="creativity",
                candidate_id=CANDIDATE_ID,
                staging_dir=staging_dir,
                expected_checksum="deadbeef",
            )
    finally:
        conn.close()


def test_ingest_staged_artifact_idempotent(
    temp_db: Path,
    staging_dir: Path,
) -> None:
    conn = ensure_database(temp_db)
    try:
        first = ingest_staged_artifact(
            conn,
            domain="creativity",
            artifact_path=staging_dir / f"{CANDIDATE_ID}.html",
        )
        second = ingest_staged_artifact(
            conn,
            domain="creativity",
            artifact_path=staging_dir / f"{CANDIDATE_ID}.html",
        )
        assert first["status"] == "ingested"
        assert second["status"] == "already_ingested"
        assert first["source_id"] == second["source_id"]
    finally:
        conn.close()


def test_run_ingest_staged_uses_candidate_metadata(
    temp_db: Path,
    staging_dir: Path,
    staged_db_with_candidate: Path,
) -> None:
    conn = ensure_database(staged_db_with_candidate)
    try:
        payload, exit_code = run_ingest_staged_command(
            conn,
            domain="creativity",
            candidate_id=CANDIDATE_ID,
            staging_dir=staging_dir,
        )
    finally:
        conn.close()
    assert exit_code == OK_EXIT_CODE
    assert payload["status"] == "ingested"
    assert payload["candidate_id"] == CANDIDATE_ID


def test_ingest_staged_cli(
    temp_db: Path,
    staging_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checksum = sha256_bytes(SAMPLE_HTML)
    exit_code = main(
        [
            "ingest-staged",
            "--domain",
            "creativity",
            "--candidate",
            CANDIDATE_ID,
            "--checksum",
            checksum,
            "--staging-dir",
            str(staging_dir),
            "--db",
            str(temp_db),
        ]
    )
    assert exit_code == OK_EXIT_CODE
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ingested"
    assert payload["chunk_count"] >= 1
    assert payload["artifact_checksum"] == checksum


def test_ingest_staged_cli_requires_target(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["ingest-staged", "--domain", "creativity"])
    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["reason"] == "missing_target"


def test_artifact_bytes_to_text_html(staging_dir: Path) -> None:
    path = staging_dir / f"{CANDIDATE_ID}.html"
    text = artifact_bytes_to_text(path.read_bytes(), path)
    assert "Human-AI co-creativity" in text
