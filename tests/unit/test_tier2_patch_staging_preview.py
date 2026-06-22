"""Tier 2 patch staging Atlas operator preview tests."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.operator_loop import build_operator_plan
from rge.modules.safety_auditor import ATLAS_PREVIEW_PUBLIC_DATA_FILES, run_safety_audit
from rge.modules.tier2_patch_staging_preview import (
    ATLAS_ARTIFACT_SCHEMA,
    Tier2PatchStagingPreviewError,
    atlas_artifact_path,
    build_atlas_safe_tier2_patch_staging_artifact,
    inspect_tier2_patch_staging_preview_status,
    refresh_tier2_patch_staging_preview,
    run_refresh_tier2_patch_staging_preview_command,
)
from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state
from tests.unit.test_tier2_patch_staging import _stage_bundle
from tests.unit.test_tier2_local_implementation import _seed_draft


def test_preview_artifact_generated_from_go_bundle(tmp_path: Path) -> None:
    rel = "rge/modules/tier2_local_implementation.py"
    bundle, _ = _stage_bundle(tmp_path, changed=[rel])
    assert bundle["validation_verdict"] == "GO"
    artifact = build_atlas_safe_tier2_patch_staging_artifact(bundle, root=tmp_path)
    assert artifact["schema_version"] == ATLAS_ARTIFACT_SCHEMA
    assert artifact["validation_verdict"] == "GO"
    assert artifact["apply_ready"] is True
    assert artifact["stop_state"] is False
    assert artifact["next_recommended_action"] == "apply_staged_patch_and_commit"
    assert artifact["changed_file_count"] == 1
    assert assert_no_private_fields({"artifact": artifact}) == []


def test_preview_artifact_generated_from_partial_or_nogo_bundle(tmp_path: Path) -> None:
    bundle, _ = _stage_bundle(
        tmp_path,
        changed=[".env.local"],
        file_contents={".env.local": "SECRET=1\n"},
    )
    artifact = build_atlas_safe_tier2_patch_staging_artifact(bundle, root=tmp_path)
    assert artifact["validation_verdict"] in {"PARTIAL", "NO-GO"}
    assert artifact["apply_ready"] is False
    assert artifact["stop_state"] is True
    assert artifact["next_recommended_action"].startswith("fix_staged_patch")


def test_missing_bundle_fails_closed(tmp_path: Path) -> None:
    from rge.modules.tier2_patch_staging_preview import main

    with pytest.raises(Tier2PatchStagingPreviewError, match="no patch staging bundle"):
        refresh_tier2_patch_staging_preview(latest=True, root=tmp_path)
    assert main(["--latest", "--root", str(tmp_path)]) == 1


def test_private_fields_scrubbed_from_preview_artifact(tmp_path: Path) -> None:
    rel = "rge/modules/tier2_local_implementation.py"
    bundle, _ = _stage_bundle(tmp_path, changed=[rel])
    bundle["validation_reasons"] = [
        "forbidden path C:\\Users\\secret\\file.py",
        "private_notes leaked",
    ]
    artifact = build_atlas_safe_tier2_patch_staging_artifact(bundle, root=tmp_path)
    reasons_blob = json.dumps(artifact["validation_reasons"])
    assert "C:\\Users" not in reasons_blob
    assert "private_notes leaked" not in reasons_blob
    assert assert_no_private_fields({"artifact": artifact}) == []


def test_refresh_sync_writes_public_artifact(tmp_path: Path) -> None:
    rel = "rge/modules/tier2_local_implementation.py"
    _stage_bundle(tmp_path, changed=[rel])
    payload = refresh_tier2_patch_staging_preview(
        latest=True,
        sync_public=True,
        root=tmp_path,
    )
    artifact_path = atlas_artifact_path(root=tmp_path)
    assert artifact_path.is_file()
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["validation_verdict"] == "GO"
    assert payload["sync"]["public_artifact_path"] == str(
        artifact_path.relative_to(tmp_path)
    ).replace("\\", "/")


def test_safety_auditor_scans_tier2_patch_staging_artifact() -> None:
    assert "atlas_tier2_patch_staging_latest.json" in ATLAS_PREVIEW_PUBLIC_DATA_FILES
    report = run_safety_audit("secrets")
    assert report["status"] == "pass", report["blocked_reasons"]
    assert any(
        "atlas_tier2_patch_staging_latest.json" in item
        for item in report["checked_secrets"]
    )


def test_safety_auditor_rejects_forbidden_content_in_preview(tmp_path: Path) -> None:
    site_data = tmp_path / "apps" / "public-site" / "public" / "data"
    site_data.mkdir(parents=True)
    for name in ("public_cards.json", "public_memos.json", "build_info.json"):
        (site_data / name).write_text("[]", encoding="utf-8")
    for name in ATLAS_PREVIEW_PUBLIC_DATA_FILES:
        if name == "atlas_tier2_patch_staging_latest.json":
            (site_data / name).write_text(
                json.dumps({"private_notes": "operator secret"}),
                encoding="utf-8",
            )
        elif (Path(__file__).resolve().parents[2] / "apps/public-site/public/data" / name).is_file():
            (site_data / name).write_text(
                (
                    Path(__file__).resolve().parents[2]
                    / "apps/public-site/public/data"
                    / name
                ).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        else:
            (site_data / name).write_text("{}", encoding="utf-8")
    report = run_safety_audit("full", root=tmp_path)
    assert report["status"] == "fail"


def test_atlas_preview_page_renders_tier2_patch_staging_panel() -> None:
    page = (
        Path(__file__).resolve().parents[2]
        / "apps/public-site/app/atlas-preview/page.tsx"
    )
    text = page.read_text(encoding="utf-8")
    assert "resolveTier2PatchStagingPreview" in text
    assert "Tier 2 patch staging (operator panel)" in text
    assert "tier2-patch-staging-panel" in text
    assert "Validation verdict" in text


def test_operator_loop_recommends_preview_refresh_when_stale(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    clean = seed_operator_neutral_plan_state(tmp_path)
    _seed_draft(tmp_path)
    rel = "rge/modules/tier2_local_implementation.py"
    _stage_bundle(tmp_path, changed=[rel])
    artifact_path = atlas_artifact_path(root=tmp_path)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        json.dumps(
            {
                "schema_version": ATLAS_ARTIFACT_SCHEMA,
                "status": "available",
                "validation_verdict": "GO",
                "updated_at": "2020-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    past = time.time() - 3600
    import os

    os.utime(artifact_path, (past, past))
    status = inspect_tier2_patch_staging_preview_status(root=tmp_path)
    assert status["preview_refresh_recommended"] is True
    plan = build_operator_plan(root=tmp_path, working_tree=clean)
    assert plan["next_recommended_action"]["action_id"] == "refresh_tier2_patch_staging_preview"


def test_dry_run_does_not_write_public_artifact(tmp_path: Path) -> None:
    rel = "rge/modules/tier2_local_implementation.py"
    _stage_bundle(tmp_path, changed=[rel])
    refresh_tier2_patch_staging_preview(
        latest=True,
        sync_public=True,
        dry_run=True,
        root=tmp_path,
    )
    assert not atlas_artifact_path(root=tmp_path).is_file()


def test_refresh_from_explicit_bundle_path(tmp_path: Path) -> None:
    rel = "rge/modules/tier2_local_implementation.py"
    _, bundle_path = _stage_bundle(tmp_path, changed=[rel])
    payload, code = run_refresh_tier2_patch_staging_preview_command(
        bundle=bundle_path,
        sync_public=True,
        root=tmp_path,
    )
    assert code == 0
    assert payload["verdict"] == "GO"
    assert atlas_artifact_path(root=tmp_path).is_file()
