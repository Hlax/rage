"""Opt-in live network + Ollama smoke for local model extraction comparison."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.local_model_extraction_comparison import (
    assert_local_model_extraction_comparison_env,
    run_local_model_extraction_comparison,
)


@pytest.fixture
def local_model_comparison_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LOCAL_MODEL_EXTRACTION_COMPARISON", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_EXPANSION_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")


@pytest.mark.live_network
@pytest.mark.live_smoke
def test_live_network_local_model_extraction_comparison(
    tmp_path: Path,
    local_model_comparison_env: None,
) -> None:
    assert_local_model_extraction_comparison_env()
    try:
        result = run_local_model_extraction_comparison(
            output_dir=tmp_path,
            limit=3,
        )
    except RuntimeError as exc:
        if "Ollama" in str(exc) or "reachable" in str(exc).casefold():
            pytest.skip(f"Ollama unavailable for live smoke: {exc}")
        raise

    artifact = result["atlas_safe_artifact"]
    aggregate = artifact.get("comparison_aggregate") or {}

    assert result["comparison_verdict"] in {"GO", "PARTIAL"}
    assert int(aggregate.get("compared_abstract_count") or 0) >= 1
    assert "mock_total_accepted" in aggregate
    assert "local_ollama_total_accepted" in aggregate
    assert artifact.get("evaluation_only") is True
    assert assert_no_private_fields({"artifact": artifact}) == []

    if result.get("artifact_path"):
        loaded = json.loads(Path(result["artifact_path"]).read_text(encoding="utf-8"))
        assert loaded.get("abstract_comparisons")
