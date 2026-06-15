"""Idempotency proof for Phase 3 rank #2 staged mock spine (ticket-160)."""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.db.connection import connect
from rge.db.repositories import RunReportRepository

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
DOMAIN_BASE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
EXTRACT_FIXTURE = "staged_fetch_second_candidate_extract_claims.json"
LINK_FIXTURE = "staged_fetch_second_candidate_link_concepts.json"
RELATIONSHIP_FIXTURE = "staged_fetch_second_candidate_build_relationships.json"
CONTRADICTION_FIXTURE = "staged_fetch_second_candidate_detect_contradictions.json"
TEST_QUESTION_ID = "rq_second_staged_idempotency_spine"
SECOND_CANDIDATE_ID = "disc_openalex_W1234567890"
SECOND_HTML = (
    b"<html><body><p>Constraint management improves AI-assisted creative team workflows.</p></body></html>"
)
SECOND_STAGED_RUN_ID = "run_second_staged_phase3_idempotency"
SECOND_STAGED_TOPIC = (
    "Constraint management idempotency (rank #2 staged Phase 3 spine)"
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
    return tmp_path / "second_staged_idempotency.sqlite"


@pytest.fixture()
def staging_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "staged"
    directory.mkdir()
    return directory


@pytest.fixture()
def report_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "reports"
    directory.mkdir()
    return directory


@dataclass(frozen=True)
class _SpineCounts:
    sources: int
    candidate_sources: int
    research_queue: int
    accepted_claims_staged: int
    rejected_claims_staged: int
    concept_links_staged: int
    relationships_staged: int
    score_events: int
    run_reports: int
    qualifies_evidence: int


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


def _staged_source_id(temp_db: Path) -> str:
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


def _spine_counts(temp_db: Path, staged_source_id: str) -> _SpineCounts:
    conn = connect(temp_db)
    try:
        sources = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        candidate_sources = conn.execute(
            "SELECT COUNT(*) FROM candidate_sources"
        ).fetchone()[0]
        research_queue = conn.execute(
            "SELECT COUNT(*) FROM research_queue"
        ).fetchone()[0]
        accepted = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ? AND status = 'accepted'",
            (staged_source_id,),
        ).fetchone()[0]
        rejected = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ? AND status = 'rejected'",
            (staged_source_id,),
        ).fetchone()[0]
        links = conn.execute(
            """
            SELECT COUNT(*) FROM claim_concepts
            WHERE claim_id IN (SELECT id FROM claims WHERE source_id = ?)
            """,
            (staged_source_id,),
        ).fetchone()[0]
        relationships = conn.execute(
            """
            SELECT COUNT(DISTINCT r.id)
            FROM relationships r
            JOIN relationship_evidence re ON re.relationship_id = r.id
            JOIN claims c ON c.id = re.claim_id
            WHERE c.source_id = ?
            """,
            (staged_source_id,),
        ).fetchone()[0]
        score_events = conn.execute("SELECT COUNT(*) FROM score_events").fetchone()[0]
        run_reports = RunReportRepository(conn).count()
        qualifies = conn.execute(
            "SELECT COUNT(*) FROM relationship_evidence WHERE stance = 'qualifies'"
        ).fetchone()[0]
        return _SpineCounts(
            sources=sources,
            candidate_sources=candidate_sources,
            research_queue=research_queue,
            accepted_claims_staged=accepted,
            rejected_claims_staged=rejected,
            concept_links_staged=links,
            relationships_staged=relationships,
            score_events=score_events,
            run_reports=run_reports,
            qualifies_evidence=qualifies,
        )
    finally:
        conn.close()


def _discover_args(temp_db: Path) -> list[str]:
    return [
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


def _fetch_args(temp_db: Path, staging_dir: Path) -> list[str]:
    return [
        "fetch-candidate",
        "--candidate",
        SECOND_CANDIDATE_ID,
        "--db",
        str(temp_db),
        "--out",
        str(staging_dir),
    ]


def _ingest_staged_args(temp_db: Path, staging_dir: Path) -> list[str]:
    return [
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


def _generate_run_report_args(temp_db: Path, report_dir: Path) -> list[str]:
    return [
        "generate-run-report",
        "--run-id",
        SECOND_STAGED_RUN_ID,
        "--topic",
        SECOND_STAGED_TOPIC,
        "--domain",
        "creativity",
        "--db",
        str(temp_db),
        "--output-dir",
        str(report_dir),
    ]


def _run_full_spine(
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
) -> str:
    _seed_domain_opposing_context(temp_db)
    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text())

    with patch(
        "rge.modules.source_providers.openalex.urllib.request.urlopen",
        _mock_urlopen_factory(fixture_payload),
    ):
        assert main(_discover_args(temp_db)) == 0

    with patch(
        "rge.modules.fetcher.urllib.request.urlopen",
        _mock_html_urlopen(SECOND_HTML),
    ):
        assert main(_fetch_args(temp_db, staging_dir)) == 0

    assert main(_ingest_staged_args(temp_db, staging_dir)) == 0
    source_id = _staged_source_id(temp_db)

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
    assert (
        main(
            [
                "detect-contradictions",
                "--source",
                source_id,
                "--fixture",
                CONTRADICTION_FIXTURE,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    assert main(["reconcile-scores", "--source", source_id, "--db", str(temp_db)]) == 0
    assert main(_generate_run_report_args(temp_db, report_dir)) == 0
    return source_id


def test_second_staged_phase3_full_spine_twice_is_idempotent(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
) -> None:
    source_id = _run_full_spine(temp_db, staging_dir, report_dir)
    first = _spine_counts(temp_db, source_id)

    assert first.sources == 2
    assert first.candidate_sources == 2
    assert first.research_queue == 2
    assert first.accepted_claims_staged == 1
    assert first.rejected_claims_staged == 1
    assert first.concept_links_staged == 3
    assert first.relationships_staged == 2
    assert first.score_events == 1
    assert first.run_reports == 1
    assert first.qualifies_evidence == 1

    _run_full_spine(temp_db, staging_dir, report_dir)
    second = _spine_counts(temp_db, source_id)
    assert second == first


def test_second_staged_phase3_per_command_reruns_are_idempotent(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
) -> None:
    source_id = _run_full_spine(temp_db, staging_dir, report_dir)
    baseline = _spine_counts(temp_db, source_id)
    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text())

    with patch(
        "rge.modules.source_providers.openalex.urllib.request.urlopen",
        _mock_urlopen_factory(fixture_payload),
    ):
        assert main(_discover_args(temp_db)) == 0
    assert _spine_counts(temp_db, source_id) == baseline

    with patch(
        "rge.modules.fetcher.urllib.request.urlopen",
        _mock_html_urlopen(SECOND_HTML),
    ):
        assert main(_fetch_args(temp_db, staging_dir)) == 0
    assert _spine_counts(temp_db, source_id) == baseline

    assert main(_ingest_staged_args(temp_db, staging_dir)) == 0
    assert _spine_counts(temp_db, source_id) == baseline

    for command in (
        [
            "extract-claims",
            "--source",
            source_id,
            "--fixture",
            EXTRACT_FIXTURE,
            "--db",
            str(temp_db),
        ],
        [
            "link-concepts",
            "--source",
            source_id,
            "--fixture",
            LINK_FIXTURE,
            "--db",
            str(temp_db),
        ],
        [
            "build-relationships",
            "--source",
            source_id,
            "--fixture",
            RELATIONSHIP_FIXTURE,
            "--db",
            str(temp_db),
        ],
        [
            "detect-contradictions",
            "--source",
            source_id,
            "--fixture",
            CONTRADICTION_FIXTURE,
            "--db",
            str(temp_db),
        ],
        ["reconcile-scores", "--source", source_id, "--db", str(temp_db)],
        _generate_run_report_args(temp_db, report_dir),
    ):
        assert main(command) == 0
        assert _spine_counts(temp_db, source_id) == baseline
