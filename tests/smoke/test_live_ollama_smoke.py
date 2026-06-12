"""Optional live Ollama smoke tests (excluded from default pytest via marker)."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.live_smoke


@pytest.fixture(autouse=True)
def require_live_smoke_env() -> None:
    allow = os.environ.get("RGE_ALLOW_LIVE_LLM", "0").strip().casefold()
    if allow not in ("1", "true", "yes"):
        pytest.skip("live smoke requires RGE_ALLOW_LIVE_LLM=1")
    if os.environ.get("RGE_LLM_MODE", "mock") != "ollama":
        pytest.skip("live smoke requires RGE_LLM_MODE=ollama")


def test_ollama_health_check_does_not_raise() -> None:
    from rge.config import load_config
    from rge.llm.registry import get_model_client

    config = load_config()
    client = get_model_client(config, mode="ollama")
    report = client.health_check()
    assert report["mode"] == "ollama"
    assert "reachable" in report
    assert "model_available" in report
