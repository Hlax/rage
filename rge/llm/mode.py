"""Effective LLM mode resolution for pipeline structured tasks.

Live structured inference requires both ``RGE_LLM_MODE=ollama`` and an explicit
``RGE_ALLOW_LIVE_LLM=1`` opt-in. Without the opt-in, pipeline modules resolve
to mock mode (identical to pre-ticket-037 behavior). Fixture orchestration and
golden tests force mock separately and are not affected by operator ``.env``.
"""

from __future__ import annotations

from rge.config import RgeConfig, load_config


def live_llm_enabled(config: RgeConfig) -> bool:
    """Return True only when live structured Ollama calls are explicitly enabled."""
    return config.llm_mode == "ollama" and config.allow_live_llm


def effective_llm_mode(config: RgeConfig | None = None) -> str:
    """Return the model client mode pipeline modules should use."""
    cfg = config if config is not None else load_config()
    if live_llm_enabled(cfg):
        return "ollama"
    return "mock"
