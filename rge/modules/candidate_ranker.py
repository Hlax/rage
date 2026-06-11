"""Rank candidate sources by relevance, quality, gap value, and drift risk.

Mostly deterministic (versioned queue-priority formula from
``docs/agents/09_RESEARCH_RUN_CONTRACT.md`` section 7). Every queue item must
store a reason. Phase 0 stub.
"""

from __future__ import annotations

from typing import Any


def rank_candidate_sources(
    candidates: list[dict[str, Any]], contract: dict[str, Any]
) -> list[dict[str, Any]]:
    """Rank candidate sources for queueing. Not implemented in Phase 0."""
    raise NotImplementedError(
        "candidate_ranker.rank_candidate_sources arrives with Phase 2/3."
    )
