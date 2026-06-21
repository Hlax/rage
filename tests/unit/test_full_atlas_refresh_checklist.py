"""Unit tests for operator full Atlas refresh checklist."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.full_atlas_refresh_checklist import (
    CHECKLIST_STEPS,
    assert_full_atlas_refresh_env,
    inspect_full_atlas_refresh_checklist_status,
    missing_live_gates,
    missing_operator_full_atlas_refresh_gate,
    run_full_atlas_refresh_checklist,
    validate_all_operator_packet_artifacts,
    write_checklist_reports,
)
from rge.modules.live_arbitrary_source_health import LIVE_SOURCE_HEALTH_ARTIFACT_NAME
from rge.modules.operator_loop import WorkingTreeStatus, build_operator_plan
from scripts.refresh_atlas_source_health_preview import validate_source_health_artifact


def _apply_live_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_OPERATOR_FULL_ATLAS_REFRESH", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")


def test_missing_live_gates_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_OPERATOR_FULL_ATLAS_REFRESH", "1")
    monkeypatch.delenv("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE", raising=False)
    monkeypatch.delenv("RGE_ALLOW_SOURCE_NETWORK", raising=False)
    monkeypatch.delenv("OPENALEX_MAILTO", raising=False)

    missing = missing_live_gates()
    assert "RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE" in missing
    assert "RGE_ALLOW_SOURCE_NETWORK" in missing
    assert "OPENALEX_MAILTO" in missing

    with pytest.raises(RuntimeError, match="RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE"):
        assert_full_atlas_refresh_env()


def test_missing_operator_gate_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RGE_ALLOW_OPERATOR_FULL_ATLAS_REFRESH", raising=False)
    missing = missing_operator_full_atlas_refresh_gate()
    assert "RGE_ALLOW_OPERATOR_FULL_ATLAS_REFRESH" in missing


def test_checklist_status_includes_required_steps() -> None:
    status = inspect_full_atlas_refresh_checklist_status()
    assert status["checklist_id"] == "operator-loop-full-atlas-refresh-checklist"
    assert list(status["checklist_steps"]) == list(CHECKLIST_STEPS)
    assert "live_abstract_evidence_quality_smoke" in status["checklist_steps"]
    assert "operator_packet_artifact_validation" in status["checklist_steps"]
    assert "fixture_operator_packet_refresh" in status["checklist_steps"]
    assert "final_status_report" in status["checklist_steps"]
    assert "run_full_atlas_refresh_checklist.py" in status["operator_command"]


def test_artifact_validation_requires_trace_summary() -> None:
    errors = validate_source_health_artifact(
        {
            "schema_version": "atlas_source_health_run_v0.1.0",
            "source_health_summary": {"sources_with_metadata": 3},
        },
        require_trace_summary=True,
    )
    assert any("trace_summary" in error for error in errors)


@pytest.mark.live_network
def test_preview_artifact_is_public_safe_after_refresh(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _apply_live_gates(monkeypatch)
    public_path = tmp_path / "public" / LIVE_SOURCE_HEALTH_ARTIFACT_NAME
    site = tmp_path / "apps" / "public-site"
    site.mkdir(parents=True)
    (site / "package.json").write_text("{}", encoding="utf-8")

    mock_build = MagicMock(return_value=MagicMock(returncode=0))
    report = run_full_atlas_refresh_checklist(
        root=tmp_path,
        output_dir=tmp_path / "export",
        public_artifact_path=public_path,
        skip_site=True,
        command_runner=mock_build,
    )
    artifact = json.loads(public_path.read_text(encoding="utf-8"))

    assert report["atlas_artifact_public_safe"] is True
    assert assert_no_private_fields({"artifact": artifact}) == []
    trace_summary = artifact.get("trace_summary") or {}
    assert int(trace_summary.get("trace_count") or 0) >= 1
    assert trace_summary.get("atlas_trace_preview")


def test_operator_loop_recommends_full_checklist_when_artifact_stale(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_STAGED_RANK2_SCAN_MAX", raising=False)
    (tmp_path / "tickets").mkdir(parents=True)
    (tmp_path / "agent_reports").mkdir(parents=True)
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        "| 40 | ticket-040 | done | prev | | |\n",
        encoding="utf-8",
    )
    (tmp_path / "agent_reports" / "2026-06-20_live-abstract-evidence-quality.md").write_text(
        "# Live Abstract Evidence Quality",
        encoding="utf-8",
    )
    site = tmp_path / "apps" / "public-site"
    public_data = site / "public" / "data"
    public_data.mkdir(parents=True)
    (site / "package.json").write_text("{}", encoding="utf-8")
    (public_data / "atlas_snapshot_preview.json").write_text("{}", encoding="utf-8")
    (public_data / "atlas_coherence_preview.json").write_text("{}", encoding="utf-8")
    scripts = tmp_path / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "run_full_atlas_refresh_checklist.py").write_text("# checklist\n", encoding="utf-8")

    plan = build_operator_plan(
        root=tmp_path,
        working_tree=WorkingTreeStatus(clean=True, branch="main", dirty_paths=[]),
    )
    checklist_status = plan["full_atlas_refresh_checklist_status"]
    action = plan["next_recommended_action"]

    assert checklist_status["full_atlas_refresh_recommended"] is True
    assert action["action_id"] == "run_full_atlas_refresh_checklist"
    assert any(
        "run_full_atlas_refresh_checklist.py" in cmd["shell"]
        for cmd in action["commands"]
    )


def test_write_checklist_reports_creates_markdown_and_json(tmp_path: Path) -> None:
    report = {
        "date": "2026-06-20",
        "overall_verdict": "GO",
        "evidence_quality_verdict": "GO",
        "test_question": "How does AI affect human creativity?",
        "live_run_summary": {
            "live_source_count": 5,
            "abstract_availability_count": 5,
            "claims_accepted": 5,
            "claims_rejected": 0,
            "purpose_fit_status_counts": {"match": 5},
            "evidence_atom_count": 5,
            "relationship_count": 5,
            "trace_summary": {"preview_row_count": 5},
        },
        "public_artifact": "apps/public-site/public/data/atlas_source_health_run_latest.json",
        "operator_export_path": "data/exports/full_atlas_refresh",
        "step_status": {step: "completed" for step in CHECKLIST_STEPS},
    }
    paths = write_checklist_reports(report, root=tmp_path)
    assert Path(paths["markdown"]).is_file()
    assert Path(paths["json"]).is_file()
    payload = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
    assert payload["overall_verdict"] == "GO"


def test_fixture_only_refresh_validates_operator_packets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_ALLOW_OPERATOR_FULL_ATLAS_REFRESH", "1")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")

    public_data = tmp_path / "apps" / "public-site" / "public" / "data"
    public_data.mkdir(parents=True)
    site = tmp_path / "apps" / "public-site"
    (site / "package.json").write_text("{}", encoding="utf-8")

    repo_public = Path(__file__).resolve().parents[2] / "apps" / "public-site" / "public" / "data"
    for name in (
        "atlas_source_health_run_latest.json",
        "atlas_multi_question_live_abstract_latest.json",
        "atlas_local_model_extraction_comparison_latest.json",
        "atlas_graph_maturity_evidence_atom_upgrade_latest.json",
    ):
        source = repo_public / name
        if source.is_file():
            (public_data / name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    report = run_full_atlas_refresh_checklist(
        root=tmp_path,
        output_dir=tmp_path / "export",
        public_artifact_path=public_data / "atlas_source_health_run_latest.json",
        skip_site=True,
        fixture_only=True,
        refresh_fixture_packets=True,
    )

    assert report["fixture_only"] is True
    assert report["operator_packet_validation"]["valid_count"] >= 5
    assert report["step_status"]["fixture_operator_packet_refresh"] == "completed"
    validation = validate_all_operator_packet_artifacts(root=tmp_path)
    assert validation["valid_count"] == validation["total_count"]
