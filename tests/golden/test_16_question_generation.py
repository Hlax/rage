"""Golden Test 16: new question generation respects research contract."""

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
CLAIM_FIXTURE = "claim_extraction_creativity_diversity_contradiction.json"
LINK_FIXTURE = "concept_linking_creativity_diversity_contradiction.json"
RELATIONSHIP_FIXTURE = "relationship_drafting_creativity_diversity_contradiction.json"
CONTRADICTION_FIXTURE = "contradiction_detection_creativity_diversity.json"
FOLLOWUP_FIXTURE = "claim_extraction_creativity_diversity_followup.json"
THEORY_FIXTURE = "theory_generation_creativity_diversity.json"
FOLLOWUP_QUESTION_FIXTURE = "followup_question_generation_golden_test_16.json"

ACTIVE_QUESTIONS = (
    "Does divergent prompting reduce semantic convergence in AI-assisted ideation?",
    "Does AI improve originality more when humans retain final selection control?",
    "Do AI-assisted workflows affect originality differently in writing versus design?",
)
PARKED_QUESTIONS = (
    "Will AI replace all creative jobs?",
    "Is AI conscious?",
    "Who owns copyright for AI-generated work?",
)
DRIFT_REASON = "out_of_scope_topic_drift"
ADJACENT_REASON = "adjacent_out_of_scope_topic"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "question_generation_test.sqlite"


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


def _run_base_graph(db_path: Path) -> None:
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
        source_id = conn.execute("SELECT id FROM sources").fetchone()[0]
    finally:
        conn.close()
    assert main(["extract-claims", "--source", source_id, "--db", str(db_path)]) == 0
    assert main(["link-concepts", "--source", source_id, "--db", str(db_path)]) == 0
    assert (
        main(["build-relationships", "--source", source_id, "--db", str(db_path)]) == 0
    )


def _prepare_contradiction_source(db_path: Path) -> None:
    from rge.cli import main

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
    from rge.db.connection import connect

    conn = connect(db_path)
    try:
        row = conn.execute(
            """
            SELECT id FROM sources
            WHERE title = 'creativity_ai_diversity_contradiction.txt'
            """
        ).fetchone()
        assert row is not None
        source_id = row[0]
    finally:
        conn.close()
    assert (
        main(
            [
                "extract-claims",
                "--source",
                source_id,
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
                source_id,
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
                source_id,
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
                "detect-contradictions",
                "--source",
                source_id,
                "--fixture",
                CONTRADICTION_FIXTURE,
                "--db",
                str(db_path),
            ]
        )
        == 0
    )


def _prepare_followup_source(db_path: Path) -> None:
    from rge.cli import main

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
    from rge.db.connection import connect

    conn = connect(db_path)
    try:
        row = conn.execute(
            """
            SELECT id FROM sources
            WHERE title = 'creativity_ai_diversity_followup_short.txt'
            """
        ).fetchone()
        assert row is not None
        source_id = row[0]
    finally:
        conn.close()
    assert (
        main(
            [
                "extract-claims",
                "--source",
                source_id,
                "--fixture",
                FOLLOWUP_FIXTURE,
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    assert main(["reconcile-scores", "--source", source_id, "--db", str(db_path)]) == 0


def _prepare_intelligence_context(db_path: Path, report_dir: Path) -> None:
    from rge.cli import main

    _run_base_graph(db_path)
    _prepare_contradiction_source(db_path)
    _prepare_followup_source(db_path)
    assert (
        main(
            [
                "generate-cluster-report",
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
                "generate-theory-candidates",
                "--domain",
                "creativity",
                "--db",
                str(db_path),
                "--fixture",
                THEORY_FIXTURE,
                "--output-dir",
                str(report_dir),
            ]
        )
        == 0
    )


def test_followup_generation_queues_on_scope_and_parks_off_scope(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.modules.research_planner import GOLDEN_CONTRACT_ID

    _prepare_intelligence_context(temp_db, report_dir)
    assert (
        main(
            [
                "generate-followup-questions",
                "--db",
                str(temp_db),
                "--fixture",
                FOLLOWUP_QUESTION_FIXTURE,
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        rows = conn.execute(
            """
            SELECT last_error, status, reason
            FROM research_queue
            WHERE contract_id = ? AND item_type = 'question'
            """,
            (GOLDEN_CONTRACT_ID,),
        ).fetchall()
        by_text = {row["last_error"]: row for row in rows}

        for question in ACTIVE_QUESTIONS:
            assert question in by_text
            assert by_text[question]["status"] == "queued"
            assert by_text[question]["reason"]

        for question in PARKED_QUESTIONS:
            assert question in by_text
            assert by_text[question]["status"] == "parked"
            assert by_text[question]["reason"]

        assert by_text[PARKED_QUESTIONS[0]]["reason"] == DRIFT_REASON
        assert by_text[PARKED_QUESTIONS[1]]["reason"] == DRIFT_REASON
        assert by_text[PARKED_QUESTIONS[2]]["reason"] == ADJACENT_REASON

        parked_in_active = conn.execute(
            """
            SELECT COUNT(*) FROM research_queue
            WHERE contract_id = ? AND item_type = 'question'
              AND status = 'queued'
              AND last_error IN (?, ?, ?)
            """,
            (GOLDEN_CONTRACT_ID, *PARKED_QUESTIONS),
        ).fetchone()[0]
        assert parked_in_active == 0
    finally:
        conn.close()


def test_followup_questions_are_not_generic_only(temp_db: Path, report_dir: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.modules.research_planner import GOLDEN_CONTRACT_ID

    _prepare_intelligence_context(temp_db, report_dir)
    assert (
        main(
            [
                "generate-followup-questions",
                "--db",
                str(temp_db),
                "--fixture",
                FOLLOWUP_QUESTION_FIXTURE,
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        queued = conn.execute(
            """
            SELECT last_error FROM research_queue
            WHERE contract_id = ? AND item_type = 'question' AND status = 'queued'
            """,
            (GOLDEN_CONTRACT_ID,),
        ).fetchall()
        texts = " ".join(row["last_error"].casefold() for row in queued)
        assert "originality" in texts or "semantic" in texts or "ideation" in texts
        assert "what do you think" not in texts
    finally:
        conn.close()


def test_generate_followup_questions_is_idempotent(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.modules.research_planner import GOLDEN_CONTRACT_ID

    _prepare_intelligence_context(temp_db, report_dir)
    args = [
        "generate-followup-questions",
        "--db",
        str(temp_db),
        "--fixture",
        FOLLOWUP_QUESTION_FIXTURE,
    ]
    assert main(args) == 0
    assert main(args) == 0

    conn = connect(temp_db)
    try:
        count = conn.execute(
            """
            SELECT COUNT(*) FROM research_queue
            WHERE contract_id = ? AND item_type = 'question'
            """,
            (GOLDEN_CONTRACT_ID,),
        ).fetchone()[0]
        assert count >= len(ACTIVE_QUESTIONS) + len(PARKED_QUESTIONS)
    finally:
        conn.close()


def test_generate_followup_questions_cli_emits_machine_readable_json(
    temp_db: Path, report_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    _prepare_intelligence_context(temp_db, report_dir)
    capsys.readouterr()
    assert (
        main(
            [
                "generate-followup-questions",
                "--db",
                str(temp_db),
                "--fixture",
                FOLLOWUP_QUESTION_FIXTURE,
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "generate-followup-questions"
    assert payload["status"] == "completed"
    assert payload["queued_count"] >= len(ACTIVE_QUESTIONS)
    assert payload["parked_count"] >= len(PARKED_QUESTIONS)
    assert payload["followups"]
