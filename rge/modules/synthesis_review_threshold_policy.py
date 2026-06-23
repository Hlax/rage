"""Review-threshold policy for synthesis throughput instrumentation (ticket-059 bridge)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from rge.llm.cloud_synthesis_providers import normalize_provider_id
from rge.llm.openai_synthesis_client import missing_live_openai_http_gates


@dataclass(frozen=True)
class ReviewThresholdPolicy:
    local_review_every_reports: int = 25
    local_review_every_claims: int = 100
    openai_big_review_every_reports: int = 100
    openai_big_review_every_claims: int = 500


def _positive_int(raw: str | None, default: int) -> int:
    if raw is None or not str(raw).strip():
        return default
    try:
        value = int(str(raw).strip())
    except ValueError:
        return default
    return value if value > 0 else default


def load_review_threshold_policy() -> ReviewThresholdPolicy:
    return ReviewThresholdPolicy(
        local_review_every_reports=_positive_int(
            os.environ.get("RGE_SYNTHESIS_LOCAL_REVIEW_EVERY_REPORTS"),
            25,
        ),
        local_review_every_claims=_positive_int(
            os.environ.get("RGE_SYNTHESIS_LOCAL_REVIEW_EVERY_CLAIMS"),
            100,
        ),
        openai_big_review_every_reports=_positive_int(
            os.environ.get("RGE_SYNTHESIS_OPENAI_REVIEW_EVERY_REPORTS"),
            100,
        ),
        openai_big_review_every_claims=_positive_int(
            os.environ.get("RGE_SYNTHESIS_OPENAI_REVIEW_EVERY_CLAIMS"),
            500,
        ),
    )


def policy_defaults_document() -> dict[str, int]:
    policy = ReviewThresholdPolicy()
    return {
        "local_review_every_reports": policy.local_review_every_reports,
        "local_review_every_claims": policy.local_review_every_claims,
        "openai_big_review_every_reports": policy.openai_big_review_every_reports,
        "openai_big_review_every_claims": policy.openai_big_review_every_claims,
    }


def _immediate_review_triggered(quality_signals: dict[str, Any] | None) -> tuple[bool, list[str]]:
    if not quality_signals:
        return False, []
    reasons: list[str] = []
    if quality_signals.get("drift_warning_active"):
        reasons.append("drift_warning_active")
    if quality_signals.get("contradiction_threshold_exceeded"):
        reasons.append("contradiction_threshold_exceeded")
    if quality_signals.get("quality_threshold_failed"):
        reasons.append("quality_threshold_failed")
    if quality_signals.get("grounding_failed"):
        reasons.append("grounding_failed")
    return bool(reasons), reasons


def evaluate_synthesis_review_threshold(
    *,
    provider: str,
    throughput: dict[str, Any],
    quality_signals: dict[str, Any] | None = None,
    root: Any | None = None,
) -> dict[str, Any]:
    """Recommend review tier without making live OpenAI calls."""
    policy = load_review_threshold_policy()
    resolved = normalize_provider_id(provider)
    reports_completed = int(throughput.get("reports_completed") or 0)
    claim_count = int(throughput.get("claim_count") or 0)
    immediate, immediate_reasons = _immediate_review_triggered(quality_signals)
    missing_live = missing_live_openai_http_gates(root=root)
    openai_gates_satisfied = not missing_live

    review_tier = "none"
    review_recommended = False
    reasons: list[str] = []

    if immediate:
        review_tier = "immediate"
        review_recommended = True
        reasons.extend(immediate_reasons)
    elif resolved in {"mock_cloud", "mock", "ollama"}:
        if (
            reports_completed > 0
            and reports_completed % policy.local_review_every_reports == 0
        ):
            review_tier = "local"
            review_recommended = True
            reasons.append(
                f"reports_completed={reports_completed} reached local interval "
                f"{policy.local_review_every_reports}"
            )
        elif claim_count > 0 and claim_count % policy.local_review_every_claims == 0:
            review_tier = "local"
            review_recommended = True
            reasons.append(
                f"claim_count={claim_count} reached local interval "
                f"{policy.local_review_every_claims}"
            )
    elif resolved == "openai":
        if (
            reports_completed > 0
            and reports_completed % policy.openai_big_review_every_reports == 0
        ):
            review_tier = "openai_big"
            review_recommended = True
            reasons.append(
                f"reports_completed={reports_completed} reached OpenAI big-review interval "
                f"{policy.openai_big_review_every_reports}"
            )
        elif (
            claim_count > 0
            and claim_count % policy.openai_big_review_every_claims == 0
        ):
            review_tier = "openai_big"
            review_recommended = True
            reasons.append(
                f"claim_count={claim_count} reached OpenAI big-review interval "
                f"{policy.openai_big_review_every_claims}"
            )

    openai_review_eligible = review_tier == "openai_big" and openai_gates_satisfied
    return {
        "review_recommended": review_recommended,
        "review_tier": review_tier,
        "policy": policy_defaults_document(),
        "openai_review_eligible": openai_review_eligible,
        "openai_live_call_blocked": review_tier == "openai_big" and not openai_gates_satisfied,
        "openai_live_gates_missing": missing_live if review_tier == "openai_big" else {},
        "reasons": reasons,
    }
