"""Unit tests for calibrated Ollama claim-extraction prompt (no live Ollama)."""

from __future__ import annotations

from rge.llm.ollama_client import OllamaModelClient


def test_claim_extraction_prompt_requires_subject_predicate_object_and_scoped_claim_text() -> None:
    client = OllamaModelClient(base_url="http://127.0.0.1:11434", model="qwen2.5:7b")
    prompt = client._claim_extraction_prompt(
        chunk={"chunk_text": "Sample source text about short-form writing tasks."},
        contract={"domain_pack": "creativity"},
        domain_pack="creativity",
        schema_version="0.1.0",
    )
    assert '"subject"' in prompt
    assert '"predicate"' in prompt
    assert '"object"' in prompt
    assert "include the scope phrase verbatim" in prompt
    assert "concise (about 3-7 words)" in prompt
    assert "divergent condition ideation tasks" in prompt
    assert "Positive example" in prompt
    assert "Negative example" in prompt


def test_claim_extraction_prompt_includes_manual_text_arbitrary_calibration() -> None:
    client = OllamaModelClient(base_url="http://127.0.0.1:11434", model="qwen2.5:7b")
    prompt = client._claim_extraction_prompt(
        chunk={"chunk_text": "Human-AI pairs completed draft verses faster in this workshop setting."},
        contract={"domain_pack": "creativity", "manual_text_arbitrary_live": True},
        domain_pack="creativity",
        schema_version="0.1.0",
    )
    assert "Manual arbitrary source mode" in prompt
    assert "this workshop setting" in prompt
    assert "manual_text_arbitrary_live" in prompt
