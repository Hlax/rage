"""Opt-in live network smoke for graph maturity evidence atom upgrade."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.graph_maturity_evidence_atom_upgrade import (
    assert_live_graph_maturity_evidence_atom_upgrade_env,
    run_graph_maturity_with_fresh_db,
)


@pytest.fixture
def graph_maturity_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_GRAPH_MATURITY_EVIDENCE_ATOM_UPGRADE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_MULTI_QUESTION_ABSTRACT_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_EXPANSION_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")


@pytest.mark.live_network
def test_live_network_graph_maturity_evidence_atom_upgrade(
    tmp_path: Path,
    graph_maturity_env: None,
) -> None:
    assert_live_graph_maturity_evidence_atom_upgrade_env()
    result = run_graph_maturity_with_fresh_db(
        output_dir=tmp_path,
        limit_per_question=2,
    )

    artifact = result["atlas_safe_artifact"]
    assert result["graph_maturity_verdict"] in {"GO", "PARTIAL"}
    assert int(artifact.get("total_accepted_claims") or 0) >= 1
    assert artifact.get("maturity_before")
    assert artifact.get("maturity_after")
    assert artifact.get("cluster_maturity_explanations") is not None
    assert assert_no_private_fields({"artifact": artifact}) == []

    loaded = json.loads(Path(result["artifact_path"]).read_text(encoding="utf-8"))
    assert loaded.get("maturity_delta")
