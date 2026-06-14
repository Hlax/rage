"""Find candidate sources from manual fixtures and search APIs.

Mixed deterministic/model-assisted. Starts with manual/fixture sources;
search APIs come later. Browser automation is a fallback, never the default.
Phase 3 entry: structured CLI stub only (ticket-138).
"""

from __future__ import annotations

from typing import Any

DISCOVER_SOURCES_COMMAND = "discover-sources"
DISCOVER_SOURCES_PHASE = "3"
DISCOVER_SOURCES_NOT_IMPLEMENTED_DETAIL = (
    "Phase 3 source discovery is not implemented yet."
)
NOT_IMPLEMENTED_EXIT_CODE = 2


def build_discover_sources_not_implemented_payload() -> dict[str, str]:
    """Single source of truth for the Phase 3 discover-sources stub response."""
    return {
        "status": "not_implemented",
        "command": DISCOVER_SOURCES_COMMAND,
        "phase": DISCOVER_SOURCES_PHASE,
        "detail": DISCOVER_SOURCES_NOT_IMPLEMENTED_DETAIL,
    }


def discover_sources_not_implemented_result() -> tuple[dict[str, str], int]:
    """Return structured stub payload and exit code for discover-sources CLI."""
    return build_discover_sources_not_implemented_payload(), NOT_IMPLEMENTED_EXIT_CODE


def discover_candidate_sources(contract: dict[str, Any]) -> list[dict[str, Any]]:
    """Discover candidate sources for a contract. Not implemented in Phase 3 yet."""
    _ = contract
    raise NotImplementedError(DISCOVER_SOURCES_NOT_IMPLEMENTED_DETAIL)
