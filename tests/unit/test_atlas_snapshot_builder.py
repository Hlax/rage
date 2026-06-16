"""Atlas snapshot builder from fixture-mode DB (ticket-279)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.cli import FIXTURE_RUN_ID, GOLDEN_MVP_TOPIC, execute_fixture_mode_run
from rge.contracts.atlas_snapshot_v0 import validate_atlas_snapshot
from rge.modules.atlas_snapshot_builder import (
    ATLAS_FIXTURE_GENERATED_AT,
    ATLAS_FIXTURE_SAFETY_AUDIT_ID,
    ATLAS_FIXTURE_SNAPSHOT_ID,
    assert_no_private_fields,
    build_atlas_snapshot_from_db,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CREATIVITY_FIXTURE = REPO_ROOT / "fixtures" / "atlas" / "atlas_snapshot_v0_creativity_fixture.json"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "atlas_snapshot_builder.sqlite"


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


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def _build_fixture_mvp_db(temp_db: Path, artifact_dirs: dict[str, Path]) -> None:
    result = execute_fixture_mode_run(
        topic=GOLDEN_MVP_TOPIC,
        domain="creativity",
        db_path=temp_db,
        run_id=FIXTURE_RUN_ID,
        report_dir=artifact_dirs["reports"],
        ticket_dir=artifact_dirs["tickets"],
        export_dirs=[artifact_dirs["export"]],
    )
    assert result["status"] == "completed"
    assert result["card_count"] >= 2


def test_build_atlas_snapshot_run_lineage_contract_fields(
    temp_db: Path,
    artifact_dirs: dict[str, Path],
) -> None:
    from rge.db.connection import connect
    from rge.modules.research_planner import DEFAULT_RESEARCH_QUESTION_ID

    _build_fixture_mvp_db(temp_db, artifact_dirs)
    conn = connect(temp_db)
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

    assert len(snapshot["runs"]) >= 1
    root_run = snapshot["runs"][0]
    assert root_run["run_id"] == FIXTURE_RUN_ID
    assert root_run["research_question_id"] == DEFAULT_RESEARCH_QUESTION_ID
    assert root_run["parent_question_id"] is None
    assert "spawned_from_report_id" not in root_run
    assert assert_no_private_fields(snapshot) == []


def test_build_atlas_snapshot_run_spawn_lineage_for_followup_run(
    temp_db: Path,
    artifact_dirs: dict[str, Path],
) -> None:
    from rge.db.connection import connect
    from rge.modules.research_planner import DEFAULT_RESEARCH_QUESTION_ID, GOLDEN_CONTRACT_ID

    _build_fixture_mvp_db(temp_db, artifact_dirs)
    conn = connect(temp_db)
    try:
        conn.execute(
            """
            INSERT INTO research_runs (
                id, contract_id, topic, domain_pack, mode, status,
                started_at, finished_at, summary_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "run_followup_fixture_spawn",
                GOLDEN_CONTRACT_ID,
                "Does divergent prompting reduce semantic convergence?",
                "creativity",
                "fixture",
                "completed",
                "2099-01-01T00:00:00Z",
                "2099-01-01T00:00:00Z",
                '{"fixture_mode": true, "spawned": true}',
            ),
        )
        conn.commit()
        snapshot = build_atlas_snapshot_from_db(
            conn,
            topic=GOLDEN_MVP_TOPIC,
            domain_pack="creativity",
            fixture_mode=True,
            repo_root=REPO_ROOT,
        )
    finally:
        conn.close()

    followup = next(
        run for run in snapshot["runs"] if run["run_id"] == "run_followup_fixture_spawn"
    )
    assert followup["parent_question_id"] == DEFAULT_RESEARCH_QUESTION_ID
    assert followup["spawned_from_report_id"].startswith("crpt_")
    assert followup["spawned_from_claim_ids"]
    assert followup["spawn_reason"]


def test_build_atlas_snapshot_from_fixture_db_has_cards_and_nodes(
    temp_db: Path,
    artifact_dirs: dict[str, Path],
) -> None:
    from rge.db.connection import connect

    _build_fixture_mvp_db(temp_db, artifact_dirs)
    conn = connect(temp_db)
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

    assert len(snapshot["cards"]) >= 2
    assert len(snapshot["nodes"]) >= 3
    assert len(snapshot["edges"]) >= 1
    assert snapshot["schema_version"] == "atlas_snapshot_v0.1.0"
    assert snapshot["safety"]["public_safe"] is True
    validate_atlas_snapshot(snapshot)
    assert assert_no_private_fields(snapshot) == []


def test_build_atlas_snapshot_matches_committed_creativity_fixture(
    temp_db: Path,
    artifact_dirs: dict[str, Path],
) -> None:
    from rge.db.connection import connect

    _build_fixture_mvp_db(temp_db, artifact_dirs)
    conn = connect(temp_db)
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

    expected = json.loads(CREATIVITY_FIXTURE.read_text(encoding="utf-8"))
    assert snapshot == expected


def test_build_atlas_snapshot_rejects_private_field_leakage(
    temp_db: Path,
    artifact_dirs: dict[str, Path],
) -> None:
    from rge.db.connection import connect

    _build_fixture_mvp_db(temp_db, artifact_dirs)
    conn = connect(temp_db)
    try:
        snapshot = build_atlas_snapshot_from_db(
            conn,
            topic=GOLDEN_MVP_TOPIC,
            domain_pack="creativity",
            fixture_mode=True,
            repo_root=REPO_ROOT,
        )
        snapshot["cards"][0]["claim_id"] = "claim_secret"
        violations = assert_no_private_fields(snapshot)
        assert violations
    finally:
        conn.close()


def test_atlas_snapshot_fixture_metadata_constants() -> None:
    fixture = json.loads(CREATIVITY_FIXTURE.read_text(encoding="utf-8"))
    assert fixture["snapshot_id"] == ATLAS_FIXTURE_SNAPSHOT_ID
    assert fixture["generated_at"] == ATLAS_FIXTURE_GENERATED_AT
    assert fixture["safety"]["safety_audit_id"] == ATLAS_FIXTURE_SAFETY_AUDIT_ID
