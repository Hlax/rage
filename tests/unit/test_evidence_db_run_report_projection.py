"""Evidence DB run report projection for atlas coherence (ticket-295)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.cli import main
from rge.db.connection import connect
from rge.modules.atlas_coherence_report import build_atlas_coherence_report
from rge.modules.atlas_snapshot_builder import build_atlas_snapshot_from_db
from rge.modules.evidence_db_atlas import ensure_evidence_run_report

from tests.unit.test_evidence_db_atlas_projection import (
    REPO_ROOT,
    TICKET127_SOURCE,
    TOPIC,
    _ingest_ticket127,
    _run_mock_live_spine,
    mock_llm_env,
)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "evidence_run_report.sqlite"


def test_ensure_evidence_run_report_creates_run_reports_row(
    temp_db: Path, mock_llm_env: None
) -> None:
    source_id = _ingest_ticket127(temp_db)
    _run_mock_live_spine(temp_db, source_id)

    conn = connect(temp_db)
    try:
        result = ensure_evidence_run_report(conn, topic=TOPIC, domain_pack="creativity")
        assert result["status"] in {"created", "already_present"}
        row = conn.execute(
            "SELECT run_id, report_json FROM run_reports WHERE run_id = ?",
            (result["run_id"],),
        ).fetchone()
        assert row is not None
        assert row["run_id"] == result["run_id"]
    finally:
        conn.close()


def test_atlas_snapshot_includes_reports_with_run_id(
    temp_db: Path, mock_llm_env: None
) -> None:
    source_id = _ingest_ticket127(temp_db)
    _run_mock_live_spine(temp_db, source_id)

    conn = connect(temp_db)
    try:
        snapshot = build_atlas_snapshot_from_db(
            conn,
            topic=TOPIC,
            domain_pack="creativity",
            fixture_mode=False,
            repo_root=REPO_ROOT,
        )
        assert len(snapshot["reports"]) >= 1
        assert snapshot["reports"][0]["run_id"].startswith("run_evidence_")

        report = build_atlas_coherence_report(snapshot)
        assert report["population"]["reports"] >= 1
        assert report["population"]["runs"] >= 1
        assert (
            report["verdict"]["meaningful_atlas_data_from_research_loop"]["verdict"]
            == "pass"
        )
        assert (
            report["verdict"]["reports_and_hypotheses_frontend_ready"]["verdict"]
            == "pass"
        )
    finally:
        conn.close()


def test_export_atlas_snapshot_cli_populates_reports(
    temp_db: Path, tmp_path: Path, mock_llm_env: None
) -> None:
    source_id = _ingest_ticket127(temp_db)
    _run_mock_live_spine(temp_db, source_id)
    out_path = tmp_path / "atlas_snapshot.json"
    exit_code = main(
        [
            "export-atlas-snapshot",
            "--db",
            str(temp_db),
            "--out",
            str(out_path),
            "--topic",
            TOPIC,
            "--domain",
            "creativity",
        ]
    )
    assert exit_code == 0
    snapshot = json.loads(out_path.read_text(encoding="utf-8"))
    assert snapshot["reports"]
    assert snapshot["reports"][0]["run_id"]
