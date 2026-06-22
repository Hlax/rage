"""Cloud synthesis provider registry (normalization only; no API calls)."""

from __future__ import annotations

_PROVIDER_ALIASES = {
    "mock": "mock_cloud",
    "mock_cloud": "mock_cloud",
    "openai": "openai",
    "openrouter": "openrouter",
    "live_openai": "openai",
    "live_openrouter": "openrouter",
}


def normalize_provider_id(value: str | None) -> str:
    raw = str(value or "unknown").strip()
    if not raw:
        return "unknown"
    return _PROVIDER_ALIASES.get(raw.casefold(), raw)
