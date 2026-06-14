"""Phase 3 spine through generate-run-report on staged-ingested source (ticket-149)."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.db.connection import connect
from rge.db.repositories import RunReportRepository
from rge.modules.research_planner import GOLDEN_CONTRACT_ID

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
DOMAIN_BASE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
TEST_QUESTION_ID = "rq_staged_run_report_spine"
CANDIDATE_ID = "disc_openalex_W2741809807"
STAGED_CHUNK_TEXT = "Human-AI co-creativity supports diverse songwriting outputs."
SAMPLE_HTML = (
    f"<html><body><p>{STAGED_CHUNK_TEXT}</p></body></html>"
).encode("utf-8")
STAGED_RUN_ID = "run_staged_phase3_spine"
STAGED_TOPIC = "Human-AI co-creativity and semantic diversity (staged Phase 3 spine)"


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
    return tmp_path / "staged_run_report_spine.sqlite"


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


def _run_spine_through_reconcile_scores(temp_db: Path, staging_dir: Path) -> str:
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
    assert main(["detect-contradictions", "--source", source_id, "--db", str(temp_db)]) == 0
    assert main(["reconcile-scores", "--source", source_id, "--db", str(temp_db)]) == 0
    return source_id


def test_staged_spine_through_generate_run_report(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
) -> None:
    _run_spine_through_reconcile_scores(temp_db, staging_dir)
    assert (
        main(
            [
                "generate-run-report",
                "--run-id",
                STAGED_RUN_ID,
                "--topic",
                STAGED_TOPIC,
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

    conn = connect(temp_db)
    try:
        assert RunReportRepository(conn).count() == 1
        row = conn.execute(
            "SELECT run_id, topic, domain_pack, report_json FROM run_reports"
        ).fetchone()
        report = json.loads(row["report_json"])

        assert row["run_id"] == STAGED_RUN_ID
        assert row["topic"] == STAGED_TOPIC
        assert row["domain_pack"] == "creativity"
        assert report["report_type"] == "run_report"
        assert report["run_id"] == STAGED_RUN_ID
        assert report["topic"] == STAGED_TOPIC
        assert report["domain_pack"] == "creativity"
        assert report["contract_id"] == GOLDEN_CONTRACT_ID
        assert report["sources_discovered"] >= 2
        assert report["sources_ingested"] >= 2
        assert report["claims_accepted"] >= 3
        assert report["claims_rejected"] >= 1
        assert report["relationships_updated"] >= 2
        assert report["score_events_created"] >= 1
        assert report["tickets_generated"] == 0
        reasons = {item["reason"] for item in report["top_failure_modes"]}
        assert "missing_quote_span" in reasons

        research_run = conn.execute(
            "SELECT status FROM research_runs WHERE id = ?",
            (STAGED_RUN_ID,),
        ).fetchone()
        assert research_run is not None
    finally:
        conn.close()

    assert (report_dir / "run_report_latest.json").is_file()


def test_generate_run_report_staged_spine_is_idempotent(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
) -> None:
    _run_spine_through_reconcile_scores(temp_db, staging_dir)
    args = [
        "generate-run-report",
        "--run-id",
        STAGED_RUN_ID,
        "--topic",
        STAGED_TOPIC,
        "--domain",
        "creativity",
        "--db",
        str(temp_db),
        "--output-dir",
        str(report_dir),
    ]
    assert main(args) == 0
    assert main(args) == 0

    conn = connect(temp_db)
    try:
        assert RunReportRepository(conn).count() == 1
    finally:
        conn.close()


def test_generate_run_report_cli_json_for_staged_spine(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _run_spine_through_reconcile_scores(temp_db, staging_dir)
    capsys.readouterr()
    assert (
        main(
            [
                "generate-run-report",
                "--run-id",
                STAGED_RUN_ID,
                "--topic",
                STAGED_TOPIC,
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
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "generated"
    assert payload["command"] == "generate-run-report"
    assert payload["run_id"] == STAGED_RUN_ID
    assert payload["report_count"] == 1
    assert payload["report"]["score_events_created"] >= 1
