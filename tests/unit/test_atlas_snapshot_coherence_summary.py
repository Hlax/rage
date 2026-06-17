"""Atlas snapshot inline coherence summary projection (ticket-306)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.cli import FIXTURE_RUN_ID, GOLDEN_MVP_TOPIC, execute_fixture_mode_run, main
from rge.contracts.atlas_snapshot_v0 import validate_atlas_snapshot
from rge.modules.atlas_coherence_report import build_atlas_coherence_report
from rge.modules.atlas_snapshot_builder import (
    _project_coherence_summary,
    assert_no_private_fields,
    build_atlas_snapshot_from_db,
    export_atlas_snapshot_to_path,
)

from tests.unit.test_evidence_db_atlas_projection import (
    REPO_ROOT,
    TOPIC,
    _ingest_ticket127,
    _run_mock_live_spine,
    mock_llm_env,
)

CREATIVITY_FIXTURE = REPO_ROOT / "fixtures" / "atlas" / "atlas_snapshot_v0_creativity_fixture.json"
EXPECTED_PREVIEW_LABEL = "Fixture-mode creativity atlas (mock-safe)"


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


def test_project_coherence_summary_whitelists_verdict_and_label_only() -> None:
    snapshot = json.loads(CREATIVITY_FIXTURE.read_text(encoding="utf-8"))
    snapshot.pop("coherence_summary", None)
    summary = _project_coherence_summary(snapshot, fixture_mode=True)
    assert set(summary.keys()) == {"overall_coherence_verdict", "preview_label"}
    assert summary["overall_coherence_verdict"] == "pass"
    assert summary["preview_label"] == EXPECTED_PREVIEW_LABEL
    assert "population" not in summary
    assert "verdict" not in summary


def test_fixture_mode_atlas_includes_coherence_summary(
    tmp_path: Path,
    artifact_dirs: dict[str, Path],
) -> None:
    temp_db = tmp_path / "atlas_coherence.sqlite"
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
    assert snapshot["coherence_summary"]["overall_coherence_verdict"] == "pass"
    assert snapshot["coherence_summary"]["preview_label"] == EXPECTED_PREVIEW_LABEL
    report = build_atlas_coherence_report(snapshot)
    assert (
        report["overall_coherence_verdict"]
        == snapshot["coherence_summary"]["overall_coherence_verdict"]
    )
    assert_no_private_fields(snapshot) == []
    validate_atlas_snapshot(snapshot)


def test_committed_creativity_fixture_has_coherence_summary() -> None:
    snapshot = json.loads(CREATIVITY_FIXTURE.read_text(encoding="utf-8"))
    assert snapshot["coherence_summary"]["overall_coherence_verdict"] == "pass"
    assert snapshot["coherence_summary"]["preview_label"] == EXPECTED_PREVIEW_LABEL


def test_export_atlas_snapshot_matches_committed_fixture_after_coherence_summary(
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


def test_evidence_db_snapshot_coherence_summary_non_fixture_label(
    tmp_path: Path,
    mock_llm_env: None,
) -> None:
    temp_db = tmp_path / "evidence_coherence.sqlite"
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
    finally:
        conn.close()
    assert snapshot["coherence_summary"]["preview_label"].endswith(
        "atlas coherence projection"
    )


def test_export_cli_includes_coherence_summary(
    tmp_path: Path,
    artifact_dirs: dict[str, Path],
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
    assert snapshot["coherence_summary"]["overall_coherence_verdict"] == "pass"
