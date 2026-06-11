"""Link claims to concepts and domain metadata. Model-assisted, validated.

Uses domain pack ontology/aliases (e.g. ``domain_packs/creativity/``) to map
claims to canonical concepts without duplicates. Domain-specific values live
in ``domain_metadata``, validated by the domain pack, never hardcoded here.
Phase 0 stub.
"""

from __future__ import annotations

from typing import Any


def link_claim_concepts(
    claims: list[dict[str, Any]], domain_pack: str
) -> list[dict[str, Any]]:
    """Propose and validate concept links for claims. Not implemented in Phase 0."""
    raise NotImplementedError(
        "concept_linker.link_claim_concepts arrives with Phase 1/2."
    )
