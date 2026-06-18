"""Committed public-site atlas preview fixture checks (ticket-320)."""

from __future__ import annotations

import json
from pathlib import Path

from rge.contracts.atlas_snapshot_v0 import validate_atlas_snapshot
from rge.modules.atlas_preview_curator import (
    STAGED_PREVIEW_LABEL,
    STAGED_PREVIEW_SNAPSHOT_ID,
    curate_snapshot_for_public_preview,
    validate_public_preview_snapshot,
    write_public_preview_fixtures,
)
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.evidence_db_atlas import STAGED_SPINE_RUN_PREFIX

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DATA = REPO_ROOT / "apps" / "public-site" / "public" / "data"
SNAPSHOT_PATH = PUBLIC_DATA / "atlas_snapshot_preview.json"
COHERENCE_PATH = PUBLIC_DATA / "atlas_coherence_preview.json"
STAGED_FIXTURE_PATH = (
    REPO_ROOT / "fixtures" / "atlas" / "atlas_snapshot_staged_spine_preview.json"
)


def _load_snapshot() -> dict:
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def _load_coherence() -> dict:
    return json.loads(COHERENCE_PATH.read_text(encoding="utf-8"))


def test_committed_atlas_preview_passes_contract_and_private_field_scan() -> None:
    snapshot = _load_snapshot()
    validate_atlas_snapshot(snapshot)
    validate_public_preview_snapshot(snapshot)
    assert not assert_no_private_fields(snapshot)


def test_committed_atlas_preview_reflects_staged_spine_shape() -> None:
    snapshot = _load_snapshot()
    assert snapshot["snapshot_id"] == STAGED_PREVIEW_SNAPSHOT_ID
    assert len(snapshot["clusters"]) >= 2
    assert len(snapshot["follow_up_questions"]) >= 1
    assert all(
        str(run["run_id"]).startswith(STAGED_SPINE_RUN_PREFIX)
        for run in snapshot["runs"]
    )
    assert all(
        str(cluster.get("run_id") or "").startswith(STAGED_SPINE_RUN_PREFIX)
        for cluster in snapshot["clusters"]
        if cluster.get("run_id")
    )
    assert snapshot["coherence_summary"]["preview_label"] == STAGED_PREVIEW_LABEL


def test_committed_follow_ups_use_queued_status_for_ui() -> None:
    snapshot = _load_snapshot()
    assert snapshot["follow_up_questions"]
    assert all(
        item["status"] == "queued" for item in snapshot["follow_up_questions"]
    )


def test_committed_coherence_preview_matches_snapshot_summary() -> None:
    snapshot = _load_snapshot()
    coherence = _load_coherence()
    summary = snapshot["coherence_summary"]
    assert coherence["overall_coherence_verdict"] == summary["overall_coherence_verdict"]
    assert coherence["preview_label"] == summary["preview_label"]
    assert coherence["population"]["clusters"] >= 2
    assert coherence["population"]["follow_up_questions"] >= 1


def test_curate_snapshot_maps_active_followups_to_queued() -> None:
    snapshot = _load_snapshot()
    mutated = json.loads(json.dumps(snapshot))
    mutated["follow_up_questions"] = [
        {**mutated["follow_up_questions"][0], "status": "active"}
    ]
    curated = curate_snapshot_for_public_preview(mutated)
    assert curated["follow_up_questions"][0]["status"] == "queued"


def test_fixtures_atlas_staged_spine_reference_matches_public_preview() -> None:
    public_snapshot = _load_snapshot()
    fixture_snapshot = json.loads(STAGED_FIXTURE_PATH.read_text(encoding="utf-8"))
    validate_atlas_snapshot(fixture_snapshot)
    validate_public_preview_snapshot(fixture_snapshot)
    assert fixture_snapshot == public_snapshot


def test_write_public_preview_fixtures_syncs_fixtures_reference(tmp_path: Path) -> None:
    snapshot = _load_snapshot()
    snapshot_path = tmp_path / "atlas_snapshot_preview.json"
    coherence_path = tmp_path / "atlas_coherence_preview.json"
    fixtures_path = tmp_path / "fixtures" / "atlas_snapshot_staged_spine_preview.json"
    result = write_public_preview_fixtures(
        snapshot,
        snapshot_path=snapshot_path,
        coherence_path=coherence_path,
        fixtures_reference_path=fixtures_path,
    )
    assert result["fixtures_reference_path"] == str(fixtures_path)
    public_written = json.loads(snapshot_path.read_text(encoding="utf-8"))
    fixture_written = json.loads(fixtures_path.read_text(encoding="utf-8"))
    assert fixture_written == public_written
