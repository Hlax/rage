"""Purpose-aware resolver query expansion when metadata-only records dominate."""

from __future__ import annotations

from typing import Any

from rge.modules.source_resolver.status import (
    ABSTRACT_AVAILABLE,
    METADATA_ONLY,
    OA_PDF_AVAILABLE,
    OA_TEI_AVAILABLE,
    rank_records_by_extractability,
    source_status_rank,
)

_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "for",
        "with",
        "how",
        "does",
        "do",
        "is",
        "are",
        "what",
        "when",
        "where",
        "why",
        "which",
        "that",
        "this",
        "human",
        "ai",
    }
)

_DEFAULT_ALTERNATE_QUERIES = (
    "human AI creativity",
    "generative AI creative output",
    "AI assisted creativity research",
)


def _record_key(record: dict[str, Any]) -> str:
    return str(record.get("source_id") or record.get("provider_id") or "")


def purpose_aware_alternate_queries(query: str) -> list[str]:
    """Build OpenAlex-safe alternate queries from a research question or keyword query."""
    cleaned = str(query or "").replace("?", "").strip()
    tokens = [
        token
        for token in cleaned.lower().split()
        if token not in _STOP_WORDS and len(token) > 2
    ]
    keyword_query = " ".join(tokens[:6]).strip()
    ordered: list[str] = []
    for candidate in (
        keyword_query,
        *_DEFAULT_ALTERNATE_QUERIES,
        cleaned,
    ):
        normalized = str(candidate or "").strip()
        if not normalized or normalized in ordered:
            continue
        if "?" in normalized:
            continue
        ordered.append(normalized)
    return ordered


def metadata_only_dominates(records: list[dict[str, Any]]) -> bool:
    """True when metadata-only rows outnumber extractable discovery statuses."""
    if not records:
        return False
    metadata_only = 0
    extractable = 0
    for record in records:
        status = str(record.get("source_status") or "")
        if status == METADATA_ONLY:
            metadata_only += 1
            continue
        if status in {ABSTRACT_AVAILABLE, OA_PDF_AVAILABLE, OA_TEI_AVAILABLE}:
            extractable += 1
            continue
        if str(record.get("abstract_text") or "").strip():
            extractable += 1
    return metadata_only >= 2 and metadata_only > extractable


def merge_unique_resolver_records(
    base_records: list[dict[str, Any]],
    extra_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge resolver records by source/provider id without duplicates."""
    merged = list(base_records)
    seen = {_record_key(record) for record in merged if _record_key(record)}
    for record in extra_records:
        key = _record_key(record)
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        merged.append(record)
    return merged


def expand_records_for_metadata_dominance(
    records: list[dict[str, Any]],
    *,
    query: str,
    domain_pack: str,
    limit: int,
    backends: list[str],
    discover_backend,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fetch alternate queries when the first pass is metadata-only heavy."""
    if not metadata_only_dominates(records):
        return records, {"expanded": False, "reason": "metadata_only_not_dominant"}

    alternates = purpose_aware_alternate_queries(query)
    attempted: list[str] = []
    merged = list(records)
    for alt_query in alternates:
        if alt_query.casefold() == str(query or "").casefold():
            continue
        attempted.append(alt_query)
        extra: list[dict[str, Any]] = []
        for backend in backends:
            if backend == "unpaywall":
                continue
            extra.extend(
                discover_backend(
                    backend,
                    query=alt_query,
                    domain_pack=domain_pack,
                    limit=max(2, limit),
                )
            )
        merged = merge_unique_resolver_records(merged, extra)
        merged = rank_records_by_extractability(merged)
        if not metadata_only_dominates(merged[:limit]):
            break

    merged = rank_records_by_extractability(merged)
    if len(merged) > limit:
        merged = merged[:limit]
    return merged, {
        "expanded": True,
        "alternate_queries": attempted,
        "metadata_only_before": sum(
            1 for record in records if record.get("source_status") == METADATA_ONLY
        ),
        "metadata_only_after": sum(
            1 for record in merged if record.get("source_status") == METADATA_ONLY
        ),
        "top_status_rank_after": source_status_rank(
            str((merged[0] or {}).get("source_status") or "")
        )
        if merged
        else 0,
    }
