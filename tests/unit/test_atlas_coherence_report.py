"""Unit tests for atlas coherence report builder (ticket-289)."""

from __future__ import annotations

import json
from pathlib import Path

from rge.contracts.atlas_snapshot_v0 import load_atlas_snapshot_fixture
from rge.modules.atlas_coherence_report import (
    REPORT_SCHEMA_VERSION,
    build_atlas_coherence_report,
    format_atlas_coherence_report_markdown,
    write_atlas_coherence_report,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CREATIVITY_FIXTURE = (
    REPO_ROOT / "fixtures" / "atlas" / "atlas_snapshot_v0_creativity_fixture.json"
)


def test_build_coherence_report_from_creativity_fixture() -> None:
    snapshot = json.loads(CREATIVITY_FIXTURE.read_text(encoding="utf-8"))
    report = build_atlas_coherence_report(snapshot)

    assert report["report_schema_version"] == REPORT_SCHEMA_VERSION
    assert report["atlas_schema_version"] == "atlas_snapshot_v0.1.0"
    assert report["overall_coherence_verdict"] in {"pass", "partial", "fail"}
    assert report["population"]["cards"] >= 2
    assert report["population"]["nodes"] >= 1
    assert report["population"]["runs"] >= 1
    assert report["population"]["reports"] >= 1
    assert report["safety"]["contract_valid"] is True
    assert report["safety"]["private_field_violations"] == []
    assert "meaningful_atlas_data_from_research_loop" in report["verdict"]
    assert "claims_linked_to_sources_and_concepts" in report["verdict"]
    assert "reports_and_hypotheses_frontend_ready" in report["verdict"]
    assert "missing_fields_create_refactor_risk" in report["verdict"]


def test_coherence_report_markdown_includes_verdicts() -> None:
    snapshot = load_atlas_snapshot_fixture(REPO_ROOT)
    report = build_atlas_coherence_report(snapshot.model_dump(mode="json"))
    markdown = format_atlas_coherence_report_markdown(report)

    assert "# Research Atlas Coherence Report" in markdown
    assert "Overall verdict" in markdown
    assert "Coherence verdicts" in markdown
    assert "meaningful atlas data" in markdown.casefold()


def test_write_coherence_report_writes_json_and_markdown(tmp_path: Path) -> None:
    snapshot = json.loads(CREATIVITY_FIXTURE.read_text(encoding="utf-8"))
    json_path = tmp_path / "coherence_report.json"
    md_path = tmp_path / "coherence_report.md"

    result = write_atlas_coherence_report(
        snapshot,
        json_path=json_path,
        markdown_path=md_path,
    )

    assert result["status"] == "completed"
    assert json_path.is_file()
    assert md_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["population"]["cards"] >= 2
