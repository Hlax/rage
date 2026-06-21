"""Source discovery network opt-in helpers."""

from __future__ import annotations

import os

from rge.config import RgeConfig, load_config


def source_network_enabled(config: RgeConfig | None = None) -> bool:
    """Return True only when source discovery network calls are explicitly enabled."""
    cfg = config if config is not None else load_config()
    return cfg.allow_source_network


def assert_source_network_enabled(*, command: str = "source-network") -> dict[str, str]:
    """Fail closed unless operator opts into outbound source network calls."""
    allow = os.environ.get("RGE_ALLOW_SOURCE_NETWORK", "0").strip().casefold()
    if allow not in {"1", "true", "yes"}:
        raise RuntimeError(f"{command} requires RGE_ALLOW_SOURCE_NETWORK=1.")
    return {"RGE_ALLOW_SOURCE_NETWORK": allow}
