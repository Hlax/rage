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
    assert assert_no_private_fields({"artifact": artifact}) == []


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
