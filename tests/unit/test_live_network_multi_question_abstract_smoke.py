"""Opt-in live network smoke for multi-question abstract evidence proof.

Requires explicit operator env gates and live OpenAlex/arXiv network access.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.modules.multi_question_live_abstract import (
    MULTI_QUESTION_BUNDLE_NAME,
    assert_live_multi_question_abstract_smoke_env,
    run_live_multi_question_abstract_smoke,
)


def require_live_multi_question_env() -> None:
    assert_live_multi_question_abstract_smoke_env()


@pytest.fixture
def live_multi_question_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_MULTI_QUESTION_ABSTRACT_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")


def test_live_multi_question_smoke_blocked_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("RGE_ALLOW_LIVE_MULTI_QUESTION_ABSTRACT_SMOKE", raising=False)
    with pytest.raises(RuntimeError, match="RGE_ALLOW_LIVE_MULTI_QUESTION_ABSTRACT_SMOKE"):
        assert_live_multi_question_abstract_smoke_env()


@pytest.mark.live_network
def test_live_network_multi_question_abstract_smoke(
    tmp_path: Path,
    live_multi_question_env: None,
) -> None:
    require_live_multi_question_env()
    output_dir = tmp_path / "multi_question"
    result = run_live_multi_question_abstract_smoke(output_dir=output_dir)

    assert result["status"] == "completed"
    assert result["verdict"] in {"GO", "PARTIAL"}
    assert result["purpose_routing_validation"]["purpose_routing_valid"] is True
    assert len(result["question_runs"]) == 5

    for run in result["question_runs"]:
        assert int(run.get("live_source_count") or 0) >= 1
        assert run.get("purpose_fit_status_counts") is not None
        assert "question_id" in run
        assert "?" not in str(run.get("resolver_query") or "")

    bundle_path = Path(result["bundle_path"])
    assert bundle_path.name == MULTI_QUESTION_BUNDLE_NAME
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert bundle["question_count"] == 5
    assert bundle["aggregate"]["questions_with_live_sources"] == 5

    strict_runs = [run for run in result["question_runs"] if run.get("gate_mode") == "strict"]
    assert len(strict_runs) == 2
    for run in strict_runs:
        assert run.get("purpose_gate_decision_counts") is not None
