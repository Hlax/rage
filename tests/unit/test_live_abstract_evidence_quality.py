"""Unit tests for live abstract evidence quality summary and verdict logic."""

from __future__ import annotations

from rge.modules.live_arbitrary_source_health import (
    LOCAL_SAFE_ARBITRARY_QUESTION,
    build_live_abstract_evidence_quality_summary,
    classify_live_abstract_evidence_quality_verdict,
)


def _base_pipeline(*, accepted: int = 1, quote_backed: int = 1) -> dict:
    return {
        "status": "completed",
        "question": LOCAL_SAFE_ARBITRARY_QUESTION,
        "resolver_mode": "live_network_abstract_evidence_quality",
        "resolved_count": 5,
        "run_report": {
            "claims_accepted": accepted,
            "claims_rejected": 5 - accepted,
            "evidence_atoms_created": 5,
            "relationships_updated": 5,
            "top_failure_modes": [],
        },
        "evidence": {
            "live_abstract_mode": True,
            "accepted_count": accepted,
            "rejected_count": 5 - accepted,
            "cards": [
                {
                    "status": "completed",
                    "extraction_mode": "live_deterministic_quote",
                    "accepted_count": quote_backed,
                    "rejected_count": 0,
                    "rejected_claims": [],
                }
            ],
        },
        "source_health": {
            "sources_with_metadata": 5,
            "purpose_fit_status_counts": {"match": 5},
            "purpose_gate_decision_counts": {"accepted": 5},
        },
        "atlas_safe_artifact": {
            "source_health_summary": {"sources_with_metadata": 5},
            "graph_summary": {"connection_metrics": {"totals": {"atoms": 5}}},
            "readiness_warnings": [],
            "trace_summary": {
                "trace_count": 5,
                "atom_count": 5,
                "accepted_claim_count": accepted,
                "frontend_ready_trace_count": 5,
                "atlas_trace_preview": [{"trace_ref": "trace_001", "visibility": "public_safe"}],
            },
        },
    }


def test_build_live_abstract_evidence_quality_summary_counts() -> None:
    records = [{"abstract_text": "AI tools may reshape creative workflows."} for _ in range(5)]
    summary = build_live_abstract_evidence_quality_summary(
        _base_pipeline(),
        records=records,
    )
    assert summary["question"] == LOCAL_SAFE_ARBITRARY_QUESTION
    assert summary["live_source_count"] == 5
    assert summary["abstract_availability_count"] == 5
    assert summary["claims_accepted"] == 1
    assert summary["quote_backed_accepted_count"] == 1
    assert summary["purpose_fit_status_counts"]["match"] == 5
    assert summary["evidence_atom_count"] == 5
    assert summary["trace_summary"]["trace_count"] == 5
    assert summary["atlas_artifact_public_safe"] is True
    assert summary["atlas_preview_panels_present"]["trace_summary"] is True


def test_classify_live_abstract_evidence_quality_verdict_go() -> None:
    summary = build_live_abstract_evidence_quality_summary(_base_pipeline())
    verdict, rationale = classify_live_abstract_evidence_quality_verdict(summary)
    assert verdict == "GO"
    assert "quote-backed" in rationale


def test_classify_live_abstract_evidence_quality_verdict_partial() -> None:
    summary = build_live_abstract_evidence_quality_summary(
        _base_pipeline(accepted=0, quote_backed=0),
        records=[{"abstract_text": "Creativity research abstract."}],
    )
    verdict, _ = classify_live_abstract_evidence_quality_verdict(summary)
    assert verdict == "PARTIAL"


def test_classify_live_abstract_evidence_quality_verdict_no_go_missing_trace() -> None:
    pipeline = _base_pipeline()
    pipeline["atlas_safe_artifact"]["trace_summary"] = {
        "trace_count": 0,
        "atom_count": 0,
        "accepted_claim_count": 0,
        "atlas_trace_preview": [],
    }
    summary = build_live_abstract_evidence_quality_summary(pipeline)
    verdict, rationale = classify_live_abstract_evidence_quality_verdict(summary)
    assert verdict == "NO-GO"
    assert "trace" in rationale.casefold()
