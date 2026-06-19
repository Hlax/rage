"""Unified source resolver: OpenAlex, Unpaywall, arXiv, and manual fixtures."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

from rge.modules.source_network import source_network_enabled
from rge.modules.source_providers.openalex import SourceDiscoveryProviderError
from rge.modules.source_resolver.evidence import explain_resolved_sources, explain_source_evidence
from rge.modules.source_resolver.records import (
    resolved_record_from_arxiv_entry,
    resolved_record_from_manual_fixture,
    resolved_record_from_openalex_candidate,
)
from rge.modules.source_resolver.status import normalize_doi

RESOLVE_SOURCES_COMMAND = "resolve-sources"
OK_EXIT_CODE = 0
BLOCKED_EXIT_CODE = 1
ERROR_EXIT_CODE = 1

REPO_ROOT = Path(__file__).resolve().parents[3]
MANUAL_FIXTURE_PATH = REPO_ROOT / "fixtures" / "source_providers" / "manual_resolver_fixtures.json"
DEFAULT_SOURCE_BACKENDS = ("openalex",)


def parse_source_backends(raw: str | None) -> list[str]:
    if not raw:
        return list(DEFAULT_SOURCE_BACKENDS)
    backends = [item.strip().lower() for item in raw.split(",") if item.strip()]
    return backends or list(DEFAULT_SOURCE_BACKENDS)


def load_manual_fixture_records(
    *,
    domain_pack: str,
    fixture_path: Path | None = None,
) -> list[dict[str, Any]]:
    path = fixture_path or MANUAL_FIXTURE_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("records") or payload.get("candidates") or []
    records: list[dict[str, Any]] = []
    for entry in entries:
        item = dict(entry)
        item.setdefault("domain_pack", domain_pack)
        records.append(resolved_record_from_manual_fixture(item))
    return records


def _discover_backend_candidates(
    backend: str,
    *,
    query: str,
    domain_pack: str,
    limit: int,
) -> list[dict[str, Any]]:
    from rge.modules.source_providers import get_provider

    if backend == "manual_fixture":
        return load_manual_fixture_records(domain_pack=domain_pack)

    provider = get_provider(backend)
    if provider is None:
        raise SourceDiscoveryProviderError(
            f"Unknown resolver backend {backend!r}."
        )
    raw_candidates = provider.discover(query, domain_pack, limit)
    if backend == "openalex":
        return [resolved_record_from_openalex_candidate(item) for item in raw_candidates]
    if backend == "arxiv":
        return [resolved_record_from_arxiv_entry(item) for item in raw_candidates]
    return [
        resolved_record_from_openalex_candidate(item)
        if item.get("provider") == "openalex"
        else resolved_record_from_arxiv_entry(item)
        for item in raw_candidates
    ]


def enrich_records_with_unpaywall(
    records: list[dict[str, Any]],
    *,
    enricher: Any | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Enrich DOI-backed records with Unpaywall without failing the run."""
    from rge.modules.source_providers.unpaywall import (
        UnpaywallEnricher,
        enrich_record_with_unpaywall,
        fetch_unpaywall_work,
    )

    active = enricher or UnpaywallEnricher()
    enriched: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for record in records:
        doi = normalize_doi(record.get("doi"))
        if not doi:
            enriched.append(record)
            skipped.append(
                {
                    "source_id": str(record.get("source_id") or ""),
                    "reason": "missing_doi",
                }
            )
            continue
        try:
            payload = fetch_unpaywall_work(
                doi,
                email=active._email(),
                urlopen=active._urlopen or urllib.request.urlopen,
            )
            merged = enrich_record_with_unpaywall(record, payload)
            enriched.append(merged)
        except SourceDiscoveryProviderError as exc:
            enriched.append(record)
            skipped.append(
                {
                    "source_id": str(record.get("source_id") or ""),
                    "reason": "unpaywall_error",
                    "detail": str(exc),
                }
            )
    return enriched, skipped


def resolve_work_candidates(
    *,
    query: str,
    domain_pack: str = "creativity",
    limit: int = 10,
    backends: list[str] | None = None,
    enrich_unpaywall: bool = False,
    fixture_mode: bool = False,
    enricher: Any | None = None,
) -> dict[str, Any]:
    """Resolve candidate works across configured backends into unified records."""
    selected_backends = list(backends or DEFAULT_SOURCE_BACKENDS)
    if fixture_mode:
        selected_backends = ["manual_fixture"]

    records: list[dict[str, Any]] = []
    backend_counts: dict[str, int] = {}

    for backend in selected_backends:
        if backend == "unpaywall":
            continue
        candidates = _discover_backend_candidates(
            backend,
            query=query,
            domain_pack=domain_pack,
            limit=limit,
        )
        backend_counts[backend] = len(candidates)
        records.extend(candidates)

    unpaywall_skipped: list[dict[str, str]] = []
    if enrich_unpaywall:
        records, unpaywall_skipped = enrich_records_with_unpaywall(
            records,
            enricher=enricher,
        )

    evidence = explain_resolved_sources(records)
    return {
        "query": query,
        "domain_pack": domain_pack,
        "limit": limit,
        "backends": selected_backends,
        "fixture_mode": fixture_mode,
        "enrich_unpaywall": enrich_unpaywall,
        "resolved_count": len(records),
        "backend_counts": backend_counts,
        "records": records,
        "evidence_summaries": evidence,
        "unpaywall_skipped": unpaywall_skipped,
    }


def build_resolve_sources_blocked_payload(*, reason: str, detail: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "command": RESOLVE_SOURCES_COMMAND,
        "reason": reason,
        "detail": detail,
    }


def build_resolve_sources_error_payload(*, reason: str, detail: str) -> dict[str, Any]:
    return {
        "status": "error",
        "command": RESOLVE_SOURCES_COMMAND,
        "reason": reason,
        "detail": detail,
    }


def run_resolve_sources_command(
    *,
    query: str | None,
    domain_pack: str,
    limit: int,
    backends: list[str] | None,
    enrich_unpaywall: bool,
    fixture_mode: bool,
    explain_only: bool = False,
    health: bool = False,
) -> tuple[dict[str, Any], int]:
    from rge.modules.source_providers import get_provider, list_provider_ids
    from rge.modules.source_providers.unpaywall import UnpaywallEnricher

    if health:
        checks: dict[str, Any] = {}
        for backend in parse_source_backends(",".join(backends or [])):
            if backend == "manual_fixture":
                checks[backend] = {"provider": backend, "configured": True}
                continue
            if backend == "unpaywall":
                checks[backend] = UnpaywallEnricher().health_check()
                continue
            provider = get_provider(backend)
            if provider is None:
                checks[backend] = {
                    "provider": backend,
                    "configured": False,
                    "detail": "unknown provider",
                }
            else:
                checks[backend] = provider.health_check()
        return (
            {
                "command": RESOLVE_SOURCES_COMMAND,
                "status": "ok",
                "health": checks,
                "available_providers": list_provider_ids(),
            },
            OK_EXIT_CODE,
        )

    if not query and not fixture_mode:
        payload = build_resolve_sources_error_payload(
            reason="missing_query",
            detail="--query is required unless --fixture-mode is set.",
        )
        return payload, ERROR_EXIT_CODE

    selected = list(backends or DEFAULT_SOURCE_BACKENDS)
    needs_network = not fixture_mode and any(
        backend not in {"manual_fixture", "unpaywall"} for backend in selected
    ) or enrich_unpaywall
    if needs_network and not source_network_enabled():
        payload = build_resolve_sources_blocked_payload(
            reason="source_network_disabled",
            detail="Source resolver network calls require RGE_ALLOW_SOURCE_NETWORK=1.",
        )
        return payload, BLOCKED_EXIT_CODE

    try:
        result = resolve_work_candidates(
            query=query or "",
            domain_pack=domain_pack,
            limit=limit,
            backends=selected,
            enrich_unpaywall=enrich_unpaywall,
            fixture_mode=fixture_mode,
        )
    except SourceDiscoveryProviderError as exc:
        payload = build_resolve_sources_error_payload(
            reason="resolver_error",
            detail=str(exc),
        )
        return payload, ERROR_EXIT_CODE

    payload = {
        "command": RESOLVE_SOURCES_COMMAND,
        "status": "ok",
        **result,
    }
    if explain_only:
        payload = {
            "command": RESOLVE_SOURCES_COMMAND,
            "status": "ok",
            "query": result["query"],
            "resolved_count": result["resolved_count"],
            "evidence_summaries": result["evidence_summaries"],
        }
    return payload, OK_EXIT_CODE


__all__ = [
    "RESOLVE_SOURCES_COMMAND",
    "explain_source_evidence",
    "load_manual_fixture_records",
    "resolve_work_candidates",
    "run_resolve_sources_command",
]
