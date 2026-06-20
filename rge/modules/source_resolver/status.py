"""Source acquisition status vocabulary for the unified resolver layer."""

from __future__ import annotations

from typing import Any

# Discovery-time statuses (resolver layer).
METADATA_ONLY = "metadata_only"
ABSTRACT_AVAILABLE = "abstract_available"
OA_PDF_AVAILABLE = "oa_pdf_available"
OA_TEI_AVAILABLE = "oa_tei_available"

# Post-acquisition statuses (fetch/parse pipeline; resolver may carry forward).
DOWNLOAD_FAILED = "download_failed"
PARSE_FAILED = "parse_failed"
CLEAN_TEXT_READY = "clean_text_ready"
EXTRACTABLE = "extractable"

SOURCE_STATUS_VALUES: tuple[str, ...] = (
    METADATA_ONLY,
    ABSTRACT_AVAILABLE,
    OA_PDF_AVAILABLE,
    OA_TEI_AVAILABLE,
    DOWNLOAD_FAILED,
    PARSE_FAILED,
    CLEAN_TEXT_READY,
    EXTRACTABLE,
)

DISCOVERY_STATUSES: frozenset[str] = frozenset(
    {
        METADATA_ONLY,
        ABSTRACT_AVAILABLE,
        OA_PDF_AVAILABLE,
        OA_TEI_AVAILABLE,
    }
)

ACQUISITION_STATUSES: frozenset[str] = frozenset(
    {
        DOWNLOAD_FAILED,
        PARSE_FAILED,
        CLEAN_TEXT_READY,
        EXTRACTABLE,
    }
)

_STATUS_RANK: dict[str, int] = {
    METADATA_ONLY: 10,
    ABSTRACT_AVAILABLE: 20,
    OA_PDF_AVAILABLE: 30,
    OA_TEI_AVAILABLE: 40,
    DOWNLOAD_FAILED: 50,
    PARSE_FAILED: 55,
    CLEAN_TEXT_READY: 60,
    EXTRACTABLE: 70,
}


def source_status_rank(status: str | None) -> int:
    """Higher rank means more extractable / acquisition-ready."""
    return _STATUS_RANK.get(str(status or "").strip(), 0)


def rank_records_by_extractability(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Prefer abstract/OA-ready records before metadata-only truncation."""
    return sorted(
        records,
        key=lambda record: (
            source_status_rank(str(record.get("source_status") or "")),
            bool(str(record.get("abstract_text") or "").strip()),
        ),
        reverse=True,
    )


def normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    value = str(doi).strip()
    if value.startswith("https://doi.org/"):
        return value.removeprefix("https://doi.org/")
    if value.startswith("http://doi.org/"):
        return value.removeprefix("http://doi.org/")
    if value.startswith("doi:"):
        return value.removeprefix("doi:").strip()
    return value or None


def has_abstract_text(abstract_text: str | None) -> bool:
    return bool(str(abstract_text or "").strip())


def derive_discovery_source_status(
    *,
    abstract_text: str | None,
    pdf_url: str | None = None,
    tei_url: str | None = None,
) -> str:
    """Derive the best discovery-time status from resolver metadata."""
    if tei_url:
        return OA_TEI_AVAILABLE
    if pdf_url:
        return OA_PDF_AVAILABLE
    if has_abstract_text(abstract_text):
        return ABSTRACT_AVAILABLE
    return METADATA_ONLY


def merge_source_status(current: str | None, incoming: str) -> str:
    """Keep the higher-ranked explicit status when enriching records."""
    if not current:
        return incoming
    current_rank = _STATUS_RANK.get(current, 0)
    incoming_rank = _STATUS_RANK.get(incoming, 0)
    return incoming if incoming_rank >= current_rank else current


def apply_acquisition_source_status(
    record: dict[str, Any],
    *,
    download_failed: bool = False,
    parse_failed: bool = False,
    clean_text_ready: bool = False,
    extractable: bool = False,
) -> str:
    """Update a resolved record with post-fetch/parse acquisition status."""
    if extractable:
        status = EXTRACTABLE
    elif clean_text_ready:
        status = CLEAN_TEXT_READY
    elif parse_failed:
        status = PARSE_FAILED
    elif download_failed:
        status = DOWNLOAD_FAILED
    else:
        status = derive_discovery_source_status(
            abstract_text=record.get("abstract_text"),
            pdf_url=record.get("pdf_url"),
            tei_url=record.get("tei_url"),
        )
    record["source_status"] = status
    return status
