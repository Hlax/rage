"""Shared candidate selection helpers for live staged pytest proofs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from rge.modules.fetcher import html_to_text, run_fetch_candidate_command
from rge.modules.staged_candidate_selection import (
    Rank2StagedCandidateNotFoundError,
    count_staged_candidates,
    select_rank2_staged_candidate_id,
)

MOCK_STAGED_ARTIFACT_MARKERS = (
    "human-ai co-creativity",
    "songwriting",
)


def artifact_missing_markers(
    artifact_path: Path,
    markers: tuple[str, ...],
) -> list[str]:
    """Return marker phrases absent from artifact text."""
    data = artifact_path.read_bytes()
    if artifact_path.suffix.casefold() == ".html":
        text = html_to_text(data.decode("utf-8", errors="replace"))
    else:
        text = data.decode("utf-8", errors="replace")
    folded = text.casefold()
    return [marker for marker in markers if marker.casefold() not in folded]


def _artifact_matches_markers(artifact_path: Path, markers: tuple[str, ...]) -> bool:
    return not artifact_missing_markers(artifact_path, markers)


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
    max_scan: int = 10,
) -> str:
    """Return rank-2 staged candidate id using title heuristic scan."""
    try:
        return select_rank2_staged_candidate_id(
            conn,
            research_question_id,
            min_candidates=min_candidates,
            max_scan=max_scan,
        )
    except Rank2StagedCandidateNotFoundError as exc:
        pytest.skip(json.dumps(exc.to_skip_payload(), indent=2))


def list_top_staged_candidate_ids(
    conn: Any,
    research_question_id: str,
    *,
    max_candidates: int = 10,
) -> list[str]:
    """Return top-N queued candidate ids ordered by priority."""
    rows = conn.execute(
        """
        SELECT id
        FROM candidate_sources
        WHERE research_question_id = ?
          AND status = 'queued'
        ORDER BY priority_score DESC
        LIMIT ?
        """,
        (research_question_id, max_candidates),
    ).fetchall()
    return [str(row["id"]) for row in rows]


def fetch_first_fetchable_staged_candidate(
    conn: Any,
    *,
    research_question_id: str,
    staging_dir: Path,
    max_candidates: int = 10,
    urlopen: Any | None = None,
) -> tuple[str, dict[str, Any]]:
    """Try fetch-candidate across top-N candidates until one succeeds (layer 1)."""
    candidate_ids = list_top_staged_candidate_ids(
        conn,
        research_question_id,
        max_candidates=max_candidates,
    )
    assert candidate_ids, (
        f"live discover must enqueue at least one candidate for {research_question_id}"
    )

    failures: list[dict[str, Any]] = []
    for candidate_id in candidate_ids:
        payload, exit_code = run_fetch_candidate_command(
            conn,
            candidate_id=candidate_id,
            output_dir=staging_dir,
            urlopen=urlopen,
        )
        if exit_code == 0 and payload.get("status") in {"completed", "already_fetched"}:
            return candidate_id, payload
        failures.append(
            {
                "candidate_id": candidate_id,
                "exit_code": exit_code,
                "reason": payload.get("reason"),
                "detail": payload.get("detail"),
                "attempted_urls": payload.get("attempted_urls", []),
            }
        )

    failure_summary = "; ".join(
        f"{item['candidate_id']}:{item.get('reason')}" for item in failures[:5]
    )
    raise AssertionError(
        "no fetchable candidate in top "
        f"{max_candidates} for {research_question_id}; failures: {failure_summary}"
    )
