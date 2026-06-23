"""Operator env loader tests (ticket-059)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.modules.operator_env_loader import (
    assert_public_site_does_not_load_operator_env,
    load_operator_env,
    openai_key_available,
    operator_cloud_env_status,
    redact_operator_env,
)


def test_public_site_guard_flags_operator_env_loader_reference() -> None:
    violations = assert_public_site_does_not_load_operator_env(
        "import { operator_env_loader } from 'rge/modules/operator_env_loader'",
        "apps/public-site/lib/example.ts",
    )
    assert violations


def test_redact_operator_env_removes_secret_keys() -> None:
    redacted = redact_operator_env(
        {
            "RGE_CLOUD_LLM_ENABLED": "1",
            "OPENAI_API_KEY": "sk-secret",
            "OPENAI_MODEL": "gpt-4o-mini",
        }
    )
    assert "OPENAI_API_KEY" not in redacted
    assert redacted["OPENAI_MODEL"] == "gpt-4o-mini"


def test_load_operator_env_applies_non_secret_values(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / "operator.env"
    env_file.write_text(
        "\n".join(
            [
                "RGE_CLOUD_LLM_ENABLED=1",
                "OPENAI_API_KEY=sk-from-file",
                "RGE_CLOUD_MAX_USD_PER_RUN=0.25",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("RGE_CLOUD_LLM_ENABLED", raising=False)
    monkeypatch.delenv("RGE_CLOUD_MAX_USD_PER_RUN", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    merged = load_operator_env(apply=True, env_file=env_file, repo_root=tmp_path)
    assert merged["RGE_CLOUD_LLM_ENABLED"] == "1"
    assert "OPENAI_API_KEY" not in merged
    assert os.environ["RGE_CLOUD_LLM_ENABLED"] == "1"
    assert os.environ["OPENAI_API_KEY"] == "sk-from-file"
    assert openai_key_available() is True


def test_openai_key_available_is_boolean_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-boolean-check")
    assert openai_key_available() is True
    status = operator_cloud_env_status()
    blob = json.dumps(status)
    assert "sk-boolean-check" not in blob
    assert status["openai_key_available"] is True
