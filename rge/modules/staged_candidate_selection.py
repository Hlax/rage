"""Staged OpenAlex candidate selection for rank-1 and rank-2 spine paths."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from rge.config import DEFAULT_STAGED_RANK2_SCAN_MAX, parse_staged_rank2_scan_max
from rge.modules.fetcher import OK_EXIT_CODE, is_fetch_access_blocked
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


def _candidate_has_pdf_route(url_candidates_json: str | None) -> bool:
    if not url_candidates_json:
        return False
    return "pdf" in url_candidates_json.casefold()


def list_rank1_fetch_candidate_ids(
    conn: Any,
    research_question_id: str,
    *,
    live_orchestrator_fallback: bool = False,
    max_scan: int | None = None,
) -> list[str]:
    """Return ordered rank-1 fetch candidate ids (PDF routes first when live)."""
    effective_max_scan = (
        parse_staged_rank2_scan_max(max_scan)
        if max_scan is not None
        else parse_staged_rank2_scan_max()
    )
    rows = conn.execute(
        """
        SELECT id, url_candidates_json FROM candidate_sources
        WHERE research_question_id = ?
        ORDER BY priority_score DESC
        LIMIT ?
        """,
        (research_question_id, effective_max_scan),
    ).fetchall()
    if not rows:
        raise ValueError(
            "staged spine requires at least one candidate for "
            f"{research_question_id}"
        )
    if not live_orchestrator_fallback:
        return [str(rows[0]["id"])]

    ordered_ids: list[str] = []
    for row in rows:
        candidate_id = str(row["id"])
        if _candidate_has_pdf_route(row["url_candidates_json"]):
            ordered_ids.append(candidate_id)
    for row in rows:
        candidate_id = str(row["id"])
        if candidate_id not in ordered_ids:
            ordered_ids.append(candidate_id)
    return ordered_ids


def select_rank1_staged_candidate_id(
    conn: Any,
    research_question_id: str,
    *,
    live_orchestrator_fallback: bool = False,
) -> str:
    """Return the top-ranked discovered candidate id (rank index 0)."""
    return list_rank1_fetch_candidate_ids(
        conn,
        research_question_id,
        live_orchestrator_fallback=live_orchestrator_fallback,
    )[0]


def select_rank2_staged_candidate_id(
    conn: Any,
    research_question_id: str,
    *,
    min_candidates: int = 2,
    max_scan: int | None = None,
    live_orchestrator_fallback: bool = False,
    exclude_ids: frozenset[str] | None = None,
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

    excluded = exclude_ids or frozenset()
    scanned_ids: list[str] = []
    fallback_ids: list[str] = []
    for row in rows:
        candidate_id = str(row["id"])
        if candidate_id in excluded:
            continue
        scanned_ids.append(candidate_id)
        title = str(row["title"] or "")
        if is_staged_rank2_fetch_spine_source(SimpleNamespace(title=title)):
            return candidate_id
        fallback_ids.append(candidate_id)

    if live_orchestrator_fallback and fallback_ids:
        return fallback_ids[0]

    raise Rank2StagedCandidateNotFoundError(
        research_question_id=research_question_id,
        scanned_candidates=len(scanned_ids),
        candidate_ids=scanned_ids,
        min_candidates=min_candidates,
        max_scan=effective_max_scan,
    )


class Rank1StagedFetchAccessBlockedError(RuntimeError):
    """All scanned rank-1 candidates returned publisher access blocks."""

    def __init__(
        self,
        *,
        research_question_id: str,
        blocked_candidate_ids: list[str],
        max_scan: int,
    ) -> None:
        self.research_question_id = research_question_id
        self.blocked_candidate_ids = blocked_candidate_ids
        self.max_scan = max_scan
        super().__init__(
            "all rank-1 staged fetch candidates blocked for "
            f"{research_question_id}; tried {len(blocked_candidate_ids)} candidate(s)"
        )


def fetch_rank1_with_access_fallback(
    conn: Any,
    *,
    research_question_id: str,
    output_dir: Path,
    fetch_command: Callable[..., tuple[dict[str, Any], int]],
    live_orchestrator_fallback: bool = False,
    max_scan: int | None = None,
) -> tuple[str, list[str]]:
    """Fetch rank-1 candidate bytes, skipping publisher access blocks."""
    effective_max_scan = (
        parse_staged_rank2_scan_max(max_scan)
        if max_scan is not None
        else parse_staged_rank2_scan_max()
    )
    candidate_ids = list_rank1_fetch_candidate_ids(
        conn,
        research_question_id,
        live_orchestrator_fallback=live_orchestrator_fallback,
        max_scan=effective_max_scan,
    )
    blocked_ids: list[str] = []
    for candidate_id in candidate_ids:
        payload, exit_code = fetch_command(
            conn,
            candidate_id=candidate_id,
            output_dir=output_dir,
        )
        if exit_code == OK_EXIT_CODE and payload.get("status") == "completed":
            return candidate_id, blocked_ids

        reason = str(payload.get("reason") or "")
        if live_orchestrator_fallback and is_fetch_access_blocked(reason):
            blocked_ids.append(candidate_id)
            continue

        detail = payload.get("detail") or reason or "fetch-candidate failed"
        raise RuntimeError(
            f"fetch-candidate failed for {candidate_id}: {detail}"
        )

    raise Rank1StagedFetchAccessBlockedError(
        research_question_id=research_question_id,
        blocked_candidate_ids=blocked_ids,
        max_scan=effective_max_scan,
    )


def resolve_live_staged_spine_fetch_pair(
    conn: Any,
    *,
    research_question_id: str,
    output_dir: Path,
    fetch_command: Callable[..., tuple[dict[str, Any], int]],
    max_scan: int | None = None,
) -> tuple[str, str, list[str]]:
    """Resolve rank-1/rank-2 candidate ids with rank-1 fetch access fallback."""
    rank1_candidate_id, blocked_ids = fetch_rank1_with_access_fallback(
        conn,
        research_question_id=research_question_id,
        output_dir=output_dir,
        fetch_command=fetch_command,
        live_orchestrator_fallback=True,
        max_scan=max_scan,
    )
    exclude_ids = frozenset(blocked_ids) | {rank1_candidate_id}
    rank2_candidate_id = select_rank2_staged_candidate_id(
        conn,
        research_question_id,
        live_orchestrator_fallback=True,
        exclude_ids=exclude_ids,
        max_scan=max_scan,
    )
    return rank1_candidate_id, rank2_candidate_id, blocked_ids
