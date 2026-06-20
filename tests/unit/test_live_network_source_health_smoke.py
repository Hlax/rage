"""Opt-in live network smoke for source-health + purpose-gate pipeline.

```powershell
$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_network_source_health_smoke.py -m live_network -q
```
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.db.connection import ensure_database
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.live_arbitrary_source_health import (
    LIVE_NETWORK_RUN_ID,
    LIVE_SOURCE_HEALTH_ARTIFACT_NAME,
    LOCAL_SAFE_ARBITRARY_QUESTION,
    assert_live_source_health_smoke_env,
    run_live_network_source_health_smoke,
)


def require_live_source_health_smoke_env() -> None:
    try:
        assert_live_source_health_smoke_env()
    except RuntimeError as exc:
        pytest.skip(str(exc))


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def live_source_health_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)


def test_live_source_health_smoke_blocked_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", raising=False)
    with pytest.raises(RuntimeError, match="RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE"):
        assert_live_source_health_smoke_env()


@pytest.mark.live_network
def test_live_network_source_health_smoke_persists_source_health(
    live_source_health_env: None,
    tmp_path: Path,
) -> None:
    require_live_source_health_smoke_env()
    conn = ensure_database(tmp_path / "live_network_health.sqlite")
    try:
        result = run_live_network_source_health_smoke(
            conn,
            output_dir=tmp_path,
            limit=5,
        )
        report = result["run_report"]
        artifact = result["atlas_safe_artifact"]
        source_health = result["source_health"]
        evidence = result["evidence"]

        assert result["status"] == "completed"
        assert result["resolver_mode"] == "live_network"
        assert 1 <= result["resolved_count"] <= 5
        assert source_health["sources_with_metadata"] >= 1
        assert source_health["resolver_source_counts"]
        assert source_health["purpose_fit_status_counts"]
        assert source_health["purpose_gate_decision_counts"]
        assert "acquisition_quality_summary" in report
        aq = report["acquisition_quality_summary"]
        assert aq["sources_with_metadata"] >= 1
        assert aq.get("resolver_source_counts")
        assert evidence["skipped_before_extraction"] >= 0
        assert artifact["source_health_summary"]["sources_with_metadata"] >= 1
        assert artifact["purpose_fit_summary"]
        assert result["artifact_path"]
        artifact_path = tmp_path / LIVE_SOURCE_HEALTH_ARTIFACT_NAME
        assert artifact_path.is_file()
        loaded = json.loads(artifact_path.read_text(encoding="utf-8"))
        assert loaded["question"] == LOCAL_SAFE_ARBITRARY_QUESTION
        assert assert_no_private_fields({"artifact": artifact}) == []
        joined = json.dumps(artifact)
        for forbidden in (
            "source_id",
            "claim_id",
            "quote_id",
            "chunk_id",
            "local_path",
            "prompt",
            "hidden evaluator",
        ):
            assert forbidden not in joined.casefold()
        assert report.get("run_id") == LIVE_NETWORK_RUN_ID
    finally:
        conn.close()


@pytest.mark.live_network
def test_live_network_source_health_smoke_resolver_breakdown(
    live_source_health_env: None,
    tmp_path: Path,
) -> None:
    require_live_source_health_smoke_env()
    conn = ensure_database(tmp_path / "live_breakdown.sqlite")
    try:
        result = run_live_network_source_health_smoke(
            conn,
            output_dir=tmp_path,
            limit=5,
        )
        breakdown = result["resolver_breakdown"]
        backend_counts = result["backend_counts"]
        assert sum(breakdown.values()) >= 1
        assert sum(backend_counts.values()) >= 1
        assert any(
            backend in breakdown
            for backend in ("openalex", "arxiv")
        )
    finally:
        conn.close()
