"""Validate claim fields, quote spans, scope, and injection safety.

Deterministic; no model use. The only gate between candidate claims and the
staged/accepted graph. Rejection reasons: missing_quote_span,
overgeneralized_scope, unsupported_claim, invalid_json, weak_concept_mapping,
missing_source_id, unsafe_or_injected_content. Rejected claims are stored
with reasons, never discarded. Phase 0 stub.
"""

from __future__ import annotations

from typing import Any


def validate_candidate_claims(
    candidates: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Split candidates into accepted/rejected with reasons. Not implemented in Phase 0."""
    raise NotImplementedError(
        "claim_validator.validate_candidate_claims arrives with Phase 1."
    )
