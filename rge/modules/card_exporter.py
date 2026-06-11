"""Create public-safe card JSON. Deterministic; no model use.

Selects accepted/public-safe records, strips everything not in the curated
public field list (``docs/agents/10_SAFETY_MODEL.md`` section 7), and fails
closed: one unsafe record blocks the whole export. Output flows to
``data/exports/`` and ``apps/public-site/public/data/`` only after the safety
audit passes. Phase 0 stub.
"""

from __future__ import annotations

from typing import Any


def export_public_cards(limit: int = 100) -> dict[str, Any]:
    """Export public-safe cards as JSON. Not implemented in Phase 0."""
    raise NotImplementedError("card_exporter.export_public_cards arrives with Phase 4.")
