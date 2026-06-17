"""Atlas snapshot public report summary projection (ticket-304)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.cli import FIXTURE_RUN_ID, GOLDEN_MVP_TOPIC, execute_fixture_mode_run, main
from rge.contracts.atlas_snapshot_v0 import validate_atlas_snapshot
from rge.modules.atlas_coherence_report import build_atlas_coherence_report
from rge.modules.atlas_snapshot_builder import (
    _project_public_report_summary,
    assert_no_private_fields,
    build_atlas_snapshot_from_db,
    export_atlas_snapshot_to_path,
)

from tests.unit.test_evidence_db_run_report_projection import (
    TOPIC,
    _ingest_ticket127,
    _run_mock_live_spine,
)
from tests.unit.test_evidence_db_atlas_projection import REPO_ROOT, mock_llm_env

CREATIVITY_FIXTURE = REPO_ROOT / "fixtures" / "atlas" / "atlas_snapshot_v0_creativity_fixture.json"


@pytest.fixture()
def artifact_dirs(tmp_path: Path) -> dict[str, Path]:
    export_dir = tmp_path / "export"
    report_dir = tmp_path / "reports"
    ticket_dir = tmp_path / "tickets"
    for directory in (export_dir, report_dir, ticket_dir):
        directory.mkdir(parents=True, exist_ok=True)
    return {
        "export": export_dir,
        "reports": report_dir,
        "tickets": ticket_dir,
    }


def test_project_public_report_summary_uses_whitelisted_metrics_only() -> None:
    summary = _project_public_report_summary(
        {
            "topic": "Does AI improve creative output?",
            "sources_ingested": 3,
            "claims_accepted": 4,
            "claims_rejected": 1,
            "relationships_updated": 2,
            "score_events_created": 2,
            "cards_exported": 2,
            "cluster_reports_created": 1,
            "contract_id": "contract_hidden",
            "top_failure_modes": [{"mode": "missing_quote_span"}],
        }
    )
    assert "4 claims accepted from 3 ingested sources" in summary
    assert "contract_hidden" not in summary
    assert "missing_quote_span" not in summary


def test_fixture_mode_atlas_reports_include_public_summary(
    tmp_path: Path,
    artifact_dirs: dict[str, Path],
) -> None:
    temp_db = tmp_path / "atlas_report_summary.sqlite"
    execute_fixture_mode_run(
        topic=GOLDEN_MVP_TOPIC,
        domain="creativity",
        db_path=temp_db,
        run_id=FIXTURE_RUN_ID,
        report_dir=artifact_dirs["reports"],
        ticket_dir=artifact_dirs["tickets"],
        export_dirs=[artifact_dirs["export"]],
    )
    conn = __import__("rge.db.connection", fromlist=["connect"]).connect(temp_db)
    try:
        snapshot = build_atlas_snapshot_from_db(
            conn,
            topic=GOLDEN_MVP_TOPIC,
            domain_pack="creativity",
            fixture_mode=True,
            repo_root=REPO_ROOT,
        )
    finally:
        conn.close()
    assert snapshot["reports"]
    assert snapshot["reports"][0]["public_summary"]
    assert_no_private_fields(snapshot) == []
    validate_atlas_snapshot(snapshot)


def test_committed_creativity_fixture_has_public_summary() -> None:
    snapshot = json.loads(CREATIVITY_FIXTURE.read_text(encoding="utf-8"))
    assert snapshot["reports"][0]["public_summary"]
    assert "claims accepted" in snapshot["reports"][0]["public_summary"]


def test_export_atlas_snapshot_matches_committed_fixture_after_summary(
    tmp_path: Path,
    artifact_dirs: dict[str, Path],
) -> None:
    temp_db = tmp_path / "atlas_export.sqlite"
    execute_fixture_mode_run(
        topic=GOLDEN_MVP_TOPIC,
        domain="creativity",
        db_path=temp_db,
        run_id=FIXTURE_RUN_ID,
        report_dir=artifact_dirs["reports"],
        ticket_dir=artifact_dirs["tickets"],
        export_dirs=[artifact_dirs["export"]],
    )
    out_path = tmp_path / "atlas_snapshot.json"
    conn = __import__("rge.db.connection", fromlist=["connect"]).connect(temp_db)
    try:
        export_atlas_snapshot_to_path(
            conn,
            out_path,
            topic=GOLDEN_MVP_TOPIC,
            domain_pack="creativity",
            fixture_mode=True,
            repo_root=REPO_ROOT,
        )
    finally:
        conn.close()
    assert out_path.read_bytes() == CREATIVITY_FIXTURE.read_bytes()


def test_evidence_db_snapshot_reports_include_public_summary(
    tmp_path: Path,
    mock_llm_env: None,
) -> None:
    temp_db = tmp_path / "evidence_report_summary.sqlite"
    source_id = _ingest_ticket127(temp_db)
    _run_mock_live_spine(temp_db, source_id)
    conn = __import__("rge.db.connection", fromlist=["connect"]).connect(temp_db)
    try:
        snapshot = build_atlas_snapshot_from_db(
            conn,
            topic=TOPIC,
            domain_pack="creativity",
            fixture_mode=False,
            repo_root=REPO_ROOT,
        )
        report = build_atlas_coherence_report(snapshot)
    finally:
        conn.close()
    assert snapshot["reports"][0]["public_summary"]
    assert report["verdict"]["reports_and_hypotheses_frontend_ready"]["verdict"] == "pass"


def test_export_cli_stdout_reports_public_summary(
    tmp_path: Path,
    artifact_dirs: dict[str, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    temp_db = tmp_path / "atlas_cli.sqlite"
    execute_fixture_mode_run(
        topic=GOLDEN_MVP_TOPIC,
        domain="creativity",
        db_path=temp_db,
        run_id=FIXTURE_RUN_ID,
        report_dir=artifact_dirs["reports"],
        ticket_dir=artifact_dirs["tickets"],
        export_dirs=[artifact_dirs["export"]],
    )
    out_path = tmp_path / "atlas_snapshot.json"
    exit_code = main(
        [
            "export-atlas-snapshot",
            "--db",
            str(temp_db),
            "--out",
            str(out_path),
            "--topic",
            GOLDEN_MVP_TOPIC,
            "--domain",
            "creativity",
            "--fixture-mode",
        ]
    )
    assert exit_code == 0
    snapshot = json.loads(out_path.read_text(encoding="utf-8"))
    assert snapshot["reports"][0]["public_summary"]
