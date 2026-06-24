"""Synthesis packet CLI and throughput instrumentation tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.llm.openai_synthesis_client import CloudSynthesisGateError, OpenAISynthesisClient
from rge.modules.synthesis_packet_runner import (
    GROUNDED_PACKET_FIXTURE_REL,
    run_synthesis_packet,
    run_synthesis_packet_command,
    validate_synthesis_packet,
)
from rge.modules.synthesis_review_threshold_policy import (
    evaluate_synthesis_review_threshold,
    policy_defaults_document,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _grounded_packet() -> dict:
    return json.loads((REPO_ROOT / GROUNDED_PACKET_FIXTURE_REL).read_text(encoding="utf-8"))


def test_mock_packet_synthesis_uses_mock_cloud_client(tmp_path: Path) -> None:
    result = run_synthesis_packet(
        packet=_grounded_packet(),
        provider="mock_cloud",
        output_dir=tmp_path,
        root=tmp_path,
    )
    assert result["status"] == "completed"
    assert result["provider"] == "mock_cloud"
    assert result["candidate_output"]["no_paid_api_calls"] is True
    assert result["throughput"]["cloud_call_made"] is False
    assert result["throughput"]["elapsed_seconds"] >= 0
    assert (tmp_path / "synthesis_output_syn_packet_grounded_dry_run_fixture.json").is_file()


def test_live_openai_gates_fail_closed_before_request(tmp_path: Path) -> None:
    with pytest.raises(CloudSynthesisGateError):
        run_synthesis_packet(
            packet=_grounded_packet(),
            provider="openai",
            confirm=True,
            output_dir=tmp_path,
            root=tmp_path,
        )


def test_throughput_metrics_emitted(tmp_path: Path) -> None:
    result = run_synthesis_packet(
        packet=_grounded_packet(),
        provider="mock_cloud",
        output_dir=tmp_path,
        root=tmp_path,
    )
    throughput = result["throughput"]
    for key in (
        "started_at",
        "completed_at",
        "elapsed_seconds",
        "sources_processed",
        "reports_completed",
        "claim_count",
        "concept_link_count",
        "relationship_count",
        "qualification_count",
        "card_count",
        "provider",
        "mode",
        "cloud_call_made",
        "estimated_cost_usd",
    ):
        assert key in throughput


def test_openai_review_threshold_does_not_trigger_live_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_CLOUD_LLM_ENABLED", raising=False)
    review = evaluate_synthesis_review_threshold(
        provider="openai",
        throughput={"reports_completed": 100, "claim_count": 500},
    )
    assert review["review_tier"] == "openai_big"
    assert review["openai_live_call_blocked"] is True
    assert review["openai_review_eligible"] is False


def test_result_json_contains_no_secrets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-should-not-appear")
    result = run_synthesis_packet(
        packet=_grounded_packet(),
        provider="mock_cloud",
        output_dir=tmp_path,
        root=tmp_path,
    )
    blob = json.dumps(result)
    assert "sk-secret-should-not-appear" not in blob
    assert "OPENAI_API_KEY" not in blob


def test_cli_command_mock_first(tmp_path: Path) -> None:
    fixture = REPO_ROOT / GROUNDED_PACKET_FIXTURE_REL
    payload, exit_code = run_synthesis_packet_command(
        packet=fixture,
        output_dir=tmp_path / "out",
        root=REPO_ROOT,
    )
    assert exit_code == 0
    assert payload["command"] == "synthesize"
    assert payload["throughput"]["provider"] == "mock_cloud"


def test_policy_defaults_match_ticket_spec() -> None:
    defaults = policy_defaults_document()
    assert defaults["local_review_every_reports"] == 25
    assert defaults["local_review_every_claims"] == 100
    assert defaults["openai_big_review_every_reports"] == 100
    assert defaults["openai_big_review_every_claims"] == 500


def _set_openai_live_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST", "openai")
    monkeypatch.setenv("RGE_CLOUD_LLM_ENABLED", "1")
    monkeypatch.setenv("RGE_ALLOW_OPENAI_SYNTHESIS", "1")
    monkeypatch.setenv("RGE_ALLOW_OPENAI_SYNTHESIS_LIVE_HTTP", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-redacted")
    monkeypatch.setenv("RGE_CLOUD_MAX_USD_PER_RUN", "0.50")
    monkeypatch.setenv("RGE_CLOUD_MAX_TOKENS_PER_CALL", "4096")


def test_grounded_openai_injected_http_passes_grounding_and_governor(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_openai_live_gates(monkeypatch)
    grounded_text = (
        "AI-assisted brainstorming reduced semantic diversity in short-form writing tasks."
    )

    def fake_urlopen(request, timeout=180):  # noqa: ANN001, ARG001
        body = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "summary_sentences": [
                                    {
                                        "text": grounded_text,
                                        "claim_ids": ["claim_preview_a"],
                                        "atom_ids": ["atom_preview_001"],
                                        "source_refs": [
                                            {
                                                "source_id": "src_preview_a",
                                                "title": "Preview study A",
                                            }
                                        ],
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

    injected = OpenAISynthesisClient(urlopen=fake_urlopen)

    def _client(provider_id=None):  # noqa: ANN001
        if provider_id == "openai":
            return injected
        from rge.llm.openai_synthesis_client import MockCloudSynthesisClient

        return MockCloudSynthesisClient()

    monkeypatch.setattr(
        "rge.modules.synthesis_packet_runner.get_cloud_synthesis_client",
        _client,
    )

    result = run_synthesis_packet(
        packet=_grounded_packet(),
        provider="openai",
        confirm=True,
        output_dir=tmp_path,
        root=tmp_path,
    )
    assert result["status"] == "completed"
    assert result["grounding"]["grounding_passed"] is True
    assert result["governor_verdict"] == "GO"
    assert result["no_accepted_graph_writes"] is True
    assert result["candidate_output"]["summary_sentences"][0]["source_refs"] == [
        "src_preview_a"
    ]


def test_validate_openai_requires_grounded_packet() -> None:
    from rge.modules.openai_synthesis_adapter_spec import build_example_evidence_packet

    errors = validate_synthesis_packet(build_example_evidence_packet(), provider_id="openai")
    assert errors
