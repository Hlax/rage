"""Golden Test 19: every research run produces a machine-readable run report."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
CONTRADICTION_SOURCE = (
    REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_contradiction.txt"
)
FOLLOWUP_SOURCE = (
    REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_followup_short.txt"
)
MISSING_QUOTE_FIXTURE = "claim_extraction_valid_and_missing_quote.json"
FOLLOWUP_FIXTURE = "claim_extraction_creativity_diversity_followup.json"
CLAIM_FIXTURE = "claim_extraction_creativity_diversity_contradiction.json"
LINK_FIXTURE = "concept_linking_creativity_diversity_contradiction.json"
RELATIONSHIP_FIXTURE = "relationship_drafting_creativity_diversity_contradiction.json"
GOLDEN_RUN_ID = "run_golden_test_19"
GOLDEN_TOPIC = "Does AI improve creative output while reducing diversity?"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "run_report_test.sqlite"


@pytest.fixture()
def report_dir(tmp_path: Path) -> Path:
    return tmp_path / "reports"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def _prepare_fixture_spine(db_path: Path) -> None:
    from rge.cli import main

    assert main(["queue-sources", "--db", str(db_path)]) == 0

    assert (
        main(
            [
                "ingest",
                str(BASE_SOURCE),
                "--domain",
                "creativity",
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    from rge.db.connection import connect

    conn = connect(db_path)
    try:
        base_source_id = conn.execute("SELECT id FROM sources").fetchone()[0]
    finally:
        conn.close()

    assert (
        main(
            [
                "extract-claims",
                "--source",
                base_source_id,
                "--fixture",
                MISSING_QUOTE_FIXTURE,
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    assert main(["link-concepts", "--source", base_source_id, "--db", str(db_path)]) == 0
    assert (
        main(["build-relationships", "--source", base_source_id, "--db", str(db_path)])
        == 0
    )
    assert (
        main(["reconcile-scores", "--source", base_source_id, "--db", str(db_path)])
        == 0
    )

    assert (
        main(
            [
                "ingest",
                str(FOLLOWUP_SOURCE),
                "--domain",
                "creativity",
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    conn = connect(db_path)
    try:
        followup_source_id = conn.execute(
            """
            SELECT id FROM sources
            WHERE title = 'creativity_ai_diversity_followup_short.txt'
            """
        ).fetchone()[0]
    finally:
        conn.close()
    assert (
        main(
            [
                "extract-claims",
                "--source",
                followup_source_id,
                "--fixture",
                FOLLOWUP_FIXTURE,
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    assert (
        main(
            ["link-concepts", "--source", followup_source_id, "--db", str(db_path)]
        )
        == 0
    )
    assert (
        main(
            [
                "build-relationships",
                "--source",
                followup_source_id,
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    assert (
        main(
            ["reconcile-scores", "--source", followup_source_id, "--db", str(db_path)]
        )
        == 0
    )

    assert (
        main(
            [
                "ingest",
                str(CONTRADICTION_SOURCE),
                "--domain",
                "creativity",
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    conn = connect(db_path)
    try:
        contradiction_source_id = conn.execute(
            """
            SELECT id FROM sources
            WHERE title = 'creativity_ai_diversity_contradiction.txt'
            """
        ).fetchone()[0]
    finally:
        conn.close()

    assert (
        main(
            [
                "extract-claims",
                "--source",
                contradiction_source_id,
                "--fixture",
                CLAIM_FIXTURE,
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "link-concepts",
                "--source",
                contradiction_source_id,
                "--fixture",
                LINK_FIXTURE,
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "build-relationships",
                "--source",
                contradiction_source_id,
                "--fixture",
                RELATIONSHIP_FIXTURE,
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "reconcile-scores",
                "--source",
                contradiction_source_id,
                "--db",
                str(db_path),
            ]
        )
        == 0
    )


def test_run_report_includes_required_counters_and_failure_modes(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import RunReportRepository
    from rge.modules.research_planner import GOLDEN_CONTRACT_ID

    _prepare_fixture_spine(temp_db)
    assert (
        main(
            [
                "generate-run-report",
                "--run-id",
                GOLDEN_RUN_ID,
                "--topic",
                GOLDEN_TOPIC,
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
                "--output-dir",
                str(report_dir),
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        assert RunReportRepository(conn).count() == 1
        row = conn.execute(
            "SELECT run_id, topic, domain_pack, report_json FROM run_reports"
        ).fetchone()
        report = json.loads(row["report_json"])

        assert row["run_id"] == GOLDEN_RUN_ID
        assert row["topic"] == GOLDEN_TOPIC
        assert row["domain_pack"] == "creativity"
        assert report["report_type"] == "run_report"
        assert report["run_id"] == GOLDEN_RUN_ID
        assert report["topic"] == GOLDEN_TOPIC
        assert report["domain_pack"] == "creativity"
        assert report["contract_id"] == GOLDEN_CONTRACT_ID
        assert report["purpose"]["schema_version"] == "purpose_metadata_v0.1.0"
        assert "evidence_review" in report["research_intent"]
        assert "reasoning_training_candidate" in report["asset_affordance"]
        assert report["evidence_maturity"] == "seed"
        assert report["training_suitability"] == "not_ready"
        assert report["sources_discovered"] >= 1
        assert report["sources_ingested"] >= 2
        assert report["claims_extracted"] >= 2
        assert report["claims_accepted"] >= 1
        assert report["claims_rejected"] >= 1
        assert report["relationships_updated"] >= 1
        assert report["score_events_created"] >= 1
        assert report["evidence_atoms_created"] == 0
        assert isinstance(report["top_failure_modes"], list)
        assert report["top_failure_modes"]
        reasons = {item["reason"] for item in report["top_failure_modes"]}
        assert "missing_quote_span" in reasons
        assert all(
            isinstance(item["reason"], str) and isinstance(item["count"], int)
            for item in report["top_failure_modes"]
        )
        assert report["tickets_generated"] == 0

        research_run = conn.execute(
            "SELECT status FROM research_runs WHERE id = ?",
            (GOLDEN_RUN_ID,),
        ).fetchone()
        assert research_run is not None
    finally:
        conn.close()

    output_file = report_dir / "run_report_latest.json"
    assert output_file.is_file()


def test_run_report_is_queryable_json_not_prose_only(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    _prepare_fixture_spine(temp_db)
    assert (
        main(
            [
                "generate-run-report",
                "--run-id",
                GOLDEN_RUN_ID,
                "--db",
                str(temp_db),
                "--output-dir",
                str(report_dir),
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        row = conn.execute(
            "SELECT report_json FROM run_reports WHERE run_id = ?",
            (GOLDEN_RUN_ID,),
        ).fetchone()
        report = json.loads(row["report_json"])
        assert isinstance(report, dict)
        assert "claims_accepted" in report
        assert "top_failure_modes" in report
    finally:
        conn.close()


def test_generate_run_report_is_idempotent(temp_db: Path, report_dir: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import RunReportRepository

    _prepare_fixture_spine(temp_db)
    args = [
        "generate-run-report",
        "--run-id",
        GOLDEN_RUN_ID,
        "--db",
        str(temp_db),
        "--output-dir",
        str(report_dir),
    ]
    assert main(args) == 0
    assert main(args) == 0

    conn = connect(temp_db)
    try:
        assert RunReportRepository(conn).count() == 1
    finally:
        conn.close()


def test_generate_run_report_cli_emits_machine_readable_json(
    temp_db: Path, report_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    _prepare_fixture_spine(temp_db)
    capsys.readouterr()
    assert (
        main(
            [
                "generate-run-report",
                "--run-id",
                GOLDEN_RUN_ID,
                "--db",
                str(temp_db),
                "--output-dir",
                str(report_dir),
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "generate-run-report"
    assert payload["status"] in {"generated", "already_generated"}
    assert payload["report_id"].startswith("rrpt_")
    assert payload["report"]["run_id"] == GOLDEN_RUN_ID
    assert payload["report"]["top_failure_modes"]
