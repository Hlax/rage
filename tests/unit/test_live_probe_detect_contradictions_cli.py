"""Unit tests for live probe-detect-contradictions CLI (mock-only; no Ollama required)."""

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
    load_contradiction_inputs_from_relationship_report,
    run_probe_detect_contradictions,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUNDLE = (
    REPO_ROOT
    / "fixtures"
    / "probes"
    / "live_probe_contradiction_quality_bundle.json"
)


def _set_live_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")


def test_assert_live_probe_env_accepts_probe_detect_contradictions_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_live_env(monkeypatch)
    cfg = assert_live_probe_env(command="probe-detect-contradictions")
    assert cfg.llm_mode == "ollama"


def test_cli_probe_detect_contradictions_refuses_without_live_opt_in(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "0")
    exit_code = main(["probe-detect-contradictions"])
    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "probe-detect-contradictions"


def test_load_contradiction_inputs_from_relationship_report(tmp_path: Path) -> None:
    report_path = tmp_path / "probe_draft_relationships_test.json"
    report_path.write_text(
        json.dumps(
            {
                "command": "probe-draft-relationships",
                "input_claim": {
                    "id": "claim_live_probe_link_001",
                    "claim_text": "Scoped claim in short-form writing tasks.",
                    "scope": "short-form writing tasks",
                    "domain": "creativity",
                },
            }
        ),
        encoding="utf-8",
    )
    source_claims, domain_claims, relationships, rel = (
        load_contradiction_inputs_from_relationship_report(report_path, REPO_ROOT)
    )
    assert rel.endswith("probe_draft_relationships_test.json")
    assert source_claims[0]["id"] == "claim_live_probe_link_001"
    assert len(domain_claims) >= 2
    assert len(relationships) == 2
    assert any(rel["predicate"] == "may_reduce" for rel in relationships)
    assert any(rel["predicate"] == "may_increase" for rel in relationships)


def test_run_probe_detect_contradictions_writes_report_without_db(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_live_env(monkeypatch)
    reports_dir = tmp_path / "live_probes"
    mock_client = MockModelClient()

    with patch("rge.db.connection.connect") as connect:
        with patch("rge.db.connection.ensure_database") as ensure_db:
            report = run_probe_detect_contradictions(
                bundle_fixture=DEFAULT_BUNDLE,
                root=REPO_ROOT,
                reports_dir=reports_dir,
                client=mock_client,
                skip_health_check=True,
            )
            connect.assert_not_called()
            ensure_db.assert_not_called()

    assert report["status"] == "ok"
    assert report["db_writes"] is False
    assert report["command"] == "probe-detect-contradictions"
    assert report["accepted_count"] >= 1
    assert report["input_source"] == "bundle_fixture"
    assert report["relationship_triples_allowed"]

    report_file = reports_dir / Path(report["report_path"]).name
    on_disk = json.loads(report_file.read_text(encoding="utf-8"))
    assert on_disk["probe"] == "contradiction_detection"


def test_run_probe_detect_contradictions_default_db_untouched(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_live_env(monkeypatch)
    db_path = tmp_path / "data" / "db" / "creative_research.sqlite"
    db_path.parent.mkdir(parents=True)
    db_path.write_bytes(b"")
    mtime_before = db_path.stat().st_mtime

    with patch("rge.modules.live_probe.default_db_path", return_value=db_path):
        run_probe_detect_contradictions(
            bundle_fixture=DEFAULT_BUNDLE,
            root=REPO_ROOT,
            reports_dir=tmp_path / "reports",
            client=MockModelClient(),
            skip_health_check=True,
        )

    assert db_path.stat().st_mtime == mtime_before


def test_cli_probe_detect_contradictions_success_with_mock_client(
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
                exit_code = main(["probe-detect-contradictions"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert len(list(reports_dir.glob("probe_detect_contradictions_*.json"))) == 1


def test_cli_probe_detect_contradictions_rejects_conflicting_input_flags(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_live_env(monkeypatch)
    exit_code = main(
        [
            "probe-detect-contradictions",
            "--from-report",
            "data/reports/live_probes/x.json",
            "--chain-relationship",
        ]
    )
    assert exit_code == 1
    assert "one of" in json.loads(capsys.readouterr().out)["detail"]


def test_cli_probe_detect_contradictions_refuses_when_model_unavailable(
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
        exit_code = main(["probe-detect-contradictions"])
    assert exit_code == 2
    assert "ollama pull" in json.loads(capsys.readouterr().out)["detail"]
