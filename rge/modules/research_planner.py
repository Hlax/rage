"""Create research contracts and run plans.

Mixed deterministic/model-assisted. Models may draft query/contract
suggestions; Python validates and persists the durable contract
(``docs/agents/09_RESEARCH_RUN_CONTRACT.md``). Phase 0 stub.
"""

from __future__ import annotations

from typing import Any


def create_research_contract(topic: str, domain_pack: str) -> dict[str, Any]:
    """Create a durable research contract for a run. Not implemented in Phase 0."""
    raise NotImplementedError(
        "research_planner.create_research_contract arrives with Phase 3 "
        "(local research MVP)."
    )
