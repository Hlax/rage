"""Staged-spine temp DB bridge to public source-health run artifact."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.db.connection import ensure_database
from rge.modules.atlas_preview_curator import export_staged_spine_source_health_artifact
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.live_arbitrary_source_health import (
    LOCAL_SAFE_ARBITRARY_QUESTION,
    LOCAL_SAFE_RUN_ID,
    run_local_safe_arbitrary_source_health_proof,
)


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")


def test_export_staged_spine_source_health_artifact_writes_valid_json(
    tmp_path: Path,
) -> None:
    conn = ensure_database(tmp_path / "staged_source_health_sync.sqlite")
    try:
        run_local_safe_arbitrary_source_health_proof(
            conn,
            output_dir=tmp_path,
        )
        output_path = tmp_path / "atlas_source_health_run_latest.json"
        result = export_staged_spine_source_health_artifact(
            conn,
            run_id=LOCAL_SAFE_RUN_ID,
            question=LOCAL_SAFE_ARBITRARY_QUESTION,
            output_path=output_path,
        )
        artifact = json.loads(output_path.read_text(encoding="utf-8"))

        assert result["status"] == "completed"
        assert output_path.is_file()
        assert artifact["schema_version"] == "atlas_source_health_run_v0.1.0"
        assert artifact["source_health_summary"]["sources_with_metadata"] >= 1
        assert artifact.get("readiness_warnings")
        assert assert_no_private_fields({"artifact": artifact}) == []
    finally:
        conn.close()
