"""Opt-in live network + single-command staged orchestrator (ticket-193).

Default pytest collection excludes ``live_network`` tests (see ``pyproject.toml``).

Operator opt-in (real OpenAlex HTTP; mock fixtures after live ingest):

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_orchestrator_mock_spine.py -m live_network -q
```
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.cli import STAGED_FIXTURE_RUN_ID, main

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_QUESTION_ID = "rq_live_staged_orchestrator_mock_spine"
STAGED_RUN_ID = "run_live_staged_orchestrator_mock_spine"
STAGED_TOPIC = "Live staged orchestrator mock spine (single-command proof)"


def require_live_staged_orchestrator_env() -> None:
    """Skip unless operator explicitly opts into live staged orchestrator proof."""
    allow = os.environ.get("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", "0").strip().casefold()
    if allow not in ("1", "true", "yes"):
        pytest.skip(
            "live staged orchestrator requires RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=1"
        )
    network = os.environ.get("RGE_ALLOW_SOURCE_NETWORK", "0").strip().casefold()
    if network not in ("1", "true", "yes"):
        pytest.skip("live staged orchestrator requires RGE_ALLOW_SOURCE_NETWORK=1")
    if not os.environ.get("OPENALEX_MAILTO", "").strip():
        pytest.skip("live staged orchestrator requires OPENALEX_MAILTO")


def test_require_live_staged_orchestrator_skips_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", raising=False)
    with pytest.raises(pytest.skip.Exception):
        require_live_staged_orchestrator_env()


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def live_staged_orchestrator_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "live_staged_orchestrator_mock.sqlite"


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


@pytest.mark.live_network
def test_live_staged_fixture_mode_orchestrator_dual_spine(
    live_staged_orchestrator_env: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    require_live_staged_orchestrator_env()

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
            STAGED_RUN_ID,
            "--question-id",
            TEST_QUESTION_ID,
        ]
    )
    assert exit_code == 0

    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "completed"
    assert result["mode"] == "fixture_staged"
    assert result["question_id"] == TEST_QUESTION_ID
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
    assert (report_dir / "run_report_latest.json").is_file()
