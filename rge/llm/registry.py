"""Model client selection. Fails closed on unknown modes.

Selection rules (03_MODEL_RUNTIME_SPEC.md section on registry):

    RGE_LLM_MODE=mock   -> MockModelClient
    RGE_LLM_MODE=ollama -> OllamaModelClient
    anything else       -> LlmModeError (no silent fallback)

The registry never falls back from ollama to mock in normal mode; silent
fallback would hide real runtime failures. Tests explicitly choose mock.
"""

from __future__ import annotations

from rge.config import RgeConfig, load_config
from rge.llm.base import ModelClient
from rge.llm.mock_client import MockModelClient
from rge.llm.ollama_client import OllamaModelClient


class LlmModeError(Exception):
    """Raised for unknown RGE_LLM_MODE values. Fail closed."""


def get_model_client(config: RgeConfig | None = None) -> ModelClient:
    """Return the model client for the configured mode."""
    cfg = config if config is not None else load_config()
    mode = cfg.llm_mode
    if mode == "mock":
        return MockModelClient()
    if mode == "ollama":
        return OllamaModelClient(
            base_url=cfg.ollama_base_url,
            model=cfg.local_llm,
            timeout_seconds=cfg.llm_timeout_seconds,
            temperature=cfg.llm_temperature,
        )
    raise LlmModeError(
        f"Unknown RGE_LLM_MODE={mode!r}. Valid modes are 'mock' and 'ollama'. "
        "Refusing to select a model client (fail closed; no silent fallback)."
    )
