"""Staged OpenAlex candidate selection for rank-1 and rank-2 spine paths."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from rge.config import DEFAULT_STAGED_RANK2_SCAN_MAX, parse_staged_rank2_scan_max
from rge.modules.fetcher import (
    ARTIFACT_UNUSABLE_REASON,
    OK_EXIT_CODE,
    evaluate_fetch_artifact_quality,
    is_fetch_access_blocked,
)
from rge.modules.staged_spine_compatibility import (
    MOCK_STAGED_RANK1_ARTIFACT_MARKERS,
    UNSUITABLE_LIVE_ARTIFACT,
    evaluate_mock_spine_compatibility,
)
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


def _candidate_preferred_host_score(url_candidates_json: str | None) -> int:
    """Higher score when URL routes include trusted open-access mirrors."""
    if not url_candidates_json:
        return 0
    lowered = url_candidates_json.casefold()
    score = 0
    if "pmc.ncbi.nlm.nih.gov" in lowered or "ncbi.nlm.nih.gov/pmc" in lowered:
        score += 3
    if "arxiv.org" in lowered:
        score += 2
    if "springeropen.com" in lowered or "europepmc.org" in lowered:
        score += 1
    return score


def _fetch_payload_usability_issue(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Return diagnostics when a completed fetch payload is not ingest-ready."""
    artifact_path_raw = payload.get("artifact_path")
    if not artifact_path_raw:
        return {
            "reason": ARTIFACT_UNUSABLE_REASON,
            "detail": "Fetch payload missing artifact_path.",
        }
    artifact_path = Path(str(artifact_path_raw))
    if not artifact_path.is_file():
        return {
            "reason": ARTIFACT_UNUSABLE_REASON,
            "detail": f"Fetched artifact file not found: {artifact_path}",
        }
    body = artifact_path.read_bytes()
    content_type = payload.get("content_type")
    if not content_type:
        content_type = (
            "text/html" if artifact_path.suffix.casefold() == ".html" else None
        )
    quality = evaluate_fetch_artifact_quality(body, content_type)
    if quality.get("usable"):
        return None
    return {
        "reason": quality.get("reason") or ARTIFACT_UNUSABLE_REASON,
        "detail": quality.get("detail") or "Unusable fetched artifact.",
        "byte_count": quality.get("byte_count"),
        "extractable_text_chars": quality.get("extractable_text_chars"),
        "matched_markers": quality.get("matched_markers"),
    }


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
        SELECT id, url_candidates_json, priority_score FROM candidate_sources
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

    def _rank1_sort_key(row: Any) -> tuple[int, int, float]:
        url_candidates_json = row["url_candidates_json"]
        pdf_rank = 0 if _candidate_has_pdf_route(url_candidates_json) else 1
        host_rank = -_candidate_preferred_host_score(url_candidates_json)
        priority_rank = -float(row["priority_score"] or 0.0)
        return (pdf_rank, host_rank, priority_rank)

    return [str(row["id"]) for row in sorted(rows, key=_rank1_sort_key)]


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


class UnsuitableLiveArtifactError(RuntimeError):
    """No fetched rank-1 artifact satisfied mock-spine marker preconditions."""

    def __init__(
        self,
        *,
        research_question_id: str,
        blocked_candidate_ids: list[str],
        incompatible_candidates: list[dict[str, Any]],
        max_scan: int,
    ) -> None:
        self.research_question_id = research_question_id
        self.blocked_candidate_ids = blocked_candidate_ids
        self.incompatible_candidates = incompatible_candidates
        self.max_scan = max_scan
        super().__init__(
            "no mock-spine-compatible rank-1 staged fetch candidate for "
            f"{research_question_id}"
        )

    def to_payload(self) -> dict[str, Any]:
        marker_mismatch = any(
            item.get("reason") == UNSUITABLE_LIVE_ARTIFACT
            for item in self.incompatible_candidates
        )
        acquisition_failed = bool(self.incompatible_candidates) and not marker_mismatch
        if acquisition_failed:
            detail = (
                "Live source acquisition failed for all scanned candidates "
                "(publisher blocks, unusable bot-challenge pages, or empty artifacts)."
            )
            assessment = (
                "Not a mock-spine marker regression — no fetchable ingest-ready "
                "artifact was retrieved in the scan window."
            )
        else:
            detail = (
                "Live source acquisition succeeded for one or more candidates, but "
                "none of the fetched top-N artifacts satisfy mock-spine marker "
                "preconditions."
            )
            assessment = (
                "Not a fetch regression — live OpenAlex catalog text does not match "
                "checksum-pinned mock fixture phrases for this query."
            )
        return {
            "status": "skipped",
            "command": "run",
            "mode": "fixture_staged",
            "reason": UNSUITABLE_LIVE_ARTIFACT,
            "detail": detail,
            "research_question_id": self.research_question_id,
            "required_markers": list(MOCK_STAGED_RANK1_ARTIFACT_MARKERS),
            "blocked_candidate_ids": self.blocked_candidate_ids,
            "incompatible_candidates": self.incompatible_candidates,
            "max_scan": self.max_scan,
            "assessment": assessment,
        }


def fetch_rank1_with_access_fallback(
    conn: Any,
    *,
    research_question_id: str,
    output_dir: Path,
    fetch_command: Callable[..., tuple[dict[str, Any], int]],
    live_orchestrator_fallback: bool = False,
    require_mock_spine_markers: bool = True,
    max_scan: int | None = None,
) -> tuple[str, list[str], list[dict[str, Any]]]:
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
    incompatible_candidates: list[dict[str, Any]] = []
    for candidate_id in candidate_ids:
        payload, exit_code = fetch_command(
            conn,
            candidate_id=candidate_id,
            output_dir=output_dir,
        )
        if exit_code == OK_EXIT_CODE and payload.get("status") in {
            "completed",
            "already_fetched",
        }:
            if live_orchestrator_fallback:
                usability_issue = _fetch_payload_usability_issue(payload)
                if usability_issue is not None:
                    incompatible_candidates.append(
                        {"candidate_id": candidate_id, **usability_issue}
                    )
                    continue
            if live_orchestrator_fallback and require_mock_spine_markers:
                compatibility = evaluate_mock_spine_compatibility(payload)
                if not compatibility.get("compatible"):
                    incompatible_candidates.append(
                        {
                            "candidate_id": candidate_id,
                            **compatibility,
                        }
                    )
                    continue
            return candidate_id, blocked_ids, incompatible_candidates

        reason = str(payload.get("reason") or "")
        if live_orchestrator_fallback:
            if is_fetch_access_blocked(reason):
                blocked_ids.append(candidate_id)
                continue
            if exit_code != OK_EXIT_CODE or payload.get("status") not in {
                "completed",
                "already_fetched",
            }:
                incompatible_candidates.append(
                    {
                        "candidate_id": candidate_id,
                        "reason": reason or "fetch_failed",
                        "detail": payload.get("detail") or "fetch-candidate failed",
                        "attempted_urls": payload.get("attempted_urls", []),
                    }
                )
                continue

        detail = payload.get("detail") or reason or "fetch-candidate failed"
        raise RuntimeError(
            f"fetch-candidate failed for {candidate_id}: {detail}"
        )

    if incompatible_candidates:
        raise UnsuitableLiveArtifactError(
            research_question_id=research_question_id,
            blocked_candidate_ids=blocked_ids,
            incompatible_candidates=incompatible_candidates,
            max_scan=effective_max_scan,
        )

    raise Rank1StagedFetchAccessBlockedError(
        research_question_id=research_question_id,
        blocked_candidate_ids=blocked_ids,
        max_scan=effective_max_scan,
    )


def list_rank2_fetch_candidate_ids(
    conn: Any,
    research_question_id: str,
    *,
    exclude_ids: frozenset[str],
    live_orchestrator_fallback: bool = False,
    max_scan: int | None = None,
) -> list[str]:
    """Return ordered rank-2+ fetch candidate ids, excluding rank-1/skipped ids."""
    effective_max_scan = (
        parse_staged_rank2_scan_max(max_scan)
        if max_scan is not None
        else parse_staged_rank2_scan_max()
    )
    rows = conn.execute(
        """
        SELECT id, title, url_candidates_json, priority_score FROM candidate_sources
        WHERE research_question_id = ?
        ORDER BY priority_score DESC
        LIMIT ?
        OFFSET 1
        """,
        (research_question_id, effective_max_scan),
    ).fetchall()
    filtered = [row for row in rows if str(row["id"]) not in exclude_ids]
    if not filtered:
        raise ValueError(
            "staged spine requires at least one rank-2 candidate for "
            f"{research_question_id}"
        )
    if not live_orchestrator_fallback:
        for row in filtered:
            title = str(row["title"] or "")
            if is_staged_rank2_fetch_spine_source(SimpleNamespace(title=title)):
                return [str(row["id"])]
        return [str(filtered[0]["id"])]

    def _rank2_sort_key(row: Any) -> tuple[int, int, float]:
        url_candidates_json = row["url_candidates_json"]
        pdf_rank = 0 if _candidate_has_pdf_route(url_candidates_json) else 1
        host_rank = -_candidate_preferred_host_score(url_candidates_json)
        priority_rank = -float(row["priority_score"] or 0.0)
        return (pdf_rank, host_rank, priority_rank)

    return [str(row["id"]) for row in sorted(filtered, key=_rank2_sort_key)]


def fetch_rank2_with_access_fallback(
    conn: Any,
    *,
    research_question_id: str,
    output_dir: Path,
    fetch_command: Callable[..., tuple[dict[str, Any], int]],
    exclude_ids: frozenset[str],
    live_orchestrator_fallback: bool = False,
    require_mock_spine_markers: bool = True,
    max_scan: int | None = None,
) -> tuple[str, list[str], list[dict[str, Any]]]:
    """Fetch rank-2 candidate bytes with the same fallback semantics as rank-1."""
    effective_max_scan = (
        parse_staged_rank2_scan_max(max_scan)
        if max_scan is not None
        else parse_staged_rank2_scan_max()
    )
    candidate_ids = list_rank2_fetch_candidate_ids(
        conn,
        research_question_id,
        exclude_ids=exclude_ids,
        live_orchestrator_fallback=live_orchestrator_fallback,
        max_scan=effective_max_scan,
    )
    blocked_ids: list[str] = []
    incompatible_candidates: list[dict[str, Any]] = []
    for candidate_id in candidate_ids:
        payload, exit_code = fetch_command(
            conn,
            candidate_id=candidate_id,
            output_dir=output_dir,
        )
        if exit_code == OK_EXIT_CODE and payload.get("status") in {
            "completed",
            "already_fetched",
        }:
            if live_orchestrator_fallback:
                usability_issue = _fetch_payload_usability_issue(payload)
                if usability_issue is not None:
                    incompatible_candidates.append(
                        {"candidate_id": candidate_id, **usability_issue}
                    )
                    continue
            if live_orchestrator_fallback and require_mock_spine_markers:
                compatibility = evaluate_mock_spine_compatibility(payload)
                if not compatibility.get("compatible"):
                    incompatible_candidates.append(
                        {
                            "candidate_id": candidate_id,
                            **compatibility,
                        }
                    )
                    continue
            return candidate_id, blocked_ids, incompatible_candidates

        reason = str(payload.get("reason") or "")
        if live_orchestrator_fallback:
            if is_fetch_access_blocked(reason):
                blocked_ids.append(candidate_id)
                continue
            if exit_code != OK_EXIT_CODE or payload.get("status") not in {
                "completed",
                "already_fetched",
            }:
                incompatible_candidates.append(
                    {
                        "candidate_id": candidate_id,
                        "reason": reason or "fetch_failed",
                        "detail": payload.get("detail") or "fetch-candidate failed",
                        "attempted_urls": payload.get("attempted_urls", []),
                    }
                )
                continue

        detail = payload.get("detail") or reason or "fetch-candidate failed"
        raise RuntimeError(
            f"fetch-candidate failed for {candidate_id}: {detail}"
        )

    if incompatible_candidates:
        raise UnsuitableLiveArtifactError(
            research_question_id=research_question_id,
            blocked_candidate_ids=blocked_ids,
            incompatible_candidates=incompatible_candidates,
            max_scan=effective_max_scan,
        )

    raise Rank2StagedCandidateNotFoundError(
        research_question_id=research_question_id,
        scanned_candidates=len(candidate_ids),
        candidate_ids=candidate_ids,
        min_candidates=2,
        max_scan=effective_max_scan,
    )


def resolve_live_staged_spine_fetch_pair(
    conn: Any,
    *,
    research_question_id: str,
    output_dir: Path,
    fetch_command: Callable[..., tuple[dict[str, Any], int]],
    require_mock_spine_markers: bool = True,
    max_scan: int | None = None,
) -> tuple[str, str, list[str]]:
    """Resolve rank-1/rank-2 candidate ids with rank-1 fetch access fallback."""
    rank1_candidate_id, blocked_ids, incompatible_candidates = (
        fetch_rank1_with_access_fallback(
            conn,
            research_question_id=research_question_id,
            output_dir=output_dir,
            fetch_command=fetch_command,
            live_orchestrator_fallback=True,
            require_mock_spine_markers=require_mock_spine_markers,
            max_scan=max_scan,
        )
    )
    skipped_ids = {
        candidate_id
        for candidate_id in blocked_ids
    } | {
        str(item.get("candidate_id"))
        for item in incompatible_candidates
        if item.get("candidate_id")
    }
    exclude_ids = skipped_ids | {rank1_candidate_id}
    if require_mock_spine_markers:
        rank2_candidate_id = select_rank2_staged_candidate_id(
            conn,
            research_question_id,
            live_orchestrator_fallback=True,
            exclude_ids=frozenset(exclude_ids),
            max_scan=max_scan,
        )
    else:
        rank2_candidate_id, rank2_blocked, rank2_incompatible = (
            fetch_rank2_with_access_fallback(
                conn,
                research_question_id=research_question_id,
                output_dir=output_dir,
                fetch_command=fetch_command,
                exclude_ids=frozenset(exclude_ids),
                live_orchestrator_fallback=True,
                require_mock_spine_markers=False,
                max_scan=max_scan,
            )
        )
        skipped_ids |= set(rank2_blocked)
        skipped_ids |= {
            str(item.get("candidate_id"))
            for item in rank2_incompatible
            if item.get("candidate_id")
        }
    return rank1_candidate_id, rank2_candidate_id, sorted(skipped_ids)
