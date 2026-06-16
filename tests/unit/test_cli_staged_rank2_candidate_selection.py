"""Unit tests for CLI staged spine rank-2 candidate selection (ticket-258)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rge.cli import _staged_rank_candidate_ids
from rge.db.connection import ensure_database
from rge.modules.staged_candidate_selection import Rank2StagedCandidateNotFoundError

QUESTION_ID = "rq_cli_rank2_selection"
RANK1_TITLE = "Human-AI co-creativity and semantic diversity in songwriting workshops"
RANK2_OFFSET1_TITLE = "Unrelated creativity paper without staged markers"
RANK2_MATCH_TITLE = "Constraint management in AI-assisted creative teams"


def _insert_candidate(
    conn,
    *,
    candidate_id: str,
    title: str,
    priority_score: float,
) -> None:
    conn.execute(
        """
        INSERT INTO candidate_sources (
            id, research_question_id, contract_id, title, url, source_type,
            reason, relevance_score, credibility_prior, gap_fill_score,
            recency_score, source_diversity_score, novelty_score, drift_risk,
            priority_score, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            candidate_id,
            QUESTION_ID,
            "contract_golden_v0",
            title,
            f"https://example.org/{candidate_id}.html",
            "peer_reviewed_empirical",
            "test",
            priority_score,
            0.8,
            0.5,
            0.5,
            0.5,
            0.5,
            0.1,
            priority_score,
            "queued",
        ),
    )


@pytest.fixture()
def conn(tmp_path: Path):
    database = ensure_database(tmp_path / "cli_rank2_selection.sqlite")
    _insert_candidate(
        database,
        candidate_id="disc_rank1",
        title=RANK1_TITLE,
        priority_score=0.95,
    )
    _insert_candidate(
        database,
        candidate_id="disc_rank2_miss",
        title=RANK2_OFFSET1_TITLE,
        priority_score=0.85,
    )
    _insert_candidate(
        database,
        candidate_id="disc_rank3_hit",
        title=RANK2_MATCH_TITLE,
        priority_score=0.75,
    )
    database.commit()
    yield database
    database.close()


def test_staged_rank_candidate_ids_selects_rank1_and_heuristic_rank2(conn) -> None:
    rank1_id, rank2_id = _staged_rank_candidate_ids(conn, QUESTION_ID)

    assert rank1_id == "disc_rank1"
    assert rank2_id == "disc_rank3_hit"


def test_staged_rank_candidate_ids_honors_env_scan_max_override(
    conn, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RGE_STAGED_RANK2_SCAN_MAX", "1")
    with pytest.raises(Rank2StagedCandidateNotFoundError) as exc_info:
        _staged_rank_candidate_ids(conn, QUESTION_ID)
    assert exc_info.value.max_scan == 1

    monkeypatch.setenv("RGE_STAGED_RANK2_SCAN_MAX", "2")
    rank1_id, rank2_id = _staged_rank_candidate_ids(conn, QUESTION_ID)
    assert rank1_id == "disc_rank1"
    assert rank2_id == "disc_rank3_hit"
