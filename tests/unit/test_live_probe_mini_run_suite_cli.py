"""Unit tests for live probe-mini-run-suite CLI (mock-only; no Ollama required)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.llm.mock_client import MockModelClient
from rge.modules.live_probe import (
    MINI_RUN_SUITE_FIXTURES,
    LiveProbeError,
    assert_live_probe_env,
    mini_run_floors_met,
    mini_run_stage_floor_met,
    resolve_mini_run_suite_fixtures,
    run_probe_mini_run_suite,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _set_live_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")


def test_assert_live_probe_env_accepts_probe_mini_run_suite_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_live_env(monkeypatch)
    cfg = assert_live_probe_env(command="probe-mini-run-suite")
    assert cfg.llm_mode == "ollama"


def test_resolve_mini_run_suite_fixtures_defaults_to_four_committed_sources() -> None:
    fixtures = resolve_mini_run_suite_fixtures(None, root=REPO_ROOT)
    assert len(fixtures) == len(MINI_RUN_SUITE_FIXTURES)
    for fixture in fixtures:
        assert fixture.is_file()


def test_mini_run_stage_floor_met_strict_chain_skipped_contradiction() -> None:
    assert mini_run_stage_floor_met(
        "contradiction_detection",
        {"status": "skipped", "accepted_count": 0},
        strict_chain=True,
    )
    assert not mini_run_stage_floor_met(
        "contradiction_detection",
        {"status": "skipped", "accepted_count": 0},
        strict_chain=False,
    )


def test_cli_probe_mini_run_suite_refuses_without_live_opt_in(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "0")
    exit_code = main(["probe-mini-run-suite"])
    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "probe-mini-run-suite"


def test_run_probe_mini_run_suite_writes_summary_and_individual_reports(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_live_env(monkeypatch)
    reports_dir = tmp_path / "live_probes"
    mock_client = MockModelClient()

    with patch("rge.db.connection.connect") as connect:
        with patch("rge.db.connection.ensure_database") as ensure_db:
            report = run_probe_mini_run_suite(
                fixture_sources=[MINI_RUN_SUITE_FIXTURES[0]],
                root=REPO_ROOT,
                reports_dir=reports_dir,
                client=mock_client,
                skip_health_check=True,
            )
            connect.assert_not_called()
            ensure_db.assert_not_called()

    assert report["status"] == "ok"
    assert report["command"] == "probe-mini-run-suite"
    assert report["fixture_count"] == 1
    assert report["fixtures_passed"] == 1
    assert report["fixtures_failed"] == 0
    assert report["db_writes"] is False
    assert report["public_export"] is False
    assert report["cloud_calls"] is False
    assert len(report["runs"]) == 1
    assert report["runs"][0]["floors_met"] is True
    mini_reports = [
        path
        for path in reports_dir.glob("probe_mini_run_*.json")
        if "suite" not in path.name
    ]
    assert len(mini_reports) == 1
    assert len(list(reports_dir.glob("probe_mini_run_suite_*.json"))) == 1


def test_run_probe_mini_run_suite_records_fixture_error_as_partial(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_live_env(monkeypatch)
    reports_dir = tmp_path / "live_probes"
    from rge.modules import live_probe as live_probe_module

    original_mini_run = live_probe_module.run_probe_mini_run

    def _fake_mini_run(**kwargs: object) -> dict[str, object]:
        fixture = kwargs.get("fixture_source")
        if fixture and "followup" in str(fixture):
            raise LiveProbeError("simulated stage failure")
        return original_mini_run(**kwargs)  # type: ignore[arg-type]

    with patch.object(
        live_probe_module,
        "run_probe_mini_run",
        side_effect=_fake_mini_run,
    ):
        report = run_probe_mini_run_suite(
            root=REPO_ROOT,
            reports_dir=reports_dir,
            client=MockModelClient(),
            skip_health_check=True,
        )

    assert report["fixture_count"] == len(MINI_RUN_SUITE_FIXTURES)
    assert report["status"] == "partial"
    assert report["fixtures_failed"] >= 1
    errors = [entry for entry in report["runs"] if entry.get("error")]
    assert errors


def test_mini_run_floors_met_requires_stage_four_in_default_mode() -> None:
    report = {
        "strict_chain": False,
        "stages": {
            "claim_extraction": {"accepted_count": 1},
            "concept_linking": {"accepted_count": 1},
            "relationship_drafting": {"accepted_count": 1},
            "contradiction_detection": {"accepted_count": 0, "status": "ok"},
        },
    }
    assert not mini_run_floors_met(report)


def test_cli_probe_mini_run_suite_success_with_mock_client(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_live_env(monkeypatch)
    reports_dir = tmp_path / "live_probes"
    calibration = str(MINI_RUN_SUITE_FIXTURES[0].relative_to(REPO_ROOT)).replace("\\", "/")

    with patch("rge.modules.live_probe.live_probes_dir", return_value=reports_dir):
        with patch("rge.modules.live_probe.assert_ollama_health") as health:
            health.return_value = {"reachable": True, "model_available": True}
            with patch(
                "rge.modules.live_probe.get_model_client",
                return_value=MockModelClient(),
            ):
                exit_code = main(
                    [
                        "probe-mini-run-suite",
                        "--fixture-source",
                        calibration,
                    ]
                )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert payload["fixture_count"] == 1
    assert len(list(reports_dir.glob("probe_mini_run_suite_*.json"))) == 1
