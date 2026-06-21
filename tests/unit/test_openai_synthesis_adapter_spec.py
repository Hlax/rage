"""Unit tests for OpenAI synthesis adapter spec (ticket-059; no API calls)."""

from __future__ import annotations

import pytest

from rge.contracts.synthesis_evidence_packet_v0 import validate_synthesis_evidence_packet
from rge.modules.openai_synthesis_adapter_spec import (
    OpenAISynthesisSpecGateError,
    assert_cloud_synthesis_env,
    build_adapter_spec_document,
    build_example_evidence_packet,
    classify_spec_verdict,
    missing_cloud_synthesis_gates,
    run_openai_synthesis_adapter_spec,
)


def test_example_packet_rejects_raw_text() -> None:
    packet = build_example_evidence_packet()
    packet["raw_text"] = "secret document body"
    errors = validate_synthesis_evidence_packet(packet)
    assert any("forbidden" in err for err in errors)


def test_example_packet_valid_by_default() -> None:
    errors = validate_synthesis_evidence_packet(build_example_evidence_packet())
    assert errors == []


def test_cloud_gates_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RGE_CLOUD_LLM_ENABLED", raising=False)
    monkeypatch.delenv("RGE_ALLOW_OPENAI_SYNTHESIS", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert missing_cloud_synthesis_gates()
    with pytest.raises(OpenAISynthesisSpecGateError):
        assert_cloud_synthesis_env()


def test_cloud_gates_block_without_synthesis_readiness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_CLOUD_LLM_ENABLED", "1")
    monkeypatch.setenv("RGE_ALLOW_OPENAI_SYNTHESIS", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    with pytest.raises(OpenAISynthesisSpecGateError):
        assert_cloud_synthesis_env(graph_totals={"multi_claim_atom_count": 0})


def test_spec_document_blocks_implementation() -> None:
    spec = build_adapter_spec_document()
    assert spec["status"] == "spec_only_not_implemented"
    assert spec["ci_policy"]["real_api_calls"] is False


def test_classify_spec_partial_without_graph_readiness() -> None:
    verdict, _ = classify_spec_verdict(packet_errors=[], graph_totals={})
    assert verdict == "PARTIAL"


def test_run_spec_produces_artifact(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = run_openai_synthesis_adapter_spec(
        graph_totals={
            "multi_claim_atom_count": 2,
            "source_diverse_atom_count": 2,
            "synthesis_ready_cluster_count": 1,
            "weak_atom_count": 0,
        },
        root=tmp_path,
    )
    assert result["status"] == "completed"
    assert result["implementation_blocked"] is True
    assert result["spec_verdict"] == "GO"
