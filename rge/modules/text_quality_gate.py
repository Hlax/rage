"""Text quality and extraction-readiness gates before LLM claim extraction."""

from __future__ import annotations

import json
import re
from typing import Any

from rge.modules.document_parser import (
    CLEAN_TEXT_READY,
    DIRTY_TEXT,
    PARSE_FAILED,
    score_text_quality,
)

MIN_QUOTEABLE_SPAN_CHARS = 24
_BLOCKED_ACQUISITION_STATUSES = frozenset(
    {
        DIRTY_TEXT,
        PARSE_FAILED,
        "dirty_text",
        "parse_failed",
        "download_failed",
        "full_text_parse_failed",
    }
)


def discover_quoteable_spans(text: str, *, min_chars: int = MIN_QUOTEABLE_SPAN_CHARS) -> list[str]:
    """Return deterministic candidate quote spans from clean chunk text."""
    stripped = text.strip()
    if not stripped:
        return []
    spans: list[str] = []
    seen: set[str] = set()
    for sentence in re.split(r"(?<=[.!?])\s+", stripped):
        candidate = sentence.strip()
        if len(candidate) < min_chars:
            continue
        key = candidate.casefold()
        if key in seen:
            continue
        seen.add(key)
        spans.append(candidate)
    if spans:
        return spans
    if len(stripped) >= min_chars:
        return [stripped]
    return []


def assess_chunk_extractability(chunk_text: str) -> dict[str, Any]:
    """Score one chunk for quote-first extraction readiness."""
    scores = score_text_quality(chunk_text)
    quoteable_spans = discover_quoteable_spans(chunk_text)
    extractable = bool(scores["is_clean"] and quoteable_spans)
    return {
        "readable_char_ratio": round(float(scores["readable_char_ratio"]), 4),
        "sentence_count": int(scores["sentence_count"]),
        "quoteable_span_count": len(quoteable_spans),
        "extracted_char_count": int(scores["extracted_char_count"]),
        "is_clean": bool(scores["is_clean"]),
        "extractable": extractable,
        "quoteable_spans": quoteable_spans[:5],
    }


def _parse_domain_metadata(source: Any) -> dict[str, Any]:
    raw = getattr(source, "domain_metadata_json", None) or "{}"
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}


def gate_source_for_extraction(source: Any, chunks: list[Any]) -> dict[str, Any]:
    """Fail closed when acquisition/text quality is not ready for LLM extraction."""
    metadata = _parse_domain_metadata(source)
    acquisition_status = str(
        metadata.get("acquisition_status")
        or metadata.get("source_status")
        or metadata.get("text_quality_status")
        or ""
    ).strip()
    if acquisition_status in _BLOCKED_ACQUISITION_STATUSES:
        return {
            "allowed": False,
            "reason": acquisition_status,
            "detail": f"Source blocked by acquisition status: {acquisition_status}",
            "chunk_assessments": [],
        }

    assessments: list[dict[str, Any]] = []
    extractable_chunks = 0
    for chunk in chunks:
        chunk_text = getattr(chunk, "chunk_text", "") or ""
        assessment = assess_chunk_extractability(chunk_text)
        assessment["chunk_id"] = getattr(chunk, "id", None)
        assessments.append(assessment)
        if assessment["extractable"]:
            extractable_chunks += 1

    if not chunks:
        return {
            "allowed": False,
            "reason": "no_chunks",
            "detail": "Source has no chunks to extract from.",
            "chunk_assessments": [],
        }
    if extractable_chunks == 0:
        return {
            "allowed": False,
            "reason": DIRTY_TEXT,
            "detail": "No chunk passed text quality or quoteability gates.",
            "chunk_assessments": assessments,
        }
    return {
        "allowed": True,
        "reason": CLEAN_TEXT_READY,
        "detail": "At least one chunk is extractable.",
        "chunk_assessments": assessments,
        "extractable_chunk_count": extractable_chunks,
    }
