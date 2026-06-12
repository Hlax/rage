"""Unit tests for calibrated Ollama contradiction-detection prompt (no live Ollama)."""

from __future__ import annotations

from rge.llm.ollama_client import OllamaModelClient


def test_contradiction_detection_prompt_includes_triples_and_validation_rules() -> None:
    client = OllamaModelClient(base_url="http://127.0.0.1:11434", model="qwen2.5:7b")
    prompt = client._contradiction_detection_prompt(
        claims=[
            {
                "id": "claim_live_probe_qualify_001",
                "claim_text": "Increased idea diversity.",
            },
            {
                "id": "claim_live_probe_oppose_001",
                "claim_text": "Reduced semantic diversity.",
            },
        ],
        relationships=[
            {
                "id": "rel_live_probe_base_001",
                "subject_concept": "AI assistance",
                "predicate": "may_reduce",
                "object_concept": "semantic diversity",
            },
            {
                "id": "rel_live_probe_new_001",
                "subject_concept": "AI assistance",
                "predicate": "may_increase",
                "object_concept": "diversity",
            },
        ],
        domain_pack="creativity",
        schema_version="0.1.0",
    )
    assert "Known relationship triples" in prompt
    assert "may_reduce" in prompt
    assert "may_increase" in prompt
    assert "qualification_stance" in prompt
    assert "apparent_contradiction_metric_or_condition_difference" in prompt
    assert "Positive example" in prompt
    assert "Negative example" in prompt
