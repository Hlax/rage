"""Produce structured candidate claims from chunks. Model-assisted.

Future flow (03_MODEL_RUNTIME_SPEC.md section 6):

    extract_candidate_claims(...)
    -> rge.llm.registry.get_model_client(...)
    -> client.extract_claims(...) returns CandidateClaimBatch
    -> claim_validator validates quote spans / scope / source IDs
    -> Python writes staged/accepted/rejected claims
    -> node report emitted

The model only proposes candidate JSON; it never writes. Phase 0 stub.
"""

from __future__ import annotations

from typing import Any


def extract_candidate_claims(
    chunk: dict[str, Any], contract: dict[str, Any], domain_pack: str
) -> list[dict[str, Any]]:
    """Extract candidate claims from one chunk. Not implemented in Phase 0."""
    raise NotImplementedError(
        "claim_extractor.extract_candidate_claims arrives with Phase 1."
    )
