"""Unit tests for calibrated Ollama concept-linking prompt (no live Ollama)."""

from __future__ import annotations

from rge.llm.ollama_client import OllamaModelClient


def test_concept_linking_prompt_includes_ontology_labels_and_weak_mapping_rules() -> None:
    client = OllamaModelClient(base_url="http://127.0.0.1:11434", model="qwen2.5:7b")
    prompt = client._concept_linking_prompt(
        claims=[{"id": "claim_live_probe_link_001", "claim_text": "Sample claim."}],
        domain_pack="creativity",
        schema_version="0.1.0",
        ontology_labels=["brainstorming", "AI assistance", "ideation"],
    )
    assert "Allowed ontology concept labels" in prompt
    assert "brainstorming" in prompt
    assert "at least two DISTINCT specific concept labels" in prompt
    assert "claim_id MUST match" in prompt
    assert "Positive example" in prompt
    assert "Negative example" in prompt


def test_concept_linking_prompt_uses_input_claim_id_in_examples() -> None:
    client = OllamaModelClient(base_url="http://127.0.0.1:11434", model="qwen2.5:7b")
    prompt = client._concept_linking_prompt(
        claims=[{"id": "claim_live_probe_link_001", "claim_text": "x"}],
        domain_pack="creativity",
        schema_version="0.1.0",
        ontology_labels=["brainstorming"],
    )
    assert "claim_live_probe_link_001" in prompt
