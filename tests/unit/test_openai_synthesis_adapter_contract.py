"""Contract tests for mock-first OpenAI cloud synthesis adapter (ticket-059)."""

from __future__ import annotations

import json

import pytest

from rge.llm.cloud_synthesis_registry import (
    CloudSynthesisRegistryError,
    get_cloud_synthesis_client,
)
from rge.llm.cloud_synthesis_providers import registered_provider_ids
from rge.llm.openai_synthesis_client import (
    CloudSynthesisGateError,
    MockCloudSynthesisClient,
    OpenAISynthesisClient,
    assert_live_openai_http_gates,
    missing_live_openai_http_gates,
)
from rge.modules.autonomous_synthesis_governor import save_circuit_breaker
from rge.modules.openai_synthesis_adapter_spec import build_example_evidence_packet


def _set_all_live_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST", "openai")
    monkeypatch.setenv("RGE_CLOUD_LLM_ENABLED", "1")
    monkeypatch.setenv("RGE_ALLOW_OPENAI_SYNTHESIS", "1")
    monkeypatch.setenv("RGE_ALLOW_OPENAI_SYNTHESIS_LIVE_HTTP", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-redacted")
    monkeypatch.setenv("RGE_CLOUD_MAX_USD_PER_RUN", "0.50")
    monkeypatch.setenv("RGE_CLOUD_MAX_TOKENS_PER_CALL", "4096")


def test_registered_providers_include_mock_and_openai() -> None:
    assert registered_provider_ids() == frozenset({"mock_cloud", "openai"})


def test_default_client_is_mock_without_env() -> None:
    client = get_cloud_synthesis_client()
    assert isinstance(client, MockCloudSynthesisClient)


def test_mock_client_is_deterministic_and_requires_no_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    packet = build_example_evidence_packet()
    client = MockCloudSynthesisClient()
    first = client.synthesize(packet)
    second = client.synthesize(packet)
    assert first == second
    assert first["provider"] == "mock_cloud"
    assert first["no_paid_api_calls"] is True
    assert first["summary_sentences"]


def test_openai_provider_fails_closed_without_allowlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST", raising=False)
    with pytest.raises(CloudSynthesisRegistryError, match="allowlisted"):
        get_cloud_synthesis_client("openai")


def test_missing_live_gates_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RGE_CLOUD_LLM_ENABLED", raising=False)
    monkeypatch.delenv("RGE_ALLOW_OPENAI_SYNTHESIS_LIVE_HTTP", raising=False)
    assert missing_live_openai_http_gates()
    with pytest.raises(CloudSynthesisGateError):
        assert_live_openai_http_gates()


def test_live_openai_synthesize_blocks_before_http(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_all_live_gates(monkeypatch)
    monkeypatch.delenv("RGE_ALLOW_OPENAI_SYNTHESIS_LIVE_HTTP", raising=False)
    client = OpenAISynthesisClient()
    packet = build_example_evidence_packet()
    with pytest.raises(CloudSynthesisGateError, match="LIVE_HTTP"):
        client.synthesize(packet)


def test_live_openai_synthesize_uses_injected_urlopen_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_all_live_gates(monkeypatch)

    def fake_urlopen(request, timeout=180):  # noqa: ANN001, ARG001
        body = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "summary_sentences": [
                                    {
                                        "text": "Grounded synthesis sentence.",
                                        "claim_ids": ["claim_preview_a"],
                                        "atom_ids": ["atom_preview_001"],
                                        "source_refs": ["src_preview_a"],
                                    }
                                ]
                            }
                        )
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }

        class _Resp:
            def __enter__(self):
                return self

            def __exit__(self, *args):  # noqa: ANN002
                return False

            def read(self):
                return json.dumps(body).encode("utf-8")

        return _Resp()

    client = OpenAISynthesisClient(urlopen=fake_urlopen)
    output = client.synthesize(build_example_evidence_packet())
    assert output["provider"] == "openai"
    assert output["no_paid_api_calls"] is False
    assert output["summary_sentences"][0]["claim_ids"] == ["claim_preview_a"]


def test_live_gates_block_when_circuit_breaker_open(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_all_live_gates(monkeypatch)
    save_circuit_breaker(
        {
            "status": "open",
            "latest_stop_reason": "test_open_circuit",
            "consecutive_synthesis_failures": 3,
            "consecutive_unsupported_outputs": 0,
        },
        root=tmp_path,
    )
    missing = missing_live_openai_http_gates(root=tmp_path)
    assert "autonomy_circuit_breaker" in missing


def test_public_safe_live_status_never_serializes_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-value")
    from rge.llm.openai_synthesis_client import build_public_safe_live_status

    status = build_public_safe_live_status()
    blob = json.dumps(status)
    assert "sk-secret-value" not in blob
    assert status["openai_key_available"] is True
