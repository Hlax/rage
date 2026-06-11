"""Typed runtime configuration for the Research Graph Engine.

Configuration is read from environment variables, with optional defaults
loaded from a local ``.env`` file (simple ``KEY=VALUE`` lines). Environment
variables always win over ``.env`` values.

See ``.env.example`` for the documented settings and
``docs/agents/03_MODEL_RUNTIME_SPEC.md`` for the model runtime contract.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(Exception):
    """Raised when configuration is missing or invalid. Fail closed."""


VALID_LLM_MODES = ("mock", "ollama")

_DEFAULTS = {
    "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
    "RGE_LOCAL_LLM": "qwen2.5:7b",
    "RGE_LLM_MODE": "ollama",
    "RGE_TEST_LLM_MODE": "mock",
    "RGE_LLM_TIMEOUT_SECONDS": "60",
    "RGE_LLM_TEMPERATURE": "0",
    "RGE_LLM_SCHEMA_VERSION": "0.1.0",
    "RGE_EMBEDDING_MODE": "local_sentence_transformer",
    "RGE_EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
}


def _read_env_file(path: Path) -> dict[str, str]:
    """Parse a minimal .env file: KEY=VALUE lines, '#' comments, no quoting magic."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


@dataclass(frozen=True)
class RgeConfig:
    """Resolved runtime configuration."""

    ollama_base_url: str
    local_llm: str
    llm_mode: str
    test_llm_mode: str
    llm_timeout_seconds: int
    llm_temperature: float
    llm_schema_version: str
    embedding_mode: str
    embedding_model: str


def load_config(env_file: Path | None = None) -> RgeConfig:
    """Load configuration from defaults, optional .env file, then os.environ.

    Raises ConfigError on values that cannot be parsed. Does not validate
    llm_mode here; the LLM registry fails closed on unknown modes so that the
    error surfaces at client-selection time with a clear message.
    """
    merged = dict(_DEFAULTS)
    merged.update(_read_env_file(env_file if env_file is not None else Path(".env")))
    for key in _DEFAULTS:
        if key in os.environ:
            merged[key] = os.environ[key]

    try:
        timeout = int(merged["RGE_LLM_TIMEOUT_SECONDS"])
        temperature = float(merged["RGE_LLM_TEMPERATURE"])
    except ValueError as exc:
        raise ConfigError(f"Invalid numeric config value: {exc}") from exc

    return RgeConfig(
        ollama_base_url=merged["OLLAMA_BASE_URL"],
        local_llm=merged["RGE_LOCAL_LLM"],
        llm_mode=merged["RGE_LLM_MODE"],
        test_llm_mode=merged["RGE_TEST_LLM_MODE"],
        llm_timeout_seconds=timeout,
        llm_temperature=temperature,
        llm_schema_version=merged["RGE_LLM_SCHEMA_VERSION"],
        embedding_mode=merged["RGE_EMBEDDING_MODE"],
        embedding_model=merged["RGE_EMBEDDING_MODEL"],
    )
