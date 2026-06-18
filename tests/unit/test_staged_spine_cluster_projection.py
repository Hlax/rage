"""Staged spine cluster summary projection for atlas coherence (ticket-317)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.cli import STAGED_FIXTURE_QUESTION_ID, STAGED_FIXTURE_RUN_ID, main
from rge.db.connection import connect
from rge.modules.atlas_coherence_report import build_atlas_coherence_report
from rge.modules.atlas_snapshot_builder import build_atlas_snapshot_from_db
from rge.modules.evidence_db_atlas import (
    STAGED_SPINE_RUN_PREFIX,
    ensure_staged_atlas_follow_up_question,
    ensure_staged_cluster_summaries,
)

from tests.unit.test_staged_fixture_mode_run_spine import (
    OPENALEX_FIXTURE,
    RANK1_HTML,
    RANK2_HTML,
    STAGED_TOPIC,
    patched_staged_network,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXPORT_TOPIC = "Ticket-317 staged spine cluster projection proof"


@pytest.fixture(autouse=True)
def mock_llm_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def mock_network_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "staged_cluster.sqlite"


@pytest.fixture()
def staging_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "staged"
    directory.mkdir()
    return directory


@pytest.fixture()
def report_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "reports"
    directory.mkdir()
    return directory


def _run_staged_orchestrator_cli(
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    patched_staged_network: None,
) -> None:
    exit_code = main(
        [
            "run",
            "--fixture-mode",
            "--staged-spine",
            "--topic",
            STAGED_TOPIC,
            "--domain",
            "creativity",
            "--db",
            str(temp_db),
            "--staging-dir",
            str(staging_dir),
            "--output-dir",
            str(report_dir),
            "--run-id",
            STAGED_FIXTURE_RUN_ID,
            "--question-id",
            STAGED_FIXTURE_QUESTION_ID,
        ]
    )
    assert exit_code == 0


def test_ensure_staged_cluster_summaries_creates_rank_rows(
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    mock_network_env: None,
    patched_staged_network: None,
) -> None:
    _run_staged_orchestrator_cli(temp_db, staging_dir, report_dir, patched_staged_network)

    conn = connect(temp_db)
    try:
        results = ensure_staged_cluster_summaries(
            conn, topic=EXPORT_TOPIC, domain_pack="creativity"
        )
        created = [item for item in results if item["status"] in {"created", "already_present"}]
        assert len(created) >= 2
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM cluster_reports WHERE run_id LIKE ?",
            (f"{STAGED_SPINE_RUN_PREFIX}%",),
        ).fetchone()
        assert row is not None and int(row["n"]) >= 2
    finally:
        conn.close()


def test_ensure_staged_atlas_follow_up_question_seeds_golden_contract_row(
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    mock_network_env: None,
    patched_staged_network: None,
) -> None:
    _run_staged_orchestrator_cli(temp_db, staging_dir, report_dir, patched_staged_network)

    conn = connect(temp_db)
    try:
        result = ensure_staged_atlas_follow_up_question(
            conn, topic=EXPORT_TOPIC, domain_pack="creativity"
        )
        assert result["status"] in {"created", "already_present"}
        row = conn.execute(
            """
            SELECT contract_id, item_type, last_error
            FROM research_queue
            WHERE item_type = 'question' AND last_error = ?
            """,
            (EXPORT_TOPIC,),
        ).fetchone()
        assert row is not None
        assert row["contract_id"] == "contract_golden_test_10"
    finally:
        conn.close()


def test_atlas_snapshot_includes_staged_clusters_and_coherence_pass(
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    mock_network_env: None,
    patched_staged_network: None,
) -> None:
    _run_staged_orchestrator_cli(temp_db, staging_dir, report_dir, patched_staged_network)

    conn = connect(temp_db)
    try:
        snapshot = build_atlas_snapshot_from_db(
            conn,
            topic=EXPORT_TOPIC,
            domain_pack="creativity",
            fixture_mode=False,
            repo_root=REPO_ROOT,
        )
        assert len(snapshot["clusters"]) >= 2
        assert all(
            cluster["run_id"].startswith(STAGED_SPINE_RUN_PREFIX)
            for cluster in snapshot["clusters"]
        )

        report = build_atlas_coherence_report(snapshot)
        assert report["population"]["clusters"] >= 2
        notes = report["verdict"]["missing_fields_create_refactor_risk"]["notes"]
        assert not any("clusters[] empty" in note for note in notes)
        assert report["overall_coherence_verdict"] == "pass"
    finally:
        conn.close()


def test_export_atlas_snapshot_cli_populates_staged_clusters(
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    tmp_path: Path,
    mock_network_env: None,
    patched_staged_network: None,
) -> None:
    _run_staged_orchestrator_cli(temp_db, staging_dir, report_dir, patched_staged_network)
    out_path = tmp_path / "atlas_snapshot.json"
    exit_code = main(
        [
            "export-atlas-snapshot",
            "--db",
            str(temp_db),
            "--out",
            str(out_path),
            "--topic",
            EXPORT_TOPIC,
            "--domain",
            "creativity",
        ]
    )
    assert exit_code == 0
    snapshot = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(snapshot["clusters"]) >= 2
    coherence = build_atlas_coherence_report(snapshot)
    assert coherence["overall_coherence_verdict"] == "pass"
