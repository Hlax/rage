"""Operator env loading policy (CLI-only; public site must not load operator env)."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from rge.config import _merge_env_files, load_config

_FORBIDDEN_PATTERNS = (
    re.compile(r"dotenv.*\.env\.local", re.IGNORECASE),
    re.compile(r"loadOperatorEnv", re.IGNORECASE),
    re.compile(r"operator_env_loader", re.IGNORECASE),
    re.compile(r"process\.env\.(?:RGE_|OPENAI_|OPENROUTER_)", re.IGNORECASE),
)

_SECRET_ENV_KEYS = frozenset(
    {
        "OPENAI_API_KEY",
        "RGE_OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "ANTHROPIC_API_KEY",
        "OPENALEX_API_KEY",
    }
)


def _is_secret_env_key(name: str) -> bool:
    upper = name.upper()
    if upper in _SECRET_ENV_KEYS:
        return True
    return upper.endswith("_API_KEY") or upper.endswith("_SECRET")


def assert_public_site_does_not_load_operator_env(
    source_text: str,
    relative_path: str,
) -> list[str]:
    violations: list[str] = []
    for pattern in _FORBIDDEN_PATTERNS:
        if pattern.search(source_text):
            violations.append(
                f"{relative_path} may load operator env ({pattern.pattern})"
            )
    return violations


def load_operator_env(
    *,
    apply: bool = True,
    env_file: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    """Load operator env via the shared config merge path (.env then .env.local).

    Process environment variables always win. Secret values are never returned.
    """
    previous_cwd = Path.cwd()
    if repo_root is not None:
        os.chdir(repo_root)
    try:
        merged = _merge_env_files(env_file)
        for key, value in merged.items():
            if key in os.environ:
                continue
            if apply and not _is_secret_env_key(key):
                os.environ[key] = value
            elif apply and _is_secret_env_key(key):
                # Apply secrets to process env without exposing them in the return dict.
                os.environ.setdefault(key, value)
        return redact_operator_env(merged)
    finally:
        os.chdir(previous_cwd)


def redact_operator_env(values: dict[str, str]) -> dict[str, str]:
    """Return a public-safe view of env values (secrets omitted)."""
    return {
        key: value
        for key, value in values.items()
        if not _is_secret_env_key(key)
    }


def openai_key_available() -> bool:
    """Boolean-only credential presence check (never returns the key value)."""
    return bool(
        os.environ.get("OPENAI_API_KEY", "").strip()
        or os.environ.get("RGE_OPENAI_API_KEY", "").strip()
    )


def operator_cloud_env_status(*, root: Path | None = None) -> dict[str, Any]:
    """Public-safe operator cloud env summary for inspect/plan surfaces."""
    if root is not None:
        load_operator_env(apply=False, repo_root=root)
    config = load_config()
    return {
        "openai_key_available": openai_key_available(),
        "cloud_llm_enabled": config.cloud_llm_enabled,
        "cloud_synthesis_provider": config.cloud_synthesis_provider,
        "openai_synthesis_enabled": config.allow_openai_synthesis,
        "openai_live_http_enabled": config.allow_openai_synthesis_live_http,
        "cloud_max_usd_per_run": config.cloud_max_usd_per_run,
        "cloud_max_tokens_per_call": config.cloud_max_tokens_per_call,
        "env_local_loaded_via": "rge.config._merge_env_files",
    }
