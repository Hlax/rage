"""Golden Test 21: improvement tickets can be consumed by builder agents."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.modules.ticket_writer import (
    BUILDER_REQUIRED_TICKET_FIELDS,
    GOLDEN_COVERED_IMPROVEMENT_FAILURE_MODES,
    IMPROVEMENT_FAILURE_TEMPLATES,
    validate_builder_ticket,
    write_improvement_tickets,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
FOLLOWUP_SOURCE = (
    REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_followup_short.txt"
)
OVERGENERALIZED_FIXTURE = "claim_extraction_overgeneralized.json"
MISSING_QUOTE_FIXTURE = "claim_extraction_valid_and_missing_quote.json"
GOLDEN_RUN_ID = "run_golden_test_21"
GOLDEN_TOPIC = "Does AI improve creative output while reducing diversity?"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "builder_ticket_test.sqlite"


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


def test_failure_templates_include_all_builder_required_fields() -> None:
    run_report = {
        "run_id": "run_template_check",
        "top_failure_modes": [
            {"reason": reason, "count": 1}
            for reason in IMPROVEMENT_FAILURE_TEMPLATES
            if reason not in GOLDEN_COVERED_IMPROVEMENT_FAILURE_MODES
        ],
    }
    tickets = write_improvement_tickets(run_report)
    expected = {
        reason
        for reason in IMPROVEMENT_FAILURE_TEMPLATES
        if reason not in GOLDEN_COVERED_IMPROVEMENT_FAILURE_MODES
    }
    assert len(tickets) == len(expected)
    for ticket in tickets:
        for field in BUILDER_REQUIRED_TICKET_FIELDS:
            assert field in ticket
            assert ticket[field]
        assert validate_builder_ticket(ticket) == []


def _seed_weak_concept_improvement_ticket(db_path: Path, report_dir: Path) -> None:
    """Persist a non-golden-covered draft for promotion round-trip tests."""
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ImprovementTicketRepository

    _prepare_rejection_spine(db_path)
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
    tickets = write_improvement_tickets(
        {
            "run_id": GOLDEN_RUN_ID,
            "top_failure_modes": [{"reason": "weak_concept_mapping", "count": 1}],
        }
    )
    assert len(tickets) == 1
    ticket = tickets[0]
    conn = connect(db_path)
    try:
        ImprovementTicketRepository(conn).insert(
            run_id=GOLDEN_RUN_ID,
            failure_reason="weak_concept_mapping",
            priority=ticket["priority"],
            title=ticket["title"],
            problem=ticket["problem"],
            evidence=ticket["evidence"],
            affected_modules=ticket["affected_modules"],
            expected_files=ticket["expected_files"],
            acceptance_criteria=ticket["acceptance_criteria"],
            test_plan=ticket["test_plan"],
            non_goals=ticket["non_goals"],
            risk_level=ticket["risk_level"],
            rollback_plan=ticket["rollback_plan"],
            ticket=ticket,
        )
        conn.commit()
    finally:
        conn.close()


def test_generated_improvement_tickets_are_builder_consumable(
    temp_db: Path, report_dir: Path
) -> None:
    tickets = write_improvement_tickets(
        {
            "run_id": GOLDEN_RUN_ID,
            "top_failure_modes": [{"reason": "weak_concept_mapping", "count": 1}],
        }
    )
    assert tickets
    for ticket in tickets:
        violations = validate_builder_ticket(ticket)
        assert violations == [], f"ticket {ticket.get('title')}: {violations}"
        assert ticket["affected_modules"]
        assert ticket["expected_files"]
        assert all(
            isinstance(item, str) and len(item.strip()) >= 10
            for item in ticket["acceptance_criteria"]
        )


def test_validate_builder_ticket_rejects_missing_required_fields() -> None:
    violations = validate_builder_ticket({"title": "Short"})
    assert any("missing required field" in item for item in violations)


def test_validate_builder_ticket_rejects_vague_acceptance_criteria() -> None:
    ticket = {
        "title": "Improve claim extractor scope preservation",
        "problem": "High rejection rate caused by overgeneralized claims.",
        "evidence": ["run_report:run_test:overgeneralized_scope_count=1"],
        "affected_modules": ["claim_extractor"],
        "expected_files": ["rge/modules/claim_extractor.py"],
        "acceptance_criteria": ["make it better"],
        "test_plan": ["pytest tests/golden/test_02_claim_extraction.py"],
        "non_goals": ["Do not refactor orchestration."],
        "risk_level": "medium",
        "rollback_plan": "Revert extractor changes.",
    }
    violations = validate_builder_ticket(ticket)
    assert any("vague acceptance criterion" in item for item in violations)


def test_promote_improvement_ticket_round_trip(
    temp_db: Path, report_dir: Path, tmp_path: Path
) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.modules.ticket_writer import promote_improvement_ticket

    _seed_weak_concept_improvement_ticket(temp_db, report_dir)

    queue_dir = tmp_path / "tickets"
    conn = connect(temp_db)
    try:
        result = promote_improvement_ticket(
            queue_ticket_id="ticket-991",
            reviewed=True,
            output_dir=queue_dir,
            conn=conn,
            run_id=GOLDEN_RUN_ID,
            failure_reason="weak_concept_mapping",
        )
        assert result["status"] == "promoted"
        output_path = Path(result["output_path"])
        assert output_path.is_file()
        queue_ticket = json.loads(output_path.read_text(encoding="utf-8"))
        assert queue_ticket["id"] == "ticket-991"
        assert queue_ticket["status"] == "proposed"
        assert validate_builder_ticket(queue_ticket) == []
    finally:
        conn.close()

    assert (
        main(
            [
                "promote-improvement-ticket",
                "--queue-ticket-id",
                "ticket-992",
                "--run-id",
                GOLDEN_RUN_ID,
                "--failure-reason",
                "missing_quote_span",
                "--db",
                str(temp_db),
                "--output-dir",
                str(queue_dir),
            ]
        )
        == 1
    )


def test_promote_improvement_ticket_cli_with_confirm(
    temp_db: Path, report_dir: Path, tmp_path: Path
) -> None:
    from rge.cli import main

    _seed_weak_concept_improvement_ticket(temp_db, report_dir)
    queue_dir = tmp_path / "tickets"

    assert (
        main(
            [
                "promote-improvement-ticket",
                "--queue-ticket-id",
                "ticket-993",
                "--run-id",
                GOLDEN_RUN_ID,
                "--failure-reason",
                "weak_concept_mapping",
                "--confirm",
                "--db",
                str(temp_db),
                "--output-dir",
                str(queue_dir),
            ]
        )
        == 0
    )
    promoted = json.loads((queue_dir / "ticket-993.json").read_text(encoding="utf-8"))
    assert promoted["status"] == "proposed"
    assert validate_builder_ticket(promoted) == []


def test_pipeline_paths_do_not_auto_promote_tickets() -> None:
    import inspect

    from rge.cli import execute_fixture_mode_run
    from rge.modules.ticket_writer import generate_improvement_tickets

    fixture_source = inspect.getsource(execute_fixture_mode_run)
    generate_source = inspect.getsource(generate_improvement_tickets)
    assert "promote_improvement_ticket" not in fixture_source
    assert "promote_improvement_ticket" not in generate_source
