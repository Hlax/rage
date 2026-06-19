"""Config loader reads gitignored .env.local after .env."""

from __future__ import annotations

from pathlib import Path

import pytest

from rge.config import load_config


def test_load_config_reads_env_local_overlay(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    for key in (
        "RGE_ALLOW_SOURCE_NETWORK",
        "OPENALEX_MAILTO",
        "OPENALEX_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    (tmp_path / ".env").write_text(
        "RGE_ALLOW_SOURCE_NETWORK=0\nOPENALEX_MAILTO=\n",
        encoding="utf-8",
    )
    (tmp_path / ".env.local").write_text(
        "RGE_ALLOW_SOURCE_NETWORK=1\n"
        "OPENALEX_MAILTO=operator@example.com\n"
        "OPENALEX_API_KEY=test-key-local\n",
        encoding="utf-8",
    )

    config = load_config()

    assert config.allow_source_network is True
    assert config.openalex_mailto == "operator@example.com"
    assert config.openalex_api_key == "test-key-local"


def test_shell_env_overrides_env_local(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env.local").write_text(
        "OPENALEX_MAILTO=from-file@example.com\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENALEX_MAILTO", "from-shell@example.com")

    config = load_config()

    assert config.openalex_mailto == "from-shell@example.com"
