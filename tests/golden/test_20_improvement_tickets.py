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


def test_golden_covered_overgeneralized_scope_does_not_generate_improvement_ticket(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.db.connection import connect
    from rge.db.repositories import ImprovementTicketRepository
    from rge.modules.run_evaluator import build_run_report

    _prepare_rejection_spine(temp_db)
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
                str(temp_db),
                "--output-dir",
                str(report_dir),
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        report = build_run_report(
            conn,
            run_id=GOLDEN_RUN_ID,
            topic=GOLDEN_TOPIC,
            domain_pack="creativity",
        )
        reasons = {mode["reason"] for mode in report["top_failure_modes"]}
        assert "overgeneralized_scope" in reasons
    finally:
        conn.close()

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

    output_file = report_dir / "improvement_ticket_latest.json"
    assert output_file.is_file()
    assert json.loads(output_file.read_text(encoding="utf-8")) == []

    conn = connect(temp_db)
    try:
        repo = ImprovementTicketRepository(conn)
        for record in repo.list_for_run(GOLDEN_RUN_ID):
            ticket = json.loads(record.ticket_json)
            assert ticket.get("failure_reason") != "overgeneralized_scope"
            assert ticket["title"] != GOLDEN_OVERGENERALIZED_TITLE
    finally:
        conn.close()


def test_improvement_ticket_generated_from_weak_concept_mapping(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.modules.ticket_writer import write_improvement_tickets

    tickets = write_improvement_tickets(
        {
            "run_id": "run_actionable_weak_concept",
            "top_failure_modes": [{"reason": "weak_concept_mapping", "count": 1}],
        }
    )
    assert len(tickets) == 1
    ticket = tickets[0]
    assert ticket["type"] == "improvement_ticket"
    assert ticket["priority"] == "medium"
    assert ticket["title"] == "Improve concept mapping validation"
    assert ticket["failure_reason"] == "weak_concept_mapping"
    assert ticket["problem"]
    assert any(
        "run_report:" in item and "weak_concept_mapping_count=" in item
        for item in ticket["evidence"]
    )
    assert ticket["affected_modules"]
    assert ticket["expected_files"]
    assert ticket["acceptance_criteria"]
    assert ticket["test_plan"]
    assert ticket["non_goals"]
    assert ticket["risk_level"] == "medium"
    assert ticket["rollback_plan"]
    assert ticket["status"] == "draft"

    output_file = report_dir / "improvement_ticket_latest.json"
    report_dir.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(tickets, indent=2) + "\n", encoding="utf-8")
    assert output_file.is_file()


def test_improvement_tickets_are_actionable_not_vague(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.modules.ticket_writer import write_improvement_tickets

    tickets = write_improvement_tickets(
        {
            "run_id": GOLDEN_RUN_ID,
            "top_failure_modes": [{"reason": "weak_concept_mapping", "count": 1}],
        }
    )
    assert tickets
    for ticket in tickets:
        assert len(ticket["title"]) >= 10
        assert len(ticket["problem"]) >= 20
        assert ticket["acceptance_criteria"]
        assert ticket["test_plan"]


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
        assert count_after_first == 0
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
    assert payload["status"] == "skipped_golden_covered"
    assert payload["ticket_ids"] == []
    assert payload["tickets"] == []


def test_golden_covered_missing_quote_span_does_not_generate_improvement_ticket(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.db.connection import connect
    from rge.db.repositories import ImprovementTicketRepository
    from rge.modules.run_evaluator import build_run_report

    _prepare_rejection_spine(temp_db)
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
                str(temp_db),
                "--output-dir",
                str(report_dir),
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        report = build_run_report(
            conn,
            run_id=GOLDEN_RUN_ID,
            topic=GOLDEN_TOPIC,
            domain_pack="creativity",
        )
        reasons = {mode["reason"] for mode in report["top_failure_modes"]}
        assert "missing_quote_span" in reasons
    finally:
        conn.close()

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

    conn = connect(temp_db)
    try:
        repo = ImprovementTicketRepository(conn)
        assert repo.count_for_run(GOLDEN_RUN_ID) == 0
    finally:
        conn.close()


def test_write_improvement_tickets_skips_golden_covered_modes() -> None:
    from rge.modules.ticket_writer import write_improvement_tickets

    run_report = {
        "run_id": "run_only_golden_covered",
        "top_failure_modes": [
            {"reason": "missing_quote_span", "count": 1},
            {"reason": "overgeneralized_scope", "count": 1},
        ],
    }
    assert write_improvement_tickets(run_report) == []


def test_write_improvement_tickets_still_generates_weak_concept_mapping() -> None:
    from rge.modules.ticket_writer import write_improvement_tickets

    run_report = {
        "run_id": "run_weak_concept_only",
        "top_failure_modes": [{"reason": "weak_concept_mapping", "count": 1}],
    }
    tickets = write_improvement_tickets(run_report)
    assert len(tickets) == 1
    assert tickets[0]["failure_reason"] == "weak_concept_mapping"
