"""Phase 3 second candidate extract-claims mock spine (ticket-153)."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.db.connection import connect

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
EXTRACT_FIXTURE = "staged_fetch_second_candidate_extract_claims.json"
TEST_QUESTION_ID = "rq_second_staged_extract_spine"
SECOND_CANDIDATE_ID = "disc_openalex_W1234567890"
SECOND_HTML = (
    b"<html><body><p>Constraint management improves AI-assisted creative team workflows.</p></body></html>"
)
STAGED_CHUNK_TEXT = "Constraint management improves AI-assisted creative team workflows."


@pytest.fixture(autouse=True)
def mock_llm_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def mock_network_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "second_staged_extract.sqlite"


@pytest.fixture()
def staging_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "staged"
    directory.mkdir()
    return directory


def _mock_urlopen_factory(payload: dict):
    body = json.dumps(payload).encode("utf-8")

    def _urlopen(request, timeout=30):  # noqa: ARG001
        return io.BytesIO(body)

    return _urlopen


def _mock_html_urlopen(html: bytes, content_type: str = "text/html; charset=utf-8"):
    class _Response(io.BytesIO):
        headers = {"Content-Type": content_type}

    def _urlopen(request, timeout=30):  # noqa: ARG001
        return _Response(html)

    return _urlopen


def _discover_and_enqueue(temp_db: Path) -> None:
    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text())
    discover_args = [
        "discover-sources",
        "--provider",
        "openalex",
        "--query",
        "human AI creativity",
        "--rank-only",
        "--enqueue",
        "--db",
        str(temp_db),
        "--question",
        TEST_QUESTION_ID,
    ]
    with patch(
        "rge.modules.source_providers.openalex.urllib.request.urlopen",
        _mock_urlopen_factory(fixture_payload),
    ):
        assert main(discover_args) == 0


def _ingest_second_candidate(
    temp_db: Path,
    staging_dir: Path,
) -> str:
    _discover_and_enqueue(temp_db)
    with patch(
        "rge.modules.fetcher.urllib.request.urlopen",
        _mock_html_urlopen(SECOND_HTML),
    ):
        assert (
            main(
                [
                    "fetch-candidate",
                    "--candidate",
                    SECOND_CANDIDATE_ID,
                    "--db",
                    str(temp_db),
                    "--out",
                    str(staging_dir),
                ]
            )
            == 0
        )
    assert (
        main(
            [
                "ingest-staged",
                "--domain",
                "creativity",
                "--candidate",
                SECOND_CANDIDATE_ID,
                "--staging-dir",
                str(staging_dir),
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    conn = connect(temp_db)
    try:
        row = conn.execute(
            """
            SELECT id FROM sources
            WHERE title LIKE '%Constraint management%'
            """
        ).fetchone()
        assert row is not None
        return row["id"]
    finally:
        conn.close()


def test_second_staged_candidate_extract_spine(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
) -> None:
    source_id = _ingest_second_candidate(temp_db, staging_dir)
    assert (
        main(
            [
                "extract-claims",
                "--source",
                source_id,
                "--fixture",
                EXTRACT_FIXTURE,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        accepted = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ? AND status = 'accepted'",
            (source_id,),
        ).fetchone()[0]
        rejected = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ? AND status = 'rejected'",
            (source_id,),
        ).fetchone()[0]
        rejection = conn.execute(
            """
            SELECT rejection_reason FROM claims
            WHERE source_id = ? AND status = 'rejected'
            """,
            (source_id,),
        ).fetchone()
        accepted_text = conn.execute(
            """
            SELECT claim_text FROM claims
            WHERE source_id = ? AND status = 'accepted'
            """,
            (source_id,),
        ).fetchone()
    finally:
        conn.close()

    assert accepted == 1
    assert rejected == 1
    assert rejection is not None
    assert rejection["rejection_reason"] == "missing_quote_span"
    assert accepted_text is not None
    assert STAGED_CHUNK_TEXT in accepted_text["claim_text"]


def test_second_staged_candidate_extract_cli_json_and_idempotent(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_id = _ingest_second_candidate(temp_db, staging_dir)
    extract_args = [
        "extract-claims",
        "--source",
        source_id,
        "--fixture",
        EXTRACT_FIXTURE,
        "--db",
        str(temp_db),
    ]
    capsys.readouterr()
    assert main(extract_args) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["status"] == "completed"
    assert first["command"] == "extract-claims"
    assert first["source_id"] == source_id
    assert first["accepted_count"] == 1
    assert first["rejected_count"] == 1

    assert main(extract_args) == 0
    second = json.loads(capsys.readouterr().out)
    assert second["status"] == "already_extracted"
    assert second["accepted_count"] == 1
    assert second["rejected_count"] == 1
