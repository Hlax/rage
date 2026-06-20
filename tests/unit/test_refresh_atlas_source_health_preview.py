"""Operator refresh script for atlas source-health preview."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from scripts.refresh_atlas_source_health_preview import (
    refresh_public_source_health_preview,
    validate_source_health_artifact,
)


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")


def test_validate_source_health_artifact_rejects_private_fields() -> None:
    errors = validate_source_health_artifact(
        {
            "schema_version": "atlas_source_health_run_v0.1.0",
            "source_health_summary": {"sources_with_metadata": 1, "source_id": "secret"},
        }
    )
    assert errors


def test_refresh_public_source_health_preview_writes_validated_artifact(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "atlas_source_health_run_latest.json"
    result = refresh_public_source_health_preview(output_path=output_path)
    artifact = json.loads(output_path.read_text(encoding="utf-8"))

    assert result["status"] == "completed"
    assert output_path.is_file()
    assert artifact["schema_version"] == "atlas_source_health_run_v0.1.0"
    assert artifact["source_health_summary"]["sources_with_metadata"] >= 1
    trace_summary = artifact.get("trace_summary") or {}
    assert int(trace_summary.get("trace_count") or 0) >= 1
    assert trace_summary.get("atlas_trace_preview")
    assert assert_no_private_fields({"artifact": artifact}) == []


def test_validate_source_health_artifact_requires_trace_summary_when_requested() -> None:
    errors = validate_source_health_artifact(
        {
            "schema_version": "atlas_source_health_run_v0.1.0",
            "source_health_summary": {"sources_with_metadata": 1},
        },
        require_trace_summary=True,
    )
    assert any("trace_summary" in error for error in errors)


def test_refresh_rejects_artifact_without_trace_summary_when_required(
    tmp_path: Path,
) -> None:
    artifact_path = tmp_path / "missing_trace.json"
    artifact_path.write_text(
        json.dumps(
            {
                "schema_version": "atlas_source_health_run_v0.1.0",
                "source_health_summary": {"sources_with_metadata": 1},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="trace_summary"):
        refresh_public_source_health_preview(
            input_path=artifact_path,
            output_path=tmp_path / "out.json",
            require_trace_summary=True,
        )


def test_refresh_public_source_health_preview_accepts_existing_input(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "generated.json"
    refresh_public_source_health_preview(output_path=generated)
    output_path = tmp_path / "copied.json"
    result = refresh_public_source_health_preview(
        input_path=generated,
        output_path=output_path,
    )
    assert result["input_path"] == str(generated)
    assert output_path.is_file()


@pytest.mark.live_network
def test_refresh_live_atom_trace_source_writes_trace_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    output_path = tmp_path / "atlas_source_health_run_latest.json"
    result = refresh_public_source_health_preview(
        output_path=output_path,
        source="live-atom-trace",
        require_trace_summary=True,
    )
    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    trace_summary = artifact.get("trace_summary") or {}

    assert result["source"] == "live-atom-trace"
    assert int(trace_summary.get("trace_count") or 0) >= 1
    assert trace_summary.get("atlas_trace_preview")
    assert assert_no_private_fields({"artifact": artifact}) == []
