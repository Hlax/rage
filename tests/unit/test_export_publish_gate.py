"""Unit tests for live-mode public export publish gating (no Ollama)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rge.modules.card_exporter import public_site_export_dir, resolve_export_targets


def test_live_mode_default_export_skips_public_site(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")
    repo = tmp_path / "repo"
    (repo / "data" / "exports").mkdir(parents=True)
    (repo / "apps" / "public-site" / "public" / "data").mkdir(parents=True)

    targets = resolve_export_targets(output_dirs=None, repo_root=repo)
    assert targets == [repo / "data" / "exports"]
    assert public_site_export_dir(repo) not in targets


def test_live_mode_publish_allows_public_site(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")
    repo = tmp_path / "repo"
    (repo / "data" / "exports").mkdir(parents=True)
    (repo / "apps" / "public-site" / "public" / "data").mkdir(parents=True)

    targets = resolve_export_targets(
        output_dirs=None, repo_root=repo, publish_public=True
    )
    assert public_site_export_dir(repo) in targets


def test_live_mode_blocks_explicit_public_site_output_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")
    repo = tmp_path / "repo"
    public_dir = repo / "apps" / "public-site" / "public" / "data"
    public_dir.mkdir(parents=True)

    with pytest.raises(ValueError, match="requires --publish"):
        resolve_export_targets(
            output_dirs=[public_dir],
            repo_root=repo,
        )
