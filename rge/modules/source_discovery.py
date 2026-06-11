"""Find candidate sources from manual fixtures and search APIs.

Mixed deterministic/model-assisted. Starts with manual/fixture sources;
search APIs come later. Browser automation is a fallback, never the default.
Phase 0 stub.
"""

from __future__ import annotations

from typing import Any


def discover_candidate_sources(contract: dict[str, Any]) -> list[dict[str, Any]]:
    """Discover candidate sources for a contract. Not implemented in Phase 0."""
    raise NotImplementedError(
        "source_discovery.discover_candidate_sources arrives with Phase 3."
    )
