"""Draft domain proposals when strict thresholds are met. Model-assisted, validated.

Thresholds (06_DOMAIN_PACK_SPEC.md section 15): 40 accepted claims, 8
independent sources, 15 recurring specialized terms, repeated mismatch
signals, and a clear reason the parent domain is underspecified. Proposals
are drafts; domains never auto-activate. Phase 0 stub.
"""

from __future__ import annotations

from typing import Any


def propose_domain(parent_domain: str) -> dict[str, Any]:
    """Draft a domain proposal when thresholds are met. Not implemented in Phase 0."""
    raise NotImplementedError("domain_proposer.propose_domain arrives with Phase 5.")
