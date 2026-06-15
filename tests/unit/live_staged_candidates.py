"""Shared candidate selection helpers for live staged pytest proofs."""

from __future__ import annotations

from typing import Any


def count_staged_candidates(conn: Any, research_question_id: str) -> int:
    """Return how many candidate_sources rows exist for a research question."""
    return int(
        conn.execute(
            "SELECT COUNT(*) FROM candidate_sources WHERE research_question_id = ?",
            (research_question_id,),
        ).fetchone()[0]
    )


def select_staged_candidate_row(
    conn: Any,
    research_question_id: str,
    *,
    rank_index: int = 0,
) -> Any:
    """Select a candidate row ordered by ``priority_score DESC``.

    ``rank_index`` 0 is the top-ranked candidate; 1 is the second-ranked candidate.
    """
    row = conn.execute(
        """
        SELECT id
        FROM candidate_sources
        WHERE research_question_id = ?
        ORDER BY priority_score DESC
        LIMIT 1 OFFSET ?
        """,
        (research_question_id, rank_index),
    ).fetchone()
    if row is None:
        raise AssertionError(
            "no staged candidate at rank_index="
            f"{rank_index} for question {research_question_id}"
        )
    return row


def select_rank1_candidate_id(conn: Any, research_question_id: str) -> str:
    """Return the top-ranked discovered candidate id."""
    return select_staged_candidate_row(conn, research_question_id, rank_index=0)["id"]


def select_rank2_candidate_id(
    conn: Any,
    research_question_id: str,
    *,
    min_candidates: int = 2,
) -> str:
    """Return the second-ranked discovered candidate id."""
    count = count_staged_candidates(conn, research_question_id)
    assert count >= min_candidates, (
        f"live discover must enqueue at least {min_candidates} candidates"
    )
    return select_staged_candidate_row(conn, research_question_id, rank_index=1)["id"]
