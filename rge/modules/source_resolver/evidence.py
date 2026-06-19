"""Explain what evidence is available before LLM extraction."""

from __future__ import annotations

from typing import Any

from rge.modules.source_resolver.status import (
    ABSTRACT_AVAILABLE,
    EXTRACTABLE,
    METADATA_ONLY,
    OA_PDF_AVAILABLE,
    OA_TEI_AVAILABLE,
    CLEAN_TEXT_READY,
    has_abstract_text,
)


def explain_source_evidence(record: dict[str, Any]) -> dict[str, Any]:
    """Return a pre-extraction evidence summary for one resolved source."""
    status = str(record.get("source_status") or METADATA_ONLY)
    abstract_text = str(record.get("abstract_text") or "")
    has_abstract = has_abstract_text(abstract_text)
    has_pdf = bool(record.get("pdf_url"))
    has_tei = bool(record.get("tei_url"))
    has_clean_text = status in {CLEAN_TEXT_READY, EXTRACTABLE}

    can_extract_abstract_claims = has_abstract and status in {
        ABSTRACT_AVAILABLE,
        OA_PDF_AVAILABLE,
        OA_TEI_AVAILABLE,
        CLEAN_TEXT_READY,
        EXTRACTABLE,
    }
    can_fetch_full_text = has_pdf or has_tei
    can_extract_full_text_claims = has_clean_text or status == EXTRACTABLE

    if can_extract_full_text_claims:
        recommendation = "full_text_quote_first"
        summary = (
            "Clean full text is available; prefer quote-first extraction from "
            "parsed document text."
        )
    elif can_extract_abstract_claims:
        recommendation = "abstract_quote_first"
        summary = (
            "Abstract text is available; use abstract-first quote-grounded "
            "extraction. Full text is not required for this step."
        )
    elif can_fetch_full_text:
        recommendation = "fetch_full_text_then_extract"
        summary = (
            "Metadata and OA location are available but no abstract was resolved. "
            "Fetch full text before attempting quote-grounded extraction."
        )
    elif status == METADATA_ONLY:
        recommendation = "skip_llm_extraction"
        summary = (
            "Only bibliographic metadata is available. Do not call the LLM for "
            "claim extraction until abstract or full text is acquired."
        )
    else:
        recommendation = "inspect_acquisition_failure"
        summary = (
            f"Source status is {status!r}. Resolve acquisition issues before "
            "attempting claim extraction."
        )

    return {
        "source_id": record.get("source_id"),
        "source_status": status,
        "has_abstract": has_abstract,
        "abstract_char_count": len(abstract_text.strip()),
        "has_pdf_url": has_pdf,
        "has_tei_url": has_tei,
        "can_extract_abstract_claims": can_extract_abstract_claims,
        "can_fetch_full_text": can_fetch_full_text,
        "can_extract_full_text_claims": can_extract_full_text_claims,
        "extraction_recommendation": recommendation,
        "summary": summary,
    }


def explain_resolved_sources(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [explain_source_evidence(record) for record in records]
