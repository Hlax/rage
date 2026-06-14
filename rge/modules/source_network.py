"""Source discovery network opt-in helpers."""

from __future__ import annotations

from rge.config import RgeConfig, load_config


def source_network_enabled(config: RgeConfig | None = None) -> bool:
    """Return True only when source discovery network calls are explicitly enabled."""
    cfg = config if config is not None else load_config()
    return cfg.allow_source_network
