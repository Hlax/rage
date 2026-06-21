"""Opt-in live network smoke for web adapter live fetch."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.web_adapter_scrapling_proof import (
    assert_web_adapter_scrapling_proof_env,
    run_web_adapter_scrapling_with_fresh_db,
)


@pytest.fixture
def web_adapter_live_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_WEB_ADAPTER_SCRAPLING_PROOF", "1")
    monkeypatch.setenv("RGE_ALLOW_WEB_ADAPTER_SCRAPLING_LIVE_FETCH", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")


@pytest.mark.live_network
def test_live_network_web_adapter_scrapling_live_fetch(
    tmp_path: Path,
    web_adapter_live_env: None,
) -> None:
    assert_web_adapter_scrapling_proof_env(require_live_fetch=True)
    result = run_web_adapter_scrapling_with_fresh_db(
        output_dir=tmp_path,
        live_fetch=True,
    )

    artifact = result["atlas_safe_artifact"]
    live = artifact.get("live_fetch_summary") or {}

    assert result["web_adapter_verdict"] in {"GO", "PARTIAL"}
    assert live.get("status") in {"completed", "failed"}
    assert assert_no_private_fields({"artifact": artifact}) == []

    if live.get("status") == "completed":
        assert live.get("extractable") in {True, False}

    loaded = json.loads(Path(result["artifact_path"]).read_text(encoding="utf-8"))
    assert loaded.get("live_fetch_summary")
