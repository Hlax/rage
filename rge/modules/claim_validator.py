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


def _build_collapsed_index_map(text: str) -> tuple[str, list[int]]:
    """Map collapsed-whitespace indices back to original string indices."""
    collapsed_chars: list[str] = []
    index_map: list[int] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i].isspace():
            if index_map:
                collapsed_chars.append(" ")
                index_map.append(i)
            while i < n and text[i].isspace():
                i += 1
            continue
        collapsed_chars.append(text[i])
        index_map.append(i)
        i += 1
    return "".join(collapsed_chars), index_map


def locate_quote_offsets(
    quote_span: str, chunk_text: str
) -> tuple[int | None, int | None]:
    """Return char_start/char_end when quote_span matches chunk_text (exact or collapsed)."""
    quote = str(quote_span).strip()
    if not quote:
        return None, None
    start = chunk_text.find(quote)
    if start >= 0:
        return start, start + len(quote)

    collapsed_chunk, index_map = _build_collapsed_index_map(chunk_text)
    collapsed_quote = _collapse_whitespace(quote)
    start_c = collapsed_chunk.find(collapsed_quote)
    if start_c < 0 or not index_map:
        return None, None
    end_c = start_c + len(collapsed_quote) - 1
    if end_c >= len(index_map):
        return None, None
    return index_map[start_c], index_map[end_c] + 1


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


def rejection_diagnostic(
    candidate: dict[str, Any],
    *,
    chunk_text: str,
    rejection_reason: str | None = None,
) -> str:
    """Human-readable note for a rejected candidate (probe reporting only)."""
    reason = rejection_reason or REJECTION_UNSUPPORTED
    claim_text = candidate.get("claim_text") or ""
    scope = candidate.get("scope")

    if reason == REJECTION_MISSING_QUOTE:
        return "quote_span is missing or empty"
    if reason == REJECTION_UNSUPPORTED:
        if not _quote_in_chunk(str(candidate.get("quote_span") or ""), chunk_text):
            return "quote_span is not an exact substring of the source chunk"
        for field in ("subject", "predicate", "object", "evidence_type", "domain"):
            value = candidate.get(field)
            if value is None or (isinstance(value, str) and not str(value).strip()):
                return f"required field {field!r} is missing or empty"
        if candidate.get("confidence") is None:
            return "confidence is required"
        if candidate.get("limitations") is None:
            return "limitations list is required (use [] if none)"
        return "claim failed unsupported_claim checks"
    if reason == REJECTION_OVERGENERALIZED:
        if not scope or not str(scope).strip():
            return "scope field is missing or empty"
        scope_normalized = _normalize(str(scope))
        if scope_normalized and scope_normalized not in _normalize(claim_text):
            return (
                f"scope {scope!r} must appear verbatim inside claim_text; "
                "embed the scope phrase in the claim sentence"
            )
        for pattern in _OVERGENERALIZED_CLAIM_PATTERNS:
            if pattern in _normalize(claim_text):
                return f"claim_text matches blocked overgeneralized pattern {pattern!r}"
        return "claim failed overgeneralized_scope checks"
    if reason == REJECTION_MISSING_SOURCE:
        return "source_id or chunk_id is missing"
    if reason == REJECTION_INJECTED_CONTENT:
        return "candidate matched prompt-injection rejection rules"
    return reason
