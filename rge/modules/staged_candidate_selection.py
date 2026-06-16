"""Staged OpenAlex candidate selection for rank-1 and rank-2 spine paths."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from rge.config import DEFAULT_STAGED_RANK2_SCAN_MAX, parse_staged_rank2_scan_max
from rge.modules.staged_spine_heuristics import is_staged_rank2_fetch_spine_source

DEFAULT_RANK2_SCAN_WINDOW = DEFAULT_STAGED_RANK2_SCAN_MAX


class Rank2StagedCandidateNotFoundError(ValueError):
    """No queued candidate in the scan window matched rank-2 title heuristic."""

    def __init__(
        self,
        *,
        research_question_id: str,
        scanned_candidates: int,
        candidate_ids: list[str],
        min_candidates: int,
        max_scan: int,
    ) -> None:
        self.research_question_id = research_question_id
        self.scanned_candidates = scanned_candidates
        self.candidate_ids = candidate_ids
        self.min_candidates = min_candidates
        self.max_scan = max_scan
        super().__init__(
            "no rank-2 staged spine candidate in scan window for "
            f"{research_question_id}; scanned {scanned_candidates} candidate(s)"
        )

    def to_skip_payload(self) -> dict[str, Any]:
        return {
            "reason": "unsuitable_live_rank2_artifact",
            "detail": (
                "No queued candidate in rank-2 scan window matched constraint "
                "management title heuristic before fetch."
            ),
            "research_question_id": self.research_question_id,
            "scanned_candidates": self.scanned_candidates,
            "candidate_ids": self.candidate_ids,
            "max_scan": self.max_scan,
        }


def count_staged_candidates(conn: Any, research_question_id: str) -> int:
    """Return how many candidate_sources rows exist for a research question."""
    return int(
        conn.execute(
            "SELECT COUNT(*) FROM candidate_sources WHERE research_question_id = ?",
            (research_question_id,),
        ).fetchone()[0]
    )


def select_rank1_staged_candidate_id(conn: Any, research_question_id: str) -> str:
    """Return the top-ranked discovered candidate id (rank index 0)."""
    row = conn.execute(
        """
        SELECT id FROM candidate_sources
        WHERE research_question_id = ?
        ORDER BY priority_score DESC
        LIMIT 1 OFFSET 0
        """,
        (research_question_id,),
    ).fetchone()
    if row is None:
        raise ValueError(
            "staged spine requires at least one candidate for "
            f"{research_question_id}"
        )
    return str(row["id"])


def select_rank2_staged_candidate_id(
    conn: Any,
    research_question_id: str,
    *,
    min_candidates: int = 2,
    max_scan: int | None = None,
) -> str:
    """Return the first rank-2+ candidate whose title matches rank-2 spine heuristic."""
    effective_max_scan = (
        parse_staged_rank2_scan_max(max_scan)
        if max_scan is not None
        else parse_staged_rank2_scan_max()
    )
    count = count_staged_candidates(conn, research_question_id)
    if count < min_candidates:
        raise ValueError(
            f"staged spine requires at least {min_candidates} candidates for "
            f"{research_question_id}, found {count}"
        )

    rows = conn.execute(
        """
        SELECT id, title FROM candidate_sources
        WHERE research_question_id = ?
        ORDER BY priority_score DESC
        LIMIT ? OFFSET 1
        """,
        (research_question_id, effective_max_scan),
    ).fetchall()

    scanned_ids: list[str] = []
    for row in rows:
        candidate_id = str(row["id"])
        scanned_ids.append(candidate_id)
        title = str(row["title"] or "")
        if is_staged_rank2_fetch_spine_source(SimpleNamespace(title=title)):
            return candidate_id

    raise Rank2StagedCandidateNotFoundError(
        research_question_id=research_question_id,
        scanned_candidates=len(scanned_ids),
        candidate_ids=scanned_ids,
        min_candidates=min_candidates,
        max_scan=effective_max_scan,
    )
