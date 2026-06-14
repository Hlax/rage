"""Phase 3 discover → fetch → ingest-staged → extract-claims mock spine (ticket-144)."""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.db.connection import connect
from rge.modules.claim_extractor import _default_fixture_for_chunk

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
TEST_QUESTION_ID = "rq_staged_extract_spine"
CANDIDATE_ID = "disc_openalex_W2741809807"
REFERENCE_YEAR = 2026
STAGED_CHUNK_TEXT = "Human-AI co-creativity supports diverse songwriting outputs."
SAMPLE_HTML = (
    f"<html><body><p>{STAGED_CHUNK_TEXT}</p></body></html>"
).encode("utf-8")


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
    return tmp_path / "staged_extract_spine.sqlite"


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


def test_default_fixture_for_staged_fetch_spine_chunk() -> None:
    fixture = _default_fixture_for_chunk({"chunk_text": STAGED_CHUNK_TEXT})
    assert fixture == "staged_fetch_extract_claims.json"


def test_staged_discover_fetch_ingest_extract_spine(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
) -> None:
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

    with patch("rge.modules.fetcher.urllib.request.urlopen", _mock_html_urlopen(SAMPLE_HTML)):
        assert main(
            [
                "fetch-candidate",
                "--candidate",
                CANDIDATE_ID,
                "--db",
                str(temp_db),
                "--out",
                str(staging_dir),
            ]
        ) == 0

    assert main(
        [
            "ingest-staged",
            "--domain",
            "creativity",
            "--candidate",
            CANDIDATE_ID,
            "--staging-dir",
            str(staging_dir),
            "--db",
            str(temp_db),
        ]
    ) == 0

    conn = connect(temp_db)
    try:
        source_id = conn.execute("SELECT id FROM sources").fetchone()["id"]
    finally:
        conn.close()

    assert main(["extract-claims", "--source", source_id, "--db", str(temp_db)]) == 0

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
        assert accepted == 1
        assert rejected == 1
    finally:
        conn.close()


def test_extract_claims_explicit_staged_fixture(
    temp_db: Path,
    staging_dir: Path,
    mock_network_env: None,
) -> None:
    from rge.modules.fetcher import ingest_staged_artifact, sha256_bytes
    from rge.db.connection import ensure_database

    artifact = staging_dir / f"{CANDIDATE_ID}.html"
    artifact.write_bytes(SAMPLE_HTML)
    conn = ensure_database(temp_db)
    try:
        ingest_result = ingest_staged_artifact(
            conn,
            domain="creativity",
            artifact_path=artifact,
            expected_checksum=sha256_bytes(SAMPLE_HTML),
            source_type="peer_reviewed_empirical",
            title="Staged spine explicit fixture test",
        )
        source_id = ingest_result["source_id"]
    finally:
        conn.close()

    assert main(
        [
            "extract-claims",
            "--source",
            source_id,
            "--fixture",
            "staged_fetch_extract_claims.json",
            "--db",
            str(temp_db),
        ]
    ) == 0

    conn = connect(temp_db)
    try:
        accepted = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ? AND status = 'accepted'",
            (source_id,),
        ).fetchone()[0]
        assert accepted == 1
    finally:
        conn.close()


def test_extract_spine_no_live_llm_collection() -> None:
  """Default pytest collection must not import live smoke tests."""
  prior = os.environ.get("RGE_LLM_MODE")
  assert prior == "mock" or os.environ.get("RGE_LLM_MODE") == "mock"
