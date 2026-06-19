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

MIN_STAGED_RANK2_SCAN_MAX = 1
MAX_STAGED_RANK2_SCAN_MAX = 50
DEFAULT_STAGED_RANK2_SCAN_MAX = 10

_DEFAULTS = {
    "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
    "RGE_LOCAL_LLM": "qwen2.5:7b",
    "RGE_LLM_MODE": "ollama",
    "RGE_TEST_LLM_MODE": "mock",
    "RGE_ALLOW_LIVE_LLM": "0",
    "RGE_ALLOW_SOURCE_NETWORK": "0",
    "RGE_ALLOW_LIVE_SELECTIVE_FETCH": "0",
    "RGE_GROBID_URL": "",
    "OPENALEX_MAILTO": "",
    "OPENALEX_API_KEY": "",
    "UNPAYWALL_EMAIL": "",
    "RGE_LLM_TIMEOUT_SECONDS": "60",
    "RGE_LLM_TEMPERATURE": "0",
    "RGE_LLM_SCHEMA_VERSION": "0.1.0",
    "RGE_EMBEDDING_MODE": "local_sentence_transformer",
    "RGE_EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
    "RGE_STAGED_RANK2_SCAN_MAX": str(DEFAULT_STAGED_RANK2_SCAN_MAX),
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
    allow_live_llm: bool
    allow_source_network: bool
    allow_live_selective_fetch: bool
    grobid_url: str
    openalex_mailto: str
    openalex_api_key: str
    unpaywall_email: str
    llm_timeout_seconds: int
    llm_temperature: float
    llm_schema_version: str
    embedding_mode: str
    embedding_model: str
    staged_rank2_scan_max: int


def parse_staged_rank2_scan_max(raw: str | int | None = None) -> int:
    """Resolve bounded rank-2 staged candidate title scan window."""
    if raw is None:
        value_raw = os.environ.get(
            "RGE_STAGED_RANK2_SCAN_MAX",
            str(DEFAULT_STAGED_RANK2_SCAN_MAX),
        )
    else:
        value_raw = str(raw)
    try:
        value = int(str(value_raw).strip())
    except ValueError as exc:
        raise ConfigError(
            f"Invalid RGE_STAGED_RANK2_SCAN_MAX={value_raw!r}. Must be an integer."
        ) from exc
    if value < MIN_STAGED_RANK2_SCAN_MAX or value > MAX_STAGED_RANK2_SCAN_MAX:
        raise ConfigError(
            f"RGE_STAGED_RANK2_SCAN_MAX={value} out of range "
            f"[{MIN_STAGED_RANK2_SCAN_MAX}, {MAX_STAGED_RANK2_SCAN_MAX}]."
        )
    return value


def _merge_env_files(env_file: Path | None = None) -> dict[str, str]:
    """Load defaults plus optional ``.env`` / ``.env.local`` overlays."""
    merged = dict(_DEFAULTS)
    if env_file is not None:
        merged.update(_read_env_file(env_file))
        return merged
    merged.update(_read_env_file(Path(".env")))
    merged.update(_read_env_file(Path(".env.local")))
    return merged


def load_config(env_file: Path | None = None) -> RgeConfig:
    """Load configuration from defaults, optional env files, then os.environ.

    When ``env_file`` is omitted, reads ``.env`` then ``.env.local`` (gitignored
    operator profile). Process environment variables always override file values.

    Raises ConfigError on values that cannot be parsed. Does not validate
    llm_mode here; the LLM registry fails closed on unknown modes so that the
    error surfaces at client-selection time with a clear message.
    """
    merged = _merge_env_files(env_file)
    for key in _DEFAULTS:
        if key in os.environ:
            merged[key] = os.environ[key]

    try:
        timeout = int(merged["RGE_LLM_TIMEOUT_SECONDS"])
        temperature = float(merged["RGE_LLM_TEMPERATURE"])
    except ValueError as exc:
        raise ConfigError(f"Invalid numeric config value: {exc}") from exc

    allow_raw = merged.get("RGE_ALLOW_LIVE_LLM", "0").strip().casefold()
    if allow_raw in ("1", "true", "yes"):
        allow_live_llm = True
    elif allow_raw in ("0", "false", "no", ""):
        allow_live_llm = False
    else:
        raise ConfigError(
            f"Invalid RGE_ALLOW_LIVE_LLM={merged.get('RGE_ALLOW_LIVE_LLM')!r}. "
            "Use 1/true/yes to enable live structured calls or 0/false/no."
        )

    network_raw = merged.get("RGE_ALLOW_SOURCE_NETWORK", "0").strip().casefold()
    if network_raw in ("1", "true", "yes"):
        allow_source_network = True
    elif network_raw in ("0", "false", "no", ""):
        allow_source_network = False
    else:
        raise ConfigError(
            "Invalid RGE_ALLOW_SOURCE_NETWORK="
            f"{merged.get('RGE_ALLOW_SOURCE_NETWORK')!r}. "
            "Use 1/true/yes to enable source discovery network calls or 0/false/no."
        )

    selective_raw = merged.get("RGE_ALLOW_LIVE_SELECTIVE_FETCH", "0").strip().casefold()
    if selective_raw in ("1", "true", "yes"):
        allow_live_selective_fetch = True
    elif selective_raw in ("0", "false", "no", ""):
        allow_live_selective_fetch = False
    else:
        raise ConfigError(
            "Invalid RGE_ALLOW_LIVE_SELECTIVE_FETCH="
            f"{merged.get('RGE_ALLOW_LIVE_SELECTIVE_FETCH')!r}. "
            "Use 1/true/yes to enable live selective full-text fetch or 0/false/no."
        )

    return RgeConfig(
        ollama_base_url=merged["OLLAMA_BASE_URL"],
        local_llm=merged["RGE_LOCAL_LLM"],
        llm_mode=merged["RGE_LLM_MODE"],
        test_llm_mode=merged["RGE_TEST_LLM_MODE"],
        allow_live_llm=allow_live_llm,
        allow_source_network=allow_source_network,
        allow_live_selective_fetch=allow_live_selective_fetch,
        grobid_url=merged.get("RGE_GROBID_URL", "").strip(),
        openalex_mailto=merged.get("OPENALEX_MAILTO", "").strip(),
        openalex_api_key=merged.get("OPENALEX_API_KEY", "").strip(),
        unpaywall_email=(
            merged.get("UNPAYWALL_EMAIL", "").strip()
            or merged.get("OPENALEX_MAILTO", "").strip()
        ),
        llm_timeout_seconds=timeout,
        llm_temperature=temperature,
        llm_schema_version=merged["RGE_LLM_SCHEMA_VERSION"],
        embedding_mode=merged["RGE_EMBEDDING_MODE"],
        embedding_model=merged["RGE_EMBEDDING_MODEL"],
        staged_rank2_scan_max=parse_staged_rank2_scan_max(
            merged.get("RGE_STAGED_RANK2_SCAN_MAX")
        ),
    )
