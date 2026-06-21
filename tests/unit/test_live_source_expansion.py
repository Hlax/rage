"""Unit tests for live source expansion summary and verdict logic."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.live_source_expansion import (
    assert_live_source_expansion_smoke_env,
    build_source_expansion_summary,
    classify_source_expansion_verdict,
    enrich_atlas_artifact_for_source_expansion,
    resolve_live_expanded_network_source_records,
    sync_source_expansion_artifact_to_public_site,
)


def test_missing_expansion_gate_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("RGE_ALLOW_LIVE_SOURCE_EXPANSION_SMOKE", raising=False)
    with pytest.raises(RuntimeError, match="RGE_ALLOW_LIVE_SOURCE_EXPANSION_SMOKE"):
        assert_live_source_expansion_smoke_env()


def test_build_source_expansion_summary_counts_diversity() -> None:
    resolved = {
        "backends": ["openalex", "arxiv"],
        "enrich_unpaywall": True,
        "resolved_count": 3,
        "backend_counts": {"openalex": 2, "arxiv": 2},
        "records": [
            {"doi": "10.1/example", "enrichment_backends": ["unpaywall"], "source_kind": "openalex"},
            {"source_kind": "arxiv"},
            {"source_kind": "openalex", "failure_reason": "purpose_mismatch"},
        ],
        "unpaywall_skipped": [{"reason": "missing_doi"}],
    }
    source_health = {
        "resolver_source_counts": {"openalex": 2, "arxiv": 1},
        "failure_reason_counts": {"purpose_mismatch": 1},
        "availability_counts": {"oa_available": 1, "pdf_available": 0, "tei_available": 0},
    }
    summary = build_source_expansion_summary(resolved, source_health=source_health)
    assert summary["source_diversity_count"] == 2
    assert summary["resolver_breakdown"]["openalex"] == 2
    assert summary["unpaywall_enriched_count"] == 1
    assert summary["blocked_sources_visible"] is True
    assert assert_no_private_fields({"summary": summary}) == []


def test_classify_source_expansion_verdict_go_and_partial() -> None:
    summary = {
        "resolved_count": 5,
        "source_diversity_count": 2,
        "resolver_breakdown": {"openalex": 3, "arxiv": 2},
        "enrich_unpaywall": True,
        "doi_backed_count": 2,
        "unpaywall_enriched_count": 1,
        "unpaywall_skipped_counts": {"missing_doi": 1},
    }
    verdict, _ = classify_source_expansion_verdict(
        summary,
        pipeline_result={"run_report": {"claims_accepted": 3}},
    )
    assert verdict == "GO"

    partial = {**summary, "source_diversity_count": 1, "resolver_breakdown": {"openalex": 5}}
    verdict, rationale = classify_source_expansion_verdict(partial)
    assert verdict == "PARTIAL"
    assert "diversity" in rationale.casefold()


def test_resolve_live_expanded_calls_unpaywall_enrichment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_EXPANSION_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")

    captured: dict[str, object] = {}

    def fake_resolve(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {
            "records": [{"source_kind": "openalex"}],
            "resolved_count": 1,
            "backend_counts": {"openalex": 1},
            "backends": ["openalex", "arxiv"],
            "enrich_unpaywall": kwargs.get("enrich_unpaywall"),
        }

    with patch(
        "rge.modules.live_source_expansion.resolve_work_candidates",
        side_effect=fake_resolve,
    ):
        result = resolve_live_expanded_network_source_records(limit=3)

    assert captured["enrich_unpaywall"] is True
    assert captured["backends"] == ["openalex", "arxiv"]
    assert result["source_expansion_enabled"] is True


def test_build_atlas_artifact_includes_source_expansion_summary(tmp_path: Path) -> None:
    from rge.db.connection import ensure_database
    from rge.modules.live_arbitrary_source_health import (
        build_atlas_safe_run_artifact,
        persist_resolved_source_health,
    )

    conn = ensure_database(tmp_path / "expansion.sqlite")
    records = [
        {
            "source_id": "openalex:W1",
            "source_kind": "openalex",
            "source_status": "abstract_available",
            "abstract_text": "Generative AI may reshape creative workflows and ideation patterns in design teams.",
            "title": "AI creativity study",
            "doi": "10.1234/example",
            "enrichment_backends": ["unpaywall"],
            "is_oa": True,
        }
    ]
    persist_resolved_source_health(conn, records, question="How does AI affect human creativity?")
    resolved = {
        "source_expansion_enabled": True,
        "backends": ["openalex", "arxiv"],
        "enrich_unpaywall": True,
        "backend_counts": {"openalex": 1, "arxiv": 1},
        "records": records,
        "resolved_count": 1,
        "unpaywall_skipped": [],
    }
    artifact = build_atlas_safe_run_artifact(
        conn,
        question="How does AI affect human creativity?",
        resolved=resolved,
    )
    expansion = artifact.get("source_expansion_summary") or {}
    assert expansion.get("source_diversity_count", 0) >= 1
    assert "resolver_breakdown" in expansion
    assert assert_no_private_fields({"artifact": artifact}) == []


def test_enrich_and_sync_source_expansion_artifact(tmp_path: Path) -> None:
    summary = build_source_expansion_summary(
        {
            "backends": ["openalex", "arxiv"],
            "enrich_unpaywall": True,
            "resolved_count": 2,
            "backend_counts": {"openalex": 1, "arxiv": 1},
            "records": [{"source_kind": "openalex"}, {"source_kind": "arxiv"}],
            "unpaywall_skipped": [],
        }
    )
    artifact = enrich_atlas_artifact_for_source_expansion(
        {
            "schema_version": "atlas_source_health_run_v0.1.0",
            "status": "completed",
            "source_expansion_summary": summary,
        },
        verdict="GO",
        rationale="Multi-backend diversity with accepted abstract evidence.",
    )
    assert artifact["source_expansion_verdict"] == "GO"
    assert artifact["packet_id"] == "live-source-expansion"
    public_path = tmp_path / "atlas_source_health_run_latest.json"
    result = sync_source_expansion_artifact_to_public_site(
        artifact,
        public_path=public_path,
    )
    assert result["status"] == "completed"
    loaded = json.loads(public_path.read_text(encoding="utf-8"))
    assert loaded["source_expansion_verdict"] == "GO"
