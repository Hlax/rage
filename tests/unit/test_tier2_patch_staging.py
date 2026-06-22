"""Tier 2 patch staging and diff quality gate tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.operator_loop import WorkingTreeStatus, build_operator_plan
from rge.modules.release_governor import evaluate_release_governor, inspect_release_governor_plan_status
from rge.modules.tier2_local_implementation import (
    run_tier2_local_implementation_command,
)
from rge.modules.tier2_patch_staging import (
    BUNDLE_SCHEMA_VERSION,
    Tier2PatchStagingError,
    apply_staged_patch_bundle,
    build_patch_bundle_payload,
    create_patch_bundle_from_working_tree,
    discover_latest_patch_bundle_for_draft,
    inspect_tier2_patch_staging_status,
    load_patch_bundle,
    main,
    patch_staging_dir,
    public_safe_summary,
    run_tier2_patch_staging_command,
    validate_patch_bundle,
    write_patch_bundle,
)
from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state
from tests.unit.test_tier2_local_implementation import FakeGit, _seed_draft, _valid_draft


def _stage_bundle(
    tmp_path: Path,
    *,
    changed: list[str],
    draft_extra: dict | None = None,
    file_contents: dict[str, str] | None = None,
) -> tuple[dict, Path]:
    draft_path = _seed_draft(tmp_path, extra=draft_extra)
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    contents = file_contents or {rel: f"# content for {rel}\n" for rel in changed}
    for rel, body in contents.items():
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    stats = {
        "changed_file_count": len(changed),
        "lines_added": sum(len(v.splitlines()) for v in contents.values()),
        "lines_removed": 0,
        "deleted_files_count": 0,
    }
    bundle = build_patch_bundle_payload(
        draft=draft,
        draft_path=draft_path,
        branch_name="phase-3/tier2-draft-tier2-test",
        changed_files=changed,
        root=tmp_path,
        diff_stats=stats,
    )
    validation = validate_patch_bundle(bundle, draft=draft, root=tmp_path)
    bundle["validation_verdict"] = validation["validation_verdict"]
    bundle["validation_reasons"] = validation["validation_reasons"]
    bundle_path = write_patch_bundle(bundle, file_contents=contents, root=tmp_path)
    bundle["_bundle_path"] = str(bundle_path.relative_to(tmp_path)).replace("\\", "/")
    return bundle, bundle_path


def test_staging_bundle_created_from_draft_ticket(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    _seed_draft(tmp_path)
    rel = "rge/modules/tier2_local_implementation.py"
    (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / rel).write_text("# patched\n", encoding="utf-8")
    fake = FakeGit(changed=[rel])
    with patch(
        "rge.modules.tier2_patch_staging.inspect_working_tree",
        return_value=WorkingTreeStatus(clean=False, branch="main", dirty_paths=[rel]),
    ):
        bundle, bundle_path = create_patch_bundle_from_working_tree(
            latest=True,
            root=tmp_path,
            git_runner=fake,
        )
    assert bundle["schema_version"] == BUNDLE_SCHEMA_VERSION
    assert bundle_path.is_file()
    assert bundle["validation_verdict"] in {"GO", "PARTIAL", "NO-GO"}
    assert (bundle_path.parent / "validation.json").is_file()


def test_forbidden_file_touch_rejected(tmp_path: Path) -> None:
    draft_path = _seed_draft(tmp_path)
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    bundle, _ = _stage_bundle(
        tmp_path,
        changed=["tickets/TICKET_QUEUE.md"],
        file_contents={"tickets/TICKET_QUEUE.md": "# queue\n"},
    )
    assert bundle["validation_verdict"] in {"PARTIAL", "NO-GO"}
    validation = validate_patch_bundle(bundle, draft=draft, root=tmp_path)
    assert any("forbidden" in reason for reason in validation["validation_reasons"])
    assert validation["passed"] is False


def test_oversized_diff_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_TIER2_PATCH_MAX_FILES", "2")
    draft_path = _seed_draft(tmp_path)
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    changed = [f"rge/modules/file_{index}.py" for index in range(5)]
    bundle, _ = _stage_bundle(tmp_path, changed=changed)
    assert bundle["validation_verdict"] in {"PARTIAL", "NO-GO"}
    validation = validate_patch_bundle(bundle, draft=draft, root=tmp_path)
    assert any("too large" in reason for reason in validation["validation_reasons"])
    assert validation["passed"] is False


def test_test_only_change_allowed_when_ticket_test_only(tmp_path: Path) -> None:
    draft_extra = {
        "scope": "test-only",
        "expected_files": ["tests/unit/test_example.py"],
        "test_plan": ["python -c \"import sys; sys.exit(0)\""],
    }
    bundle, bundle_path = _stage_bundle(
        tmp_path,
        changed=["tests/unit/test_example.py"],
        draft_extra=draft_extra,
    )
    draft = json.loads((tmp_path / "data/operator/draft_tickets/draft_tier2_test.json").read_text(encoding="utf-8"))
    validation = validate_patch_bundle(bundle, draft=draft, root=tmp_path)
    assert validation["passed"] is True
    assert bundle["validation_verdict"] == "GO"


def test_test_only_change_rejected_without_ticket_scope(tmp_path: Path) -> None:
    draft_path = _seed_draft(tmp_path)
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    bundle, _ = _stage_bundle(tmp_path, changed=["tests/unit/test_only_change.py"])
    validation = validate_patch_bundle(bundle, draft=draft, root=tmp_path)
    assert any("test-only ticket" in reason for reason in validation["validation_reasons"])


def test_public_artifact_change_requires_safety_audit_flag(tmp_path: Path) -> None:
    draft_path = _seed_draft(tmp_path)
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    rel = "apps/public-site/public/data/atlas_fixture.json"
    bundle = build_patch_bundle_payload(
        draft=draft,
        draft_path=draft_path,
        branch_name="phase-3/tier2-test",
        changed_files=[rel],
        root=tmp_path,
        diff_stats={"changed_file_count": 1, "lines_added": 1, "lines_removed": 0, "deleted_files_count": 0},
    )
    bundle["safety_audit_required"] = False
    validation = validate_patch_bundle(bundle, draft=draft, root=tmp_path)
    assert any("safety_audit_required" in reason for reason in validation["validation_reasons"])


def test_non_goal_violation_rejected(tmp_path: Path) -> None:
    draft_path = _seed_draft(
        tmp_path,
        extra={"non_goals": ["Do not edit TICKET_QUEUE.md"]},
    )
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    bundle, _ = _stage_bundle(
        tmp_path,
        changed=["tickets/TICKET_QUEUE.md"],
        file_contents={"tickets/TICKET_QUEUE.md": "queue"},
    )
    validation = validate_patch_bundle(bundle, draft=draft, root=tmp_path)
    assert any("non-goal violated" in reason for reason in validation["validation_reasons"])


def test_clean_staged_validation_allows_apply(tmp_path: Path) -> None:
    rel = "rge/modules/tier2_local_implementation.py"
    bundle, bundle_path = _stage_bundle(tmp_path, changed=[rel])
    assert bundle["validation_verdict"] == "GO"
    loaded = load_patch_bundle(bundle_path, root=tmp_path)
    target = tmp_path / rel
    target.write_text("original\n", encoding="utf-8")
    applied = apply_staged_patch_bundle(loaded, root=tmp_path)
    assert rel in applied
    assert "content for" in target.read_text(encoding="utf-8")


def test_failed_staged_validation_blocks_apply(tmp_path: Path) -> None:
    bundle, bundle_path = _stage_bundle(
        tmp_path,
        changed=[".env.local"],
        file_contents={".env.local": "SECRET=1\n"},
    )
    loaded = load_patch_bundle(bundle_path, root=tmp_path)
    assert loaded["validation_verdict"] != "GO"
    with pytest.raises(Tier2PatchStagingError, match="validation GO"):
        apply_staged_patch_bundle(loaded, root=tmp_path)


def test_tier2_runner_honors_require_staged_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    monkeypatch.setenv("RGE_REQUIRE_TIER2_PATCH_STAGING", "1")
    _seed_draft(tmp_path)
    rel = "rge/modules/tier2_local_implementation.py"
    (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / rel).write_text("# change\n", encoding="utf-8")
    fake = FakeGit(changed=[rel])
    payload, code = run_tier2_local_implementation_command(
        latest=True,
        root=tmp_path,
        git_runner=fake,
        require_staged_validation=True,
        command_runner=lambda argv, cwd, env: subprocess.CompletedProcess(argv, 0),
    )
    assert code == 1
    assert "patch staging validation GO required" in str(payload.get("stop_reason"))


def test_tier2_runner_commit_after_go_staged_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    monkeypatch.setenv("RGE_REQUIRE_TIER2_PATCH_STAGING", "1")
    _seed_draft(tmp_path)
    rel = "rge/modules/tier2_local_implementation.py"
    bundle, bundle_path = _stage_bundle(tmp_path, changed=[rel])
    assert bundle["validation_verdict"] == "GO"
    (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / rel).write_text("# applied\n", encoding="utf-8")
    fake = FakeGit(changed=[rel])
    with patch(
        "rge.modules.tier2_local_implementation.run_release_batch_assembler_command",
        return_value=({"batch_path": "data/operator/release_batches/batch.json"}, 0),
    ):
        payload, code = run_tier2_local_implementation_command(
            latest=True,
            root=tmp_path,
            git_runner=fake,
            require_staged_validation=True,
            command_runner=lambda argv, cwd, env: subprocess.CompletedProcess(argv, 0),
        )
    assert code == 0
    assert payload["verdict"] == "GO"
    assert payload["patch_bundle_path"] is not None


def test_operator_loop_recommends_staging_when_no_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    clean = seed_operator_neutral_plan_state(tmp_path)
    _seed_draft(tmp_path)
    plan = build_operator_plan(root=tmp_path, working_tree=clean)
    assert plan["next_recommended_action"]["action_id"] == "run_tier2_patch_staging"


def test_operator_loop_recommends_validation_when_pending(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    clean = seed_operator_neutral_plan_state(tmp_path)
    _seed_draft(tmp_path)
    rel = "rge/modules/tier2_local_implementation.py"
    bundle, bundle_path = _stage_bundle(tmp_path, changed=[rel])
    bundle["validation_verdict"] = "pending"
    bundle_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    plan = build_operator_plan(root=tmp_path, working_tree=clean)
    assert plan["next_recommended_action"]["action_id"] == "run_tier2_patch_validation"


def test_operator_loop_recommends_apply_when_go(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    clean = seed_operator_neutral_plan_state(tmp_path)
    _seed_draft(tmp_path)
    rel = "rge/modules/tier2_local_implementation.py"
    _stage_bundle(tmp_path, changed=[rel])
    from rge.modules.tier2_patch_staging_preview import refresh_tier2_patch_staging_preview

    refresh_tier2_patch_staging_preview(latest=True, sync_public=True, root=tmp_path)
    plan = build_operator_plan(root=tmp_path, working_tree=clean)
    assert plan["next_recommended_action"]["action_id"] == "run_tier2_local_implementation"
    assert "apply-staged" in plan["next_recommended_action"]["commands"][0]["shell"]


def test_operator_loop_recommends_fix_on_nogo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    clean = seed_operator_neutral_plan_state(tmp_path)
    _seed_draft(tmp_path)
    bundle, bundle_path = _stage_bundle(
        tmp_path,
        changed=[".env.local"],
        file_contents={".env.local": "X=1\n"},
    )
    assert bundle["validation_verdict"] in {"PARTIAL", "NO-GO"}
    plan = build_operator_plan(root=tmp_path, working_tree=clean)
    assert plan["next_recommended_action"]["action_id"] == "fix_tier2_patch_staging"
    assert plan["next_recommended_action"]["gate"] in {"blocked", "review_gated"}


def test_release_governor_blocks_missing_staged_validation_when_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rge.modules.release_governor import build_safe_fixture_batch, load_release_batch, release_batch_dir

    monkeypatch.setenv("RGE_REQUIRE_TIER2_PATCH_STAGING", "1")
    batch = build_safe_fixture_batch(batch_id="batch_tier2_staging_gate")
    batch["branch_names"] = ["phase-3/tier2-draft-tier2-test"]
    batch["candidate_metadata"] = {
        "patch_staging": {
            "patch_bundle_path": None,
            "validation_verdict": None,
        }
    }
    batch_dir = release_batch_dir(root=tmp_path)
    batch_dir.mkdir(parents=True, exist_ok=True)
    batch_path = batch_dir / "batch_tier2_staging_gate.json"
    batch_path.write_text(json.dumps(batch), encoding="utf-8")
    evaluation = evaluate_release_governor(
        load_release_batch(batch_path, root=tmp_path),
        root=tmp_path,
        skip_site=True,
        run_verify=False,
        run_safety=False,
    )
    tier2_check = evaluation["checks"]["tier2_patch_staging"]
    assert tier2_check["passed"] is False


def test_release_governor_passes_with_go_staged_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rge.modules.release_governor import build_safe_fixture_batch, load_release_batch, release_batch_dir

    monkeypatch.setenv("RGE_REQUIRE_TIER2_PATCH_STAGING", "1")
    rel = "rge/modules/tier2_local_implementation.py"
    bundle, _ = _stage_bundle(tmp_path, changed=[rel])
    batch = build_safe_fixture_batch(batch_id="batch_tier2_staging_go")
    batch["branch_names"] = ["phase-3/tier2-draft-tier2-test"]
    batch["candidate_metadata"] = {
        "patch_staging": {
            "patch_bundle_path": bundle["_bundle_path"],
            "validation_verdict": "GO",
        }
    }
    batch_dir = release_batch_dir(root=tmp_path)
    batch_dir.mkdir(parents=True, exist_ok=True)
    batch_path = batch_dir / "batch_tier2_staging_go.json"
    batch_path.write_text(json.dumps(batch), encoding="utf-8")
    evaluation = evaluate_release_governor(
        load_release_batch(batch_path, root=tmp_path),
        root=tmp_path,
        skip_site=True,
        run_verify=False,
        run_safety=False,
    )
    tier2_check = evaluation["checks"]["tier2_patch_staging"]
    assert tier2_check["passed"] is True


def test_public_safe_summary_passes_private_field_scan() -> None:
    summary = public_safe_summary(
        {
            "verdict": "GO",
            "bundle_path": "data/operator/tier2_patch_staging/x/bundle.json",
            "validation_verdict": "GO",
        }
    )
    assert assert_no_private_fields({"patch_staging_summary": summary}) == []


def test_safety_auditor_catches_private_field_in_staging_artifact(tmp_path: Path) -> None:
    from rge.modules.safety_auditor import run_safety_audit

    staging = patch_staging_dir(root=tmp_path)
    bundle_dir = staging / "bad_bundle"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "bundle.json").write_text(
        json.dumps({"private_notes": "operator secret", "schema_version": BUNDLE_SCHEMA_VERSION}),
        encoding="utf-8",
    )
    site_data = tmp_path / "apps/public-site/public/data"
    site_data.mkdir(parents=True)
    for name in ("public_cards.json", "public_memos.json", "build_info.json"):
        (site_data / name).write_text("[]", encoding="utf-8")
    report = run_safety_audit(audit_type="full", root=tmp_path)
    assert report["status"] == "fail"


def test_discover_latest_patch_bundle_for_draft(tmp_path: Path) -> None:
    rel = "rge/modules/tier2_local_implementation.py"
    bundle, _ = _stage_bundle(tmp_path, changed=[rel])
    info = discover_latest_patch_bundle_for_draft("draft-tier2-test", root=tmp_path)
    assert info["status"] == "available"
    assert info["validation_verdict"] == bundle["validation_verdict"]


def test_cli_validate_bundle(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    rel = "rge/modules/tier2_local_implementation.py"
    _, bundle_path = _stage_bundle(tmp_path, changed=[rel])
    exit_code = main(["--bundle", str(bundle_path), "--validate", "--root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["validation_verdict"] == "GO"


def test_inspect_patch_staging_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    _seed_draft(tmp_path)
    status = inspect_tier2_patch_staging_status(root=tmp_path)
    assert status["tier2_patch_staging_recommended"] is True
    release_status = inspect_release_governor_plan_status(root=tmp_path)
    assert release_status["tier2_patch_staging_recommended"] is True


def test_run_staging_command_latest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    _seed_draft(tmp_path)
    rel = "rge/modules/tier2_local_implementation.py"
    (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / rel).write_text("# patch\n", encoding="utf-8")
    fake = FakeGit(changed=[rel])
    with patch(
        "rge.modules.tier2_patch_staging.inspect_working_tree",
        return_value=WorkingTreeStatus(clean=False, branch="main", dirty_paths=[rel]),
    ):
        payload, code = run_tier2_patch_staging_command(latest=True, root=tmp_path, git_runner=fake)
    assert code == 0
    assert payload["status"] == "staged"
    assert payload["validation_verdict"] == "GO"
