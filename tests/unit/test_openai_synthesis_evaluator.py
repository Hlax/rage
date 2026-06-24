"""Unit tests for deterministic OpenAI synthesis evaluator artifact (ticket-394)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.llm.openai_synthesis_client import OpenAISynthesisClient
from rge.modules.openai_synthesis_evaluator import (
    OpenAISynthesisEvaluatorError,
    evaluate_synthesis_artifact,
    run_openai_synthesis_evaluator,
    write_evaluator_artifact,
)
from rge.modules.synthesis_packet_runner import (
    GROUNDED_PACKET_FIXTURE_REL,
    run_synthesis_packet,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GROUNDED_TEXT = (
    "AI-assisted brainstorming reduced semantic diversity in short-form writing tasks."
)


def _grounded_packet() -> dict:
    return json.loads((REPO_ROOT / GROUNDED_PACKET_FIXTURE_REL).read_text(encoding="utf-8"))


def _set_openai_live_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST", "openai")
    monkeypatch.setenv("RGE_CLOUD_LLM_ENABLED", "1")
    monkeypatch.setenv("RGE_ALLOW_OPENAI_SYNTHESIS", "1")
    monkeypatch.setenv("RGE_ALLOW_OPENAI_SYNTHESIS_LIVE_HTTP", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-redacted")
    monkeypatch.setenv("RGE_CLOUD_MAX_USD_PER_RUN", "0.50")
    monkeypatch.setenv("RGE_CLOUD_MAX_TOKENS_PER_CALL", "4096")


def _set_evaluator_budget_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST", "openai")
    monkeypatch.setenv("RGE_CLOUD_MAX_USD_PER_RUN", "0.50")
    monkeypatch.setenv("RGE_CLOUD_MAX_TOKENS_PER_CALL", "4096")


def _build_packet_run_artifact(
    *,
    text: str,
    provider: str = "openai",
    run_status: str = "completed",
    no_accepted_graph_writes: bool = True,
) -> dict:
    return {
        "schema_version": "synthesis_packet_run_v0.1.0",
        "status": run_status,
        "command": "synthesize",
        "packet_id": "syn_packet_grounded_dry_run_fixture",
        "provider": provider,
        "candidate_output": {
            "schema_version": "synthesis_output_v0.1.0",
            "packet_id": "syn_packet_grounded_dry_run_fixture",
            "provider": provider,
            "no_paid_api_calls": provider != "openai",
            "review_mode": "live_candidate",
            "summary_sentences": [
                {
                    "text": text,
                    "claim_ids": ["claim_preview_a"],
                    "atom_ids": ["atom_preview_001"],
                    "source_refs": ["src_preview_a"],
                }
            ],
            "usage": {"tokens": 30, "prompt_tokens": 10, "completion_tokens": 20},
            "cost_estimate_usd": None,
        },
        "throughput": {
            "provider": provider,
            "model": "gpt-4o-mini",
            "cloud_call_made": provider == "openai",
            "reports_completed": 0,
            "claim_count": 2,
        },
        "grounding": {
            "needs_human_review": text != GROUNDED_TEXT,
            "grounding_passed": text == GROUNDED_TEXT,
            "flagged_sentence_count": 0 if text == GROUNDED_TEXT else 1,
        },
        "governor_verdict": "GO" if text == GROUNDED_TEXT else "NO-GO",
        "no_accepted_graph_writes": no_accepted_graph_writes,
    }


def test_evaluator_go_fixture_without_openai_api_key(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _set_evaluator_budget_env(monkeypatch)
    artifact = _build_packet_run_artifact(text=GROUNDED_TEXT)
    result = evaluate_synthesis_artifact(artifact, root=REPO_ROOT)
    assert result["evaluator_verdict"] == "GO"
    assert result["grounding_passed"] is True
    assert result["governor_verdict"] == "GO"
    assert result["no_accepted_graph_writes"] is True
    assert result["provider"] == "openai"
    assert result["packet_id"] == "syn_packet_grounded_dry_run_fixture"
    assert result["token_usage"]["tokens"] == 30
    assert result["remediation_suggestions"]
    blob = json.dumps(result)
    assert "sk-" not in blob
    assert "OPENAI_API_KEY" not in blob


def test_evaluator_partial_when_grounding_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _set_evaluator_budget_env(monkeypatch)
    artifact = _build_packet_run_artifact(
        text="The model produced unrelated prose without grounded overlap."
    )
    result = evaluate_synthesis_artifact(artifact, root=REPO_ROOT)
    assert result["evaluator_verdict"] == "PARTIAL"
    assert result["grounding_passed"] is False
    assert result["flagged_sentence_count"] >= 1
    assert any(
        "grounding" in str(item.get("problem", "")).lower()
        for item in result["remediation_suggestions"]
    )


def test_evaluator_no_go_when_graph_writes_not_blocked(tmp_path: Path) -> None:
    artifact = _build_packet_run_artifact(
        text=GROUNDED_TEXT,
        no_accepted_graph_writes=False,
    )
    result = evaluate_synthesis_artifact(artifact, root=REPO_ROOT)
    assert result["evaluator_verdict"] == "NO-GO"
    assert result["no_accepted_graph_writes"] is False


def test_evaluator_writes_public_safe_artifact(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_evaluator_budget_env(monkeypatch)
    artifact = _build_packet_run_artifact(text=GROUNDED_TEXT)
    result = evaluate_synthesis_artifact(artifact, root=REPO_ROOT)
    out = write_evaluator_artifact(result, root=REPO_ROOT, artifact_path=tmp_path / "eval.json")
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["evaluator_verdict"] == "GO"
    assert "artifact_written_at" in payload


def test_run_evaluator_from_synthesis_packet_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_openai_live_gates(monkeypatch)

    def fake_urlopen(request, timeout=180):  # noqa: ANN001, ARG001
        body = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "summary_sentences": [
                                    {
                                        "text": GROUNDED_TEXT,
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

    synthesis_path = tmp_path / "synthesis_output_syn_packet_grounded_dry_run_fixture.json"
    run_synthesis_packet(
        packet=_grounded_packet(),
        provider="openai",
        confirm=True,
        output_dir=tmp_path,
        root=REPO_ROOT,
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = run_openai_synthesis_evaluator(
        input_artifact=synthesis_path,
        root=REPO_ROOT,
        output_artifact=tmp_path / "evaluator.json",
    )
    assert result["evaluator_verdict"] == "GO"
    assert (tmp_path / "evaluator.json").is_file()


def test_evaluator_rejects_invalid_artifact(tmp_path: Path) -> None:
    with pytest.raises(OpenAISynthesisEvaluatorError, match="not a synthesis packet run"):
        evaluate_synthesis_artifact({"schema_version": "unknown"}, root=REPO_ROOT)
