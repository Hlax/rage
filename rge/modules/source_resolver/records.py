"""Normalize provider payloads into unified resolved source records."""

from __future__ import annotations

from typing import Any

from rge.modules.source_resolver.status import (
    derive_discovery_source_status,
    normalize_doi,
)


def make_source_id(*, source_kind: str, provider_id: str) -> str:
    return f"{source_kind}:{provider_id}"


def build_resolved_record(
    *,
    source_kind: str,
    provider_id: str,
    title: str = "",
    authors: list[str] | None = None,
    year: int | None = None,
    doi: str | None = None,
    openalex_id: str | None = None,
    arxiv_id: str | None = None,
    venue: str | None = None,
    abstract_text: str | None = None,
    abstract_source: str | None = None,
    is_oa: bool | None = None,
    oa_status: str | None = None,
    best_oa_location_url: str | None = None,
    pdf_url: str | None = None,
    tei_url: str | None = None,
    landing_page_url: str | None = None,
    license_info: str | None = None,
    oa_version: str | None = None,
    resolver_backend: str | None = None,
    source_status: str | None = None,
    domain_pack: str | None = None,
    discovered_at: str | None = None,
    enrichment_backends: list[str] | None = None,
    raw_provider: str | None = None,
) -> dict[str, Any]:
    """Return a unified resolved source record with explicit acquisition status."""
    normalized_doi = normalize_doi(doi)
    status = source_status or derive_discovery_source_status(
        abstract_text=abstract_text,
        pdf_url=pdf_url,
        tei_url=tei_url,
    )
    return {
        "source_id": make_source_id(source_kind=source_kind, provider_id=provider_id),
        "source_kind": source_kind,
        "provider_id": provider_id,
        "doi": normalized_doi,
        "openalex_id": openalex_id,
        "arxiv_id": arxiv_id,
        "title": title,
        "year": year,
        "authors": list(authors or []),
        "venue": venue,
        "abstract_text": abstract_text or "",
        "abstract_source": abstract_source,
        "is_oa": is_oa,
        "oa_status": oa_status,
        "best_oa_location_url": best_oa_location_url,
        "pdf_url": pdf_url,
        "tei_url": tei_url,
        "landing_page_url": landing_page_url,
        "license": license_info,
        "oa_version": oa_version,
        "resolver_backend": resolver_backend or source_kind,
        "source_status": status,
        "domain_pack": domain_pack,
        "discovered_at": discovered_at,
        "enrichment_backends": list(enrichment_backends or []),
        "raw_provider": raw_provider or source_kind,
    }


def resolved_record_from_openalex_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """Map an OpenAlex discovery candidate into a unified resolved record."""
    provider_id = str(candidate.get("provider_id") or "")
    primary = candidate.get("primary_location") or {}
    venue = None
    if isinstance(primary, dict):
        source = primary.get("source") or {}
        if isinstance(source, dict):
            venue = source.get("display_name")

    pdf_url = candidate.get("best_oa_pdf_url")
    if not pdf_url:
        for item in candidate.get("fetch_url_candidates") or []:
            kind = str(item.get("kind") or "")
            if kind.endswith(".pdf_url"):
                pdf_url = item.get("url")
                break
    abstract_text = candidate.get("abstract") or ""
    open_access_url = candidate.get("open_access_url")
    is_oa = bool(open_access_url or pdf_url or candidate.get("best_oa_landing_page_url"))

    return build_resolved_record(
        source_kind="openalex",
        provider_id=provider_id,
        title=str(candidate.get("title") or ""),
        authors=list(candidate.get("authors") or []),
        year=candidate.get("year"),
        doi=candidate.get("doi"),
        openalex_id=provider_id,
        venue=venue,
        abstract_text=abstract_text,
        abstract_source="openalex_inverted_index" if abstract_text else None,
        is_oa=is_oa,
        oa_status="open" if is_oa else "closed",
        best_oa_location_url=candidate.get("best_oa_landing_page_url")
        or candidate.get("landing_page_url"),
        pdf_url=pdf_url if isinstance(pdf_url, str) else None,
        landing_page_url=candidate.get("landing_page_url"),
        resolver_backend="openalex",
        domain_pack=candidate.get("domain_pack"),
        discovered_at=candidate.get("discovered_at"),
        raw_provider="openalex",
    )


def resolved_record_from_arxiv_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Map an arXiv metadata entry into a unified resolved record."""
    arxiv_id = str(entry.get("arxiv_id") or entry.get("provider_id") or "")
    pdf_url = entry.get("pdf_url")
    abstract_text = entry.get("abstract") or entry.get("abstract_text") or ""
    return build_resolved_record(
        source_kind="arxiv",
        provider_id=arxiv_id,
        title=str(entry.get("title") or ""),
        authors=list(entry.get("authors") or []),
        year=entry.get("year"),
        doi=entry.get("doi"),
        arxiv_id=arxiv_id,
        abstract_text=abstract_text,
        abstract_source="arxiv_api" if abstract_text else None,
        is_oa=True,
        oa_status="open",
        pdf_url=pdf_url if isinstance(pdf_url, str) else None,
        landing_page_url=entry.get("landing_page_url"),
        resolver_backend="arxiv",
        domain_pack=entry.get("domain_pack"),
        discovered_at=entry.get("discovered_at"),
        raw_provider="arxiv",
    )


def resolved_record_from_manual_fixture(entry: dict[str, Any]) -> dict[str, Any]:
    """Map a manual fixture entry into a unified resolved record."""
    fixture_id = str(entry.get("fixture_id") or entry.get("provider_id") or "manual")
    abstract_text = entry.get("abstract_text") or entry.get("abstract") or ""
    pdf_url = entry.get("pdf_url")
    tei_url = entry.get("tei_url")
    return build_resolved_record(
        source_kind="manual_fixture",
        provider_id=fixture_id,
        title=str(entry.get("title") or ""),
        authors=list(entry.get("authors") or []),
        year=entry.get("year"),
        doi=entry.get("doi"),
        abstract_text=abstract_text,
        abstract_source=entry.get("abstract_source") or "manual_fixture",
        is_oa=entry.get("is_oa"),
        oa_status=entry.get("oa_status"),
        pdf_url=pdf_url if isinstance(pdf_url, str) else None,
        tei_url=tei_url if isinstance(tei_url, str) else None,
        landing_page_url=entry.get("landing_page_url"),
        resolver_backend="manual_fixture",
        domain_pack=entry.get("domain_pack"),
        source_status=entry.get("source_status"),
        raw_provider="manual_fixture",
    )
