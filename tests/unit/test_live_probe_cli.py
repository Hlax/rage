"""Unit tests for live probe-extract-claims CLI (mock-only; no Ollama required)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rge.cli import main
from rge.llm.mock_client import MockModelClient
from rge.modules.live_probe import (
    LiveProbeGateError,
    assert_live_probe_env,
    run_probe_extract_claims,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE = (
    REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
)


def _set_live_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")


def test_assert_live_probe_env_refuses_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "0")
    with pytest.raises(LiveProbeGateError, match="RGE_ALLOW_LIVE_LLM"):
        assert_live_probe_env()


def test_assert_live_probe_env_refuses_mock_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")
    with pytest.raises(LiveProbeGateError, match="RGE_LLM_MODE=ollama"):
        assert_live_probe_env()


def test_cli_probe_refuses_without_live_opt_in(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "0")
    exit_code = main(["probe-extract-claims"])
    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert payload["command"] == "probe-extract-claims"


def test_cli_probe_refuses_when_model_unavailable(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _set_live_env(monkeypatch)
    with patch("rge.modules.live_probe.get_model_client") as get_client:
        client = MagicMock()
        client.health_check.return_value = {
            "reachable": True,
            "model_available": False,
            "action_hint": "ollama pull qwen2.5:7b",
        }
        get_client.return_value = client
        exit_code = main(["probe-extract-claims"])
    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out)
    assert "ollama pull" in payload["detail"]


def test_cli_probe_refuses_when_ollama_unreachable(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _set_live_env(monkeypatch)
    with patch("rge.modules.live_probe.get_model_client") as get_client:
        client = MagicMock()
        client.health_check.return_value = {
            "reachable": False,
            "model_available": False,
            "action_hint": "Ollama not reachable",
        }
        get_client.return_value = client
        exit_code = main(["probe-extract-claims"])
    assert exit_code == 2
    assert "reachable" in json.loads(capsys.readouterr().out)["detail"].lower()


def test_run_probe_writes_report_without_db(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_live_env(monkeypatch)
    reports_dir = tmp_path / "live_probes"
    mock_client = MockModelClient()

    with patch("rge.db.connection.connect") as connect:
        with patch("rge.db.connection.ensure_database") as ensure_db:
            report = run_probe_extract_claims(
                fixture_source=DEFAULT_FIXTURE,
                root=REPO_ROOT,
                reports_dir=reports_dir,
                client=mock_client,
                skip_health_check=True,
            )
            connect.assert_not_called()
            ensure_db.assert_not_called()

    assert report["status"] == "ok"
    assert report["db_writes"] is False
    assert report["accepted_count"] + report["rejected_count"] > 0
    if report["rejected"]:
        assert "rejection_reason" in report["rejected"][0]

    report_file = reports_dir / Path(report["report_path"]).name
    assert report_file.is_file()
    on_disk = json.loads(report_file.read_text(encoding="utf-8"))
    assert on_disk["command"] == "probe-extract-claims"
    assert on_disk["provider"] == "mock"


def test_run_probe_default_db_untouched(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_live_env(monkeypatch)
    db_path = tmp_path / "data" / "db" / "creative_research.sqlite"
    db_path.parent.mkdir(parents=True)
    db_path.write_bytes(b"")
    mtime_before = db_path.stat().st_mtime

    with patch("rge.modules.live_probe.default_db_path", return_value=db_path):
        run_probe_extract_claims(
            fixture_source=DEFAULT_FIXTURE,
            root=REPO_ROOT,
            reports_dir=tmp_path / "reports",
            client=MockModelClient(),
            skip_health_check=True,
        )

    assert db_path.stat().st_mtime == mtime_before


def test_cli_probe_success_with_mock_client(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_live_env(monkeypatch)
    reports_dir = tmp_path / "live_probes"

    with patch("rge.modules.live_probe.live_probes_dir", return_value=reports_dir):
        with patch("rge.modules.live_probe.assert_ollama_health") as health:
            health.return_value = {"reachable": True, "model_available": True}
            with patch(
                "rge.modules.live_probe.get_model_client",
                return_value=MockModelClient(),
            ):
                exit_code = main(["probe-extract-claims"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert len(list(reports_dir.glob("probe_extract_claims_*.json"))) == 1
