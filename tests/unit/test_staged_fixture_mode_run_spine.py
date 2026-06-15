"""Fixture-mode staged research run orchestration (ticket-162)."""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from itertools import cycle
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import (
    STAGED_FIXTURE_QUESTION_ID,
    STAGED_FIXTURE_RUN_ID,
    execute_staged_fixture_mode_run,
    main,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
RANK1_HTML = (
    b"<html><body><p>Human-AI co-creativity supports diverse songwriting outputs.</p></body></html>"
)
RANK2_HTML = (
    b"<html><body><p>Constraint management improves AI-assisted creative team workflows.</p></body></html>"
)
STAGED_TOPIC = "Staged fixture-mode run orchestration spine (mock)"


@dataclass(frozen=True)
class _OrchestratorCounts:
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


def _orchestrator_counts(result: dict) -> _OrchestratorCounts:
    return _OrchestratorCounts(
        sources=result["sources"],
        candidate_sources=result["candidate_sources"],
        research_queue=result["research_queue"],
        score_events=result["score_events"],
        run_reports=result["run_reports"],
        qualifies_evidence=result["qualifies_evidence"],
        rank1_accepted=result["rank1_accepted"],
        rank1_rejected=result["rank1_rejected"],
        rank1_relationships=result["rank1_relationships"],
        rank2_accepted=result["rank2_accepted"],
        rank2_rejected=result["rank2_rejected"],
        rank2_relationships=result["rank2_relationships"],
    )


def _run_staged_orchestrator(
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
) -> dict:
    return execute_staged_fixture_mode_run(
        topic=STAGED_TOPIC,
        domain="creativity",
        db_path=temp_db,
        run_id=STAGED_FIXTURE_RUN_ID,
        report_dir=report_dir,
        staging_dir=staging_dir,
        question_id=STAGED_FIXTURE_QUESTION_ID,
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
    monkeypatch.delenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", raising=False)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "staged_fixture_mode_run.sqlite"


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


def _staged_network_urlopen(openalex_payload: dict, html_sequence: list[bytes]):
    html_cycle = cycle(html_sequence)

    def _urlopen(request, timeout=30):  # noqa: ARG001
        url = request.full_url if hasattr(request, "full_url") else str(request)
        if "api.openalex.org" in url:
            return io.BytesIO(json.dumps(openalex_payload).encode("utf-8"))

        html = next(html_cycle)

        class _Response(io.BytesIO):
            headers = {"Content-Type": "text/html; charset=utf-8"}

        return _Response(html)

    return _urlopen


@pytest.fixture()
def patched_staged_network():
    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text())
    urlopen = _staged_network_urlopen(fixture_payload, [RANK1_HTML, RANK2_HTML])
    with patch(
        "rge.modules.source_providers.openalex.urllib.request.urlopen",
        urlopen,
    ), patch(
        "rge.modules.fetcher.urllib.request.urlopen",
        urlopen,
    ):
        yield


def test_execute_staged_fixture_mode_run_matches_dual_spine_counts(
    mock_network_env: None,
    patched_staged_network: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
) -> None:
    result = _run_staged_orchestrator(temp_db, staging_dir, report_dir)

    assert result["status"] == "completed"
    assert result["mode"] == "fixture_staged"
    assert _orchestrator_counts(result) == _OrchestratorCounts(
        sources=3,
        candidate_sources=2,
        research_queue=2,
        score_events=2,
        run_reports=2,
        qualifies_evidence=2,
        rank1_accepted=1,
        rank1_rejected=1,
        rank1_relationships=2,
        rank2_accepted=1,
        rank2_rejected=1,
        rank2_relationships=2,
    )


def test_execute_staged_fixture_mode_run_twice_is_idempotent(
    mock_network_env: None,
    patched_staged_network: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
) -> None:
    first = _orchestrator_counts(
        _run_staged_orchestrator(temp_db, staging_dir, report_dir)
    )
    second = _orchestrator_counts(
        _run_staged_orchestrator(temp_db, staging_dir, report_dir)
    )
    assert second == first


def test_staged_fixture_mode_run_cli_entry(
    mock_network_env: None,
    patched_staged_network: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
) -> None:
    exit_code = main(
        [
            "run",
            "--fixture-mode",
            "--staged-spine",
            "--topic",
            STAGED_TOPIC,
            "--domain",
            "creativity",
            "--db",
            str(temp_db),
            "--staging-dir",
            str(staging_dir),
            "--output-dir",
            str(report_dir),
            "--run-id",
            STAGED_FIXTURE_RUN_ID,
            "--question-id",
            STAGED_FIXTURE_QUESTION_ID,
        ]
    )
    assert exit_code == 0
