"""Phase 3 second ranked candidate fetch and ingest (ticket-152)."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.db.connection import connect
from rge.modules.fetcher import sha256_bytes

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
TEST_QUESTION_ID = "rq_second_staged_candidate_spine"
FIRST_CANDIDATE_ID = "disc_openalex_W2741809807"
SECOND_CANDIDATE_ID = "disc_openalex_W1234567890"
FIRST_HTML = (
    b"<html><body><p>Human-AI co-creativity supports diverse songwriting outputs.</p></body></html>"
)
SECOND_HTML = (
    b"<html><body><p>Constraint management improves AI-assisted creative team workflows.</p></body></html>"
)


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
    return tmp_path / "second_staged_candidate.sqlite"


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


def _mock_html_urlopen_by_url(responses: dict[str, bytes]):
    class _Response(io.BytesIO):
        def __init__(self, data: bytes, content_type: str = "text/html; charset=utf-8") -> None:
            super().__init__(data)
            self.headers = {"Content-Type": content_type}

    def _urlopen(request, timeout=30):  # noqa: ARG001
        url = request.full_url if hasattr(request, "full_url") else str(request)
        for key, html in responses.items():
            if key in url:
                return _Response(html)
        raise AssertionError(f"Unexpected fetch URL: {url!r}")

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


def _staging_artifact_paths(staging_dir: Path) -> list[Path]:
    return sorted(staging_dir.glob("disc_openalex_*.*"))


def _source_counts(temp_db: Path) -> tuple[int, int]:
    conn = connect(temp_db)
    try:
        sources = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        return int(sources), int(chunks)
    finally:
        conn.close()


def test_second_candidate_discover_enqueue_fetch_ingest(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _discover_and_enqueue(temp_db)

    conn = connect(temp_db)
    try:
        candidate_count = conn.execute(
            "SELECT COUNT(*) FROM candidate_sources"
        ).fetchone()[0]
        queue_count = conn.execute("SELECT COUNT(*) FROM research_queue").fetchone()[0]
        second_rank = conn.execute(
            """
            SELECT id, title, priority_score
            FROM candidate_sources
            WHERE id = ?
            """,
            (SECOND_CANDIDATE_ID,),
        ).fetchone()
        first_rank = conn.execute(
            """
            SELECT priority_score
            FROM candidate_sources
            WHERE id = ?
            """,
            (FIRST_CANDIDATE_ID,),
        ).fetchone()
    finally:
        conn.close()

    assert candidate_count == 2
    assert queue_count == 2
    assert second_rank is not None
    assert first_rank is not None
    assert float(second_rank["priority_score"]) < float(first_rank["priority_score"])
    assert "Constraint management" in second_rank["title"]

    urlopen = _mock_html_urlopen_by_url(
        {
            "human-ai-cocreativity": FIRST_HTML,
            "constraint-management": SECOND_HTML,
        }
    )
    with patch("rge.modules.fetcher.urllib.request.urlopen", urlopen):
        assert (
            main(
                [
                    "fetch-candidate",
                    "--candidate",
                    FIRST_CANDIDATE_ID,
                    "--db",
                    str(temp_db),
                    "--out",
                    str(staging_dir),
                ]
            )
            == 0
        )
        capsys.readouterr()
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
    fetch_payload = json.loads(capsys.readouterr().out)
    assert fetch_payload["status"] == "completed"
    assert fetch_payload["command"] == "fetch-candidate"
    assert fetch_payload["candidate_id"] == SECOND_CANDIDATE_ID
    assert fetch_payload["checksum"] == sha256_bytes(SECOND_HTML)

    artifacts = _staging_artifact_paths(staging_dir)
    assert len(artifacts) == 2
    assert {path.name for path in artifacts} == {
        f"{FIRST_CANDIDATE_ID}.html",
        f"{SECOND_CANDIDATE_ID}.html",
    }

    capsys.readouterr()
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
    ingest_payload = json.loads(capsys.readouterr().out)
    assert ingest_payload["status"] == "ingested"
    assert ingest_payload["command"] == "ingest-staged"
    assert ingest_payload["candidate_id"] == SECOND_CANDIDATE_ID
    assert ingest_payload["artifact_checksum"] == sha256_bytes(SECOND_HTML)
    assert ingest_payload["chunk_count"] >= 1

    conn = connect(temp_db)
    try:
        row = conn.execute(
            """
            SELECT title, source_type
            FROM sources
            WHERE title LIKE '%Constraint management%'
            """
        ).fetchone()
        claims_count = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    finally:
        conn.close()
    assert row is not None
    assert row["source_type"] == "unknown"
    assert claims_count == 0
    assert _source_counts(temp_db) == (1, 1)


def test_second_candidate_fetch_and_ingest_reruns_are_idempotent(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _discover_and_enqueue(temp_db)
    urlopen = _mock_html_urlopen_by_url(
        {"constraint-management": SECOND_HTML},
    )

    with patch("rge.modules.fetcher.urllib.request.urlopen", urlopen):
        fetch_args = [
            "fetch-candidate",
            "--candidate",
            SECOND_CANDIDATE_ID,
            "--db",
            str(temp_db),
            "--out",
            str(staging_dir),
        ]
        capsys.readouterr()
        assert main(fetch_args) == 0
        first_fetch = json.loads(capsys.readouterr().out)
        assert main(fetch_args) == 0
        second_fetch = json.loads(capsys.readouterr().out)

    assert first_fetch["status"] == "completed"
    assert second_fetch["status"] == "already_fetched"
    assert first_fetch["checksum"] == second_fetch["checksum"]
    assert len(_staging_artifact_paths(staging_dir)) == 1

    ingest_args = [
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
    capsys.readouterr()
    assert main(ingest_args) == 0
    first_ingest = json.loads(capsys.readouterr().out)
    baseline_sources, baseline_chunks = _source_counts(temp_db)
    assert main(ingest_args) == 0
    second_ingest = json.loads(capsys.readouterr().out)

    assert first_ingest["status"] == "ingested"
    assert second_ingest["status"] == "already_ingested"
    assert first_ingest["source_id"] == second_ingest["source_id"]
    assert _source_counts(temp_db) == (baseline_sources, baseline_chunks)
    assert baseline_sources == 1
