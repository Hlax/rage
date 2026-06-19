"""Deterministic OpenAlex URL candidate ordering for staged fetch (ticket-233)."""

from __future__ import annotations

from typing import Any

_NON_OA_URL_KINDS = frozenset(
    {
        "primary_location.landing_page_url_non_oa",
        "publisher_landing_page",
    }
)


def _host_priority_bonus(url: str) -> int:
    """Lower effective priority for trusted open mirrors; raise for brittle hosts."""
    lowered = url.casefold()
    if "pmc.ncbi.nlm.nih.gov" in lowered or "ncbi.nlm.nih.gov/pmc" in lowered:
        return -200
    if "arxiv.org" in lowered:
        return -150
    if "springeropen.com" in lowered:
        return -100
    if "europepmc.org" in lowered:
        return -90
    if "science.org" in lowered or "sciencedirect.com" in lowered:
        return 100
    if "link.springer.com" in lowered:
        return 80
    return 0


def _location_sort_key(location: dict[str, Any]) -> str:
    source = location.get("source") or {}
    return str(location.get("id") or source.get("id") or "")


def build_openalex_fetch_url_candidates(work: dict[str, Any]) -> list[dict[str, str]]:
    """Return ordered, deduplicated URL routes for one OpenAlex work payload."""
    ordered: list[tuple[int, str, str]] = []
    seen_urls: set[str] = set()

    def add(url: str | None, kind: str, priority: int) -> None:
        if not url or not isinstance(url, str):
            return
        normalized = url.strip()
        if not normalized or normalized in seen_urls:
            return
        seen_urls.add(normalized)
        ordered.append((priority, kind, normalized))

    best_oa = work.get("best_oa_location") or {}
    open_access = work.get("open_access") or {}
    primary = work.get("primary_location") or {}
    locations = work.get("locations") or []

    is_oa = bool(open_access.get("is_oa")) or bool(best_oa)

    add(best_oa.get("pdf_url"), "best_oa_location.pdf_url", 10)
    add(best_oa.get("landing_page_url"), "best_oa_location.landing_page_url", 20)
    add(open_access.get("oa_url"), "open_access.oa_url", 30)
    add(primary.get("pdf_url"), "primary_location.pdf_url", 40)
    if is_oa:
        add(
            primary.get("landing_page_url"),
            "primary_location.landing_page_url",
            50,
        )

    oa_locations = sorted(
        (loc for loc in locations if loc.get("is_oa")),
        key=_location_sort_key,
    )
    for index, location in enumerate(oa_locations):
        add(
            location.get("pdf_url"),
            f"locations[{index}].pdf_url",
            60 + (index * 2),
        )
        add(
            location.get("landing_page_url"),
            f"locations[{index}].landing_page_url",
            61 + (index * 2),
        )

    add(
        primary.get("landing_page_url"),
        "primary_location.landing_page_url_non_oa",
        900,
    )

    ordered.sort(
        key=lambda item: (item[0] + _host_priority_bonus(item[2]), item[1], item[2])
    )
    return [{"url": url, "kind": kind} for _, kind, url in ordered]


def primary_fetch_url(candidates: list[dict[str, str]]) -> str | None:
    if not candidates:
        return None
    return candidates[0]["url"]


def primary_fetch_url_kind(candidates: list[dict[str, str]]) -> str | None:
    if not candidates:
        return None
    return candidates[0]["kind"]


def is_non_oa_url_kind(kind: str) -> bool:
    return kind in _NON_OA_URL_KINDS
