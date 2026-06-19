"""Smoke tests for staged spine CLI candidate-id wiring (ticket-260)."""

from __future__ import annotations

import io
import json
from itertools import cycle
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import (
    STAGED_FIXTURE_QUESTION_ID,
    STAGED_FIXTURE_RUN_ID,
    STAGED_RANK1_CANDIDATE_ID,
    STAGED_RANK2_CANDIDATE_ID,
    execute_staged_fixture_mode_run,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
RANK1_HTML = (
    b"<html><body><p>Human-AI co-creativity supports diverse songwriting outputs.</p></body></html>"
)
RANK2_HTML = (
    b"<html><body><p>Constraint management improves AI-assisted creative team workflows.</p></body></html>"
)
STAGED_TOPIC = "Staged spine CLI candidate-id wiring smoke test (mock)"


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


def _fetch_candidate_ids_from_steps(recorded_steps: list[list[str]]) -> list[str]:
    candidate_ids: list[str] = []
    for argv in recorded_steps:
        if argv and argv[0] == "fetch-candidate" and "--candidate" in argv:
            candidate_ids.append(argv[argv.index("--candidate") + 1])
    return candidate_ids


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
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", "0")


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


def _run_with_recorded_cli_steps(
    *,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
) -> list[list[str]]:
    recorded_steps: list[list[str]] = []
    import rge.cli as cli_module

    original = cli_module._run_cli_step

    def _recording_run_cli_step(argv: list[str]) -> None:
        recorded_steps.append(list(argv))
        return original(argv)

    with patch.object(cli_module, "_run_cli_step", side_effect=_recording_run_cli_step):
        result = execute_staged_fixture_mode_run(
            topic=STAGED_TOPIC,
            domain="creativity",
            db_path=temp_db,
            run_id=STAGED_FIXTURE_RUN_ID,
            report_dir=report_dir,
            staging_dir=staging_dir,
            question_id=STAGED_FIXTURE_QUESTION_ID,
        )
    return recorded_steps, result


def test_fixture_staged_run_wires_default_candidate_ids(
    mock_network_env: None,
    patched_staged_network: None,
    tmp_path: Path,
) -> None:
    temp_db = tmp_path / "staged_candidate_wiring_default.sqlite"
    staging_dir = tmp_path / "staged"
    report_dir = tmp_path / "reports"
    staging_dir.mkdir()
    report_dir.mkdir()

    recorded_steps, result = _run_with_recorded_cli_steps(
        temp_db=temp_db,
        staging_dir=staging_dir,
        report_dir=report_dir,
    )

    assert _fetch_candidate_ids_from_steps(recorded_steps) == [
        STAGED_RANK1_CANDIDATE_ID,
        STAGED_RANK2_CANDIDATE_ID,
    ]
    assert result["rank1_candidate_id"] == STAGED_RANK1_CANDIDATE_ID
    assert result["rank2_candidate_id"] == STAGED_RANK2_CANDIDATE_ID


def test_fixture_staged_run_live_orchestrator_wires_heuristic_candidate_ids(
    mock_network_env: None,
    patched_staged_network: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", "1")
    temp_db = tmp_path / "staged_candidate_wiring_live.sqlite"
    staging_dir = tmp_path / "staged"
    report_dir = tmp_path / "reports"
    staging_dir.mkdir()
    report_dir.mkdir()

    recorded_steps, result = _run_with_recorded_cli_steps(
        temp_db=temp_db,
        staging_dir=staging_dir,
        report_dir=report_dir,
    )

    assert _fetch_candidate_ids_from_steps(recorded_steps) == [
        STAGED_RANK2_CANDIDATE_ID,
    ]
    assert result["status"] == "completed"
    assert result["mode"] == "fixture_staged"
    assert result["rank1_candidate_id"] == STAGED_RANK1_CANDIDATE_ID
    assert result["rank2_candidate_id"] == STAGED_RANK2_CANDIDATE_ID
