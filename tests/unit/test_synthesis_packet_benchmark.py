"""Synthesis packet benchmark and review-threshold dry-run tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.modules.synthesis_packet_benchmark import (
    build_benchmark_summary,
    build_cumulative_throughput,
    estimate_reports_per_hour,
    run_synthesis_packet_benchmark,
)
from rge.modules.synthesis_packet_runner import GROUNDED_PACKET_FIXTURE_REL
from rge.modules.synthesis_review_threshold_policy import evaluate_synthesis_review_threshold

REPO_ROOT = Path(__file__).resolve().parents[2]


def _fixture_result(*, elapsed_seconds: float = 1.0, claim_count: int = 2) -> dict:
    return {
        "status": "completed",
        "provider": "mock_cloud",
        "grounding": {"needs_human_review": False},
        "throughput": {
            "elapsed_seconds": elapsed_seconds,
            "claim_count": claim_count,
            "concept_link_count": 0,
            "relationship_count": 0,
            "qualification_count": 0,
            "provider": "mock_cloud",
            "mode": "mock",
            "cloud_call_made": False,
            "estimated_cost_usd": None,
        },
    }


def test_benchmark_uses_mock_cloud_by_default(tmp_path: Path) -> None:
    calls: list[str] = []

    def fake_run(**kwargs: object) -> dict:
        calls.append(str(kwargs.get("provider")))
        return _fixture_result()

    summary = run_synthesis_packet_benchmark(
        packet_path=REPO_ROOT / GROUNDED_PACKET_FIXTURE_REL,
        runs=2,
        output_dir=tmp_path,
        root=tmp_path,
        run_once=fake_run,
    )
    assert summary["provider"] == "mock_cloud"
    assert summary["cloud_call_made_any"] is False
    assert calls == ["mock_cloud", "mock_cloud"]


def test_reports_per_hour_calculation_is_deterministic() -> None:
    assert estimate_reports_per_hour(runs_completed=25, total_elapsed_seconds=25.0) == 3600.0
    assert estimate_reports_per_hour(runs_completed=0, total_elapsed_seconds=10.0) == 0.0
    assert estimate_reports_per_hour(runs_completed=10, total_elapsed_seconds=0.0) == 0.0

    summary = build_benchmark_summary(
        runs_completed=10,
        total_elapsed_seconds=20.0,
        counters={"claim_count": 20},
        provider="mock_cloud",
        mode="mock",
        cloud_call_made_any=False,
        estimated_cost_usd_total=0.0,
        local_review={"review_recommended": False},
        openai_big_review={"review_recommended": False, "openai_live_call_blocked": False},
    )
    assert summary["average_elapsed_seconds"] == 2.0
    assert summary["reports_per_hour_estimate"] == 1800.0


def test_local_review_threshold_triggers_at_configured_report_count(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("RGE_SYNTHESIS_LOCAL_REVIEW_EVERY_REPORTS", "5")
    monkeypatch.setenv("RGE_SYNTHESIS_LOCAL_REVIEW_EVERY_CLAIMS", "100")

    summary = run_synthesis_packet_benchmark(
        packet_path=REPO_ROOT / GROUNDED_PACKET_FIXTURE_REL,
        runs=5,
        output_dir=tmp_path,
        root=tmp_path,
        run_once=lambda **_kwargs: _fixture_result(claim_count=2),
    )
    assert summary["local_review_recommended"] is True
    local = summary["review_threshold"]["local"]
    assert local["review_tier"] == "local"
    assert any("reports_completed=5" in reason for reason in local["reasons"])


def test_local_review_threshold_triggers_at_configured_claim_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_SYNTHESIS_LOCAL_REVIEW_EVERY_REPORTS", "100")
    monkeypatch.setenv("RGE_SYNTHESIS_LOCAL_REVIEW_EVERY_CLAIMS", "10")

    cumulative = build_cumulative_throughput(
        runs_completed=3,
        counters={"claim_count": 10},
    )
    review = evaluate_synthesis_review_threshold(
        provider="mock_cloud",
        throughput=cumulative,
    )
    assert review["review_tier"] == "local"
    assert review["review_recommended"] is True


def test_openai_big_review_recommendation_does_not_make_live_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_CLOUD_LLM_ENABLED", raising=False)
    cumulative = build_cumulative_throughput(
        runs_completed=100,
        counters={"claim_count": 200},
    )
    review = evaluate_synthesis_review_threshold(
        provider="openai",
        throughput=cumulative,
    )
    assert review["review_tier"] == "openai_big"
    assert review["review_recommended"] is True
    assert review["openai_live_call_blocked"] is True
    assert review["openai_review_eligible"] is False


def test_benchmark_openai_big_review_flag_without_live_call(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("RGE_CLOUD_LLM_ENABLED", raising=False)

    summary = run_synthesis_packet_benchmark(
        packet_path=REPO_ROOT / GROUNDED_PACKET_FIXTURE_REL,
        runs=2,
        output_dir=tmp_path,
        root=tmp_path,
        run_once=lambda **_kwargs: _fixture_result(),
    )
    openai_review = evaluate_synthesis_review_threshold(
        provider="openai",
        throughput=build_cumulative_throughput(
            runs_completed=100,
            counters={"claim_count": 200},
        ),
    )
    assert openai_review["openai_live_call_blocked"] is True
    assert summary["cloud_call_made_any"] is False


def test_benchmark_summary_contains_no_secrets(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-should-not-appear")
    monkeypatch.setenv("DOTENV_LOCAL_SECRET", "super-secret-from-env-local")

    summary = run_synthesis_packet_benchmark(
        packet_path=REPO_ROOT / GROUNDED_PACKET_FIXTURE_REL,
        runs=1,
        output_dir=tmp_path,
        root=tmp_path,
        run_once=lambda **_kwargs: _fixture_result(),
    )
    blob = json.dumps(summary)
    assert "sk-secret-should-not-appear" not in blob
    assert "OPENAI_API_KEY" not in blob
    assert "super-secret-from-env-local" not in blob
    assert ".env.local" not in blob


def test_benchmark_rejects_openai_provider(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Benchmark refuses live OpenAI"):
        run_synthesis_packet_benchmark(
            packet_path=REPO_ROOT / GROUNDED_PACKET_FIXTURE_REL,
            runs=1,
            provider="openai",
            output_dir=tmp_path,
            root=tmp_path,
        )
