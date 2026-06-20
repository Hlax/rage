"""Opt-in live network smoke for purpose-aware resolver query expansion.

```powershell
$env:RGE_ALLOW_LIVE_QUERY_EXPANSION_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_network_query_expansion_smoke.py -m live_network -q
```
"""

from __future__ import annotations

import pytest

from rge.modules.source_resolver import resolve_work_candidates
from rge.modules.source_resolver.query_expansion import (
    assert_live_query_expansion_smoke_env,
    metadata_only_dominates,
)
from rge.modules.source_resolver.status import (
    ABSTRACT_AVAILABLE,
    METADATA_ONLY,
    OA_PDF_AVAILABLE,
    OA_TEI_AVAILABLE,
)


def require_live_query_expansion_smoke_env() -> None:
    try:
        assert_live_query_expansion_smoke_env()
    except RuntimeError as exc:
        pytest.skip(str(exc))


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def live_query_expansion_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_QUERY_EXPANSION_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)


def test_live_query_expansion_smoke_blocked_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_ALLOW_LIVE_QUERY_EXPANSION_SMOKE", raising=False)
    with pytest.raises(RuntimeError, match="RGE_ALLOW_LIVE_QUERY_EXPANSION_SMOKE"):
        assert_live_query_expansion_smoke_env()


@pytest.mark.live_network
def test_live_network_query_expansion_improves_extractable_yield(
    live_query_expansion_env: None,
) -> None:
    require_live_query_expansion_smoke_env()
    result = resolve_work_candidates(
        query="How does AI affect human creativity?",
        domain_pack="creativity",
        limit=5,
        backends=["openalex", "arxiv"],
        fixture_mode=False,
    )
    records = list(result.get("records") or [])
    expansion = dict(result.get("query_expansion") or {})

    assert result["resolved_count"] >= 1
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
