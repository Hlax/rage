"""Generate candidate theories from evidence packets. Model-assisted, validated.

Theories emerge from graph patterns and evidence packets, not model vibes:
graph pattern -> evidence packet -> constrained inference -> candidate theory
-> validation -> stored as candidate, never fact. Candidates require
supporting claims, caveats, boundary conditions, and weakening evidence.
Phase 0 stub.
"""

from __future__ import annotations

from typing import Any


def generate_theory_candidates(evidence_packet: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate candidate theories from an evidence packet. Not implemented in Phase 0."""
    raise NotImplementedError(
        "theory_generator.generate_theory_candidates arrives with Phase 3."
    )
