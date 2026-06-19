"""Research run network gates for selective full-text acquisition."""

from __future__ import annotations

from rge.config import RgeConfig, load_config


def live_selective_fetch_enabled(config: RgeConfig | None = None) -> bool:
    """Return True when live selective full-text fetch is explicitly enabled."""
    cfg = config if config is not None else load_config()
    return cfg.allow_source_network and cfg.allow_live_selective_fetch
