"""Golden Test 10: research contract prevents topic drift."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

OUT_OF_SCOPE_QUESTION = "Will AI become conscious?"
IN_SCOPE_QUESTION = (
    "Does divergent prompting reduce AI-driven semantic convergence?"
)
DRIFT_REASON = "out_of_scope_topic_drift"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "research_contract_drift_test.sqlite"


def test_out_of_scope_followup_is_parked_with_drift_reason(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.modules.research_planner import GOLDEN_CONTRACT_ID

    assert (
        main(
            [
                "validate-contract",
                "--follow-up",
                OUT_OF_SCOPE_QUESTION,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        row = conn.execute(
            """
            SELECT status, reason
            FROM research_queue
            WHERE contract_id = ? AND item_type = 'question'
            """,
            (GOLDEN_CONTRACT_ID,),
        ).fetchone()
        assert row is not None
        assert row["status"] == "parked"
        assert row["reason"] == DRIFT_REASON
    finally:
        conn.close()


def test_in_scope_followup_is_accepted(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.modules.research_planner import GOLDEN_CONTRACT_ID

    assert (
        main(
            [
                "validate-contract",
                "--follow-up",
                OUT_OF_SCOPE_QUESTION,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "validate-contract",
                "--follow-up",
                IN_SCOPE_QUESTION,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        active = conn.execute(
            """
            SELECT status, reason, priority_score
            FROM research_queue
            WHERE contract_id = ? AND item_type = 'question' AND status = 'queued'
            """,
            (GOLDEN_CONTRACT_ID,),
        ).fetchall()
        parked = conn.execute(
            """
            SELECT status, reason
            FROM research_queue
            WHERE contract_id = ? AND item_type = 'question' AND status = 'parked'
            """,
            (GOLDEN_CONTRACT_ID,),
        ).fetchall()
        assert len(active) == 1
        assert len(parked) == 1
        assert active[0]["priority_score"] > 0
        assert parked[0]["reason"] == DRIFT_REASON
    finally:
        conn.close()


def test_validate_contract_is_idempotent(temp_db: Path) -> None:
    from rge.cli import main

    args = [
        "validate-contract",
        "--follow-up",
        OUT_OF_SCOPE_QUESTION,
        "--db",
        str(temp_db),
    ]
    assert main(args) == 0
    assert main(args) == 0

    from rge.db.connection import connect
    from rge.modules.research_planner import GOLDEN_CONTRACT_ID

    conn = connect(temp_db)
    try:
        count = conn.execute(
            """
            SELECT COUNT(*) FROM research_queue
            WHERE contract_id = ? AND item_type = 'question'
            """,
            (GOLDEN_CONTRACT_ID,),
        ).fetchone()[0]
        assert count == 1
    finally:
        conn.close()


def test_validate_contract_cli_emits_machine_readable_json(
    temp_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    assert (
        main(
            [
                "validate-contract",
                "--follow-up",
                IN_SCOPE_QUESTION,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "validate-contract"
    assert payload["status"] == "completed"
    assert payload["evaluation"]["decision"] == "accepted"
    assert payload["follow_up"] == IN_SCOPE_QUESTION
