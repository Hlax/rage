"""Cloud synthesis provider registry (ticket-059; mock-first default)."""

from __future__ import annotations

import os

from rge.llm.cloud_synthesis_providers import (
    normalize_provider_id,
    registered_provider_ids,
)

_REGISTERED_PROVIDERS = registered_provider_ids()


class CloudSynthesisRegistryError(Exception):
    """Raised when provider selection fails closed."""


def provider_allowlisted(provider_id: str) -> bool:
    raw = (
        os.environ.get("RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST")
        or os.environ.get("RGE_CLOUD_PROVIDER_ALLOWLIST")
        or ""
    ).strip()
    if not raw:
        return False
    allowed = {item.strip().casefold() for item in raw.split(",") if item.strip()}
    return normalize_provider_id(provider_id).casefold() in allowed


def resolve_requested_provider() -> str:
    raw = os.environ.get("RGE_CLOUD_SYNTHESIS_PROVIDER", "mock_cloud").strip()
    return normalize_provider_id(raw or "mock_cloud")


def get_cloud_synthesis_client(
    provider_id: str | None = None,
    *,
    allow_unlisted_openai: bool = False,
):
    """Return a cloud synthesis client. Default is deterministic mock_cloud."""
    from rge.llm.openai_synthesis_client import (
        MockCloudSynthesisClient,
        OpenAISynthesisClient,
    )

    resolved = normalize_provider_id(provider_id or resolve_requested_provider())
    if resolved == "mock_cloud":
        return MockCloudSynthesisClient()
    if resolved == "openai":
        if not allow_unlisted_openai and not provider_allowlisted("openai"):
            raise CloudSynthesisRegistryError(
                "Provider 'openai' is not allowlisted. "
                "Set RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST to include openai."
            )
        return OpenAISynthesisClient()
    raise CloudSynthesisRegistryError(
        f"Unknown cloud synthesis provider {resolved!r}. "
        f"Registered providers: {', '.join(sorted(_REGISTERED_PROVIDERS))}."
    )
