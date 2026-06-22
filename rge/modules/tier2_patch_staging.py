"""Tier 2 patch staging airlock: validate diffs before apply/commit."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.autonomous_synthesis_governor import (
    FORBIDDEN_ACTION_PATTERNS,
    _safe_rel,
    utc_now_iso,
)
from rge.modules.instruction_packet_ticket_draft import latest_draft_ticket
from rge.modules.operator_loop import WorkingTreeStatus, inspect_working_tree
from rge.modules.principal_audit_gate import repo_root
from rge.modules.tier2_local_implementation import (
    Tier2ImplementationError,
    _PUBLIC_SURFACE_PREFIXES,
    _resolve_draft_ticket,
    build_tier2_branch_name,
    collect_working_changed_files,
    validate_draft_ticket_for_tier2,
    validate_implementation_paths,
)

BUNDLE_SCHEMA_VERSION = "tier2_patch_bundle_v0.1.0"
STAGING_DIR_REL = Path("data/operator/tier2_patch_staging")
PATCH_STAGING_CLI_SCRIPT = "scripts/run_tier2_patch_staging.py"

_FORBIDDEN_BUNDLE_PATHS = (
    "tickets/TICKET_QUEUE.md",
    ".env",
    ".env.local",
    "data/sources/",
    "fixtures/sources/",
    "data/operator/autonomous_synthesis_governor_ledger.json",
    "data/operator/autonomy_circuit_breaker.json",
)

_DEFAULT_MAX_FILES = 20
_DEFAULT_MAX_LINES = 2000
_DEFAULT_MAX_DELETED_FILES = 5


class Tier2PatchStagingError(RuntimeError):
    """Raised when patch staging inputs or gates fail."""


def patch_staging_dir(*, root: Path | None = None) -> Path:
    return (root or repo_root()) / STAGING_DIR_REL


def require_tier2_patch_staging_enabled() -> bool:
    return os.environ.get("RGE_REQUIRE_TIER2_PATCH_STAGING", "0").strip().casefold() in {
        "1",
        "true",
        "yes",
    }


def _max_files() -> int:
    raw = os.environ.get("RGE_TIER2_PATCH_MAX_FILES", str(_DEFAULT_MAX_FILES)).strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return _DEFAULT_MAX_FILES


def _max_lines() -> int:
    raw = os.environ.get("RGE_TIER2_PATCH_MAX_LINES", str(_DEFAULT_MAX_LINES)).strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return _DEFAULT_MAX_LINES


def _bundle_id(draft_id: str) -> str:
    stamp = utc_now_iso().replace(":", "").replace("-", "")
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", draft_id).strip("-") or "draft"
    return f"{stamp}_{slug}"


def _is_test_only_ticket(draft: dict[str, Any]) -> bool:
    if str(draft.get("scope") or "").casefold() == "test-only":
        return True
    title = str(draft.get("title") or "").casefold()
    if "test-only" in title or "tests only" in title:
        return True
    expected = [str(item).replace("\\", "/") for item in (draft.get("expected_files") or []) if item]
    return bool(expected) and all(item.startswith("tests/") for item in expected)


def _compute_diff_stats(
    *,
    root: Path,
    changed_files: list[str],
    git_numstat: list[tuple[int, int, str]] | None = None,
) -> dict[str, Any]:
    added = 0
    removed = 0
    deleted_files = 0
    if git_numstat:
        for ins, dels, path in git_numstat:
            added += ins
            removed += dels
            if ins == 0 and dels > 0:
                deleted_files += 1
    else:
        for rel in changed_files:
            path = root / rel
            if not path.is_file():
                deleted_files += 1
                continue
            try:
                lines = len(path.read_text(encoding="utf-8").splitlines())
            except OSError:
                lines = 0
            added += lines
    return {
        "changed_file_count": len(changed_files),
        "lines_added": added,
        "lines_removed": removed,
        "deleted_files_count": deleted_files,
    }


def _classify_risk(
    *,
    changed_files: list[str],
    diff_stats: dict[str, Any],
    safety_audit_required: bool,
) -> str:
    count = diff_stats.get("changed_file_count", 0)
    lines = diff_stats.get("lines_added", 0) + diff_stats.get("lines_removed", 0)
    if safety_audit_required or count > 10 or lines > 800:
        return "high"
    if count > 5 or lines > 300:
        return "medium"
    return "low"


def _violates_non_goals(draft: dict[str, Any], changed_files: list[str], *, root: Path) -> list[str]:
    reasons: list[str] = []
    non_goals = " ".join(str(item) for item in (draft.get("non_goals") or []))
    if not non_goals.strip():
        return reasons
    lowered = non_goals.casefold()
    if "do not edit ticket_queue" in lowered or "ticket_queue" in lowered:
        if any("TICKET_QUEUE.md" in path for path in changed_files):
            reasons.append("non-goal violated: TICKET_QUEUE.md must not change")
    if "no public export" in lowered or "no publish" in lowered:
        if any(path.startswith("apps/public-site/public/data/") for path in changed_files):
            reasons.append("non-goal violated: public export artifacts touched")
    blob = json.dumps({"files": changed_files})
    for pattern in FORBIDDEN_ACTION_PATTERNS:
        if pattern.search(blob):
            reasons.append("forbidden push/merge/publish language in staged diff metadata")
            break
    return reasons


def validate_patch_bundle(
    bundle: dict[str, Any],
    *,
    draft: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    """Run diff quality gates; return validation payload with verdict."""
    reasons: list[str] = []
    changed = [
        str(item).replace("\\", "/")
        for item in (bundle.get("proposed_changed_files") or [])
        if str(item).strip()
    ]
    path_reasons = validate_implementation_paths(changed, draft=draft)
    reasons.extend(path_reasons)

    for path in changed:
        if path in _FORBIDDEN_BUNDLE_PATHS or any(
            path.startswith(prefix) for prefix in _FORBIDDEN_BUNDLE_PATHS
        ):
            reasons.append(f"forbidden staged path: {path}")

    diff_stats = bundle.get("diff_summary") if isinstance(bundle.get("diff_summary"), dict) else {}
    if diff_stats.get("changed_file_count", len(changed)) > _max_files():
        reasons.append(f"diff too large: more than {_max_files()} files")
    line_total = diff_stats.get("lines_added", 0) + diff_stats.get("lines_removed", 0)
    if line_total > _max_lines():
        reasons.append(f"diff too large: more than {_max_lines()} lines changed")
    if diff_stats.get("deleted_files_count", 0) > _DEFAULT_MAX_DELETED_FILES:
        reasons.append("unexpected number of deleted files in diff")

    safety_required = bool(bundle.get("safety_audit_required"))
    public_touched = any(
        path.startswith(prefix)
        for path in changed
        for prefix in _PUBLIC_SURFACE_PREFIXES
    )
    if public_touched and not safety_required:
        reasons.append("public artifacts changed but safety_audit_required is false")

    test_only = _is_test_only_ticket(draft)
    test_changes = [path for path in changed if path.startswith("tests/")]
    source_changes = [path for path in changed if path.startswith("rge/")]
    if test_changes and not source_changes and not test_only:
        reasons.append("tests modified without corresponding source changes (not test-only ticket)")
    if source_changes and not test_changes and not test_only:
        expected = draft.get("expected_files") or []
        if any(str(item).startswith("tests/") for item in expected):
            reasons.append("source changed but expected test files were not updated")

    reasons.extend(_violates_non_goals(draft, changed, root=root))

    blob = json.dumps(bundle, sort_keys=True)
    for pattern in FORBIDDEN_ACTION_PATTERNS:
        if pattern.search(blob):
            reasons.append("bundle contains forbidden push/merge/publish/promote language")
            break

    violations = assert_no_private_fields({"patch_bundle": bundle})
    if violations:
        reasons.append("bundle blocked by private-field scan")

    if not reasons:
        verdict = "GO"
    elif len(reasons) <= 2:
        verdict = "PARTIAL"
    else:
        verdict = "NO-GO"

    return {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "validated_at": utc_now_iso(),
        "validation_verdict": verdict,
        "validation_reasons": reasons[:10],
        "passed": verdict == "GO",
    }


def build_patch_bundle_payload(
    *,
    draft: dict[str, Any],
    draft_path: Path,
    branch_name: str,
    changed_files: list[str],
    root: Path,
    diff_stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    draft_id = str(draft.get("id") or draft_path.stem)
    instruction_ref = draft.get("source_instruction_packet")
    changed = [item.replace("\\", "/") for item in changed_files]
    stats = diff_stats or _compute_diff_stats(root=root, changed_files=changed)
    safety_required = _touches_public_surface(changed)
    risk = _classify_risk(
        changed_files=changed,
        diff_stats=stats,
        safety_audit_required=safety_required,
    )
    return {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "bundle_id": _bundle_id(draft_id),
        "draft_ticket_path": _safe_rel(draft_path, root),
        "instruction_packet_path": str(instruction_ref) if instruction_ref else None,
        "branch_name": branch_name,
        "intended_files": list(draft.get("expected_files") or []),
        "proposed_changed_files": changed,
        "diff_summary": stats,
        "risk_class": risk,
        "test_plan": list(draft.get("test_plan") or []),
        "safety_audit_required": safety_required,
        "rollback_notes": str(
            draft.get("rollback_plan")
            or "Delete staged bundle and revert branch commits."
        ),
        "generated_at": utc_now_iso(),
        "validation_verdict": "pending",
        "validation_reasons": [],
    }


def _touches_public_surface(paths: list[str]) -> bool:
    return any(
        path.replace("\\", "/").startswith(prefix)
        for path in paths
        for prefix in _PUBLIC_SURFACE_PREFIXES
    )


def write_patch_bundle(
    bundle: dict[str, Any],
    *,
    file_contents: dict[str, str],
    root: Path,
) -> Path:
    bundle_dir = patch_staging_dir(root=root) / str(bundle["bundle_id"])
    files_dir = bundle_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    for rel, content in file_contents.items():
        target = files_dir / rel.replace("\\", "/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    bundle_path = bundle_dir / "bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    return bundle_path


def load_patch_bundle(path: Path, *, root: Path | None = None) -> dict[str, Any]:
    project_root = root or repo_root()
    candidate = path if path.is_absolute() else project_root / path
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    if payload.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        raise Tier2PatchStagingError(f"unsupported bundle schema: {path}")
    payload["_bundle_dir"] = _safe_rel(candidate.parent, project_root)
    payload["_bundle_path"] = _safe_rel(candidate, project_root)
    return payload


def discover_latest_patch_bundle(
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Return the newest patch bundle under the staging directory."""
    project_root = root or repo_root()
    staging = patch_staging_dir(root=project_root)
    if not staging.is_dir():
        return {"status": "missing", "bundle_path": None}
    candidates = [path for path in staging.glob("*/bundle.json") if path.is_file()]
    if not candidates:
        return {"status": "missing", "bundle_path": None}
    latest = sorted(candidates, key=lambda item: item.stat().st_mtime, reverse=True)[0]
    bundle = load_patch_bundle(latest, root=project_root)
    return {
        "status": "available",
        "bundle_path": bundle.get("_bundle_path"),
        "bundle_id": bundle.get("bundle_id"),
        "validation_verdict": bundle.get("validation_verdict"),
        "generated_at": bundle.get("generated_at"),
    }


def discover_latest_patch_bundle_for_draft(
    draft_ticket_id: str | None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = root or repo_root()
    staging = patch_staging_dir(root=project_root)
    if not staging.is_dir() or not draft_ticket_id:
        return {"status": "missing", "bundle_path": None}
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", draft_ticket_id).strip("-")
    candidates: list[Path] = []
    for bundle_path in staging.glob("*/bundle.json"):
        try:
            payload = json.loads(bundle_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        draft_ids = payload.get("draft_ticket_ids") or []
        if draft_ticket_id in draft_ids or slug in str(payload.get("bundle_id") or ""):
            candidates.append(bundle_path)
        elif payload.get("draft_ticket_path") and slug in str(payload.get("draft_ticket_path")):
            candidates.append(bundle_path)
    if not candidates:
        return {"status": "missing", "bundle_path": None}
    latest = sorted(candidates, key=lambda item: item.stat().st_mtime, reverse=True)[0]
    bundle = load_patch_bundle(latest, root=project_root)
    return {
        "status": "available",
        "bundle_path": bundle.get("_bundle_path"),
        "bundle_id": bundle.get("bundle_id"),
        "validation_verdict": bundle.get("validation_verdict"),
    }


def revalidate_patch_after_backfill_enabled() -> bool:
    return os.environ.get("RGE_REVALIDATE_PATCH_AFTER_BACKFILL", "1").strip().casefold() not in {
        "0",
        "false",
        "no",
    }


def revalidate_latest_patch_bundle_for_draft(
    draft_ticket_id: str | None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Re-run validation on the latest staged bundle for a draft ticket."""
    project_root = root or repo_root()
    discovery = discover_latest_patch_bundle_for_draft(draft_ticket_id, root=project_root)
    if discovery.get("status") != "available" or not discovery.get("bundle_path"):
        return {"status": "skipped", "reason": "no patch bundle for draft"}
    bundle_path = project_root / str(discovery["bundle_path"])
    payload, exit_code = run_tier2_patch_staging_command(
        bundle=bundle_path,
        validate_only=True,
        root=project_root,
    )
    return {
        "status": payload.get("status"),
        "bundle_path": payload.get("bundle_path"),
        "validation_verdict": payload.get("validation_verdict"),
        "validation_reasons": payload.get("validation_reasons") or [],
        "preview_sync": payload.get("preview_sync"),
        "passed": exit_code == 0,
    }


def apply_staged_patch_bundle(
    bundle: dict[str, Any],
    *,
    root: Path,
) -> list[str]:
    if bundle.get("validation_verdict") != "GO":
        raise Tier2PatchStagingError(
            "cannot apply bundle without validation GO: "
            + str(bundle.get("validation_verdict"))
        )
    bundle_dir = root / str(bundle.get("_bundle_dir") or "")
    files_dir = bundle_dir / "files"
    if not files_dir.is_dir():
        raise Tier2PatchStagingError("staged bundle files directory missing")
    applied: list[str] = []
    for rel in bundle.get("proposed_changed_files") or []:
        normalized = str(rel).replace("\\", "/")
        staged = files_dir / normalized
        if not staged.is_file():
            raise Tier2PatchStagingError(f"staged file missing in bundle: {normalized}")
        target = root / normalized
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(staged, target)
        applied.append(normalized)
    return applied


def create_patch_bundle_from_working_tree(
    *,
    draft_ticket: Path | None = None,
    latest: bool = False,
    branch_name: str | None = None,
    root: Path | None = None,
    working_tree: WorkingTreeStatus | None = None,
    git_runner: Any | None = None,
) -> tuple[dict[str, Any], Path]:
    project_root = root or repo_root()
    draft_path, draft = _resolve_draft_ticket(
        draft_ticket=draft_ticket,
        latest=latest,
        root=project_root,
    )
    draft_reasons = validate_draft_ticket_for_tier2(draft, draft_path=draft_path, root=project_root)
    if draft_reasons:
        raise Tier2PatchStagingError("; ".join(draft_reasons[:5]))

    tree = working_tree or inspect_working_tree(project_root)
    draft_id = str(draft.get("id") or draft_path.stem)
    branch = branch_name or build_tier2_branch_name(draft_id)
    changed = collect_working_changed_files(tree, root=project_root, git_runner=git_runner)
    if not changed:
        raise Tier2PatchStagingError("no changed files to stage")

    file_contents: dict[str, str] = {}
    for rel in changed:
        path = project_root / rel
        if path.is_file():
            file_contents[rel] = path.read_text(encoding="utf-8")

    stats = _compute_diff_stats(root=project_root, changed_files=changed)
    bundle = build_patch_bundle_payload(
        draft=draft,
        draft_path=draft_path,
        branch_name=branch,
        changed_files=changed,
        root=project_root,
        diff_stats=stats,
    )
    validation = validate_patch_bundle(bundle, draft=draft, root=project_root)
    bundle["validation_verdict"] = validation["validation_verdict"]
    bundle["validation_reasons"] = validation["validation_reasons"]

    bundle_path = write_patch_bundle(bundle, file_contents=file_contents, root=project_root)
    validation_path = bundle_path.parent / "validation.json"
    validation_path.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    bundle["_bundle_path"] = _safe_rel(bundle_path, project_root)
    _maybe_sync_patch_staging_preview(bundle, bundle_path, root=project_root)
    return bundle, bundle_path


def auto_sync_patch_preview_enabled() -> bool:
    return os.environ.get("RGE_AUTO_SYNC_TIER2_PATCH_PREVIEW", "1").strip().casefold() not in {
        "0",
        "false",
        "no",
    }


def execute_safe_patch_staging_enabled() -> bool:
    return os.environ.get("RGE_EXECUTE_SAFE_PATCH_STAGING", "0").strip().casefold() in {
        "1",
        "true",
        "yes",
    }


def patch_staging_execute_safe_tree_ok(
    working_tree: WorkingTreeStatus,
    *,
    root: Path | None = None,
) -> bool:
    from rge.modules.release_governor import (
        assess_release_batch_working_tree,
        non_safe_dirty_paths,
    )

    if working_tree.clean:
        return True
    assessment = assess_release_batch_working_tree(
        working_tree,
        allow_controlled_dirty=True,
    )
    if assessment.get("status") == "unsafe_dirty":
        return False
    if assessment.get("status") in {"clean", "controlled_dirty"}:
        return True
    non_safe = non_safe_dirty_paths(working_tree.dirty_paths)
    tier2_prefixes = (
        "rge/",
        "tests/",
        "scripts/",
        "apps/public-site/",
        "docs/",
        "domain_packs/",
        "fixtures/",
    )
    return bool(non_safe) and all(
        any(path.startswith(prefix) for prefix in tier2_prefixes) for path in non_safe
    )


def _maybe_sync_patch_staging_preview(
    bundle: dict[str, Any],
    bundle_path: Path,
    *,
    root: Path,
) -> dict[str, Any] | None:
    if not auto_sync_patch_preview_enabled():
        return None
    verdict = str(bundle.get("validation_verdict") or "")
    if verdict not in {"GO", "PARTIAL", "NO-GO"}:
        return None
    from rge.modules.tier2_patch_staging_preview import refresh_tier2_patch_staging_preview

    return refresh_tier2_patch_staging_preview(
        bundle=bundle_path,
        sync_public=True,
        root=root,
    )


def run_execute_safe_patch_staging_hook(
    *,
    root: Path | None = None,
    working_tree: WorkingTreeStatus | None = None,
) -> dict[str, Any] | None:
    """Optional execute-safe hook: stage when controlled-dirty, validate, refresh Atlas preview."""
    if not execute_safe_patch_staging_enabled():
        return None

    from rge.modules.autonomy_tier_policy import action_allowed, summarize_tier_policy

    project_root = root or repo_root()
    tier = summarize_tier_policy()
    if tier.get("effective_tier", 0) < 2 or not action_allowed("create_feature_branch")[0]:
        return {"status": "skipped", "reason": "tier2 branch autonomy unavailable"}

    tree = working_tree or inspect_working_tree(project_root)
    if not patch_staging_execute_safe_tree_ok(tree, root=project_root):
        return {"status": "skipped", "reason": "working tree not clean or controlled-dirty"}

    steps: list[dict[str, Any]] = []
    changed = collect_working_changed_files(tree, root=project_root)
    latest_draft = latest_draft_ticket(root=project_root)
    draft_ready = latest_draft.get("status") == "available"

    if changed and draft_ready:
        try:
            bundle, bundle_path = create_patch_bundle_from_working_tree(
                latest=True,
                root=project_root,
                working_tree=tree,
            )
            steps.append(
                {
                    "step": "stage",
                    "status": "completed",
                    "validation_verdict": bundle.get("validation_verdict"),
                    "bundle_path": bundle.get("_bundle_path"),
                }
            )
        except Tier2PatchStagingError as exc:
            steps.append({"step": "stage", "status": "error", "detail": str(exc)})

    bundle_info = discover_latest_patch_bundle(root=project_root)
    if bundle_info.get("status") == "available" and bundle_info.get("bundle_path"):
        bundle_path = project_root / str(bundle_info["bundle_path"])
        try:
            validate_payload, _ = run_tier2_patch_staging_command(
                bundle=bundle_path,
                validate_only=True,
                root=project_root,
            )
            steps.append(
                {
                    "step": "validate",
                    "status": "completed",
                    "validation_verdict": validate_payload.get("validation_verdict"),
                }
            )
        except Tier2PatchStagingError as exc:
            steps.append({"step": "validate", "status": "error", "detail": str(exc)})

        from rge.modules.tier2_patch_staging_preview import refresh_tier2_patch_staging_preview

        try:
            preview_payload = refresh_tier2_patch_staging_preview(
                bundle=bundle_path,
                sync_public=True,
                root=project_root,
            )
            steps.append(
                {
                    "step": "preview_refresh",
                    "status": "completed",
                    "validation_verdict": preview_payload.get("verdict"),
                    "public_artifact_path": (preview_payload.get("sync") or {}).get(
                        "public_artifact_path"
                    ),
                }
            )
        except Exception as exc:  # noqa: BLE001 — operator hook must not crash execute-safe
            steps.append({"step": "preview_refresh", "status": "error", "detail": str(exc)})

    if not steps:
        return {"status": "skipped", "reason": "no staged changes or patch bundle"}
    return {"status": "completed", "steps": steps}


def inspect_tier2_patch_staging_status(
    *,
    root: Path | None = None,
    working_tree: WorkingTreeStatus | None = None,
) -> dict[str, Any]:
    project_root = root or repo_root()
    latest_draft = latest_draft_ticket(root=project_root)
    draft_id = latest_draft.get("draft_ticket_id")
    draft_path = latest_draft.get("draft_ticket_path")
    draft_available = latest_draft.get("status") == "available" and bool(draft_path)
    bundle_info = discover_latest_patch_bundle_for_draft(draft_id, root=project_root)
    verdict = bundle_info.get("validation_verdict")
    has_bundle = bundle_info.get("status") == "available"

    return {
        "status": "available",
        "latest_draft_ticket_path": draft_path,
        "latest_draft_ticket_id": draft_id,
        "latest_patch_bundle_path": bundle_info.get("bundle_path"),
        "latest_patch_validation_verdict": verdict,
        "patch_staging_required": require_tier2_patch_staging_enabled(),
        "tier2_patch_staging_recommended": draft_available and not has_bundle,
        "tier2_patch_validation_recommended": has_bundle and verdict in {None, "pending"},
        "tier2_patch_apply_recommended": has_bundle and verdict == "GO",
        "tier2_patch_fix_recommended": has_bundle and verdict in {"PARTIAL", "NO-GO"},
        "operator_commands": {
            "stage_latest": f"python {PATCH_STAGING_CLI_SCRIPT} --latest",
            "validate_bundle": f"python {PATCH_STAGING_CLI_SCRIPT} --bundle PATH --validate",
            "apply_bundle": f"python {PATCH_STAGING_CLI_SCRIPT} --bundle PATH --apply",
            "tier2_apply_staged": (
                "python scripts/run_tier2_local_implementation.py --latest "
                "--apply-staged PATH --require-staged-validation"
            ),
        },
    }


def patch_staging_metadata_for_batch(
    *,
    draft_id: str | None,
    root: Path | None = None,
) -> dict[str, Any]:
    info = discover_latest_patch_bundle_for_draft(draft_id, root=root)
    if info.get("status") != "available":
        return {"patch_bundle_path": None, "validation_verdict": None}
    project_root = root or repo_root()
    bundle = load_patch_bundle(project_root / str(info["bundle_path"]), root=project_root)
    diff = bundle.get("diff_summary") if isinstance(bundle.get("diff_summary"), dict) else {}
    return {
        "patch_bundle_path": info.get("bundle_path"),
        "validation_verdict": bundle.get("validation_verdict"),
        "diff_risk_class": bundle.get("risk_class"),
        "changed_file_count": diff.get("changed_file_count"),
        "lines_added": diff.get("lines_added"),
        "lines_removed": diff.get("lines_removed"),
        "safety_audit_required": bundle.get("safety_audit_required"),
    }


def run_tier2_patch_staging_command(
    *,
    draft_ticket: Path | None = None,
    latest: bool = False,
    bundle: Path | None = None,
    validate_only: bool = False,
    apply: bool = False,
    root: Path | None = None,
    git_runner: Any | None = None,
) -> tuple[dict[str, Any], int]:
    project_root = root or repo_root()
    if bundle is None and (latest or draft_ticket is not None):
        bundle_payload, bundle_path = create_patch_bundle_from_working_tree(
            draft_ticket=draft_ticket,
            latest=latest,
            root=project_root,
            git_runner=git_runner,
        )
        payload = {
            "status": "staged",
            "verdict": bundle_payload.get("validation_verdict"),
            "bundle_path": _safe_rel(bundle_path, project_root),
            "validation_verdict": bundle_payload.get("validation_verdict"),
            "validation_reasons": bundle_payload.get("validation_reasons") or [],
            "risk_class": bundle_payload.get("risk_class"),
            "changed_file_count": (bundle_payload.get("diff_summary") or {}).get("changed_file_count"),
            "safety_audit_required": bundle_payload.get("safety_audit_required"),
        }
        exit_code = 0 if bundle_payload.get("validation_verdict") == "GO" else 1
        return payload, exit_code

    if bundle is None:
        raise Tier2PatchStagingError("requires --latest, --draft-ticket, or --bundle PATH")

    bundle_payload = load_patch_bundle(bundle, root=project_root)
    draft_path = project_root / str(bundle_payload["draft_ticket_path"])
    draft = json.loads(draft_path.read_text(encoding="utf-8"))

    if validate_only or (not apply and bundle_payload.get("validation_verdict") == "pending"):
        validation = validate_patch_bundle(bundle_payload, draft=draft, root=project_root)
        bundle_payload["validation_verdict"] = validation["validation_verdict"]
        bundle_payload["validation_reasons"] = validation["validation_reasons"]
        bundle_file = project_root / str(bundle_payload["_bundle_path"])
        bundle_file.write_text(json.dumps(bundle_payload, indent=2) + "\n", encoding="utf-8")
        (bundle_file.parent / "validation.json").write_text(
            json.dumps(validation, indent=2) + "\n",
            encoding="utf-8",
        )
        preview_sync = _maybe_sync_patch_staging_preview(
            bundle_payload,
            bundle_file,
            root=project_root,
        )
        payload = {
            "status": "validated",
            "verdict": validation["validation_verdict"],
            "bundle_path": bundle_payload.get("_bundle_path"),
            "validation_verdict": validation["validation_verdict"],
            "validation_reasons": validation["validation_reasons"],
            "preview_sync": preview_sync,
        }
        return payload, 0 if validation["passed"] else 1

    if apply:
        applied = apply_staged_patch_bundle(bundle_payload, root=project_root)
        payload = {
            "status": "applied",
            "verdict": "GO",
            "bundle_path": bundle_payload.get("_bundle_path"),
            "applied_files": applied,
        }
        return payload, 0

    payload = {
        "status": "available",
        "verdict": bundle_payload.get("validation_verdict"),
        "bundle_path": bundle_payload.get("_bundle_path"),
    }
    return payload, 0


def public_safe_summary(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "status",
        "verdict",
        "bundle_path",
        "validation_verdict",
        "validation_reasons",
        "risk_class",
        "changed_file_count",
        "safety_audit_required",
        "applied_files",
        "stop_reason",
        "preview_sync",
    }
    return {key: payload[key] for key in allowed if key in payload}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tier 2 patch staging and diff validation.")
    parser.add_argument("--draft-ticket", type=Path, default=None)
    parser.add_argument("--latest", action="store_true")
    parser.add_argument("--bundle", type=Path, default=None)
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        payload, exit_code = run_tier2_patch_staging_command(
            draft_ticket=args.draft_ticket,
            latest=args.latest,
            bundle=args.bundle,
            validate_only=args.validate,
            apply=args.apply,
            root=args.root,
        )
    except (Tier2PatchStagingError, Tier2ImplementationError) as exc:
        print(json.dumps({"status": "error", "verdict": "NO-GO", "stop_reason": str(exc)}, indent=2))
        return 1
    print(json.dumps(public_safe_summary(payload), indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
