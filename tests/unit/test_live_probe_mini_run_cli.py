"""Unit tests for live probe-mini-run CLI (mock-only; no Ollama required)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rge.cli import main
from rge.llm.mock_client import MockModelClient
from rge.modules.contradiction_detector import (
    claim_dicts_as_objects,
    propose_contradictions,
    validate_contradiction_probe_batch,
)
from rge.modules.live_probe import (
    assert_live_probe_env,
    chain_inputs_suitable_for_contradiction,
    load_default_contradiction_bundle,
    merge_qualifying_claim_from_relationship_report,
    run_probe_mini_run,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = (
    REPO_ROOT / "fixtures" / "sources" / "live_probe_claim_calibration_short.txt"
)


def _set_live_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")


def test_assert_live_probe_env_accepts_probe_mini_run_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_live_env(monkeypatch)
    cfg = assert_live_probe_env(command="probe-mini-run")
    assert cfg.llm_mode == "ollama"


def test_chain_inputs_suitable_for_contradiction_requires_gt07_shape() -> None:
    assert not chain_inputs_suitable_for_contradiction(
        [{"claim_text": "AI reduced semantic diversity"}],
        [
            {
                "predicate": "supports",
                "subject_concept": "AI assistance",
                "object_concept": "ideation",
            }
        ],
    )
    assert chain_inputs_suitable_for_contradiction(
        [
            {
                "claim_text": "AI increased idea diversity when participants diverged."
            },
            {"claim_text": "AI reduced semantic diversity in writing tasks."},
        ],
        [
            {
                "predicate": "may_reduce",
                "subject_concept": "AI assistance",
                "object_concept": "semantic diversity",
            },
            {
                "predicate": "may_increase",
                "subject_concept": "AI assistance",
                "object_concept": "diversity",
            },
        ],
    )


def test_merge_opposing_only_hybrid_overlay_preserves_qualifying_source() -> None:
    default_source, default_domain, _ = load_default_contradiction_bundle(REPO_ROOT)
    opposing_input = {
        "id": "claim_live_probe_link_001",
        "claim_text": (
            "AI-assisted brainstorming reduced semantic diversity across submitted "
            "ideas in short-form writing tasks."
        ),
    }
    source_claims, domain_claims = merge_qualifying_claim_from_relationship_report(
        {"input_claim": opposing_input},
        default_source,
        default_domain,
    )
    assert source_claims[0]["id"] == "claim_live_probe_qualify_001"
    assert "increased idea diversity" in source_claims[0]["claim_text"].casefold()
    opposing_ids = [
        claim["id"]
        for claim in domain_claims
        if "reduced semantic diversity" in claim["claim_text"].casefold()
    ]
    assert len(opposing_ids) == 1
    assert opposing_ids[0] != source_claims[0]["id"]


def test_opposing_hybrid_overlay_passes_contradiction_validation() -> None:
    default_source, default_domain, relationships = load_default_contradiction_bundle(
        REPO_ROOT
    )
    opposing_input = {
        "id": "claim_live_probe_link_001",
        "claim_text": (
            "AI-assisted brainstorming reduced semantic diversity across submitted "
            "ideas in short-form writing tasks."
        ),
    }
    source_claims, domain_claims = merge_qualifying_claim_from_relationship_report(
        {"input_claim": opposing_input},
        default_source,
        default_domain,
    )
    proposed = propose_contradictions(
        domain_claims,
        relationships,
        "creativity",
        client=MockModelClient(),
        fixture_name="contradiction_detection_live_probe_quality.json",
    )
    validation = validate_contradiction_probe_batch(
        proposed,
        source_claims=claim_dicts_as_objects(source_claims),
        domain_claims=claim_dicts_as_objects(domain_claims),
        relationships=relationships,
    )
    assert len(validation["accepted"]) >= 1


def test_cli_probe_mini_run_refuses_without_live_opt_in(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "0")
    exit_code = main(["probe-mini-run"])
    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "probe-mini-run"


def test_run_probe_mini_run_writes_combined_report_without_db(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_live_env(monkeypatch)
    reports_dir = tmp_path / "live_probes"
    mock_client = MockModelClient()

    with patch("rge.db.connection.connect") as connect:
        with patch("rge.db.connection.ensure_database") as ensure_db:
            report = run_probe_mini_run(
                fixture_source=DEFAULT_SOURCE,
                root=REPO_ROOT,
                reports_dir=reports_dir,
                client=mock_client,
                skip_health_check=True,
            )
            connect.assert_not_called()
            ensure_db.assert_not_called()

    assert report["status"] in ("ok", "partial")
    assert report["db_writes"] is False
    assert report["public_export"] is False
    assert report["cloud_calls"] is False
    assert report["command"] == "probe-mini-run"
    assert report["contradiction_input_mode"] == "hybrid_overlay"
    assert "claim_extraction" in report["stages"]
    assert "concept_linking" in report["stages"]
    assert "relationship_drafting" in report["stages"]
    assert "contradiction_detection" in report["stages"]
    assert report["stages"]["claim_extraction"]["accepted_count"] >= 1
    assert report["stages"]["concept_linking"]["accepted_count"] >= 1
    assert report["stages"]["relationship_drafting"]["accepted_count"] >= 1
    assert report["stages"]["contradiction_detection"]["accepted_count"] >= 1

    report_file = reports_dir / Path(report["report_path"]).name
    on_disk = json.loads(report_file.read_text(encoding="utf-8"))
    assert on_disk["report_type"] == "live_probe_mini_run_report"


def test_run_probe_mini_run_strict_chain_skips_contradiction_when_insufficient(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_live_env(monkeypatch)
    report = run_probe_mini_run(
        fixture_source=DEFAULT_SOURCE,
        strict_chain=True,
        root=REPO_ROOT,
        reports_dir=tmp_path / "live_probes",
        client=MockModelClient(),
        skip_health_check=True,
    )
    assert report["status"] == "partial"
    assert (
        report["contradiction_input_mode"]
        == "skipped_strict_chain_insufficient_inputs"
    )
    contradiction = report["stages"]["contradiction_detection"]
    assert contradiction["status"] == "skipped"
    assert contradiction["accepted_count"] == 0
    assert "skip_reason" in contradiction


def test_run_probe_mini_run_default_db_untouched(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_live_env(monkeypatch)
    db_path = tmp_path / "data" / "db" / "creative_research.sqlite"
    db_path.parent.mkdir(parents=True)
    db_path.write_bytes(b"")
    mtime_before = db_path.stat().st_mtime

    with patch("rge.modules.live_probe.default_db_path", return_value=db_path):
        run_probe_mini_run(
            fixture_source=DEFAULT_SOURCE,
            root=REPO_ROOT,
            reports_dir=tmp_path / "reports",
            client=MockModelClient(),
            skip_health_check=True,
        )

    assert db_path.stat().st_mtime == mtime_before


def test_cli_probe_mini_run_success_with_mock_client(
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
                exit_code = main(["probe-mini-run"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] in ("ok", "partial")
    assert len(list(reports_dir.glob("probe_mini_run_*.json"))) == 1


def test_cli_probe_mini_run_refuses_when_model_unavailable(
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
        exit_code = main(["probe-mini-run"])
    assert exit_code == 2
    assert "ollama pull" in json.loads(capsys.readouterr().out)["detail"]
