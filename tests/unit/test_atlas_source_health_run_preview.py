"""Atlas source-health run artifact preview wiring tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.modules.atlas_snapshot_builder import assert_no_private_fields

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_PATH = (
    REPO_ROOT / "apps" / "public-site" / "public" / "data" / "atlas_source_health_run_latest.json"
)
ATLAS_PREVIEW_PAGE = REPO_ROOT / "apps" / "public-site" / "app" / "atlas-preview" / "page.tsx"
ATLAS_PREVIEW_LIB = REPO_ROOT / "apps" / "public-site" / "lib" / "atlasPreview.ts"


def test_atlas_source_health_run_artifact_is_public_safe() -> None:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "atlas_source_health_run_v0.1.0"
    assert artifact["source_health_summary"]["sources_with_metadata"] >= 1
    assert assert_no_private_fields({"artifact": artifact}) == []


def test_atlas_preview_wires_source_health_resolver() -> None:
    page = ATLAS_PREVIEW_PAGE.read_text(encoding="utf-8")
    lib = ATLAS_PREVIEW_LIB.read_text(encoding="utf-8")
    assert "resolveSourceHealthPreview" in lib
    assert "resolveSourceHealthPreview" in page
    assert "resolveGapsNextMovePreview" in lib
    assert "resolveGapsNextMovePreview" in page
    assert "resolveQuestionHeaderPreview" in lib
    assert "resolveQuestionHeaderPreview" in page
    assert "resolveReadinessPanelPreview" in lib
    assert "resolveReadinessPanelPreview" in page
    assert "resolvePurposePanelPreview" in lib
    assert "resolvePurposePanelPreview" in page
    assert "resolveGraphSummaryPanelPreview" in lib
    assert "resolveGraphSummaryPanelPreview" in page
    assert "resolveTracePanelPreview" in lib
    assert "resolveTracePanelPreview" in page
    assert "Graph summary panel" in page
    assert "atlas_source_health_run_latest.json" in lib
    assert "fetch(" not in page


def test_atlas_source_health_run_artifact_includes_purpose_for_header() -> None:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    purpose = artifact.get("purpose") or {}
    assert purpose.get("research_intent")
    assert purpose.get("asset_affordance")
    assert artifact.get("purpose_fit_summary")
    assert artifact["question"]


def test_atlas_source_health_run_artifact_includes_purpose_panel_fields() -> None:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    purpose = artifact.get("purpose") or {}
    assert purpose.get("evidence_need")
    assert purpose.get("output_targets")
    assert purpose.get("acceptable_source_types")


def test_atlas_source_health_run_artifact_includes_graph_summary_fields() -> None:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    graph = artifact.get("graph_summary") or {}
    totals = (graph.get("connection_metrics") or {}).get("totals") or {}
    assert graph.get("relationships") is not None or totals.get("relationships") is not None
    assert totals.get("weak_atom_count") is not None
    assert totals.get("frontend_ready_trace_count") is not None
    assert totals.get("clustered_atom_count") is not None
    assert artifact.get("next_recommended_packet")


def test_atlas_preview_graph_summary_resolver_supports_fixture_fallback() -> None:
    lib = ATLAS_PREVIEW_LIB.read_text(encoding="utf-8")
    assert "mapFixtureGraphSummaryPanel" in lib
    assert "preview_source: 'fixture'" in lib
    assert "mapRunArtifactToGraphSummaryPanel" in lib


def test_atlas_preview_trace_resolver_supports_fixture_fallback() -> None:
    lib = ATLAS_PREVIEW_LIB.read_text(encoding="utf-8")
    assert "mapFixtureTracePanel" in lib
    assert "mapRunArtifactToTracePanel" in lib
    assert "preview_source: 'fixture'" in lib


def test_atlas_source_health_run_artifact_includes_trace_summary_fields() -> None:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    trace_summary = artifact.get("trace_summary") or {}
    assert int(trace_summary.get("trace_count") or 0) >= 1
    assert trace_summary.get("atlas_trace_preview")
    assert int(trace_summary.get("atom_count") or 0) >= 1
    assert int(trace_summary.get("accepted_claim_count") or 0) >= 1


def test_committed_artifact_enables_run_artifact_trace_panel_by_default() -> None:
    """Golden gate: trace panel resolver prefers run artifact when preview rows exist."""
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    trace_summary = artifact.get("trace_summary") or {}
    preview_rows = trace_summary.get("atlas_trace_preview") or []
    assert artifact["schema_version"] == "atlas_source_health_run_v0.1.0"
    assert len(preview_rows) >= 1
    first = preview_rows[0]
    assert first.get("trace_ref")
    assert first.get("visibility") == "public_safe"
    assert assert_no_private_fields({"trace_preview_row": first}) == []


def test_atlas_source_health_run_artifact_includes_gaps_fields() -> None:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert "readiness_warnings" in artifact
    assert artifact.get("next_recommended_packet")
    assert artifact.get("next_recommended_reason")
