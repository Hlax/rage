"""Opt-in live network smoke for source expansion proof."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.db.connection import ensure_database
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.live_source_expansion import (
    assert_live_source_expansion_smoke_env,
    run_live_source_expansion_smoke,
)


@pytest.fixture
def live_source_expansion_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_EXPANSION_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")


@pytest.mark.live_network
def test_live_network_source_expansion_smoke(
    tmp_path: Path,
    live_source_expansion_env: None,
) -> None:
    assert_live_source_expansion_smoke_env()
    conn = ensure_database(tmp_path / "live_source_expansion.sqlite")
    try:
        result = run_live_source_expansion_smoke(conn, output_dir=tmp_path, limit=5)
    finally:
        conn.close()

    artifact = result["atlas_safe_artifact"]
    expansion = artifact.get("source_expansion_summary") or {}

    assert result["source_expansion_verdict"] in {"GO", "PARTIAL"}
    assert int(expansion.get("source_diversity_count") or 0) >= 2
    assert expansion.get("resolver_breakdown")
    assert expansion.get("persisted_resolver_source_counts")
    assert "blocked_source_reason_counts" in expansion
    assert assert_no_private_fields({"artifact": artifact}) == []

    if result.get("artifact_path"):
        loaded = json.loads(Path(result["artifact_path"]).read_text(encoding="utf-8"))
        assert loaded.get("source_expansion_summary")
