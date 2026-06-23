"""Follow-up tests: execute-safe patch staging hook, auto preview sync, expected_files inference."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.modules.instruction_packet_ticket_draft import (
    build_draft_ticket_payload,
    infer_expected_files,
    parse_instruction_packet_text,
)
from rge.modules.operator_loop import WorkingTreeStatus, execute_safe_checks
from rge.modules.tier2_patch_staging import (
    auto_sync_patch_preview_enabled,
    create_patch_bundle_from_working_tree,
    execute_safe_patch_staging_enabled,
    run_execute_safe_patch_staging_hook,
)
from rge.modules.tier2_patch_staging_preview import atlas_artifact_path
from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state
from tests.unit.test_tier2_local_implementation import FakeGit, _seed_draft, _valid_draft
from tests.unit.test_tier2_patch_staging import _stage_bundle


def test_infer_expected_files_adds_companion_unit_test(tmp_path: Path) -> None:
    target = tmp_path / "tests/unit/test_release_governor.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# test\n", encoding="utf-8")
    parsed = {
        "likely_files": ["rge/modules/release_governor.py"],
        "tests_recommended": [],
        "build_title": "",
        "summary": "",
        "rollback_plan": "",
    }
    inferred = infer_expected_files(parsed, root=tmp_path)
    assert "rge/modules/release_governor.py" in inferred
    assert "tests/unit/test_release_governor.py" in inferred


def test_infer_expected_files_extracts_backtick_paths() -> None:
    parsed = {
        "likely_files": [],
        "build_title": "Update `rge/modules/tier2_patch_staging.py`",
        "summary": "",
        "tests_recommended": [],
        "rollback_plan": "",
    }
    inferred = infer_expected_files(parsed)
    assert "rge/modules/tier2_patch_staging.py" in inferred


def test_build_draft_ticket_payload_uses_inferred_expected_files(tmp_path: Path) -> None:
    parsed = {
        "packet_id": "packet-infer-files",
        "likely_files": ["rge/modules/tier2_patch_staging.py"],
        "acceptance_criteria": [],
        "tests_recommended": ["python -m pytest tests/unit/test_tier2_patch_staging.py -q"],
        "non_goals": [],
        "safety_notes": ["governor verdict: GO"],
        "summary": "Infer files",
        "build_title": "Tier2 staging",
        "rollback_plan": "Revert",
    }
    draft = build_draft_ticket_payload(
        parsed=parsed,
        instruction_packet_path="data/operator/instruction_packets/p.md",
        validation={"passed": True, "reasons": []},
        root=tmp_path,
    )
    assert draft["expected_files_inferred"] is True
    assert "rge/modules/tier2_patch_staging.py" in draft["expected_files"]
    assert any(path.startswith("tests/") for path in draft["expected_files"])


def test_inferred_expected_files_reduce_source_without_test_partial(
    tmp_path: Path,
) -> None:
    from rge.modules.tier2_patch_staging import build_patch_bundle_payload, validate_patch_bundle

    draft_path = _seed_draft(
        tmp_path,
        extra={
            "expected_files": infer_expected_files(
                {"likely_files": ["rge/modules/tier2_local_implementation.py"]},
                root=tmp_path,
            ),
        },
    )
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    changed = [
        "rge/modules/tier2_local_implementation.py",
        "tests/unit/test_tier2_local_implementation.py",
    ]
    bundle = build_patch_bundle_payload(
        draft=draft,
        draft_path=draft_path,
        branch_name="phase-3/tier2-test",
        changed_files=changed,
        root=tmp_path,
        diff_stats={"changed_file_count": 2, "lines_added": 2, "lines_removed": 0, "deleted_files_count": 0},
    )
    validation = validate_patch_bundle(bundle, draft=draft, root=tmp_path)
    assert validation["passed"] is True


def test_auto_sync_preview_after_bundle_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_AUTO_SYNC_TIER2_PATCH_PREVIEW", "1")
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
        create_patch_bundle_from_working_tree(latest=True, root=tmp_path, git_runner=fake)
    assert atlas_artifact_path(root=tmp_path).is_file()
    artifact = json.loads(atlas_artifact_path(root=tmp_path).read_text(encoding="utf-8"))
    assert artifact["validation_verdict"] == "GO"


def test_auto_sync_preview_can_be_disabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_AUTO_SYNC_TIER2_PATCH_PREVIEW", "0")
    assert auto_sync_patch_preview_enabled() is False


def test_execute_safe_patch_staging_hook_stages_and_refreshes_preview(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_EXECUTE_SAFE_PATCH_STAGING", "1")
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    _seed_draft(tmp_path)
    rel = "rge/modules/tier2_local_implementation.py"
    (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / rel).write_text("# change\n", encoding="utf-8")
    tree = WorkingTreeStatus(clean=False, branch="main", dirty_paths=[rel])
    fake = FakeGit(changed=[rel])
    with patch(
        "rge.modules.tier2_patch_staging.inspect_working_tree",
        return_value=tree,
    ), patch(
        "rge.modules.tier2_patch_staging.collect_working_changed_files",
        return_value=[rel],
    ):
        result = run_execute_safe_patch_staging_hook(root=tmp_path, working_tree=tree)
    assert result is not None
    assert result["status"] == "completed"
    step_names = [row["step"] for row in result["steps"]]
    assert "stage" in step_names
    assert "validate" in step_names
    assert "preview_refresh" in step_names
    assert atlas_artifact_path(root=tmp_path).is_file()


def test_execute_safe_hook_skipped_when_env_disabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RGE_EXECUTE_SAFE_PATCH_STAGING", raising=False)
    assert run_execute_safe_patch_staging_hook(root=tmp_path) is None


def test_execute_safe_runs_patch_staging_hook_on_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_EXECUTE_SAFE_PATCH_STAGING", "1")
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "2")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    clean = seed_operator_neutral_plan_state(tmp_path)
    rel = "rge/modules/tier2_local_implementation.py"
    _seed_draft(tmp_path)
    _stage_bundle(tmp_path, changed=[rel])

    def _fake_runner(argv, cwd, env):  # noqa: ANN001
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    with patch(
        "rge.modules.operator_loop.safe_verification_commands",
        return_value=[],
    ):
        result = execute_safe_checks(
            root=tmp_path,
            working_tree=clean,
            command_runner=_fake_runner,
        )
    assert result["execution_status"] == "pass"
    hook = result.get("tier2_patch_staging_execute_safe_hook")
    assert hook is not None
    assert hook.get("status") == "completed"
    assert any(step["step"] == "preview_refresh" for step in hook.get("steps") or [])


def test_parse_instruction_packet_and_infer_files_integration() -> None:
    text = """# Instruction packet

## Summary
Update `rge/modules/tier2_patch_staging.py`.

## Files likely affected
- `rge/modules/tier2_patch_staging.py`

## Acceptance criteria
- Tests pass

## Tests to run
- `python -m pytest tests/unit/test_tier2_patch_staging.py -q`

## Safety notes
- governor verdict: GO
"""
    parsed = parse_instruction_packet_text(text)
    inferred = infer_expected_files(parsed)
    assert "rge/modules/tier2_patch_staging.py" in inferred
