"""Golden Test 20: rejection patterns generate improvement tickets."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
FOLLOWUP_SOURCE = (
    REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_followup_short.txt"
)
OVERGENERALIZED_FIXTURE = "claim_extraction_overgeneralized.json"
MISSING_QUOTE_FIXTURE = "claim_extraction_valid_and_missing_quote.json"
GOLDEN_RUN_ID = "run_golden_test_20"
GOLDEN_TOPIC = "Does AI improve creative output while reducing diversity?"
GOLDEN_OVERGENERALIZED_TITLE = "Improve claim extractor scope preservation"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "improvement_ticket_test.sqlite"


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


def _prepare_rejection_spine(db_path: Path) -> None:
    from rge.cli import main

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
                OVERGENERALIZED_FIXTURE,
                "--db",
                str(db_path),
            ]
        )
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
                MISSING_QUOTE_FIXTURE,
                "--db",
                str(db_path),
            ]
        )
        == 0
    )


def _generate_run_and_tickets(db_path: Path, report_dir: Path) -> None:
    from rge.cli import main

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
                str(db_path),
                "--output-dir",
                str(report_dir),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "generate-improvement-tickets",
                "--run-id",
                GOLDEN_RUN_ID,
                "--db",
                str(db_path),
                "--output-dir",
                str(report_dir),
            ]
        )
        == 0
    )


def test_improvement_ticket_generated_from_overgeneralized_rejections(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.db.connection import connect
    from rge.db.repositories import ImprovementTicketRepository

    _prepare_rejection_spine(temp_db)
    _generate_run_and_tickets(temp_db, report_dir)

    conn = connect(temp_db)
    try:
        repo = ImprovementTicketRepository(conn)
        assert repo.count_for_run(GOLDEN_RUN_ID) >= 1
        records = repo.list_for_run(GOLDEN_RUN_ID)
        overgeneralized = next(
            (
                json.loads(record.ticket_json)
                for record in records
                if "overgeneralized_scope" in record.evidence_json
            ),
            None,
        )
        assert overgeneralized is not None
        assert overgeneralized["type"] == "improvement_ticket"
        assert overgeneralized["priority"] == "high"
        assert overgeneralized["title"] == GOLDEN_OVERGENERALIZED_TITLE
        assert overgeneralized["problem"]
        assert overgeneralized["evidence"]
        assert any(
            "run_report:" in item and "overgeneralized_scope_count=" in item
            for item in overgeneralized["evidence"]
        )
        assert overgeneralized["affected_modules"]
        assert overgeneralized["expected_files"]
        assert overgeneralized["acceptance_criteria"]
        assert overgeneralized["test_plan"]
        assert overgeneralized["non_goals"]
        assert overgeneralized["risk_level"] == "medium"
        assert overgeneralized["rollback_plan"]
        assert overgeneralized["status"] == "draft"
    finally:
        conn.close()

    output_file = report_dir / "improvement_ticket_latest.json"
    assert output_file.is_file()


def test_improvement_tickets_are_actionable_not_vague(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.db.connection import connect

    _prepare_rejection_spine(temp_db)
    _generate_run_and_tickets(temp_db, report_dir)

    conn = connect(temp_db)
    try:
        rows = conn.execute(
            "SELECT title, problem, acceptance_criteria_json, test_plan_json FROM improvement_tickets"
        ).fetchall()
        assert rows
        for row in rows:
            assert len(row["title"]) >= 10
            assert len(row["problem"]) >= 20
            assert json.loads(row["acceptance_criteria_json"])
            assert json.loads(row["test_plan_json"])
    finally:
        conn.close()


def test_generate_improvement_tickets_is_idempotent(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ImprovementTicketRepository

    _prepare_rejection_spine(temp_db)
    _generate_run_and_tickets(temp_db, report_dir)
    args = [
        "generate-improvement-tickets",
        "--run-id",
        GOLDEN_RUN_ID,
        "--db",
        str(temp_db),
        "--output-dir",
        str(report_dir),
    ]
    assert main(args) == 0

    conn = connect(temp_db)
    try:
        count_after_first = ImprovementTicketRepository(conn).count_for_run(GOLDEN_RUN_ID)
        assert main(args) == 0
        assert (
            ImprovementTicketRepository(conn).count_for_run(GOLDEN_RUN_ID)
            == count_after_first
        )
    finally:
        conn.close()


def test_generate_improvement_tickets_cli_emits_machine_readable_json(
    temp_db: Path, report_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    _prepare_rejection_spine(temp_db)
    _generate_run_and_tickets(temp_db, report_dir)
    capsys.readouterr()
    assert (
        main(
            [
                "generate-improvement-tickets",
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
    assert payload["command"] == "generate-improvement-tickets"
    assert payload["status"] in {"generated", "already_generated"}
    assert payload["ticket_ids"][0].startswith("imp_")
    assert payload["tickets"]
    titles = {ticket["title"] for ticket in payload["tickets"]}
    assert GOLDEN_OVERGENERALIZED_TITLE in titles
