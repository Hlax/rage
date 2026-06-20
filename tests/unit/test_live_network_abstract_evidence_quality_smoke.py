"""Opt-in live network smoke for abstract evidence quality proof.

```powershell
$env:RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE = "1"
$env:RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE = "1"
$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_network_abstract_evidence_quality_smoke.py -m live_network -q
```
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.db.connection import ensure_database
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.live_arbitrary_source_health import (
    LIVE_ABSTRACT_EVIDENCE_QUALITY_RUN_ID,
    LIVE_SOURCE_HEALTH_ARTIFACT_NAME,
    LOCAL_SAFE_ARBITRARY_QUESTION,
    assert_live_abstract_evidence_quality_smoke_env,
    run_live_network_abstract_evidence_quality_smoke,
)


def require_live_abstract_evidence_quality_env() -> None:
    try:
        assert_live_abstract_evidence_quality_smoke_env()
    except RuntimeError as exc:
        pytest.skip(str(exc))


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def live_abstract_evidence_quality_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)


def test_live_abstract_evidence_quality_smoke_blocked_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE", raising=False)
    with pytest.raises(RuntimeError, match="RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE"):
        assert_live_abstract_evidence_quality_smoke_env()


@pytest.mark.live_network
def test_live_network_abstract_evidence_quality_smoke(
    live_abstract_evidence_quality_env: None,
    tmp_path: Path,
) -> None:
    require_live_abstract_evidence_quality_env()
    conn = ensure_database(tmp_path / "live_abstract_evidence_quality.sqlite")
    try:
        result = run_live_network_abstract_evidence_quality_smoke(
            conn,
            output_dir=tmp_path,
            limit=5,
        )
        summary = result["evidence_quality_summary"]
        artifact = result["atlas_safe_artifact"]
        panels = summary["atlas_preview_panels_present"]

        assert result["status"] == "completed"
        assert result["question"] == LOCAL_SAFE_ARBITRARY_QUESTION
        assert result["resolver_mode"] == "live_network_abstract_evidence_quality"
        assert summary["live_source_count"] >= 1
        assert summary["sources_with_metadata"] >= 1
        assert summary["live_abstract_mode"] is True
        assert panels["source_health"]
        assert panels["graph_summary"]
        assert panels["readiness"]
        assert panels["trace_summary"]
        assert int(summary["trace_summary"]["trace_count"] or 0) >= 1
        assert result["evidence_quality_verdict"] in {"GO", "PARTIAL"}
        if result["evidence_quality_verdict"] == "GO":
            assert summary["claims_accepted"] >= 1
            assert summary["quote_backed_accepted_count"] >= 1
            assert summary["evidence_atom_count"] >= 1
        assert result["artifact_path"]
        assert (tmp_path / LIVE_SOURCE_HEALTH_ARTIFACT_NAME).is_file()
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
        assert result["run_report"].get("run_id") == LIVE_ABSTRACT_EVIDENCE_QUALITY_RUN_ID
    finally:
        conn.close()
