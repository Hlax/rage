"""Queue candidate sources and follow-up questions. Deterministic; no model use.

The queue controls execution: statuses queued/fetching/fetched/parsing/
extracting/staged/accepted/rejected/failed/needs_manual_review/parked.
Phase 0 stub.
"""

from __future__ import annotations

from typing import Any


def enqueue(items: list[dict[str, Any]]) -> None:
    """Add ranked items to the research queue. Not implemented in Phase 0."""
    raise NotImplementedError("research_queue.enqueue arrives with Phase 3.")
