"""Assemble release batch JSON from draft tickets, branch state, and test artifacts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rge.modules.autonomy_tier_policy import summarize_tier_policy
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.autonomous_synthesis_governor import _safe_rel, utc_now_iso
from rge.modules.instruction_packet_ticket_draft import latest_draft_ticket
from rge.modules.operator_loop import inspect_working_tree, latest_agent_report
from rge.modules.release_governor import (
    BATCH_SCHEMA_VERSION,
    ReleaseGovernorError,
    assess_release_batch_working_tree,
    release_batch_dir,
    sync_public_release_governor_artifact,
    validate_batch_schema,
)
from rge.modules.principal_audit_gate import repo_root
from rge.subprocess_capture import run_captured

ASSEMBLER_SCHEMA_VERSION = "release_batch_assembler_v0.1.0"
DEFAULT_TEST_RESULTS_REL = Path("data/operator/release_batch_test_results_latest.json")
DEFAULT_SAFETY_RESULTS_REL = Path("data/operator/release_batch_safety_results_latest.json")
ASSEMBLER_CLI_SCRIPT = "scripts/run_release_batch_assembler.py"

_FORBIDDEN_CHANGED_FILE_PREFIXES = (
    ".env",
    ".env.local",
    "data/sources/",
    "fixtures/sources/",
)
_FORBIDDEN_CHANGED_FILE_NAMES = frozenset({".env", ".env.local", ".env.example"})


def _filter_batch_changed_files(paths: list[str]) -> list[str]:
    filtered: list[str] = []
    for raw in paths:
        normalized = raw.replace("\\", "/").strip()
        if not normalized:
            continue
        base = Path(normalized).name
        if base in _FORBIDDEN_CHANGED_FILE_NAMES:
            continue
        if any(normalized.startswith(prefix) for prefix in _FORBIDDEN_CHANGED_FILE_PREFIXES):
            continue
        filtered.append(normalized)
    return filtered


class ReleaseBatchAssemblerError(RuntimeError):
    """Raised when batch assembly inputs or validation fail."""


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _batch_name(batch_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", batch_id).strip("-") or "batch"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}_{safe}.json"


def _resolve_draft_ticket(
    *,
    draft_ticket: Path | None,
    latest: bool,
    root: Path,
) -> tuple[Path, dict[str, Any]]:
    if draft_ticket is not None:
        path = draft_ticket if draft_ticket.is_absolute() else root / draft_ticket
    elif latest:
        discovery = latest_draft_ticket(root=root)
        if discovery.get("status") != "available":
            raise ReleaseBatchAssemblerError("no draft ticket found (--latest)")
        path = root / str(discovery["draft_ticket_path"])
    else:
        raise ReleaseBatchAssemblerError("requires --draft-ticket PATH or --latest")
    payload = _load_json(path)
    if payload is None:
        raise ReleaseBatchAssemblerError(f"draft ticket unreadable: {path}")
    return path, payload


def _git_value(argv: list[str], *, root: Path) -> str | None:
    try:
        completed = run_captured(argv, cwd=str(root))
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value or None


def _collect_changed_files(*, root: Path, explicit: list[str] | None) -> list[str]:
    if explicit:
        return [item.replace("\\", "/") for item in explicit if item.strip()]
    from_status = _git_value(["git", "diff", "--name-only", "HEAD"], root=root)
    if from_status:
        return [line.strip().replace("\\", "/") for line in from_status.splitlines() if line.strip()]
    porcelain = inspect_working_tree(root).dirty_paths
    changed: list[str] = []
    for line in porcelain:
        path = line[3:].strip() if len(line) > 3 else line.strip()
        if path:
            changed.append(path.replace("\\", "/"))
    return changed


def _resolve_agent_reports(*, root: Path, explicit: list[str] | None) -> list[str]:
    if explicit:
        return explicit
    reports: list[str] = []
    latest_md = latest_agent_report(root=root)
    if latest_md:
        reports.append(latest_md)
        stem = Path(latest_md).stem
        latest_json = root / "agent_reports" / f"{stem}-latest.json"
        if not latest_json.is_file():
            candidates = sorted(
                (root / "agent_reports").glob(f"{stem}*.json"),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
            if candidates:
                latest_json = candidates[0]
        if latest_json.is_file():
            reports.append(_safe_rel(latest_json, root))
    return reports


def _resolve_test_results(
    *,
    root: Path,
    test_results: Path | None,
    draft: dict[str, Any],
) -> dict[str, Any]:
    if test_results is not None:
        path = test_results if test_results.is_absolute() else root / test_results
        payload = _load_json(path)
        if payload is None:
            raise ReleaseBatchAssemblerError(f"test results unreadable: {path}")
        return payload
    default_path = root / DEFAULT_TEST_RESULTS_REL
    payload = _load_json(default_path) if default_path.is_file() else None
    if payload is not None:
        return payload
    commands = [
        str(item)
        for item in (draft.get("test_plan") or [])
        if isinstance(item, str) and item.strip()
    ]
    return {
        "passed": False,
        "commands": commands,
        "detail": "Attach test results via --test-results or release_batch_test_results_latest.json",
    }


def _resolve_safety_results(*, root: Path, safety_results: Path | None) -> dict[str, Any]:
    if safety_results is not None:
        path = safety_results if safety_results.is_absolute() else root / safety_results
        payload = _load_json(path)
        if payload is None:
            raise ReleaseBatchAssemblerError(f"safety results unreadable: {path}")
        return payload
    default_path = root / DEFAULT_SAFETY_RESULTS_REL
    payload = _load_json(default_path) if default_path.is_file() else None
    if payload is not None:
        return payload
    return {
        "status": "pending",
        "detail": "Run safety audit and write release_batch_safety_results_latest.json before governor",
    }


def assemble_release_batch_payload(
    *,
    draft_ticket: Path | None = None,
    latest: bool = False,
    branch: str | None = None,
    commit_hash: str | None = None,
    test_results: Path | None = None,
    safety_results: Path | None = None,
    changed_files: list[str] | None = None,
    reports: list[str] | None = None,
    allow_controlled_dirty: bool = False,
    batch_id: str | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = root or repo_root()
    draft_path, draft = _resolve_draft_ticket(
        draft_ticket=draft_ticket,
        latest=latest,
        root=project_root,
    )
    tree = inspect_working_tree(project_root)
    tree_assessment = assess_release_batch_working_tree(
        tree,
        allow_controlled_dirty=allow_controlled_dirty,
    )
    if tree_assessment.get("blocks_batch_assembly"):
        reasons: list[str] = []
        if tree_assessment.get("unsafe_paths"):
            reasons.append(
                "unsafe dirty paths: " + ", ".join(tree_assessment["unsafe_paths"][:5])
            )
        if tree_assessment.get("non_safe_dirty_paths"):
            reasons.append(
                "non-operator dirty paths: "
                + ", ".join(tree_assessment["non_safe_dirty_paths"][:5])
            )
        detail = "; ".join(reasons) if reasons else "working tree blocks batch assembly"
        raise ReleaseBatchAssemblerError(detail)

    resolved_branch = branch or tree.branch
    if not resolved_branch:
        raise ReleaseBatchAssemblerError("could not resolve git branch")
    resolved_commit = commit_hash or _git_value(["git", "rev-parse", "HEAD"], root=project_root)
    if not resolved_commit:
        raise ReleaseBatchAssemblerError("could not resolve commit hash")

    draft_id = str(draft.get("id") or draft_path.stem)
    instruction_ref = draft.get("source_instruction_packet")
    instruction_refs = [str(instruction_ref)] if instruction_ref else []

    test_payload = _resolve_test_results(
        root=project_root,
        test_results=test_results,
        draft=draft,
    )
    safety_payload = _resolve_safety_results(
        root=project_root,
        safety_results=safety_results,
    )
    changed = _filter_batch_changed_files(
        _collect_changed_files(root=project_root, explicit=changed_files)
    )
    report_paths = _resolve_agent_reports(root=project_root, explicit=reports)

    from rge.modules.tier2_patch_staging import patch_staging_metadata_for_batch

    patch_meta = patch_staging_metadata_for_batch(draft_id=draft_id, root=project_root)

    batch = {
        "schema_version": BATCH_SCHEMA_VERSION,
        "batch_id": batch_id or f"batch-{draft_id}",
        "status": "candidate",
        "created_at": utc_now_iso(),
        "draft_ticket_ids": [draft_id],
        "instruction_packet_refs": instruction_refs,
        "branch_names": [resolved_branch],
        "commit_hashes": [resolved_commit],
        "test_results": test_payload,
        "safety_results": safety_payload,
        "reports": report_paths,
        "rollback_plan": str(
            draft.get("rollback_plan")
            or "Revert feature branch commits and delete the release batch artifact."
        ),
        "proposed_release_summary": str(
            draft.get("title") or f"Release batch for {draft_id}"
        ),
        "changed_files": changed,
        "allow_controlled_dirty": allow_controlled_dirty or tree_assessment.get("controlled_dirty"),
        "candidate_metadata": {
            "source_draft_ticket_path": _safe_rel(draft_path, project_root),
            "source_instruction_packet_path": (
                str(instruction_ref) if instruction_ref else None
            ),
            "branch_name": resolved_branch,
            "commit_hash": resolved_commit,
            "changed_files": changed,
            "reports": report_paths,
            "rollback_plan": str(
                draft.get("rollback_plan")
                or "Revert feature branch commits and delete the release batch artifact."
            ),
            "test_results_passed": bool(test_payload.get("passed")),
            "safety_results_status": str(safety_payload.get("status") or "pending"),
            "autonomy_tier_required_for_next_action": 0,
            "next_release_action": "release_governor_dry_run",
            "autonomy_tier": summarize_tier_policy().get("effective_tier"),
            "patch_staging": patch_meta,
        },
        "assembler_metadata": {
            "schema_version": ASSEMBLER_SCHEMA_VERSION,
            "draft_ticket_path": _safe_rel(draft_path, project_root),
            "assembled_at": utc_now_iso(),
        },
    }
    errors = validate_batch_schema(batch)
    if errors:
        raise ReleaseBatchAssemblerError("assembled batch invalid: " + "; ".join(errors[:5]))
    violations = assert_no_private_fields({"release_batch": batch})
    if violations:
        raise ReleaseBatchAssemblerError("assembled batch blocked: " + "; ".join(violations[:5]))
    return batch


def run_release_batch_assembler_command(
    *,
    draft_ticket: Path | None = None,
    latest: bool = False,
    dry_run: bool = False,
    out_dir: Path | None = None,
    test_results: Path | None = None,
    safety_results: Path | None = None,
    allow_controlled_dirty: bool = False,
    sync_public: bool = True,
    root: Path | None = None,
) -> tuple[dict[str, Any], int]:
    project_root = root or repo_root()
    batch = assemble_release_batch_payload(
        draft_ticket=draft_ticket,
        latest=latest,
        test_results=test_results,
        safety_results=safety_results,
        allow_controlled_dirty=allow_controlled_dirty,
        root=project_root,
    )
    batch_path: str | None = None
    if not dry_run:
        target_dir = out_dir or release_batch_dir(root=project_root)
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / _batch_name(str(batch["batch_id"]))
        path.write_text(json.dumps(batch, indent=2) + "\n", encoding="utf-8")
        batch_path = _safe_rel(path, project_root)

    payload = {
        "status": "dry_run" if dry_run else "completed",
        "verdict": "GO",
        "batch_id": batch.get("batch_id"),
        "batch_path": batch_path,
        "draft_ticket_ids": batch.get("draft_ticket_ids") or [],
        "branch_names": batch.get("branch_names") or [],
        "commit_hashes": batch.get("commit_hashes") or [],
        "test_results_passed": (batch.get("test_results") or {}).get("passed"),
        "safety_results_status": (batch.get("safety_results") or {}).get("status"),
        "changed_files_count": len(batch.get("changed_files") or []),
        "reports_count": len(batch.get("reports") or []),
        "dry_run": dry_run,
    }
    if sync_public and not dry_run:
        payload["atlas_refresh"] = sync_public_release_governor_artifact(root=project_root)
    return payload, 0


def public_safe_summary(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "status",
        "verdict",
        "batch_id",
        "batch_path",
        "draft_ticket_ids",
        "branch_names",
        "commit_hashes",
        "test_results_passed",
        "safety_results_status",
        "changed_files_count",
        "reports_count",
        "dry_run",
        "detail",
    }
    return {key: payload[key] for key in allowed if key in payload}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Assemble a release batch JSON from draft ticket and branch state.",
    )
    parser.add_argument("--draft-ticket", type=Path, default=None)
    parser.add_argument("--latest", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--test-results", type=Path, default=None)
    parser.add_argument("--safety-results", type=Path, default=None)
    parser.add_argument("--allow-controlled-dirty", action="store_true")
    parser.add_argument("--no-sync-public", action="store_true")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        payload, exit_code = run_release_batch_assembler_command(
            draft_ticket=args.draft_ticket,
            latest=args.latest,
            dry_run=args.dry_run,
            out_dir=args.out_dir,
            test_results=args.test_results,
            safety_results=args.safety_results,
            allow_controlled_dirty=args.allow_controlled_dirty,
            sync_public=not args.no_sync_public,
            root=args.root,
        )
    except ReleaseBatchAssemblerError as exc:
        print(json.dumps({"status": "error", "verdict": "NO-GO", "detail": str(exc)}, indent=2))
        return 1
    print(json.dumps(public_safe_summary(payload), indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
