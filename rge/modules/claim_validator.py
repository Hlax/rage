"""Validate claim fields, quote spans, scope, and injection safety.

Deterministic; no model use. The only gate between candidate claims and the
accepted graph. Rejection reasons: missing_quote_span, overgeneralized_scope,
unsupported_claim, invalid_json, weak_concept_mapping, missing_source_id,
unsafe_or_injected_content. Rejected claims are stored with reasons, never
discarded.
"""

from __future__ import annotations

from typing import Any

from rge.safety.prompt_injection import (
    REJECTION_REASON_INJECTED_CONTENT,
    candidate_has_prompt_injection,
)

REJECTION_MISSING_QUOTE = "missing_quote_span"
REJECTION_OVERGENERALIZED = "overgeneralized_scope"
REJECTION_MISSING_SOURCE = "missing_source_id"
REJECTION_UNSUPPORTED = "unsupported_claim"
REJECTION_INJECTED_CONTENT = REJECTION_REASON_INJECTED_CONTENT

_OVERGENERALIZED_CLAIM_PATTERNS = (
    "ai reduces creativity",
    "ai is bad for originality",
    "ai improves creativity",
)


def _normalize(text: str | None) -> str:
    return (text or "").strip().casefold()


def _collapse_whitespace(text: str) -> str:
    return " ".join(text.split())


def _quote_in_chunk(quote_span: str, chunk_text: str) -> bool:
    return _collapse_whitespace(quote_span) in _collapse_whitespace(chunk_text)


def validate_candidate_claim(
    candidate: dict[str, Any],
    *,
    chunk_text: str,
) -> tuple[str, dict[str, Any] | None, str | None]:
    """Validate one candidate claim.

    Returns ``(status, claim_dict, rejection_reason)`` where status is
    ``accepted`` or ``rejected``.
    """
    source_id = candidate.get("source_id")
    chunk_id = candidate.get("chunk_id")
    if not source_id or not chunk_id:
        return "rejected", None, REJECTION_MISSING_SOURCE

    quote_span = candidate.get("quote_span")
    if not quote_span or not str(quote_span).strip():
        return "rejected", None, REJECTION_MISSING_QUOTE

    if not _quote_in_chunk(str(quote_span), chunk_text):
        return "rejected", None, REJECTION_UNSUPPORTED

    if candidate_has_prompt_injection(candidate):
        return "rejected", None, REJECTION_INJECTED_CONTENT

    scope = candidate.get("scope")
    if not scope or not str(scope).strip():
        return "rejected", None, REJECTION_OVERGENERALIZED

    claim_text = candidate.get("claim_text") or ""
    normalized_claim = _normalize(claim_text)
    for pattern in _OVERGENERALIZED_CLAIM_PATTERNS:
        if pattern in normalized_claim:
            return "rejected", None, REJECTION_OVERGENERALIZED

    scope_normalized = _normalize(str(scope))
    if scope_normalized and scope_normalized not in _normalize(claim_text):
        return "rejected", None, REJECTION_OVERGENERALIZED

    required_fields = (
        "claim_text",
        "subject",
        "predicate",
        "object",
        "evidence_type",
        "domain",
    )
    for field in required_fields:
        value = candidate.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            return "rejected", None, REJECTION_UNSUPPORTED

    if candidate.get("confidence") is None:
        return "rejected", None, REJECTION_UNSUPPORTED

    limitations = candidate.get("limitations")
    if limitations is None:
        return "rejected", None, REJECTION_UNSUPPORTED

    return "accepted", dict(candidate), None


def validate_candidate_claims(
    candidates: list[dict[str, Any]],
    *,
    chunk_text: str,
) -> dict[str, list[dict[str, Any]]]:
    """Split candidates into accepted and rejected buckets with reasons."""
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for candidate in candidates:
        status, claim_dict, reason = validate_candidate_claim(
            candidate, chunk_text=chunk_text
        )
        if status == "accepted" and claim_dict is not None:
            accepted.append(claim_dict)
        else:
            rejected.append(
                {
                    **candidate,
                    "rejection_reason": reason or REJECTION_UNSUPPORTED,
                }
            )

    return {"accepted": accepted, "rejected": rejected}
