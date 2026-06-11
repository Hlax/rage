"""Build support/contradict/qualify edges between concepts.

Model-assisted, validated. Contradictions are assets: preserve disagreement
and distinguish real contradictions from metric/scope differences. Every
relationship needs evidence links with stance, confidence, and scope.
Phase 0 stub.
"""

from __future__ import annotations

from typing import Any


def build_relationships(
    claims: list[dict[str, Any]], domain_pack: str
) -> list[dict[str, Any]]:
    """Build evidence relationships from accepted claims. Not implemented in Phase 0."""
    raise NotImplementedError(
        "relationship_builder.build_relationships arrives with Phase 1."
    )
