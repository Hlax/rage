"""Cloud synthesis provider id normalization (shared; no client imports)."""

from __future__ import annotations

_PROVIDER_ALIASES = {
    "mock": "mock_cloud",
    "mock_cloud": "mock_cloud",
    "openai": "openai",
    "live_openai": "openai",
}

_REGISTERED_PROVIDERS = frozenset({"mock_cloud", "openai"})


def normalize_provider_id(value: str | None) -> str:
    raw = str(value or "unknown").strip()
    if not raw:
        return "unknown"
    return _PROVIDER_ALIASES.get(raw.casefold(), raw)


def registered_provider_ids() -> frozenset[str]:
    return _REGISTERED_PROVIDERS
