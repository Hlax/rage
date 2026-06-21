"""Unit tests for local model extraction comparison logic."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from rge.llm.schemas import CandidateClaimBatch_v0_1, SCHEMA_VERSION_0_1_0
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.local_model_extraction_comparison import (
    LocalModelExtractionComparisonGateError,
    assert_local_model_extraction_comparison_env,
    build_atlas_safe_comparison_artifact,
    build_comparison_aggregate,
    classify_comparison_verdict,
    classify_local_model_readiness,
    compare_extractions_on_chunk,
    quote_span_is_literal_in_chunk,
    summarize_extraction_validation,
)


SAMPLE_ABSTRACT = (
    "This study investigates human-AI co-creativity in songwriting workflows and "
    "reports measurable changes in lyrical originality under assisted drafting."
)


class _FakeOllamaClient:
    def __init__(self, *, valid_quote: bool = True) -> None:
        self.valid_quote = valid_quote

    def extract_claims(self, **kwargs: Any) -> CandidateClaimBatch_v0_1:
        chunk_text = str(kwargs["chunk"].get("chunk_text") or "")
        quote = (
            "human-AI co-creativity in songwriting workflows"
            if self.valid_quote
            else "quote not present in abstract"
        )
        if quote not in chunk_text and self.valid_quote:
            quote = chunk_text[:48].rstrip()
        return CandidateClaimBatch_v0_1.model_validate(
            {
                "task_name": "claim_extraction",
                "schema_version": SCHEMA_VERSION_0_1_0,
                "items": [
                    {
                        "claim_text": (
                            "In songwriting workflows, human-AI co-creativity "
                            "shows measurable lyrical originality changes."
                        ),
                        "quote_span": quote,
                        "subject": "Human-AI co-creativity",
                        "predicate": "shows",
                        "object": "measurable lyrical originality changes",
                        "scope": "songwriting workflows",
                        "evidence_type": "empirical",
                        "confidence": 0.6,
                        "limitations": ["Abstract-only evidence."],
                        "domain": "creativity",
                        "domain_metadata": {},
                    }
                ],
            }
        )


def _sample_chunk() -> dict[str, Any]:
    return {
        "id": "abstract_openalex_W_test",
        "source_id": "openalex:W_test",
        "chunk_text": SAMPLE_ABSTRACT,
        "domain_pack": "creativity",
    }


def test_quote_span_is_literal_in_chunk() -> None:
    assert quote_span_is_literal_in_chunk(
        "human-AI co-creativity in songwriting workflows",
        SAMPLE_ABSTRACT,
    )
    assert not quote_span_is_literal_in_chunk("invented quote span", SAMPLE_ABSTRACT)


def test_summarize_extraction_validation_is_public_safe() -> None:
    validation = {
        "accepted": [
            {
                "claim_text": "secret claim text",
                "quote_span": "human-AI co-creativity in songwriting workflows",
            }
        ],
        "rejected": [],
    }
    summary = summarize_extraction_validation(
        validation,
        chunk_text=SAMPLE_ABSTRACT,
        backend="local_ollama",
    )
    assert summary["accepted_count"] == 1
    assert summary["quote_valid_accepted_count"] == 1
    assert "claim_text" not in summary
    assert "quote_span" not in summary
    assert assert_no_private_fields({"summary": summary}) == []


def test_compare_extractions_mock_vs_ollama() -> None:
    row = compare_extractions_on_chunk(
        _sample_chunk(),
        domain_pack="creativity",
        ollama_client=_FakeOllamaClient(valid_quote=True),
    )
    assert row["mock_deterministic"]["accepted_count"] >= 1
    assert row["local_ollama"]["accepted_count"] >= 1
    assert row["comparison"]["quality_vs_mock"] in {
        "thinner",
        "better",
        "comparable",
        "worse_quote_validity",
        "better_quote_validity",
    }
    assert assert_no_private_fields({"row": row}) == []


def test_ollama_invalid_quote_rejected_or_not_quote_valid() -> None:
    row = compare_extractions_on_chunk(
        _sample_chunk(),
        domain_pack="creativity",
        ollama_client=_FakeOllamaClient(valid_quote=False),
    )
    ollama = row["local_ollama"]
    assert ollama["quote_valid_accepted_count"] == 0 or ollama["accepted_count"] == 0


def test_build_comparison_aggregate_and_verdict() -> None:
    rows = [
        {
            "mock_deterministic": {
                "accepted_count": 1,
                "quote_valid_accepted_count": 1,
            },
            "local_ollama": {
                "accepted_count": 0,
                "quote_valid_accepted_count": 0,
                "rejection_reason_counts": {"unsupported_claim": 1},
            },
            "comparison": {"quality_vs_mock": "thinner"},
        },
        {
            "mock_deterministic": {
                "accepted_count": 1,
                "quote_valid_accepted_count": 1,
            },
            "local_ollama": {
                "accepted_count": 1,
                "quote_valid_accepted_count": 1,
                "rejection_reason_counts": {},
            },
            "comparison": {"quality_vs_mock": "comparable"},
        },
    ]
    aggregate = build_comparison_aggregate(rows)
    assert aggregate["compared_abstract_count"] == 2
    assert aggregate["mock_total_accepted"] == 2
    verdict, _ = classify_comparison_verdict(
        aggregate,
        ollama_health={"reachable": True, "model": "qwen2.5:7b"},
    )
    assert verdict == "GO"


def test_build_atlas_safe_comparison_artifact() -> None:
    aggregate = build_comparison_aggregate([])
    artifact = build_atlas_safe_comparison_artifact(
        aggregate=aggregate,
        rows=[],
        verdict="PARTIAL",
        rationale="Thin coverage.",
        ollama_model="qwen2.5:7b",
    )
    assert artifact["schema_version"].startswith("atlas_local_model_extraction")
    assert artifact["evaluation_only"] is True
    assert assert_no_private_fields({"artifact": artifact}) == []


def test_missing_comparison_gate_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_EXPANSION_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")
    monkeypatch.delenv("RGE_ALLOW_LOCAL_MODEL_EXTRACTION_COMPARISON", raising=False)
    with pytest.raises(
        LocalModelExtractionComparisonGateError,
        match="RGE_ALLOW_LOCAL_MODEL_EXTRACTION_COMPARISON",
    ):
        assert_local_model_extraction_comparison_env()


def test_run_local_model_extraction_comparison_mocked_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_ALLOW_LOCAL_MODEL_EXTRACTION_COMPARISON", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_EXPANSION_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")

    fake_records = {
        "records": [
            {
                "source_id": "openalex:W1",
                "source_status": "abstract_available",
                "abstract_text": SAMPLE_ABSTRACT,
                "source_kind": "openalex",
            }
        ],
        "resolved_count": 1,
        "backend_counts": {"openalex": 1},
    }

    from rge.modules import local_model_extraction_comparison as module

    with patch.object(
        module,
        "resolve_live_expanded_network_source_records",
        return_value=fake_records,
    ):
        result = module.run_local_model_extraction_comparison(
            output_dir=tmp_path,
            client=_FakeOllamaClient(valid_quote=True),
            skip_health_check=True,
            limit=1,
        )

    assert result["comparison_verdict"] in {"GO", "PARTIAL"}
    artifact_path = Path(result["artifact_path"])
    loaded = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert loaded["comparison_aggregate"]["compared_abstract_count"] == 1
    assert assert_no_private_fields({"artifact": loaded}) == []


def test_sync_comparison_artifact_to_public_site(tmp_path: Path) -> None:
    from rge.modules.local_model_extraction_comparison import (
        sync_comparison_artifact_to_public_site,
    )

    aggregate = build_comparison_aggregate(
        [
            {
                "mock_deterministic": {
                    "accepted_count": 1,
                    "quote_valid_accepted_count": 1,
                },
                "local_ollama": {
                    "accepted_count": 1,
                    "quote_valid_accepted_count": 1,
                    "rejection_reason_counts": {},
                },
                "comparison": {"quality_vs_mock": "comparable"},
            }
        ]
    )
    artifact = build_atlas_safe_comparison_artifact(
        aggregate=aggregate,
        rows=[],
        verdict="GO",
        rationale="Compared mock vs Ollama on live abstracts.",
        ollama_model="qwen2.5:7b",
    )
    public_path = tmp_path / "atlas_local_model_extraction_comparison_latest.json"
    result = sync_comparison_artifact_to_public_site(
        artifact,
        public_path=public_path,
    )
    assert result["status"] == "completed"
    loaded = json.loads(public_path.read_text(encoding="utf-8"))
    assert loaded["comparison_verdict"] == "GO"


def test_local_model_readiness_partial_without_quote_validity() -> None:
    aggregate = {
        "local_ollama_total_accepted": 2,
        "local_ollama_quote_validity_rate": 0.5,
        "mock_quote_validity_rate": 1.0,
    }
    status, notes = classify_local_model_readiness(aggregate, comparison_verdict="GO")
    assert status == "PARTIAL"
    assert "below threshold" in notes


def test_local_model_readiness_go_when_quote_validity_meets_mock() -> None:
    aggregate = {
        "local_ollama_total_accepted": 3,
        "local_ollama_quote_validity_rate": 1.0,
        "mock_quote_validity_rate": 1.0,
    }
    status, _notes = classify_local_model_readiness(aggregate, comparison_verdict="GO")
    assert status == "GO"
