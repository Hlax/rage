"""Unit tests for calibrated Ollama relationship-drafting prompt (no live Ollama)."""

from __future__ import annotations

from rge.llm.ollama_client import OllamaModelClient


def test_relationship_drafting_prompt_includes_labels_and_validation_rules() -> None:
    client = OllamaModelClient(base_url="http://127.0.0.1:11434", model="qwen2.5:7b")
    prompt = client._relationship_drafting_prompt(
        claims=[
            {
                "id": "claim_live_probe_link_001",
                "claim_text": "Sample claim.",
                "scope": "short-form writing tasks",
            }
        ],
        concepts=[
            {"id": "concept_live_probe_001", "label": "brainstorming"},
            {"id": "concept_live_probe_002", "label": "AI assistance"},
        ],
        domain_pack="creativity",
        schema_version="0.1.0",
    )
    assert "Allowed concept labels" in prompt
    assert "brainstorming" in prompt
    assert "supporting_claim_ids" in prompt
    assert "claim_live_probe_link_001" in prompt
    assert "low" in prompt and "medium" in prompt and "high" in prompt
    assert "Positive example" in prompt
    assert "Negative example" in prompt
