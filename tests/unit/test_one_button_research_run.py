"""Unit tests for one-button research run orchestrator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.modules.one_button_research_run import (
    OneButtonResearchRunGateError,
    assert_live_llm_extract_gates,
    assert_live_network_gates,
    execute_one_button_research_run,
)


def test_one_button_research_run_mock_completes(tmp_path: Path) -> None:
    db_path = tmp_path / "scratch.sqlite"
    artifact_dir = tmp_path / "artifacts"
    result = execute_one_button_research_run(
        topic="Does AI improve creative output while reducing diversity?",
        domain="creativity",
        db_path=db_path,
        artifact_dir=artifact_dir,
        export_atlas=True,
        root=tmp_path,
    )
    assert result["status"] == "completed"
    assert result["llm_mode"] == "mock"
    assert result["no_auto_promotion"] is True
    assert result["no_public_publish"] is True
    assert Path(result["artifacts"]["research_quality"]).is_file()
    assert Path(result["artifacts"]["atlas_snapshot"]).is_file()
    quality = json.loads(
        Path(result["artifacts"]["research_quality"]).read_text(encoding="utf-8")
    )
    assert "research_quality_verdict" in quality


def test_live_network_gate_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RGE_ALLOW_SOURCE_NETWORK", raising=False)
    monkeypatch.delenv("OPENALEX_MAILTO", raising=False)
    with pytest.raises(OneButtonResearchRunGateError):
        assert_live_network_gates()


def test_live_llm_extract_gate_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    with pytest.raises(OneButtonResearchRunGateError):
        assert_live_llm_extract_gates()
