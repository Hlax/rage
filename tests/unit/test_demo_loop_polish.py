"""Unit tests for demo loop polish proof."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import rge.modules.source_providers  # noqa: F401 — register resolver providers

from rge.db.connection import ensure_database
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.demo_loop_polish import (
    DemoLoopPolishGateError,
    assert_demo_loop_polish_env,
    build_atlas_safe_demo_loop_artifact,
    classify_demo_loop_verdict,
    run_demo_loop_polish_smoke,
    summarize_source_status_counts,
)


def test_missing_demo_loop_gate_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RGE_ALLOW_DEMO_LOOP_POLISH", raising=False)
    with pytest.raises(DemoLoopPolishGateError, match="RGE_ALLOW_DEMO_LOOP_POLISH"):
        assert_demo_loop_polish_env()


def test_summarize_source_status_counts() -> None:
    counts = summarize_source_status_counts(
        [
            {"source_status": "abstract_available"},
            {"source_status": "metadata_only"},
            {"source_status": "abstract_available"},
        ]
    )
    assert counts["abstract_available"] == 2
    assert counts["metadata_only"] == 1


def test_run_demo_loop_polish_fixture_proof(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_DEMO_LOOP_POLISH", "1")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    result = run_demo_loop_polish_smoke(output_dir=tmp_path)

    artifact = result["atlas_safe_artifact"]

    assert result["demo_loop_verdict"] in {"GO", "PARTIAL"}
    assert artifact["abstract_evidence_summary"]["accepted_claims_total"] >= 1
    assert artifact["improvement_recommendation"]["recommended_packet"]
    assert artifact["selective_fulltext_summary"]["acquisition_count"] >= 1
    assert assert_no_private_fields({"artifact": artifact}) == []

    loaded = json.loads(Path(result["artifact_path"]).read_text(encoding="utf-8"))
    assert loaded["fixture_mode"] is True


def test_run_demo_loop_polish_db_persist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_DEMO_LOOP_POLISH", "1")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    conn = ensure_database(tmp_path / "demo.sqlite")
    try:
        result = run_demo_loop_polish_smoke(
            conn,
            persist_claims=True,
            output_dir=tmp_path,
        )
    finally:
        conn.close()

    artifact = result["atlas_safe_artifact"]
    assert artifact["db_spine_summary"]["status"] == "completed"
    assert result["demo_loop_verdict"] in {"GO", "PARTIAL"}


def test_build_atlas_safe_demo_loop_artifact_public_safe() -> None:
    artifact = build_atlas_safe_demo_loop_artifact(
        topic="AI creativity",
        domain_pack="creativity",
        mode="abstract-first",
        fixture_mode=True,
        resolver_summary={"resolved_count": 4, "backend_counts": {"manual_fixture": 4}},
        source_status_counts={"abstract_available": 2},
        ranked_source_count=3,
        abstract_summary={"accepted_claims_total": 2, "rejected_claims_total": 0},
        fulltext_summary={"acquisition_count": 2, "status_counts": {}},
        improvement={
            "recommended_packet": "MVP-P7-demo-loop",
            "dominant_signal": "ok",
            "rationale": "Demo complete.",
        },
        field_report_summary={"cluster_count": 1},
        db_spine_summary={"status": "completed", "accepted_claims_total": 1},
        trace_summary={"trace_count": 1, "atom_count": 1, "atlas_trace_preview": [{}]},
        verdict="GO",
        rationale="Fixture proof.",
    )
    assert artifact["schema_version"].startswith("atlas_demo_loop")
    assert assert_no_private_fields({"artifact": artifact}) == []


def test_sync_demo_loop_artifact_to_public_site(tmp_path: Path) -> None:
    from rge.modules.demo_loop_polish import sync_demo_loop_artifact_to_public_site

    artifact = build_atlas_safe_demo_loop_artifact(
        topic="AI creativity",
        domain_pack="creativity",
        mode="abstract-first",
        fixture_mode=True,
        resolver_summary={"resolved_count": 4, "backend_counts": {"manual_fixture": 4}},
        source_status_counts={"abstract_available": 2},
        ranked_source_count=3,
        abstract_summary={"accepted_claims_total": 2, "rejected_claims_total": 0},
        fulltext_summary={"acquisition_count": 2, "status_counts": {}},
        improvement={
            "recommended_packet": "MVP-P7-demo-loop",
            "dominant_signal": "ok",
            "rationale": "Demo complete.",
        },
        field_report_summary={"cluster_count": 1},
        db_spine_summary={"status": "completed", "accepted_claims_total": 1},
        trace_summary={"trace_count": 1, "atom_count": 1, "atlas_trace_preview": [{}]},
        verdict="GO",
        rationale="Fixture proof.",
    )
    public_path = tmp_path / "atlas_demo_loop_polish_latest.json"
    result = sync_demo_loop_artifact_to_public_site(
        artifact,
        public_path=public_path,
    )
    assert result["status"] == "completed"
    loaded = json.loads(public_path.read_text(encoding="utf-8"))
    assert loaded["demo_loop_verdict"] == "GO"


def test_classify_demo_loop_verdict_go() -> None:
    verdict, _ = classify_demo_loop_verdict(
        demo_status="ok",
        abstract_summary={"accepted_claims_total": 2},
        fulltext_summary={"status_counts": {"full_text_clean_text_ready": 1}},
        field_report={"report_type": "field_map"},
        improvement={"recommended_packet": "MVP-P7-demo-loop"},
        db_spine_summary={"accepted_claims_total": 0},
        trace_summary={"trace_count": 0},
    )
    assert verdict == "GO"
