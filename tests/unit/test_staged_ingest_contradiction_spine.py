"""Phase 3 spine through detect-contradictions on staged-ingested source (ticket-147)."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.db.connection import connect
from rge.db.repositories import RelationshipRepository
from rge.modules.contradiction_detector import _default_contradiction_fixture_for_source

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
DOMAIN_BASE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
TEST_QUESTION_ID = "rq_staged_contradiction_spine"
CANDIDATE_ID = "disc_openalex_W2741809807"
STAGED_CHUNK_TEXT = "Human-AI co-creativity supports diverse songwriting outputs."
SAMPLE_HTML = (
    f"<html><body><p>{STAGED_CHUNK_TEXT}</p></body></html>"
).encode("utf-8")
STAGED_TITLE = "Human-AI co-creativity and semantic diversity in songwriting workshops"
CLASSIFICATION = "apparent_contradiction_metric_or_condition_difference"


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
    return tmp_path / "staged_contradiction_spine.sqlite"


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


def _seed_domain_opposing_context(temp_db: Path) -> None:
    """Seed GT7-style base graph so staged qualification has an opposing domain edge."""
    assert (
        main(
            [
                "ingest",
                str(DOMAIN_BASE_SOURCE),
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    conn = connect(temp_db)
    try:
        base_source_id = conn.execute("SELECT id FROM sources").fetchone()["id"]
    finally:
        conn.close()
    assert main(["extract-claims", "--source", base_source_id, "--db", str(temp_db)]) == 0
    assert main(["link-concepts", "--source", base_source_id, "--db", str(temp_db)]) == 0
    assert main(["build-relationships", "--source", base_source_id, "--db", str(temp_db)]) == 0


def _run_spine_through_build_relationships(temp_db: Path, staging_dir: Path) -> str:
    _seed_domain_opposing_context(temp_db)

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
        source_id = conn.execute(
            """
            SELECT id FROM sources
            WHERE title LIKE '%songwriting%'
            ORDER BY rowid DESC
            LIMIT 1
            """
        ).fetchone()["id"]
    finally:
        conn.close()

    assert main(["extract-claims", "--source", source_id, "--db", str(temp_db)]) == 0
    assert main(["link-concepts", "--source", source_id, "--db", str(temp_db)]) == 0
    assert main(["build-relationships", "--source", source_id, "--db", str(temp_db)]) == 0
    return source_id


def test_default_contradiction_fixture_for_staged_spine_source() -> None:
    class _Source:
        title = STAGED_TITLE
        source_type = "peer_reviewed_empirical"

    assert (
        _default_contradiction_fixture_for_source(_Source())
        == "staged_fetch_detect_contradictions.json"
    )


def test_staged_spine_through_detect_contradictions(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
) -> None:
    source_id = _run_spine_through_build_relationships(temp_db, staging_dir)
    assert main(["detect-contradictions", "--source", source_id, "--db", str(temp_db)]) == 0

    conn = connect(temp_db)
    try:
        qualifications = conn.execute(
            """
            SELECT re.stance, re.claim_id, r.domain_metadata_json
            FROM relationship_evidence re
            JOIN relationships r ON r.id = re.relationship_id
            WHERE re.stance = 'qualifies'
            """
        ).fetchall()
        assert len(qualifications) >= 1
        row = qualifications[0]
        assert row["stance"] == "qualifies"
        metadata = json.loads(row["domain_metadata_json"])
        assert metadata.get("contradiction_classification") == CLASSIFICATION

        active = RelationshipRepository(conn).list_active()
        assert any(
            rel["subject_concept"] == "co-creation"
            and rel["predicate"] == "may_increase"
            and rel["object_concept"] == "semantic diversity"
            for rel in active
        )
        assert any(
            rel["subject_concept"] == "AI assistance"
            and rel["predicate"] == "may_reduce"
            and rel["object_concept"] == "semantic diversity"
            for rel in active
        )
    finally:
        conn.close()


def test_detect_contradictions_explicit_staged_fixture(
    temp_db: Path,
    staging_dir: Path,
    mock_network_env: None,
) -> None:
    source_id = _run_spine_through_build_relationships(temp_db, staging_dir)
    assert main(
        [
            "detect-contradictions",
            "--source",
            source_id,
            "--fixture",
            "staged_fetch_detect_contradictions.json",
            "--db",
            str(temp_db),
        ]
    ) == 0

    conn = connect(temp_db)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM relationship_evidence WHERE stance = 'qualifies'"
        ).fetchone()[0]
        assert count >= 1
    finally:
        conn.close()
