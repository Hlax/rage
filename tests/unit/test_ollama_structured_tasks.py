"""Unit tests for Ollama structured tasks and live-mode opt-in (no live Ollama)."""

from __future__ import annotations

import io
import json
from unittest.mock import patch

import pytest

from rge.config import load_config
from rge.llm.mock_client import MockModelClient
from rge.llm.mode import effective_llm_mode, live_llm_enabled
from rge.llm.ollama_client import (
    UNTRUSTED_SOURCE_PREAMBLE,
    OllamaModelClient,
    OllamaStructuredCallError,
)
from rge.llm.registry import get_model_client
from rge.llm.schemas import SCHEMA_VERSION_0_1_0


def _valid_claim_batch() -> dict:
    return {
        "task_name": "claim_extraction",
        "schema_version": SCHEMA_VERSION_0_1_0,
        "items": [
            {
                "claim_text": "AI-assisted brainstorming reduced semantic diversity.",
                "quote_span": "reduced semantic diversity",
                "scope": "short-form writing tasks",
                "evidence_type": "empirical",
                "confidence": 0.6,
                "limitations": [],
                "domain": "creativity",
                "domain_metadata": {},
            }
        ],
    }


def _ollama_response(payload: dict) -> bytes:
    return json.dumps({"response": json.dumps(payload)}).encode("utf-8")


@pytest.fixture()
def ollama_client() -> OllamaModelClient:
    return OllamaModelClient(
        base_url="http://127.0.0.1:11434",
        model="qwen2.5:7b",
        timeout_seconds=5,
        temperature=0.0,
    )


def test_effective_mode_stays_mock_without_live_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "0")
    config = load_config()
    assert live_llm_enabled(config) is False
    assert effective_llm_mode(config) == "mock"
    client = get_model_client(config, mode=effective_llm_mode(config))
    assert isinstance(client, MockModelClient)


def test_effective_mode_uses_ollama_with_explicit_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")
    config = load_config()
    assert live_llm_enabled(config) is True
    assert effective_llm_mode(config) == "ollama"
    client = get_model_client(config, mode=effective_llm_mode(config))
    assert client.provider == "ollama"


def test_claim_extraction_prompt_includes_untrusted_source_delimiter(
    ollama_client: OllamaModelClient,
) -> None:
    prompt = ollama_client._claim_extraction_prompt(
        chunk={"chunk_text": "Sample source text about creativity."},
        contract={"domain_pack": "creativity"},
        domain_pack="creativity",
        schema_version=SCHEMA_VERSION_0_1_0,
    )
    assert UNTRUSTED_SOURCE_PREAMBLE in prompt
    assert "UNTRUSTED SOURCE TEXT BEGIN" in prompt
    assert "Sample source text about creativity." in prompt


def test_extract_claims_parses_valid_canned_json(
    ollama_client: OllamaModelClient,
) -> None:
    payload = _valid_claim_batch()

    def fake_urlopen(request, timeout=0):  # noqa: ARG001
        return io.BytesIO(_ollama_response(payload))

    with patch("rge.llm.ollama_client.urllib.request.urlopen", fake_urlopen):
        batch = ollama_client.extract_claims(
            chunk={"chunk_text": "reduced semantic diversity"},
            contract={"domain_pack": "creativity"},
            domain_pack="creativity",
            schema_version=SCHEMA_VERSION_0_1_0,
        )

    assert batch.task_name == "claim_extraction"
    assert len(batch.items) == 1
    assert "semantic diversity" in batch.items[0].claim_text


def test_extract_claims_rejects_schema_version_mismatch(
    ollama_client: OllamaModelClient,
) -> None:
    payload = _valid_claim_batch()
    payload["schema_version"] = "9.9.9"

    def fake_urlopen(request, timeout=0):  # noqa: ARG001
        return io.BytesIO(_ollama_response(payload))

    with patch("rge.llm.ollama_client.urllib.request.urlopen", fake_urlopen):
        with pytest.raises(OllamaStructuredCallError, match="schema_version"):
            ollama_client.extract_claims(
                chunk={"chunk_text": "sample"},
                contract={},
                domain_pack="creativity",
                schema_version=SCHEMA_VERSION_0_1_0,
            )


def test_extract_claims_rejects_malformed_json_response(
    ollama_client: OllamaModelClient,
) -> None:
    def fake_urlopen(request, timeout=0):  # noqa: ARG001
        return io.BytesIO(json.dumps({"response": "not-json"}).encode("utf-8"))

    with patch("rge.llm.ollama_client.urllib.request.urlopen", fake_urlopen):
        with pytest.raises(OllamaStructuredCallError, match="not valid JSON"):
            ollama_client.extract_claims(
                chunk={"chunk_text": "sample"},
                contract={},
                domain_pack="creativity",
                schema_version=SCHEMA_VERSION_0_1_0,
            )


def test_extract_claims_rejects_invalid_batch_shape(
    ollama_client: OllamaModelClient,
) -> None:
    payload = _valid_claim_batch()
    payload["items"] = "not-a-list"

    def fake_urlopen(request, timeout=0):  # noqa: ARG001
        return io.BytesIO(_ollama_response(payload))

    with patch("rge.llm.ollama_client.urllib.request.urlopen", fake_urlopen):
        with pytest.raises(OllamaStructuredCallError, match="schema validation"):
            ollama_client.extract_claims(
                chunk={"chunk_text": "sample"},
                contract={},
                domain_pack="creativity",
                schema_version=SCHEMA_VERSION_0_1_0,
            )


def test_structured_call_raises_on_unreachable_ollama(
    ollama_client: OllamaModelClient,
) -> None:
    with patch(
        "rge.llm.ollama_client.urllib.request.urlopen",
        side_effect=OSError("connection refused"),
    ):
        with pytest.raises(OllamaStructuredCallError, match="unreachable"):
            ollama_client.extract_claims(
                chunk={"chunk_text": "sample"},
                contract={},
                domain_pack="creativity",
                schema_version=SCHEMA_VERSION_0_1_0,
            )
