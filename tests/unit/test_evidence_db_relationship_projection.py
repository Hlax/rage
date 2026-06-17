"""Evidence DB relationship edge projection for atlas coherence (ticket-297)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.cli import main
from rge.db.connection import connect
from rge.modules.atlas_coherence_report import build_atlas_coherence_report
from rge.modules.atlas_snapshot_builder import build_atlas_snapshot_from_db
from rge.modules.evidence_db_atlas import ensure_evidence_relationship_edges

from tests.unit.test_evidence_db_atlas_projection import (
    REPO_ROOT,
    TOPIC,
    _ingest_ticket127,
    _run_mock_live_spine,
    mock_llm_env,
)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "evidence_relationship.sqlite"


def test_ensure_evidence_relationship_edges_creates_active_rows(
    temp_db: Path, mock_llm_env: None
) -> None:
    source_id = _ingest_ticket127(temp_db)
    _run_mock_live_spine(temp_db, source_id)

    conn = connect(temp_db)
    try:
        result = ensure_evidence_relationship_edges(
            conn, topic=TOPIC, domain_pack="creativity"
        )
        assert result["status"] in {"created", "already_present"}
        if result["status"] == "created":
            assert result["relationship_ids"]
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM relationships WHERE status = 'active'"
        ).fetchone()
        assert row is not None and int(row["n"]) >= 1
    finally:
        conn.close()


def test_atlas_snapshot_includes_edges_and_overall_coherence_pass(
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
        assert len(snapshot["edges"]) >= 1
        assert snapshot["edges"][0]["source_node_id"]
        assert snapshot["edges"][0]["target_node_id"]

        report = build_atlas_coherence_report(snapshot)
        assert report["population"]["edges"] >= 1
        notes = report["verdict"]["missing_fields_create_refactor_risk"]["notes"]
        assert not any("relationship edges" in note.casefold() for note in notes)
        assert report["overall_coherence_verdict"] == "pass"
    finally:
        conn.close()


def test_export_atlas_snapshot_cli_populates_edges(
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
    assert snapshot["edges"]
    assert snapshot["edges"][0]["predicate"]
