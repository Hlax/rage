"""Unit tests for staged candidate URL fetch (ticket-142)."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.db.connection import ensure_database
from rge.modules.fetcher import (
    BLOCKED_EXIT_CODE,
    ERROR_EXIT_CODE,
    OK_EXIT_CODE,
    extension_for_content_type,
    fetch_staged_candidate_artifact,
    run_fetch_candidate_command,
    sha256_bytes,
)
from rge.modules.research_queue import enqueue_discovered_candidates, rank_discovered_candidates

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
TEST_QUESTION_ID = "rq_fetch_candidate_test"
CANDIDATE_ID = "disc_openalex_W2741809807"
REFERENCE_YEAR = 2026


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def mock_network_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "fetch_candidate.sqlite"


@pytest.fixture()
def staged_db_with_candidate(temp_db: Path, mock_network_env: None) -> Path:
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


def _mock_html_urlopen(html: bytes, content_type: str = "text/html; charset=utf-8"):
    class _Response(io.BytesIO):
        headers = {"Content-Type": content_type}

    def _urlopen(request, timeout=30):  # noqa: ARG001
        return _Response(html)

    return _urlopen


def test_extension_for_content_type() -> None:
    assert extension_for_content_type("text/html; charset=utf-8") == ".html"
    assert extension_for_content_type("application/pdf") == ".pdf"
    assert extension_for_content_type(None) == ".bin"


def test_fetch_staged_candidate_artifact_writes_file(
    mock_network_env: None,
    tmp_path: Path,
) -> None:
    candidate = {
        "id": CANDIDATE_ID,
        "url": "https://example.org/landing/human-ai-cocreativity",
    }
    html = b"<html><body>Human-AI co-creativity evidence.</body></html>"
    result = fetch_staged_candidate_artifact(
        candidate,
        output_dir=tmp_path,
        urlopen=_mock_html_urlopen(html),
    )
    assert result["status"] == "completed"
    assert result["content_type"] == "text/html; charset=utf-8"
    assert result["checksum"] == sha256_bytes(html)
    artifact = Path(result["artifact_path"])
    assert artifact.is_file()
    assert artifact.read_bytes() == html


def test_fetch_staged_candidate_blocked_without_network(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "0")
    candidate = {
        "id": CANDIDATE_ID,
        "url": "https://example.org/landing/page",
    }
    result = fetch_staged_candidate_artifact(candidate, output_dir=tmp_path)
    assert result["status"] == "blocked"
    assert result["reason"] == "source_network_disabled"


def test_run_fetch_candidate_command_completed(
    staged_db_with_candidate: Path,
    mock_network_env: None,
    tmp_path: Path,
) -> None:
    html = b"<html><body>Staged candidate fetch test.</body></html>"
    conn = ensure_database(staged_db_with_candidate)
    try:
        payload, exit_code = run_fetch_candidate_command(
            conn,
            candidate_id=CANDIDATE_ID,
            output_dir=tmp_path,
            urlopen=_mock_html_urlopen(html),
        )
    finally:
        conn.close()
    assert exit_code == OK_EXIT_CODE
    assert payload["status"] == "completed"
    assert payload["byte_count"] == len(html)


def test_run_fetch_candidate_command_candidate_not_found(temp_db: Path) -> None:
    conn = ensure_database(temp_db)
    try:
        payload, exit_code = run_fetch_candidate_command(
            conn,
            candidate_id="disc_openalex_missing",
        )
    finally:
        conn.close()
    assert exit_code == ERROR_EXIT_CODE
    assert payload["reason"] == "candidate_not_found"


def test_run_fetch_candidate_command_missing_url(
    staged_db_with_candidate: Path,
    mock_network_env: None,
) -> None:
    conn = ensure_database(staged_db_with_candidate)
    try:
        conn.execute(
            "UPDATE candidate_sources SET url = NULL, url_candidates_json = NULL WHERE id = ?",
            (CANDIDATE_ID,),
        )
        conn.commit()
        payload, exit_code = run_fetch_candidate_command(
            conn,
            candidate_id=CANDIDATE_ID,
        )
    finally:
        conn.close()
    assert exit_code == ERROR_EXIT_CODE
    assert payload["reason"] == "no_fetchable_url"


def test_fetch_staged_candidate_artifact_idempotent(
    mock_network_env: None,
    tmp_path: Path,
) -> None:
    candidate = {
        "id": CANDIDATE_ID,
        "url": "https://example.org/landing/page",
    }
    html = b"<html><body>Idempotent fetch.</body></html>"
    urlopen = _mock_html_urlopen(html)
    first = fetch_staged_candidate_artifact(
        candidate,
        output_dir=tmp_path,
        urlopen=urlopen,
    )
    second = fetch_staged_candidate_artifact(
        candidate,
        output_dir=tmp_path,
        urlopen=urlopen,
    )
    assert first["status"] == "completed"
    assert second["status"] == "already_fetched"
    assert first["checksum"] == second["checksum"]


def test_fetch_candidate_cli(
    staged_db_with_candidate: Path,
    mock_network_env: None,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    html = b"<html><body>CLI fetch candidate.</body></html>"
    with patch("rge.modules.fetcher.urllib.request.urlopen", _mock_html_urlopen(html)):
        exit_code = main(
            [
                "fetch-candidate",
                "--candidate",
                CANDIDATE_ID,
                "--db",
                str(staged_db_with_candidate),
                "--out",
                str(tmp_path),
            ]
        )
    assert exit_code == OK_EXIT_CODE
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert Path(payload["artifact_path"]).is_file()

    from rge.db.connection import connect

    conn = connect(staged_db_with_candidate)
    try:
        sources_count = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        claims_count = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    finally:
        conn.close()
    assert sources_count == 0
    assert claims_count == 0
