"""Unit tests for live probe-link-concepts CLI (mock-only; no Ollama required)."""

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
    load_claims_from_probe_report,
    run_probe_link_concepts,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CLAIM_FIXTURE = (
    REPO_ROOT
    / "fixtures"
    / "claims"
    / "live_probe_concept_link_quality_claim.json"
)


def _set_live_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")


def test_assert_live_probe_env_accepts_probe_link_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_live_env(monkeypatch)
    cfg = assert_live_probe_env(command="probe-link-concepts")
    assert cfg.llm_mode == "ollama"


def test_cli_probe_link_refuses_without_live_opt_in(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "0")
    exit_code = main(["probe-link-concepts"])
    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "probe-link-concepts"


def test_load_claims_from_probe_report_assigns_ids(tmp_path: Path) -> None:
    report_path = tmp_path / "probe_extract_claims_test.json"
    report_path.write_text(
        json.dumps(
            {
                "command": "probe-extract-claims",
                "accepted": [
                    {
                        "claim_text": "Scoped claim in short-form writing tasks.",
                        "subject": "x",
                        "predicate": "increased",
                        "object": "y",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    claims, rel = load_claims_from_probe_report(report_path, tmp_path)
    assert rel.endswith("probe_extract_claims_test.json")
    assert claims[0]["id"] == "claim_live_probe_001"


def test_run_probe_link_writes_report_without_db(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_live_env(monkeypatch)
    reports_dir = tmp_path / "live_probes"
    mock_client = MockModelClient()

    with patch("rge.db.connection.connect") as connect:
        with patch("rge.db.connection.ensure_database") as ensure_db:
            report = run_probe_link_concepts(
                claim_fixture=DEFAULT_CLAIM_FIXTURE,
                root=REPO_ROOT,
                reports_dir=reports_dir,
                client=mock_client,
                skip_health_check=True,
            )
            connect.assert_not_called()
            ensure_db.assert_not_called()

    assert report["status"] == "ok"
    assert report["db_writes"] is False
    assert report["command"] == "probe-link-concepts"
    assert report["accepted_count"] + report["rejected_count"] > 0
    if report["rejected"]:
        assert "validation_diagnostic" in report["rejected"][0]

    report_file = reports_dir / Path(report["report_path"]).name
    on_disk = json.loads(report_file.read_text(encoding="utf-8"))
    assert on_disk["probe"] == "concept_linking"
    assert on_disk["ontology_labels_exposed"]


def test_run_probe_link_default_db_untouched(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_live_env(monkeypatch)
    db_path = tmp_path / "data" / "db" / "creative_research.sqlite"
    db_path.parent.mkdir(parents=True)
    db_path.write_bytes(b"")
    mtime_before = db_path.stat().st_mtime

    with patch("rge.modules.live_probe.default_db_path", return_value=db_path):
        run_probe_link_concepts(
            claim_fixture=DEFAULT_CLAIM_FIXTURE,
            root=REPO_ROOT,
            reports_dir=tmp_path / "reports",
            client=MockModelClient(),
            skip_health_check=True,
        )

    assert db_path.stat().st_mtime == mtime_before


def test_cli_probe_link_success_with_mock_client(
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
                exit_code = main(["probe-link-concepts"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert len(list(reports_dir.glob("probe_link_concepts_*.json"))) == 1


def test_cli_probe_link_rejects_conflicting_input_flags(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_live_env(monkeypatch)
    exit_code = main(
        [
            "probe-link-concepts",
            "--from-report",
            "data/reports/live_probes/x.json",
            "--chain-extract",
        ]
    )
    assert exit_code == 1
    assert "one of" in json.loads(capsys.readouterr().out)["detail"]
