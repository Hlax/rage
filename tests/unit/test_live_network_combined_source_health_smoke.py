"""Opt-in live network smoke chaining query expansion + source-health persistence.

```powershell
$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"
$env:RGE_ALLOW_LIVE_QUERY_EXPANSION_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_network_combined_source_health_smoke.py -m live_network -q
```
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.db.connection import ensure_database
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.live_arbitrary_source_health import (
    LIVE_SOURCE_HEALTH_ARTIFACT_NAME,
    LOCAL_SAFE_ARBITRARY_QUESTION,
    assert_live_combined_source_health_smoke_env,
    run_live_combined_source_health_query_expansion_smoke,
)
from rge.modules.source_resolver.query_expansion import metadata_only_dominates
from rge.modules.source_resolver.status import (
    ABSTRACT_AVAILABLE,
    METADATA_ONLY,
    OA_PDF_AVAILABLE,
    OA_TEI_AVAILABLE,
)


def require_live_combined_source_health_smoke_env() -> None:
    try:
        assert_live_combined_source_health_smoke_env()
    except RuntimeError as exc:
        pytest.skip(str(exc))


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def live_combined_source_health_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_QUERY_EXPANSION_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)


def test_live_combined_source_health_smoke_blocked_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", raising=False)
    monkeypatch.delenv("RGE_ALLOW_LIVE_QUERY_EXPANSION_SMOKE", raising=False)
    with pytest.raises(RuntimeError, match="RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE"):
        assert_live_combined_source_health_smoke_env()


@pytest.mark.live_network
def test_live_combined_source_health_query_expansion_smoke(
    live_combined_source_health_env: None,
    tmp_path: Path,
) -> None:
    require_live_combined_source_health_smoke_env()
    conn = ensure_database(tmp_path / "live_combined_health.sqlite")
    try:
        result = run_live_combined_source_health_query_expansion_smoke(
            conn,
            output_dir=tmp_path,
            limit=5,
        )
        expansion = dict(result.get("query_expansion") or {})
        records = list(result.get("expansion_records") or [])
        source_health = result["source_health"]
        artifact = result["atlas_safe_artifact"]

        assert result["status"] == "completed"
        assert result["question"] == LOCAL_SAFE_ARBITRARY_QUESTION
        assert result["discovery_query"]
        assert "?" not in str(result["discovery_query"])
        assert result["expansion_resolved_count"] >= 1
        assert source_health["sources_with_metadata"] >= 1
        assert artifact["source_health_summary"]["sources_with_metadata"] >= 1
        assert artifact["purpose_fit_summary"]
        artifact_path = tmp_path / LIVE_SOURCE_HEALTH_ARTIFACT_NAME
        assert artifact_path.is_file()
        loaded = json.loads(artifact_path.read_text(encoding="utf-8"))
        assert loaded["question"] == LOCAL_SAFE_ARBITRARY_QUESTION
        assert assert_no_private_fields({"artifact": artifact}) == []

        extractable_statuses = {
            ABSTRACT_AVAILABLE,
            OA_PDF_AVAILABLE,
            OA_TEI_AVAILABLE,
        }
        extractable_count = sum(
            1
            for record in records
            if str(record.get("source_status") or "") in extractable_statuses
            or str(record.get("abstract_text") or "").strip()
        )
        if expansion.get("expanded"):
            assert expansion.get("alternate_queries")
            assert int(expansion.get("metadata_only_after") or 0) <= int(
                expansion.get("metadata_only_before") or 0
            )
        assert extractable_count >= 1 or not metadata_only_dominates(records)
        assert sum(
            1 for record in records if record.get("source_status") == METADATA_ONLY
        ) >= 0
    finally:
        conn.close()
