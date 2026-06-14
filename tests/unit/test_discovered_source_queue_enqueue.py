"""Unit tests for discovered-source staging enqueue (ticket-141)."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.db.connection import connect, ensure_database
from rge.modules.research_queue import (
    discovered_candidate_source_id,
    enqueue_discovered_candidates,
    rank_discovered_candidates,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
REFERENCE_YEAR = 2026
TEST_QUESTION_ID = "rq_discovered_enqueue_test"


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
    return tmp_path / "discovered_enqueue.sqlite"


def _mock_urlopen_factory(payload: dict):
    body = json.dumps(payload).encode("utf-8")

    def _urlopen(request, timeout=30):  # noqa: ARG001
        return io.BytesIO(body)

    return _urlopen


def _openalex_candidates(domain_pack: str = "creativity") -> list[dict]:
    from rge.modules.source_providers.openalex import OpenAlexProvider

    provider = OpenAlexProvider(
        urlopen=_mock_urlopen_factory(json.loads(OPENALEX_FIXTURE.read_text()))
    )
    return provider.discover("human AI creativity", domain_pack, 10)


def test_discovered_candidate_source_id_stable() -> None:
    assert discovered_candidate_source_id("openalex", "W2741809807") == (
        "disc_openalex_W2741809807"
    )


def test_enqueue_discovered_candidates_persists_staging_rows(temp_db: Path) -> None:
    candidates = _openalex_candidates()
    ranked = rank_discovered_candidates(
        candidates,
        query="human AI creativity",
        domain_pack="creativity",
        reference_year=REFERENCE_YEAR,
    )
    conn = ensure_database(temp_db)
    try:
        result = enqueue_discovered_candidates(
            conn,
            ranked,
            provider_id="openalex",
            research_question_id=TEST_QUESTION_ID,
        )
        assert result["enqueue_status"] == "completed"
        assert result["queue_count"] == 2

        candidate_rows = conn.execute(
            "SELECT * FROM candidate_sources WHERE research_question_id = ?",
            (TEST_QUESTION_ID,),
        ).fetchall()
        assert len(candidate_rows) == 2
        assert all(row["id"].startswith("disc_openalex_") for row in candidate_rows)

        queue_rows = conn.execute(
            "SELECT * FROM research_queue WHERE research_question_id = ?",
            (TEST_QUESTION_ID,),
        ).fetchall()
        assert len(queue_rows) == 2

        sources_count = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        claims_count = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
        assert sources_count == 0
        assert claims_count == 0
    finally:
        conn.close()


def test_enqueue_discovered_candidates_idempotent(temp_db: Path) -> None:
    candidates = _openalex_candidates()
    ranked = rank_discovered_candidates(
        candidates,
        query="human AI creativity",
        reference_year=REFERENCE_YEAR,
    )
    conn = ensure_database(temp_db)
    try:
        first = enqueue_discovered_candidates(
            conn,
            ranked,
            provider_id="openalex",
            research_question_id=TEST_QUESTION_ID,
        )
        second = enqueue_discovered_candidates(
            conn,
            ranked,
            provider_id="openalex",
            research_question_id=TEST_QUESTION_ID,
        )
        assert first["enqueue_status"] == "completed"
        assert second["enqueue_status"] == "already_queued"
        assert second["queue_count"] == first["queue_count"]

        queue_count = conn.execute(
            "SELECT COUNT(*) FROM research_queue WHERE research_question_id = ?",
            (TEST_QUESTION_ID,),
        ).fetchone()[0]
        assert queue_count == 2
    finally:
        conn.close()


def test_enqueue_skips_rejected_marketing_candidate(temp_db: Path) -> None:
    candidates = _openalex_candidates()
    candidates.append(
        {
            "provider": "openalex",
            "provider_id": "W999",
            "title": "10 Ways AI Will Supercharge Your Creativity",
            "authors": [],
            "year": 2026,
            "doi": None,
            "open_access_url": None,
            "landing_page_url": "https://example.org/marketing",
            "abstract": "",
            "domain_pack": "creativity",
            "discovered_at": "2026-06-14T12:00:00Z",
        }
    )
    ranked = rank_discovered_candidates(
        candidates,
        query="human AI creativity",
        reference_year=REFERENCE_YEAR,
    )
    conn = ensure_database(temp_db)
    try:
        result = enqueue_discovered_candidates(
            conn,
            ranked,
            provider_id="openalex",
            research_question_id=TEST_QUESTION_ID,
        )
        assert result["queue_count"] == 2
        rejected = conn.execute(
            """
            SELECT * FROM candidate_sources
            WHERE research_question_id = ? AND status = 'rejected'
            """,
            (TEST_QUESTION_ID,),
        ).fetchall()
        assert len(rejected) == 1
        assert rejected[0]["id"] == discovered_candidate_source_id("openalex", "W999")
    finally:
        conn.close()


def test_discover_sources_enqueue_cli(
    mock_network_env: None,
    temp_db: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text())
    with patch(
        "rge.modules.source_providers.openalex.urllib.request.urlopen",
        _mock_urlopen_factory(fixture_payload),
    ):
        exit_code = main(
            [
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
        )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["enqueue_status"] == "completed"
    assert payload["queue_count"] == 2
    assert len(payload["ranked_candidates"]) == 2

    conn = connect(temp_db)
    try:
        queue_count = conn.execute(
            "SELECT COUNT(*) FROM research_queue WHERE research_question_id = ?",
            (TEST_QUESTION_ID,),
        ).fetchone()[0]
        assert queue_count == 2
    finally:
        conn.close()


def test_discover_sources_enqueue_requires_rank_only(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "discover-sources",
            "--provider",
            "openalex",
            "--query",
            "human AI creativity",
            "--enqueue",
            "--db",
            "data/db/test.sqlite",
        ]
    )
    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["reason"] == "enqueue_requires_rank_only"


def test_discover_sources_enqueue_requires_db(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "discover-sources",
            "--provider",
            "openalex",
            "--query",
            "human AI creativity",
            "--rank-only",
            "--enqueue",
        ]
    )
    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["reason"] == "missing_db"


def test_discover_sources_enqueue_idempotent_cli(
    mock_network_env: None,
    temp_db: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text())
    args = [
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
        assert main(args) == 0
        capsys.readouterr()
        assert main(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["enqueue_status"] == "already_queued"
    assert payload["queue_count"] == 2
