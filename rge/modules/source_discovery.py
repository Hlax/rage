"""Find candidate sources from manual fixtures and search APIs.

Mixed deterministic/model-assisted. Starts with manual/fixture sources;
search APIs come later. Browser automation is a fallback, never the default.
Phase 3: provider registry + OpenAlex metadata discovery (ticket-139).
"""

from __future__ import annotations

from typing import Any

DISCOVER_SOURCES_COMMAND = "discover-sources"
DISCOVER_SOURCES_PHASE = "3"
DISCOVER_SOURCES_NOT_IMPLEMENTED_DETAIL = (
    "Phase 3 source discovery is not implemented yet."
)
NOT_IMPLEMENTED_EXIT_CODE = 2
BLOCKED_EXIT_CODE = 1
ERROR_EXIT_CODE = 1
OK_EXIT_CODE = 0


def build_discover_sources_not_implemented_payload() -> dict[str, str]:
    """Single source of truth for the Phase 3 discover-sources stub response."""
    return {
        "status": "not_implemented",
        "command": DISCOVER_SOURCES_COMMAND,
        "phase": DISCOVER_SOURCES_PHASE,
        "detail": DISCOVER_SOURCES_NOT_IMPLEMENTED_DETAIL,
    }


def discover_sources_not_implemented_result() -> tuple[dict[str, str], int]:
    """Return structured stub payload and exit code for discover-sources CLI."""
    return build_discover_sources_not_implemented_payload(), NOT_IMPLEMENTED_EXIT_CODE


def build_source_network_blocked_payload(
    *, provider: str | None = None
) -> dict[str, Any]:
    return {
        "status": "blocked",
        "command": DISCOVER_SOURCES_COMMAND,
        "reason": "source_network_disabled",
        "provider": provider,
        "detail": (
            "Source discovery network calls require RGE_ALLOW_SOURCE_NETWORK=1."
        ),
    }


def build_discover_sources_error_payload(
    *,
    reason: str,
    detail: str,
    provider: str | None = None,
) -> dict[str, Any]:
    return {
        "status": "error",
        "command": DISCOVER_SOURCES_COMMAND,
        "reason": reason,
        "provider": provider,
        "detail": detail,
    }


def run_discover_sources_command(
    *,
    provider_id: str | None,
    query: str | None,
    domain_pack: str,
    limit: int,
    health: bool,
) -> tuple[dict[str, Any], int]:
    """Execute discover-sources CLI logic with structured JSON responses."""
    if not provider_id:
        return discover_sources_not_implemented_result()

    from rge.modules.source_network import source_network_enabled
    from rge.modules.source_providers import get_provider, list_provider_ids
    from rge.modules.source_providers.openalex import SourceDiscoveryProviderError

    provider = get_provider(provider_id)
    if provider is None:
        payload = build_discover_sources_error_payload(
            reason="unknown_provider",
            detail=(
                f"Unknown provider {provider_id!r}. "
                f"Available providers: {', '.join(list_provider_ids()) or 'none'}."
            ),
            provider=provider_id,
        )
        return payload, ERROR_EXIT_CODE

    if health:
        payload = {
            "command": DISCOVER_SOURCES_COMMAND,
            "status": "ok",
            "health": provider.health_check(),
        }
        return payload, OK_EXIT_CODE

    if not query:
        payload = build_discover_sources_error_payload(
            reason="missing_query",
            detail="--query is required when --provider is set.",
            provider=provider_id,
        )
        return payload, ERROR_EXIT_CODE

    if not source_network_enabled():
        payload = build_source_network_blocked_payload(provider=provider_id)
        return payload, BLOCKED_EXIT_CODE

    try:
        candidates = provider.discover(query, domain_pack, limit)
    except SourceDiscoveryProviderError as exc:
        payload = build_discover_sources_error_payload(
            reason="provider_error",
            detail=str(exc),
            provider=provider_id,
        )
        return payload, ERROR_EXIT_CODE

    payload = {
        "command": DISCOVER_SOURCES_COMMAND,
        "status": "ok",
        "provider": provider_id,
        "query": query,
        "domain_pack": domain_pack,
        "limit": limit,
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    return payload, OK_EXIT_CODE


def discover_candidate_sources(contract: dict[str, Any]) -> list[dict[str, Any]]:
    """Discover candidate sources for a contract via configured providers."""
    query = str(contract.get("topic") or contract.get("query") or "").strip()
    domain_pack = str(contract.get("domain") or contract.get("domain_pack") or "")
    limit = int(contract.get("limit") or 10)
    provider_id = str(contract.get("provider") or "openalex")
    payload, exit_code = run_discover_sources_command(
        provider_id=provider_id,
        query=query or None,
        domain_pack=domain_pack,
        limit=limit,
        health=False,
    )
    if exit_code != OK_EXIT_CODE:
        detail = payload.get("detail") or payload.get("reason") or "discovery failed"
        raise NotImplementedError(str(detail))
    return list(payload.get("candidates") or [])
