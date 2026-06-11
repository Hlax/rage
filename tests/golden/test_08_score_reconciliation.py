"""Golden Test 8: score reconciliation updates relationship confidence with history."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
FOLLOWUP_SOURCE = (
    REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_followup_short.txt"
)
FOLLOWUP_FIXTURE = "claim_extraction_creativity_diversity_followup.json"
GOLDEN_OLD_SCORE = 0.52
GOLDEN_NEW_SCORE = 0.64
GOLDEN_REASON = "New supporting empirical claim from higher-credibility source."


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "score_reconciliation_test.sqlite"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def _run_base_graph(db_path: Path) -> str:
    from rge.cli import main

    assert (
        main(
            [
                "ingest",
                str(FIXTURE_SOURCE),
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
    return source_id


def _seed_golden_initial_confidence(db_path: Path) -> str:
    from rge.db.connection import connect

    conn = connect(db_path)
    try:
        row = conn.execute(
            """
            SELECT r.id
            FROM relationships r
            JOIN concepts sub ON sub.id = r.subject_concept_id
            JOIN concepts obj ON obj.id = r.object_concept_id
            WHERE sub.label = 'AI assistance'
              AND obj.label = 'semantic diversity'
              AND r.predicate = 'may_reduce'
            """
        ).fetchone()
        assert row is not None
        relationship_id = row[0]
        conn.execute(
            "UPDATE relationships SET confidence = ? WHERE id = ?",
            (GOLDEN_OLD_SCORE, relationship_id),
        )
        conn.commit()
        return relationship_id
    finally:
        conn.close()


def _ingest_followup_source(db_path: Path) -> str:
    from rge.cli import main
    from rge.db.connection import connect

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
        row = conn.execute(
            """
            SELECT id FROM sources
            WHERE title = ?
            """,
            ("creativity_ai_diversity_followup_short.txt",),
        ).fetchone()
        assert row is not None
        followup_id = row[0]
    finally:
        conn.close()
    assert (
        main(
            [
                "extract-claims",
                "--source",
                followup_id,
                "--db",
                str(db_path),
                "--fixture",
                FOLLOWUP_FIXTURE,
            ]
        )
        == 0
    )
    return followup_id


def test_score_reconciliation_updates_confidence_with_history(
    temp_db: Path,
) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import RelationshipRepository, ScoreEventRepository
    from rge.modules.score_reconciler import FORMULA_VERSION

    _run_base_graph(temp_db)
    relationship_id = _seed_golden_initial_confidence(temp_db)
    followup_source_id = _ingest_followup_source(temp_db)

    assert (
        main(
            [
                "reconcile-scores",
                "--source",
                followup_source_id,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        relationship = RelationshipRepository(conn).get_by_id(relationship_id)
        assert relationship is not None
        assert relationship["confidence"] == pytest.approx(GOLDEN_NEW_SCORE)

        events = ScoreEventRepository(conn).list_for_entity(
            "relationship", relationship_id
        )
        assert len(events) == 1
        event = events[0]
        assert event["old_score"] == pytest.approx(GOLDEN_OLD_SCORE)
        assert event["new_score"] == pytest.approx(GOLDEN_NEW_SCORE)
        assert event["triggering_claim_id"]
        assert event["triggering_source_id"] == followup_source_id
        assert event["reason"] == GOLDEN_REASON
        assert event["formula_version"] == FORMULA_VERSION
    finally:
        conn.close()


def test_score_events_survive_process_restart(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ScoreEventRepository

    _run_base_graph(temp_db)
    relationship_id = _seed_golden_initial_confidence(temp_db)
    followup_source_id = _ingest_followup_source(temp_db)
    assert (
        main(
            [
                "reconcile-scores",
                "--source",
                followup_source_id,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        count = len(
            ScoreEventRepository(conn).list_for_entity("relationship", relationship_id)
        )
        assert count == 1
    finally:
        conn.close()

    conn2 = connect(temp_db)
    try:
        events = ScoreEventRepository(conn2).list_for_entity(
            "relationship", relationship_id
        )
        assert len(events) == 1
        assert events[0]["old_score"] == pytest.approx(GOLDEN_OLD_SCORE)
    finally:
        conn2.close()


def test_reconcile_scores_is_idempotent(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ScoreEventRepository

    _run_base_graph(temp_db)
    _seed_golden_initial_confidence(temp_db)
    followup_source_id = _ingest_followup_source(temp_db)
    args = [
        "reconcile-scores",
        "--source",
        followup_source_id,
        "--db",
        str(temp_db),
    ]
    assert main(args) == 0
    assert main(args) == 0

    conn = connect(temp_db)
    try:
        events = ScoreEventRepository(conn).list_for_source(followup_source_id)
        assert len(events) == 1
    finally:
        conn.close()


def test_reconcile_scores_cli_emits_machine_readable_json(
    temp_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    _run_base_graph(temp_db)
    _seed_golden_initial_confidence(temp_db)
    followup_source_id = _ingest_followup_source(temp_db)
    capsys.readouterr()
    exit_code = main(
        [
            "reconcile-scores",
            "--source",
            followup_source_id,
            "--db",
            str(temp_db),
        ]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["command"] == "reconcile-scores"
    assert payload["score_events_created"] == 1
    assert payload["relationships_updated"] == 1
    assert payload["score_events"][0]["new_score"] == pytest.approx(GOLDEN_NEW_SCORE)
