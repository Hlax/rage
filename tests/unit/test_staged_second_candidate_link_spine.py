"""Phase 3 second candidate link-concepts mock spine (ticket-154)."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.db.connection import connect
from rge.db.repositories import ClaimConceptRepository

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
EXTRACT_FIXTURE = "staged_fetch_second_candidate_extract_claims.json"
LINK_FIXTURE = "staged_fetch_second_candidate_link_concepts.json"
TEST_QUESTION_ID = "rq_second_staged_link_spine"
SECOND_CANDIDATE_ID = "disc_openalex_W1234567890"
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
    return tmp_path / "second_staged_link.sqlite"


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


def _run_spine_through_extract(temp_db: Path, staging_dir: Path) -> str:
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
        source_id = row["id"]
    finally:
        conn.close()

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
    return source_id


def test_second_staged_candidate_extract_link_spine(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
) -> None:
    source_id = _run_spine_through_extract(temp_db, staging_dir)
    assert (
        main(
            [
                "link-concepts",
                "--source",
                source_id,
                "--fixture",
                LINK_FIXTURE,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        link_count = conn.execute(
            """
            SELECT COUNT(*) FROM claim_concepts cc
            JOIN claims c ON c.id = cc.claim_id
            WHERE c.source_id = ? AND c.status = 'accepted'
            """,
            (source_id,),
        ).fetchone()[0]
        links = ClaimConceptRepository(conn).list_for_source(source_id)
        linked_labels = {link["concept_label"] for link in links}
    finally:
        conn.close()

    assert link_count >= 2
    assert "constraint" in linked_labels
    assert "AI assistance" in linked_labels


def test_second_staged_candidate_link_cli_json_and_idempotent(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_id = _run_spine_through_extract(temp_db, staging_dir)
    link_args = [
        "link-concepts",
        "--source",
        source_id,
        "--fixture",
        LINK_FIXTURE,
        "--db",
        str(temp_db),
    ]
    capsys.readouterr()
    assert main(link_args) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["status"] == "completed"
    assert first["command"] == "link-concepts"
    assert first["source_id"] == source_id
    assert first["link_count"] >= 2

    assert main(link_args) == 0
    second = json.loads(capsys.readouterr().out)
    assert second["status"] == "already_linked"
    assert second["link_count"] >= 2
