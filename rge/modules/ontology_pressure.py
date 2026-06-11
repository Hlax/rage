"""Detect concept/domain vocabulary pressure. Mixed; model-assisted, validated.

Detects recurring uncaptured vocabulary and creates draft ontology proposals.
Proposals never auto-activate concepts; activation requires review
(``docs/agents/08_REPORTING_SPEC.md`` section 11). Phase 0 stub.
"""

from __future__ import annotations

from typing import Any


def detect_ontology_pressure(domain_pack: str) -> list[dict[str, Any]]:
    """Detect ontology pressure and draft proposals. Not implemented in Phase 0."""
    raise NotImplementedError(
        "ontology_pressure.detect_ontology_pressure arrives with Phase 5."
    )
