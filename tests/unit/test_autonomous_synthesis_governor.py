"""Autonomous synthesis governor cloud gate regression tests (ticket-059)."""

from __future__ import annotations

import pytest

from rge.modules.autonomous_synthesis_governor import (
    evaluate_budget_gate,
    evaluate_synthesis_governor,
    save_circuit_breaker,
)
from rge.modules.openai_synthesis_adapter_spec import build_example_evidence_packet


def test_budget_gate_blocks_openai_without_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST", raising=False)
    result = evaluate_budget_gate(provider_id="openai")
    assert result["passed"] is False
    assert any("allowlist" in reason for reason in result["reasons"])


def test_budget_gate_passes_with_caps_and_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST", "openai")
    monkeypatch.setenv("RGE_CLOUD_MAX_USD_PER_RUN", "0.50")
    monkeypatch.setenv("RGE_CLOUD_MAX_TOKENS_PER_CALL", "2048")
    result = evaluate_budget_gate(provider_id="openai", output=None)
    assert result["passed"] is True


def test_governor_blocks_when_circuit_open(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST", "openai")
    monkeypatch.setenv("RGE_CLOUD_MAX_USD_PER_RUN", "0.50")
    monkeypatch.setenv("RGE_CLOUD_MAX_TOKENS_PER_CALL", "2048")
    save_circuit_breaker(
        {
            "status": "open",
            "latest_stop_reason": "test_open",
            "consecutive_synthesis_failures": 2,
            "consecutive_unsupported_outputs": 0,
        },
        root=tmp_path,
    )
    packet = build_example_evidence_packet()
    result = evaluate_synthesis_governor(
        packet=packet,
        provider_id="openai",
        root=tmp_path,
        write_ledger=False,
        write_instruction=False,
        update_circuit=False,
    )
    assert result["governor_verdict"] == "NO-GO"
    assert any("circuit breaker open" in reason for reason in result["failure_reasons"])
