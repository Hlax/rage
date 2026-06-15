"""Dual-candidate Phase 3 staged mock spine idempotency (ticket-161)."""

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
RANK1_CANDIDATE_ID = "disc_openalex_W2741809807"
RANK2_CANDIDATE_ID = "disc_openalex_W1234567890"
RANK1_HTML = (
    b"<html><body><p>Human-AI co-creativity supports diverse songwriting outputs.</p></body></html>"
)
RANK2_HTML = (
    b"<html><body><p>Constraint management improves AI-assisted creative team workflows.</p></body></html>"
)
RANK2_EXTRACT_FIXTURE = "staged_fetch_second_candidate_extract_claims.json"
RANK2_LINK_FIXTURE = "staged_fetch_second_candidate_link_concepts.json"
RANK2_RELATIONSHIP_FIXTURE = "staged_fetch_second_candidate_build_relationships.json"
RANK2_CONTRADICTION_FIXTURE = "staged_fetch_second_candidate_detect_contradictions.json"
TEST_QUESTION_ID = "rq_dual_staged_idempotency_spine"
RANK1_RUN_ID = "run_dual_staged_rank1_idempotency"
RANK1_TOPIC = "Rank #1 dual-candidate idempotency (staged Phase 3 spine)"
RANK2_RUN_ID = "run_dual_staged_rank2_idempotency"
RANK2_TOPIC = "Rank #2 dual-candidate idempotency (staged Phase 3 spine)"


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
    return tmp_path / "dual_staged_idempotency.sqlite"


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
class _DualCounts:
    sources: int
    candidate_sources: int
    research_queue: int
    score_events: int
    run_reports: int
    qualifies_evidence: int
    rank1_accepted: int
    rank1_rejected: int
    rank1_relationships: int
    rank2_accepted: int
    rank2_rejected: int
    rank2_relationships: int


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


def _fetch_args(temp_db: Path, staging_dir: Path, candidate_id: str) -> list[str]:
    return [
        "fetch-candidate",
        "--candidate",
        candidate_id,
        "--db",
        str(temp_db),
        "--out",
        str(staging_dir),
    ]


def _ingest_staged_args(temp_db: Path, staging_dir: Path, candidate_id: str) -> list[str]:
    return [
        "ingest-staged",
        "--domain",
        "creativity",
        "--candidate",
        candidate_id,
        "--staging-dir",
        str(staging_dir),
        "--db",
        str(temp_db),
    ]


def _rank1_source_id(temp_db: Path) -> str:
    conn = connect(temp_db)
    try:
        row = conn.execute(
            """
            SELECT id FROM sources
            WHERE title LIKE '%songwriting%'
            ORDER BY rowid DESC
            LIMIT 1
            """
        ).fetchone()
        assert row is not None
        return row["id"]
    finally:
        conn.close()


def _rank2_source_id(temp_db: Path) -> str:
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


def _relationships_for_source(temp_db: Path, source_id: str) -> int:
    conn = connect(temp_db)
    try:
        return conn.execute(
            """
            SELECT COUNT(DISTINCT r.id)
            FROM relationships r
            JOIN relationship_evidence re ON re.relationship_id = r.id
            JOIN claims c ON c.id = re.claim_id
            WHERE c.source_id = ?
            """,
            (source_id,),
        ).fetchone()[0]
    finally:
        conn.close()


def _dual_counts(temp_db: Path, rank1_id: str, rank2_id: str) -> _DualCounts:
    conn = connect(temp_db)
    try:
        rank1_accepted = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ? AND status = 'accepted'",
            (rank1_id,),
        ).fetchone()[0]
        rank1_rejected = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ? AND status = 'rejected'",
            (rank1_id,),
        ).fetchone()[0]
        rank2_accepted = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ? AND status = 'accepted'",
            (rank2_id,),
        ).fetchone()[0]
        rank2_rejected = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ? AND status = 'rejected'",
            (rank2_id,),
        ).fetchone()[0]
        return _DualCounts(
            sources=conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0],
            candidate_sources=conn.execute(
                "SELECT COUNT(*) FROM candidate_sources"
            ).fetchone()[0],
            research_queue=conn.execute(
                "SELECT COUNT(*) FROM research_queue"
            ).fetchone()[0],
            score_events=conn.execute("SELECT COUNT(*) FROM score_events").fetchone()[0],
            run_reports=RunReportRepository(conn).count(),
            qualifies_evidence=conn.execute(
                "SELECT COUNT(*) FROM relationship_evidence WHERE stance = 'qualifies'"
            ).fetchone()[0],
            rank1_accepted=rank1_accepted,
            rank1_rejected=rank1_rejected,
            rank1_relationships=_relationships_for_source(temp_db, rank1_id),
            rank2_accepted=rank2_accepted,
            rank2_rejected=rank2_rejected,
            rank2_relationships=_relationships_for_source(temp_db, rank2_id),
        )
    finally:
        conn.close()


def _discover_candidates(temp_db: Path) -> None:
    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text())
    with patch(
        "rge.modules.source_providers.openalex.urllib.request.urlopen",
        _mock_urlopen_factory(fixture_payload),
    ):
        assert main(_discover_args(temp_db)) == 0


def _run_rank1_spine(temp_db: Path, staging_dir: Path, report_dir: Path) -> str:
    with patch(
        "rge.modules.fetcher.urllib.request.urlopen",
        _mock_html_urlopen(RANK1_HTML),
    ):
        assert main(_fetch_args(temp_db, staging_dir, RANK1_CANDIDATE_ID)) == 0

    assert main(_ingest_staged_args(temp_db, staging_dir, RANK1_CANDIDATE_ID)) == 0
    source_id = _rank1_source_id(temp_db)

    assert main(["extract-claims", "--source", source_id, "--db", str(temp_db)]) == 0
    assert main(["link-concepts", "--source", source_id, "--db", str(temp_db)]) == 0
    assert main(["build-relationships", "--source", source_id, "--db", str(temp_db)]) == 0
    assert main(["detect-contradictions", "--source", source_id, "--db", str(temp_db)]) == 0
    assert main(["reconcile-scores", "--source", source_id, "--db", str(temp_db)]) == 0
    assert (
        main(
            [
                "generate-run-report",
                "--run-id",
                RANK1_RUN_ID,
                "--topic",
                RANK1_TOPIC,
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
                "--output-dir",
                str(report_dir),
            ]
        )
        == 0
    )
    return source_id


def _run_rank2_spine(temp_db: Path, staging_dir: Path, report_dir: Path) -> str:
    with patch(
        "rge.modules.fetcher.urllib.request.urlopen",
        _mock_html_urlopen(RANK2_HTML),
    ):
        assert main(_fetch_args(temp_db, staging_dir, RANK2_CANDIDATE_ID)) == 0

    assert main(_ingest_staged_args(temp_db, staging_dir, RANK2_CANDIDATE_ID)) == 0
    source_id = _rank2_source_id(temp_db)

    assert (
        main(
            [
                "extract-claims",
                "--source",
                source_id,
                "--fixture",
                RANK2_EXTRACT_FIXTURE,
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
                RANK2_LINK_FIXTURE,
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
                RANK2_RELATIONSHIP_FIXTURE,
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
                RANK2_CONTRADICTION_FIXTURE,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    assert main(["reconcile-scores", "--source", source_id, "--db", str(temp_db)]) == 0
    assert (
        main(
            [
                "generate-run-report",
                "--run-id",
                RANK2_RUN_ID,
                "--topic",
                RANK2_TOPIC,
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
                "--output-dir",
                str(report_dir),
            ]
        )
        == 0
    )
    return source_id


def _run_dual_spine(
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    *,
    seed_domain: bool,
) -> tuple[str, str]:
    if seed_domain:
        _seed_domain_opposing_context(temp_db)
    _discover_candidates(temp_db)
    rank1_id = _run_rank1_spine(temp_db, staging_dir, report_dir)
    rank2_id = _run_rank2_spine(temp_db, staging_dir, report_dir)
    return rank1_id, rank2_id


def test_dual_candidate_staged_spine_twice_is_idempotent(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
) -> None:
    rank1_id, rank2_id = _run_dual_spine(
        temp_db, staging_dir, report_dir, seed_domain=True
    )
    first = _dual_counts(temp_db, rank1_id, rank2_id)

    assert first.sources == 3
    assert first.candidate_sources == 2
    assert first.research_queue == 2
    assert first.rank1_accepted == 1
    assert first.rank1_rejected == 1
    assert first.rank2_accepted == 1
    assert first.rank2_rejected == 1
    assert first.rank1_relationships == 2
    assert first.rank2_relationships == 2
    assert first.score_events == 2
    assert first.run_reports == 2
    assert first.qualifies_evidence == 2

    _run_dual_spine(temp_db, staging_dir, report_dir, seed_domain=False)
    second = _dual_counts(temp_db, rank1_id, rank2_id)
    assert second == first


def test_dual_candidate_per_command_spot_check_is_idempotent(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
) -> None:
    rank1_id, rank2_id = _run_dual_spine(
        temp_db, staging_dir, report_dir, seed_domain=True
    )
    baseline = _dual_counts(temp_db, rank1_id, rank2_id)

    _discover_candidates(temp_db)
    assert _dual_counts(temp_db, rank1_id, rank2_id) == baseline

    with patch(
        "rge.modules.fetcher.urllib.request.urlopen",
        _mock_html_urlopen(RANK1_HTML),
    ):
        assert main(_fetch_args(temp_db, staging_dir, RANK1_CANDIDATE_ID)) == 0
    assert _dual_counts(temp_db, rank1_id, rank2_id) == baseline

    with patch(
        "rge.modules.fetcher.urllib.request.urlopen",
        _mock_html_urlopen(RANK2_HTML),
    ):
        assert main(_fetch_args(temp_db, staging_dir, RANK2_CANDIDATE_ID)) == 0
    assert _dual_counts(temp_db, rank1_id, rank2_id) == baseline

    assert main(["extract-claims", "--source", rank1_id, "--db", str(temp_db)]) == 0
    assert (
        main(
            [
                "extract-claims",
                "--source",
                rank2_id,
                "--fixture",
                RANK2_EXTRACT_FIXTURE,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    assert _dual_counts(temp_db, rank1_id, rank2_id) == baseline

    assert main(["reconcile-scores", "--source", rank1_id, "--db", str(temp_db)]) == 0
    assert main(["reconcile-scores", "--source", rank2_id, "--db", str(temp_db)]) == 0
    assert _dual_counts(temp_db, rank1_id, rank2_id) == baseline
