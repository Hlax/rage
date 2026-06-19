"""Packet 1 purpose classifier tests."""

from __future__ import annotations

from rge.modules.research_purpose import classify_research_purpose


def test_ai_creativity_question_gets_theory_evidence_and_reasoning_affordance() -> None:
    purpose = classify_research_purpose(
        "Does AI improve creative output while reducing diversity?",
        domain="creativity",
        question_id="rq_ai_creativity",
    )

    assert "theory_building" in purpose["research_intent"]
    assert "evidence_review" in purpose["research_intent"]
    assert "reasoning_training_candidate" in purpose["asset_affordance"]
    assert purpose["evidence_need"] == "mixed_empirical_theory"
    assert purpose["training_suitability"] == "not_ready"


def test_art_design_question_gets_visual_descriptor_affordance() -> None:
    purpose = classify_research_purpose(
        "What visual style patterns recur in AI-assisted product design?",
        domain="design",
        question_id="rq_design_visual",
    )

    assert "style_taxonomy" in purpose["research_intent"]
    assert "visual_descriptor_mining" in purpose["research_intent"]
    assert "visual_descriptor_candidate" in purpose["asset_affordance"]
    assert purpose["evidence_need"] == "visual_examples_required"


def test_benchmark_question_gets_eval_and_benchmark_affordance() -> None:
    purpose = classify_research_purpose(
        "How should we design an evaluation benchmark for creative reasoning?",
        domain="creativity",
        question_id="rq_benchmark",
    )

    assert "benchmark_design" in purpose["research_intent"]
    assert "eval_design" in purpose["research_intent"]
    assert "eval_question_candidate" in purpose["asset_affordance"]
    assert purpose["evidence_need"] == "empirical_required"


def test_generic_question_uses_conservative_field_mapping_fallback() -> None:
    purpose = classify_research_purpose(
        "What is happening in this research field?",
        domain="general",
        question_id="rq_generic",
    )

    assert purpose["research_intent"] == ["field_mapping"]
    assert purpose["asset_affordance"] == ["memo_candidate"]
    assert purpose["evidence_maturity"] == "seed"
    assert purpose["training_suitability"] == "not_ready"
