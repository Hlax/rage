"""Opt-in live network proof for selective full-text fetch.

```powershell
$env:RGE_ALLOW_LIVE_SELECTIVE_FETCH = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_selective_fulltext_validation.py -m live_network -q
```
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from rge.modules.research_run import run_research_demo


def require_live_selective_fetch_env() -> None:
    allow = os.environ.get("RGE_ALLOW_LIVE_SELECTIVE_FETCH", "0").strip().casefold()
    if allow not in ("1", "true", "yes"):
        pytest.skip("live selective fetch requires RGE_ALLOW_LIVE_SELECTIVE_FETCH=1")
    network = os.environ.get("RGE_ALLOW_SOURCE_NETWORK", "0").strip().casefold()
    if network not in ("1", "true", "yes"):
        pytest.skip("live selective fetch requires RGE_ALLOW_SOURCE_NETWORK=1")
    if not os.environ.get("OPENALEX_MAILTO", "").strip():
        pytest.skip("live selective fetch requires OPENALEX_MAILTO")


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def live_selective_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_SELECTIVE_FETCH", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)


@pytest.mark.live_network
def test_live_selective_fetch_openalex_top_source(
    live_selective_env: None,
    tmp_path: Path,
) -> None:
    require_live_selective_fetch_env()
    payload = run_research_demo(
        topic="human AI creativity songwriting",
        max_candidates=5,
        top_sources=2,
        full_text_top_n=1,
        mode="full-text-augmented",
        fixture_mode=False,
    )
    fulltext = payload.get("selective_fulltext") or {}
    acquisitions = list(fulltext.get("acquisitions") or [])
    assert acquisitions, "expected at least one selective acquisition attempt"
    first = acquisitions[0]
    assert first.get("requested") is True
    assert first.get("acquisition_status") != "live_selective_fetch_disabled"


@pytest.mark.live_network
def test_live_selective_fetch_blocked_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_SELECTIVE_FETCH", raising=False)

    payload = run_research_demo(
        topic="human AI creativity",
        max_candidates=3,
        top_sources=1,
        full_text_top_n=1,
        mode="full-text-augmented",
        fixture_mode=False,
    )
    acquisition = (payload.get("selective_fulltext") or {}).get("acquisitions", [{}])[0]
    assert acquisition.get("blocked") is True
    assert acquisition.get("blocked_reason") == "live_selective_fetch_disabled"
