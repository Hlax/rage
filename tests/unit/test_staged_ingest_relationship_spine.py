"""Phase 3 spine through build-relationships on staged-ingested source (ticket-146)."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.db.connection import connect
from rge.db.repositories import RelationshipEvidenceRepository, RelationshipRepository
from rge.modules.relationship_builder import _default_relationship_fixture_for_source

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
TEST_QUESTION_ID = "rq_staged_relationship_spine"
CANDIDATE_ID = "disc_openalex_W2741809807"
STAGED_CHUNK_TEXT = "Human-AI co-creativity supports diverse songwriting outputs."
SAMPLE_HTML = (
    f"<html><body><p>{STAGED_CHUNK_TEXT}</p></body></html>"
).encode("utf-8")
STAGED_TITLE = "Human-AI co-creativity and semantic diversity in songwriting workshops"


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
    return tmp_path / "staged_relationship_spine.sqlite"


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


def _run_spine_through_link(temp_db: Path, staging_dir: Path) -> str:
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
    assert main(["link-concepts", "--source", source_id, "--db", str(temp_db)]) == 0
    return source_id


def test_default_relationship_fixture_for_staged_spine_source() -> None:
    class _Source:
        title = STAGED_TITLE
        source_type = "peer_reviewed_empirical"

    assert (
        _default_relationship_fixture_for_source(_Source())
        == "staged_fetch_build_relationships.json"
    )


def test_staged_discover_fetch_ingest_extract_link_build_relationships_spine(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
) -> None:
    source_id = _run_spine_through_link(temp_db, staging_dir)
    assert main(["build-relationships", "--source", source_id, "--db", str(temp_db)]) == 0

    conn = connect(temp_db)
    try:
        rel_repo = RelationshipRepository(conn)
        relationships = rel_repo.list_for_source(source_id)
        assert len(relationships) >= 1

        match = next(
            (
                rel
                for rel in relationships
                if rel["subject_concept"] == "co-creation"
                and rel["object_concept"] == "semantic diversity"
                and rel["predicate"] == "may_increase"
            ),
            None,
        )
        assert match is not None
        assert match["scope"] == "songwriting workshops"
        assert match["status"] == "active"
        assert match["confidence"] == pytest.approx(0.5)

        evidence = RelationshipEvidenceRepository(conn).list_for_source(source_id)
        support = next(
            (
                row
                for row in evidence
                if row["relationship_id"] == match["id"] and row["stance"] == "supports"
            ),
            None,
        )
        assert support is not None
    finally:
        conn.close()


def test_build_relationships_explicit_staged_fixture(
    temp_db: Path,
    staging_dir: Path,
    mock_network_env: None,
) -> None:
    source_id = _run_spine_through_link(temp_db, staging_dir)
    assert main(
        [
            "build-relationships",
            "--source",
            source_id,
            "--fixture",
            "staged_fetch_build_relationships.json",
            "--db",
            str(temp_db),
        ]
    ) == 0

    conn = connect(temp_db)
    try:
        assert RelationshipRepository(conn).count_for_source(source_id) >= 1
    finally:
        conn.close()
