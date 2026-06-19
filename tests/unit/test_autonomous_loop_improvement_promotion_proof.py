"""Autonomous loop → improvement promotion closure proof (ticket-363).

Mock-only: autonomous researcher loop emits quality-driven DB-backed drafts that
promote to builder-consumable queue ticket JSON via promote-improvement-ticket.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.cli import FIXTURE_RUN_ID, GOLDEN_MVP_TOPIC, main
from rge.db.connection import connect
from rge.modules.autonomous_researcher_loop import execute_autonomous_researcher_loop
from rge.modules.ticket_writer import (
    improvement_draft_is_actionable,
    promote_improvement_ticket,
    validate_builder_ticket,
)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "autonomous_promotion.sqlite"


@pytest.fixture()
def artifact_dir(tmp_path: Path) -> Path:
    return tmp_path / "autonomous_promotion_artifacts"


@pytest.fixture()
def queue_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "queue_tickets"
    directory.mkdir()
    return directory


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def test_autonomous_loop_quality_draft_promotes_from_database(
    temp_db: Path,
    artifact_dir: Path,
    queue_dir: Path,
) -> None:
    result = execute_autonomous_researcher_loop(
        topic=GOLDEN_MVP_TOPIC,
        domain="creativity",
        db_path=temp_db,
        artifact_dir=artifact_dir,
        run_id=FIXTURE_RUN_ID,
        recommended_ticket_id="ticket-363",
    )
    assert result["status"] == "completed"

    draft_path = Path(result["artifacts"]["improvement_tickets"])
    drafts = json.loads(draft_path.read_text(encoding="utf-8"))
    assert len(drafts) >= 1
    draft = drafts[0]
    assert draft["failure_reason"] == "weak_ticket_generation"
    assert improvement_draft_is_actionable(draft)

    conn = connect(temp_db)
    try:
        promotion = promote_improvement_ticket(
            queue_ticket_id="ticket-363",
            reviewed=True,
            output_dir=queue_dir,
            conn=conn,
            run_id=FIXTURE_RUN_ID,
            failure_reason="weak_ticket_generation",
        )
    finally:
        conn.close()

    assert promotion["status"] == "promoted"
    output_path = Path(promotion["output_path"])
    queue_ticket = json.loads(output_path.read_text(encoding="utf-8"))
    assert queue_ticket["id"] == "ticket-363"
    assert queue_ticket["status"] == "proposed"
    assert validate_builder_ticket(queue_ticket) == []


def test_autonomous_loop_quality_draft_promotes_via_cli_from_json(
    temp_db: Path,
    artifact_dir: Path,
    queue_dir: Path,
) -> None:
    result = execute_autonomous_researcher_loop(
        topic=GOLDEN_MVP_TOPIC,
        domain="creativity",
        db_path=temp_db,
        artifact_dir=artifact_dir,
        run_id=FIXTURE_RUN_ID,
        recommended_ticket_id="ticket-364",
    )
    assert result["status"] == "completed"

    draft_path = Path(result["artifacts"]["improvement_tickets"])
    single_draft = json.loads(draft_path.read_text(encoding="utf-8"))[0]
    single_draft_path = artifact_dir / "single_improvement_draft.json"
    single_draft_path.write_text(json.dumps(single_draft, indent=2) + "\n", encoding="utf-8")

    exit_code = main(
        [
            "promote-improvement-ticket",
            "--queue-ticket-id",
            "ticket-364",
            "--from-json",
            str(single_draft_path),
            "--confirm",
            "--output-dir",
            str(queue_dir),
        ]
    )
    assert exit_code == 0

    queue_ticket = json.loads((queue_dir / "ticket-364.json").read_text(encoding="utf-8"))
    assert queue_ticket["id"] == "ticket-364"
    assert validate_builder_ticket(queue_ticket) == []
    assert queue_ticket["evidence"]
