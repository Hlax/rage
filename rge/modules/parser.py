"""Parse text/PDF/HTML sources into chunks. Deterministic; no model use.

Produces ``chunks`` records with checksums for deduplication. Parsed text
remains untrusted data, never instructions. Phase 0 stub.
"""

from __future__ import annotations

from typing import Any


def parse_source(source: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse one fetched source into chunks. Not implemented in Phase 0."""
    raise NotImplementedError("parser.parse_source arrives with Phase 1.")
