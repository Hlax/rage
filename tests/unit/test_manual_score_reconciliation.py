"""Manual source score reconciliation proof (ticket-099)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.modules.score_reconciler import (
    FORMULA_VERSION,
    STRONGER_SOURCE_BOOST,
    STRONGER_SOURCE_REASON,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNTHNOTE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "manual_synthnote.txt"
FOLLOWUP_SOURCE = REPO_ROOT / "fixtures" / "sources" / "manual_synthnote_followup.txt"
SYNTHNOTE_TITLE = (
    "Synthetic Source Note: AI-Assisted Ideation and Semantic Diversity"
)
FOLLOWUP_TITLE = (
    "Synthetic Follow-Up Note: AI Assistance and Semantic Diversity Replication"
)
FOLLOWUP_CHECKSUM = (
    "c5d1add68657e7ece8286c956cc5b3c494a45d33495ceb48927dd6d9ce628a16"
)
INITIAL_CONFIDENCE = 0.5
EXPECTED_NEW_CONFIDENCE = round(INITIAL_CONFIDENCE + STRONGER_SOURCE_BOOST, 2)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "manual_score_reconciliation.sqlite"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def _run_synthnote_spine(db_path: Path) -> str:
    from rge.cli import main
    from rge.db.connection import connect

    assert (
        main(
            [
                "ingest",
                str(SYNTHNOTE_SOURCE),
                "--domain",
                "creativity",
                "--source-type",
                "manual_text",
                "--source-title",
                SYNTHNOTE_TITLE,
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
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
    assert (
        main(["detect-contradictions", "--source", source_id, "--db", str(db_path)]) == 0
    )
    return source_id


def _ingest_followup_manual_source(db_path: Path) -> str:
    from rge.cli import main
    from rge.db.connection import connect

    assert (
        main(
            [
                "ingest",
                str(FOLLOWUP_SOURCE),
                "--domain",
                "creativity",
                "--source-type",
                "manual_text",
                "--source-title",
                FOLLOWUP_TITLE,
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    conn = connect(db_path)
    try:
        row = conn.execute(
            "SELECT id, raw_text_checksum FROM sources WHERE title = ?",
            (FOLLOWUP_TITLE,),
        ).fetchone()
        assert row is not None
        assert row["raw_text_checksum"] == FOLLOWUP_CHECKSUM
        return row["id"]
    finally:
        conn.close()


def test_followup_fixture_map_resolves_checksum() -> None:
    from rge.modules.manual_source_fixtures import extract_fixture_for_manual_source

    class _Source:
        source_type = "manual_text"
        raw_text_checksum = FOLLOWUP_CHECKSUM

    assert (
        extract_fixture_for_manual_source(_Source())
        == "claim_extraction_manual_synthnote_followup.json"
    )


def test_reconcile_scores_after_manual_followup_boosts_may_reduce_edge(
    temp_db: Path,
) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    _run_synthnote_spine(temp_db)
    followup_id = _ingest_followup_manual_source(temp_db)
    assert (
        main(["extract-claims", "--source", followup_id, "--db", str(temp_db)]) == 0
    )
    assert (
        main(["reconcile-scores", "--source", followup_id, "--db", str(temp_db)]) == 0
    )

    conn = connect(temp_db)
    try:
        relationship = conn.execute(
            """
            SELECT r.id, r.confidence
            FROM relationships r
            JOIN concepts sub ON sub.id = r.subject_concept_id
            JOIN concepts obj ON obj.id = r.object_concept_id
            WHERE sub.label = 'AI assistance'
              AND obj.label = 'semantic diversity'
              AND r.predicate = 'may_reduce'
            """
        ).fetchone()
        assert relationship is not None
        assert float(relationship["confidence"]) == EXPECTED_NEW_CONFIDENCE

        event = conn.execute(
            """
            SELECT old_score, new_score, reason, formula_version, triggering_claim_id
            FROM score_events
            WHERE entity_type = 'relationship' AND entity_id = ?
            """,
            (relationship["id"],),
        ).fetchone()
        assert event is not None
        assert float(event["old_score"]) == INITIAL_CONFIDENCE
        assert float(event["new_score"]) == EXPECTED_NEW_CONFIDENCE
        assert event["reason"] == STRONGER_SOURCE_REASON
        assert event["formula_version"] == FORMULA_VERSION
    finally:
        conn.close()


def test_reconcile_scores_manual_followup_is_idempotent(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    _run_synthnote_spine(temp_db)
    followup_id = _ingest_followup_manual_source(temp_db)
    assert main(["extract-claims", "--source", followup_id, "--db", str(temp_db)]) == 0
    args = ["reconcile-scores", "--source", followup_id, "--db", str(temp_db)]
    assert main(args) == 0
    assert main(args) == 0

    conn = connect(temp_db)
    try:
        count = conn.execute("SELECT COUNT(*) FROM score_events").fetchone()[0]
        assert count == 1
    finally:
        conn.close()


def test_reconcile_scores_cli_json_for_manual_followup(
    temp_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    _run_synthnote_spine(temp_db)
    followup_id = _ingest_followup_manual_source(temp_db)
    assert main(["extract-claims", "--source", followup_id, "--db", str(temp_db)]) == 0
    capsys.readouterr()
    assert main(["reconcile-scores", "--source", followup_id, "--db", str(temp_db)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["score_events_created"] == 1


def test_golden_fixture_followup_still_reconciles_with_explicit_fixture(
    temp_db: Path,
) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    base_source = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
    followup_source = (
        REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_followup_short.txt"
    )

    assert (
        main(
            [
                "ingest",
                str(base_source),
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    conn = connect(temp_db)
    try:
        base_id = conn.execute("SELECT id FROM sources").fetchone()[0]
    finally:
        conn.close()
    assert main(["extract-claims", "--source", base_id, "--db", str(temp_db)]) == 0
    assert main(["link-concepts", "--source", base_id, "--db", str(temp_db)]) == 0
    assert (
        main(["build-relationships", "--source", base_id, "--db", str(temp_db)]) == 0
    )

    assert (
        main(
            [
                "ingest",
                str(followup_source),
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    conn = connect(temp_db)
    try:
        followup_id = conn.execute(
            "SELECT id FROM sources WHERE title = ?",
            ("creativity_ai_diversity_followup_short.txt",),
        ).fetchone()[0]
    finally:
        conn.close()
    assert (
        main(
            [
                "extract-claims",
                "--source",
                followup_id,
                "--fixture",
                "claim_extraction_creativity_diversity_followup.json",
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    assert (
        main(["reconcile-scores", "--source", followup_id, "--db", str(temp_db)]) == 0
    )

    conn = connect(temp_db)
    try:
        count = conn.execute("SELECT COUNT(*) FROM score_events").fetchone()[0]
        assert count >= 1
    finally:
        conn.close()
