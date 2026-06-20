"""Opt-in live network smoke for abstract quote → atom → trace pipeline.

```powershell
$env:RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE = "1"
$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_network_abstract_evidence_atom_trace_smoke.py -m live_network -q
```
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.db.connection import ensure_database
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.live_arbitrary_source_health import (
    LIVE_ABSTRACT_ATOM_TRACE_RUN_ID,
    LIVE_SOURCE_HEALTH_ARTIFACT_NAME,
    LOCAL_SAFE_ARBITRARY_QUESTION,
    assert_live_abstract_evidence_atom_trace_smoke_env,
    run_live_network_abstract_evidence_atom_trace_smoke,
)


def require_live_abstract_atom_trace_env() -> None:
    try:
        assert_live_abstract_evidence_atom_trace_smoke_env()
    except RuntimeError as exc:
        pytest.skip(str(exc))


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def live_abstract_atom_trace_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)


def test_live_abstract_atom_trace_smoke_blocked_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE", raising=False)
    with pytest.raises(RuntimeError, match="RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE"):
        assert_live_abstract_evidence_atom_trace_smoke_env()


@pytest.mark.live_network
def test_live_network_abstract_evidence_atom_trace_smoke(
    live_abstract_atom_trace_env: None,
    tmp_path: Path,
) -> None:
    require_live_abstract_atom_trace_env()
    conn = ensure_database(tmp_path / "live_abstract_atom_trace.sqlite")
    try:
        result = run_live_network_abstract_evidence_atom_trace_smoke(
            conn,
            output_dir=tmp_path,
            limit=5,
        )
        report = result["run_report"]
        artifact = result["atlas_safe_artifact"]
        evidence = result["evidence"]
        atom_trace = result["atom_trace"]
        trace_summary = artifact.get("trace_summary") or {}

        assert result["status"] == "completed"
        assert result["resolver_mode"] == "live_network_abstract_atom_trace"
        assert evidence.get("live_abstract_mode") is True
        assert evidence["accepted_count"] >= 1
        assert report["claims_accepted"] >= 1
        assert atom_trace.get("status") == "completed"
        assert int(atom_trace.get("promoted_atom_count") or 0) >= 1
        assert int(atom_trace.get("relationship_count") or 0) >= 1
        assert int(trace_summary.get("trace_count") or 0) >= 1
        assert trace_summary.get("atlas_trace_preview")
        assert result["artifact_path"]
        assert (tmp_path / LIVE_SOURCE_HEALTH_ARTIFACT_NAME).is_file()
        loaded = json.loads((tmp_path / LIVE_SOURCE_HEALTH_ARTIFACT_NAME).read_text(encoding="utf-8"))
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
        assert report.get("run_id") == LIVE_ABSTRACT_ATOM_TRACE_RUN_ID
    finally:
        conn.close()
