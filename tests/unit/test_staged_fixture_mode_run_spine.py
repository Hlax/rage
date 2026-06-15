"""Fixture-mode staged research run orchestration (ticket-162)."""

from __future__ import annotations

import io
import json
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
    html_queue = list(html_sequence)

    def _urlopen(request, timeout=30):  # noqa: ARG001
        url = request.full_url if hasattr(request, "full_url") else str(request)
        if "api.openalex.org" in url:
            return io.BytesIO(json.dumps(openalex_payload).encode("utf-8"))

        html = html_queue.pop(0) if html_queue else html_sequence[-1]

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
    result = execute_staged_fixture_mode_run(
        topic=STAGED_TOPIC,
        domain="creativity",
        db_path=temp_db,
        run_id=STAGED_FIXTURE_RUN_ID,
        report_dir=report_dir,
        staging_dir=staging_dir,
        question_id=STAGED_FIXTURE_QUESTION_ID,
    )

    assert result["status"] == "completed"
    assert result["mode"] == "fixture_staged"
    assert result["sources"] == 3
    assert result["candidate_sources"] == 2
    assert result["research_queue"] == 2
    assert result["score_events"] == 2
    assert result["run_reports"] == 2
    assert result["qualifies_evidence"] == 2
    assert result["rank1_accepted"] == 1
    assert result["rank1_rejected"] == 1
    assert result["rank2_accepted"] == 1
    assert result["rank2_rejected"] == 1
    assert result["rank1_relationships"] == 2
    assert result["rank2_relationships"] == 2


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
