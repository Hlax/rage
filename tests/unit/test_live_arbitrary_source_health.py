"""Local-safe arbitrary source purpose gate + Atlas source health tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.contracts.atlas_snapshot_v0 import validate_atlas_snapshot
from rge.db.connection import ensure_database
from rge.modules.atlas_snapshot_builder import (
    assert_no_private_fields,
    build_atlas_snapshot_from_db,
)
from rge.modules.live_arbitrary_source_health import (
    LOCAL_SAFE_ARBITRARY_QUESTION,
    build_atlas_safe_run_artifact,
    persist_abstract_evidence_outcomes,
    persist_resolved_source_health,
    run_local_safe_arbitrary_source_health_proof,
)
from rge.modules.source_resolver import load_manual_fixture_records


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")


def test_local_safe_arbitrary_run_persists_source_health_and_artifact(
    tmp_path: Path,
) -> None:
    conn = ensure_database(tmp_path / "local_safe_health.sqlite")
    try:
        result = run_local_safe_arbitrary_source_health_proof(
            conn,
            output_dir=tmp_path,
        )
        report = result["run_report"]
        artifact = result["atlas_safe_artifact"]
        source_health = report["acquisition_quality_summary"]

        assert result["status"] == "completed"
        assert result["resolved_count"] == 4
        assert source_health["sources_with_metadata"] == 4
        assert source_health["source_status_counts"]["abstract_available"] >= 1
        assert source_health["parser_backend_counts"]["abstract_record"] >= 1
        assert source_health["purpose_fit_status_counts"]["match"] >= 1
        assert report["claims_accepted"] >= 1
        assert artifact["source_health_summary"]["sources_with_metadata"] == 4
        assert artifact["purpose_fit_summary"]["accepted_evidence_count"] >= 1
        assert artifact["next_recommended_packet"]
        assert result["artifact_path"]
        assert (tmp_path / "atlas_source_health_run_latest.json").is_file()
        assert assert_no_private_fields({"artifact": artifact}) == []
    finally:
        conn.close()


def test_atlas_snapshot_exports_source_health_without_private_ids(tmp_path: Path) -> None:
    conn = ensure_database(tmp_path / "atlas_health.sqlite")
    try:
        run_local_safe_arbitrary_source_health_proof(conn, output_dir=tmp_path)
        snapshot = build_atlas_snapshot_from_db(
            conn,
            topic=LOCAL_SAFE_ARBITRARY_QUESTION,
            domain_pack="creativity",
            fixture_mode=False,
        )
        validate_atlas_snapshot(snapshot)
        assert assert_no_private_fields(snapshot) == []

        health = snapshot["source_health_preview"]
        assert health["sources_with_metadata"] == 4
        assert health["source_rows"]
        assert "source_ref" in health["source_rows"][0]
        joined = json.dumps(health)
        assert "source_id" not in joined
        assert "local_path" not in joined
        assert "raw_text" not in joined
    finally:
        conn.close()


def test_dirty_or_unextractable_sources_do_not_reach_abstract_extraction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rge.modules import abstract_evidence

    records = load_manual_fixture_records(domain_pack="creativity")
    calls: list[str] = []
    original = abstract_evidence.extract_and_validate_for_chunk

    def _spy(chunk, *args, **kwargs):  # type: ignore[no-untyped-def]
        calls.append(str(chunk["source_id"]))
        return original(chunk, *args, **kwargs)

    monkeypatch.setattr(abstract_evidence, "extract_and_validate_for_chunk", _spy)

    conn = ensure_database(tmp_path / "blocking.sqlite")
    try:
        persist_resolved_source_health(conn, records)
        outcome = persist_abstract_evidence_outcomes(conn, records)

        metadata_only = next(
            record for record in records if record["source_status"] == "metadata_only"
        )
        assert metadata_only["source_id"] not in calls
        assert outcome["skipped_before_extraction"] >= 1
    finally:
        conn.close()


def test_purpose_mismatch_is_rejected_with_clear_reason(tmp_path: Path) -> None:
    records = load_manual_fixture_records(domain_pack="creativity")
    question = "What visual style patterns recur in AI-assisted product design?"
    conn = ensure_database(tmp_path / "purpose_mismatch.sqlite")
    try:
        persist_resolved_source_health(conn, records, question=question)
        outcome = persist_abstract_evidence_outcomes(conn, records, question=question)
        source_health = build_atlas_safe_run_artifact(
            conn,
            question=question,
            run_report={
                "claims_accepted": outcome["accepted_count"],
                "claims_rejected": outcome["rejected_count"],
                "claims_extracted": outcome["accepted_count"] + outcome["rejected_count"],
                "relationships_updated": 0,
                "graph_connection_metrics": {},
            },
        )["source_health_summary"]

        assert outcome["rejected_count"] >= 1
        assert source_health["purpose_fit_status_counts"]["mismatch"] >= 1
        rejected_reasons = [
            row["rejection_reason"]
            for row in conn.execute(
                "SELECT rejection_reason FROM claims WHERE status = 'rejected'"
            ).fetchall()
        ]
        assert "purpose_mismatch" in rejected_reasons
    finally:
        conn.close()


def test_public_safe_artifact_excludes_private_field_names(tmp_path: Path) -> None:
    conn = ensure_database(tmp_path / "artifact_safety.sqlite")
    try:
        result = run_local_safe_arbitrary_source_health_proof(conn, output_dir=tmp_path)
        artifact_text = json.dumps(result["atlas_safe_artifact"])
        forbidden = (
            "source_id",
            "claim_id",
            "quote_id",
            "chunk_id",
            "local_path",
            "raw_text",
            "prompt",
            "private",
        )
        for item in forbidden:
            assert item not in artifact_text
    finally:
        conn.close()
