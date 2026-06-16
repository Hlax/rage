"""Evidence DB cluster summary projection for atlas coherence (ticket-296)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.cli import main
from rge.db.connection import connect
from rge.modules.atlas_coherence_report import build_atlas_coherence_report
from rge.modules.atlas_snapshot_builder import build_atlas_snapshot_from_db
from rge.modules.evidence_db_atlas import ensure_evidence_cluster_summary

from tests.unit.test_evidence_db_atlas_projection import (
    REPO_ROOT,
    TOPIC,
    _ingest_ticket127,
    _run_mock_live_spine,
    mock_llm_env,
)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "evidence_cluster.sqlite"


def test_ensure_evidence_cluster_summary_creates_cluster_reports_row(
    temp_db: Path, mock_llm_env: None
) -> None:
    source_id = _ingest_ticket127(temp_db)
    _run_mock_live_spine(temp_db, source_id)

    conn = connect(temp_db)
    try:
        result = ensure_evidence_cluster_summary(
            conn, topic=TOPIC, domain_pack="creativity"
        )
        assert result["status"] in {"created", "already_present"}
        row = conn.execute(
            "SELECT run_id, cluster_label FROM cluster_reports WHERE id = ?",
            (result["cluster_report_id"],),
        ).fetchone()
        assert row is not None
        assert row["run_id"] == result["run_id"]
        assert row["cluster_label"]
    finally:
        conn.close()


def test_atlas_snapshot_includes_clusters_and_clears_cluster_warn(
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
        assert len(snapshot["clusters"]) >= 1
        assert snapshot["clusters"][0]["run_id"].startswith("run_evidence_")
        assert snapshot["clusters"][0]["cluster_label"]

        report = build_atlas_coherence_report(snapshot)
        assert report["population"]["clusters"] >= 1
        notes = report["verdict"]["missing_fields_create_refactor_risk"]["notes"]
        assert not any("clusters[] empty" in note for note in notes)
        # Extract+link-only spine has no relationship edges; document remaining blocker.
        if report["overall_coherence_verdict"] != "pass":
            assert any("relationship edges" in note.casefold() for note in notes)
    finally:
        conn.close()


def test_export_atlas_snapshot_cli_populates_clusters(
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
    assert snapshot["clusters"]
    assert snapshot["clusters"][0]["cluster_id"]
