"""Unit tests for scheduled research loop."""

from __future__ import annotations

from pathlib import Path

import pytest

from rge.modules.scheduled_research_loop import (
    ScheduledResearchLoopBlockedError,
    assert_scheduled_mock_profile,
    execute_scheduled_research_loop,
)


def test_scheduled_mock_profile_enforces_mock_llm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_ALLOW_SOURCE_NETWORK", raising=False)
    gates = assert_scheduled_mock_profile(profile="local_mock_daily")
    assert gates["RGE_LLM_MODE"] == "mock"


def test_scheduled_profile_blocks_live_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    with pytest.raises(ScheduledResearchLoopBlockedError):
        assert_scheduled_mock_profile(profile="local_mock_daily")


def test_execute_scheduled_loop_writes_reports(tmp_path: Path) -> None:
    payload = execute_scheduled_research_loop(
        profile="local_mock_daily",
        root=tmp_path,
        report_dir=tmp_path / "scheduled",
        refresh_atlas=True,
    )
    assert payload["live_network_blocked"] is True
    assert payload["live_llm_blocked"] is True
    assert payload["no_merge"] is True
    assert payload["no_public_publish"] is True
    assert payload["step_status"]["one_button_research_run"] == "completed"
    assert Path(payload["report_paths"]["json_latest"]).is_file()
