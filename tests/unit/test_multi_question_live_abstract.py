"""Unit tests for multi-question live abstract runs and purpose routing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.multi_question_live_abstract import (
    GENERIC_DIVERSITY_FIXTURE_TEXT,
    MULTI_QUESTION_LIVE_ABSTRACT_PROFILES,
    assert_live_multi_question_abstract_smoke_env,
    build_multi_question_atlas_bundle,
    classify_multi_question_verdict,
    list_profile_purpose_families,
    validate_generic_diversity_blocked_on_strict_questions,
)


def test_profiles_cover_five_question_types() -> None:
    assert len(MULTI_QUESTION_LIVE_ABSTRACT_PROFILES) == 5
    gate_modes = {profile.gate_mode for profile in MULTI_QUESTION_LIVE_ABSTRACT_PROFILES}
    assert gate_modes == {"open", "strict"}
    families = list_profile_purpose_families()
    strict = [item for item in families if item["gate_mode"] == "strict"]
    assert len(strict) == 2
    assert all(item["families"] for item in strict)


def test_generic_diversity_blocked_on_strict_questions_only() -> None:
    validation = validate_generic_diversity_blocked_on_strict_questions()
    assert validation["purpose_routing_valid"] is True
    assert validation["strict_questions_reject_generic"] is True
    assert validation["open_questions_allow_generic"] is True

    for item in validation["per_question_decisions"]:
        if item["gate_mode"] == "strict":
            assert item["decision"] == "rejected"
            assert "Generic AI/diversity" in str(item["why"])
        else:
            assert item["decision"] != "rejected"


def test_generic_diversity_fixture_text_is_ai_diversity_only() -> None:
    validation = validate_generic_diversity_blocked_on_strict_questions(
        generic_text=GENERIC_DIVERSITY_FIXTURE_TEXT,
    )
    agency = next(
        item
        for item in validation["per_question_decisions"]
        if item["question_id"] == "mq_cocreation_agency"
    )
    style = next(
        item
        for item in validation["per_question_decisions"]
        if item["question_id"] == "mq_artist_style_originality"
    )
    assert agency["decision"] == "rejected"
    assert style["decision"] == "rejected"


def test_multi_question_bundle_is_public_safe() -> None:
    validation = validate_generic_diversity_blocked_on_strict_questions()
    question_runs = [
        {
            "question_id": profile.question_id,
            "question": profile.question,
            "gate_mode": profile.gate_mode,
            "live_source_count": 5,
            "claims_accepted": 2 if profile.gate_mode == "open" else 0,
            "claims_rejected": 1,
            "purpose_fit_status_counts": {"match": 3, "mismatch": 2},
            "purpose_gate_decision_counts": {"accepted": 2, "rejected": 1},
            "trace_summary": {"trace_count": 2, "preview_row_count": 2},
        }
        for profile in MULTI_QUESTION_LIVE_ABSTRACT_PROFILES
    ]
    bundle = build_multi_question_atlas_bundle(
        question_runs,
        purpose_routing_validation=validation,
    )
    assert bundle["question_count"] == 5
    assert assert_no_private_fields({"bundle": bundle}) == []
    assert bundle["purpose_routing_validation"]["purpose_routing_valid"] is True


def test_classify_multi_question_verdict_go_and_partial() -> None:
    validation = validate_generic_diversity_blocked_on_strict_questions()
    go_runs = [
        {
            "question_id": profile.question_id,
            "gate_mode": profile.gate_mode,
            "live_source_count": 5,
            "claims_accepted": 3,
            "purpose_fit_status_counts": {"match": 3},
            "purpose_gate_decision_counts": {"accepted": 3},
        }
        for profile in MULTI_QUESTION_LIVE_ABSTRACT_PROFILES
    ]
    verdict, _ = classify_multi_question_verdict(
        go_runs,
        purpose_routing_validation=validation,
    )
    assert verdict == "GO"

    partial_runs = list(go_runs)
    partial_runs[0] = {**partial_runs[0], "live_source_count": 0}
    verdict, rationale = classify_multi_question_verdict(
        partial_runs,
        purpose_routing_validation=validation,
    )
    assert verdict == "PARTIAL"
    assert "discovery" in rationale.casefold()


def test_missing_multi_question_gate_fail_closed(
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


def test_sync_multi_question_bundle_to_public_site(tmp_path: Path) -> None:
    from rge.modules.multi_question_live_abstract import sync_multi_question_bundle_to_public_site

    validation = validate_generic_diversity_blocked_on_strict_questions()
    bundle = build_multi_question_atlas_bundle(
        [
            {
                "question_id": "mq_ai_human_creativity",
                "question": "How does AI affect human creativity?",
                "gate_mode": "open",
                "live_source_count": 5,
                "claims_accepted": 3,
                "purpose_fit_status_counts": {"match": 5},
                "purpose_gate_decision_counts": {"accepted": 3},
                "trace_summary": {"trace_count": 3, "preview_row_count": 3},
            }
        ],
        purpose_routing_validation=validation,
    )
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    public_path = tmp_path / "public" / "atlas_multi_question_live_abstract_latest.json"
    result = sync_multi_question_bundle_to_public_site(
        bundle_path,
        public_path=public_path,
    )
    assert result["status"] == "completed"
    assert public_path.is_file()
    loaded = json.loads(public_path.read_text(encoding="utf-8"))
    assert loaded["question_count"] == 1
