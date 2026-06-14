"""Phase 3 second candidate build-relationships mock spine (ticket-155)."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.db.connection import connect
from rge.db.repositories import RelationshipEvidenceRepository, RelationshipRepository

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
EXTRACT_FIXTURE = "staged_fetch_second_candidate_extract_claims.json"
LINK_FIXTURE = "staged_fetch_second_candidate_link_concepts.json"
RELATIONSHIP_FIXTURE = "staged_fetch_second_candidate_build_relationships.json"
TEST_QUESTION_ID = "rq_second_staged_relationship_spine"
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
    return tmp_path / "second_staged_relationship.sqlite"


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


def _run_spine_through_link(temp_db: Path, staging_dir: Path) -> str:
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
    return source_id


def test_second_staged_candidate_extract_link_build_relationships_spine(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
) -> None:
    source_id = _run_spine_through_link(temp_db, staging_dir)
    assert (
        main(
            [
                "build-relationships",
                "--source",
                source_id,
                "--fixture",
                RELATIONSHIP_FIXTURE,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        relationships = RelationshipRepository(conn).list_for_source(source_id)
        assert len(relationships) >= 1
        match = next(
            (
                rel
                for rel in relationships
                if rel["subject_concept"] == "constraint"
                and rel["object_concept"] == "human control"
                and rel["predicate"] == "may_increase"
            ),
            None,
        )
        assert match is not None
        assert match["scope"] == "AI-assisted creative team workflows"
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


def test_second_staged_candidate_build_relationships_idempotent(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_id = _run_spine_through_link(temp_db, staging_dir)
    build_args = [
        "build-relationships",
        "--source",
        source_id,
        "--fixture",
        RELATIONSHIP_FIXTURE,
        "--db",
        str(temp_db),
    ]
    capsys.readouterr()
    assert main(build_args) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["status"] == "completed"
    assert first["relationship_count"] >= 1

    conn = connect(temp_db)
    try:
        baseline = RelationshipRepository(conn).count_for_source(source_id)
    finally:
        conn.close()

    assert main(build_args) == 0
    second = json.loads(capsys.readouterr().out)
    assert second["status"] == "already_built"
    assert second["relationship_count"] == baseline

    conn = connect(temp_db)
    try:
        assert RelationshipRepository(conn).count_for_source(source_id) == baseline
    finally:
        conn.close()
