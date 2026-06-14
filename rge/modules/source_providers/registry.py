"""Registry for API-first source discovery providers."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SourceProvider(Protocol):
    provider_id: str

    def health_check(self) -> dict[str, Any]:
        """Return provider readiness metadata without secret values."""

    def discover(
        self, query: str, domain_pack: str, limit: int
    ) -> list[dict[str, Any]]:
        """Return candidate source metadata records (no ingest/fetch)."""


_PROVIDERS: dict[str, SourceProvider] = {}


def register_provider(provider: SourceProvider) -> None:
    _PROVIDERS[provider.provider_id] = provider


def get_provider(provider_id: str) -> SourceProvider | None:
    return _PROVIDERS.get(provider_id)


def list_provider_ids() -> list[str]:
    return sorted(_PROVIDERS)


def clear_providers_for_tests() -> None:
    """Test helper to reset registry state."""
    _PROVIDERS.clear()
