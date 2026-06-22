"""Tier 2 local branch implementation runner for draft tickets.

Creates local feature branches and commits only. Never push, merge, publish,
promote canonical tickets, reset circuit breaker, or call paid/live network APIs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any, Callable

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.autonomy_tier_policy import action_allowed, summarize_tier_policy
from rge.modules.autonomous_synthesis_governor import (
    FORBIDDEN_ACTION_PATTERNS,
    FORBIDDEN_GATE_WEAKENING_PATTERNS,
    _safe_rel,
    dirty_paths_in_unsafe_paths,
    load_circuit_breaker,
    utc_now_iso,
)
from rge.modules.instruction_packet_ticket_draft import latest_draft_ticket
from rge.modules.operator_loop import WorkingTreeStatus, inspect_working_tree
from rge.modules.principal_audit_gate import repo_root
from rge.modules.release_batch_assembler import (
    DEFAULT_SAFETY_RESULTS_REL,
    DEFAULT_TEST_RESULTS_REL,
    run_release_batch_assembler_command,
)
from rge.modules.release_governor import (
    assess_release_batch_working_tree,
    discover_release_batch_for_draft,
)
from rge.modules.safety_auditor import run_safety_audit
from rge.subprocess_capture import run_captured

RUNNER_SCHEMA_VERSION = "tier2_local_implementation_v0.1.0"
TIER2_CLI_SCRIPT = "scripts/run_tier2_local_implementation.py"
TIER2_BRANCH_PREFIX = "phase-3/tier2-"

_FORBIDDEN_DRAFT_COMMAND_PATTERNS = (
    re.compile(r"\bgit\s+push\b", re.IGNORECASE),
    re.compile(r"\bgit\s+merge\b", re.IGNORECASE),
    re.compile(r"\bexport-public\b", re.IGNORECASE),
    re.compile(r"\bpromote(?:\s+\w+){0,3}\s+(?:ticket|queue)\b", re.IGNORECASE),
    re.compile(r"\breset-circuit-breaker\b", re.IGNORECASE),
)

_ALLOWED_IMPLEMENTATION_PREFIXES = (
    "rge/",
    "tests/",
    "docs/",
    "agent_reports/",
    "apps/public-site/",
    "scripts/",
    "data/operator/",
    "fixtures/",
    "domain_packs/",
)

_FORBIDDEN_IMPLEMENTATION_PATHS = (
    "tickets/TICKET_QUEUE.md",
    ".env",
    ".env.local",
    "data/sources/",
    "fixtures/sources/",
)

_PUBLIC_SURFACE_PREFIXES = (
    "apps/public-site/public/",
    "apps/public-site/app/",
    "apps/public-site/lib/",
)

GitCommandRunner = Callable[[list[str], Path], subprocess.CompletedProcess[str]]
CommandRunner = Callable[[list[str], Path, dict[str, str]], subprocess.CompletedProcess[str]]


class Tier2ImplementationError(RuntimeError):
    """Raised when Tier 2 implementation gates fail."""


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def default_git_runner(argv: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    lowered = " ".join(argv).lower()
    for forbidden in ("push", "merge", "publish", "reset-circuit-breaker"):
        if forbidden in lowered:
            raise Tier2ImplementationError(f"forbidden git/command blocked: {forbidden}")
    return run_captured(argv, cwd=str(root))


def build_tier2_branch_name(draft_id: str, *, override: str | None = None) -> str:
    if override:
        safe = re.sub(r"[^A-Za-z0-9/_.-]+", "-", override.strip()).strip("-")
        if not safe.startswith(TIER2_BRANCH_PREFIX):
            if "/" not in safe:
                safe = f"{TIER2_BRANCH_PREFIX}{safe}"
        return safe[:120]
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", draft_id).strip("-") or "draft"
    return f"{TIER2_BRANCH_PREFIX}{slug}"[:120]


def _normalize_dirty_path(raw: str) -> str:
    path = raw[3:].strip() if len(raw) > 3 and raw[:2].strip() else raw.strip()
    return path.replace("\\", "/")


def collect_working_changed_files(
    working_tree: WorkingTreeStatus,
    *,
    root: Path,
    git_runner: GitCommandRunner | None = None,
) -> list[str]:
    runner = git_runner or default_git_runner
    from_status = runner(["git", "diff", "--name-only", "HEAD"], root)
    if from_status.returncode == 0 and from_status.stdout.strip():
        return [
            line.strip().replace("\\", "/")
            for line in from_status.stdout.splitlines()
            if line.strip()
        ]
    return [_normalize_dirty_path(line) for line in working_tree.dirty_paths if line.strip()]


def _branch_has_commits_ahead_of_main(
    *,
    root: Path,
    branch: str | None,
    git_runner: GitCommandRunner | None = None,
) -> bool:
    if not branch or branch in {"main", "master"}:
        return False
    runner = git_runner or default_git_runner
    for base in ("main", "master"):
        completed = runner(["git", "rev-list", "--count", f"{base}..HEAD"], root)
        if completed.returncode == 0 and completed.stdout.strip().isdigit():
            return int(completed.stdout.strip()) > 0
    return False


def is_tier2_implementation_branch(branch: str | None, draft_id: str | None = None) -> bool:
    if not branch:
        return False
    if branch.startswith(TIER2_BRANCH_PREFIX):
        return True
    if draft_id:
        slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", draft_id).strip("-")
        return slug in branch
    return False


def validate_draft_ticket_for_tier2(
    draft: dict[str, Any],
    *,
    draft_path: Path,
    root: Path,
) -> list[str]:
    reasons: list[str] = []
    verdict = str(draft.get("governor_verdict") or "").upper()
    if verdict in {"PARTIAL", "NO-GO"}:
        reasons.append(f"draft ticket governor verdict is {verdict}")
    elif verdict != "GO":
        reasons.append("draft ticket is not from a GO governor output")

    validation = draft.get("validation") if isinstance(draft.get("validation"), dict) else {}
    if validation and not validation.get("passed"):
        reasons.extend(str(item) for item in (validation.get("reasons") or [])[:3])
        if not validation.get("reasons"):
            reasons.append("draft ticket validation did not pass")

    blob = json.dumps(draft, sort_keys=True)
    for pattern in (*FORBIDDEN_ACTION_PATTERNS, *FORBIDDEN_GATE_WEAKENING_PATTERNS, *_FORBIDDEN_DRAFT_COMMAND_PATTERNS):
        if pattern.search(blob):
            reasons.append("draft ticket contains forbidden push/merge/publish/promote language")
            break

    instruction_ref = draft.get("source_instruction_packet")
    if instruction_ref:
        packet_path = root / str(instruction_ref)
        if packet_path.is_file():
            packet_text = packet_path.read_text(encoding="utf-8")
            for pattern in (*FORBIDDEN_ACTION_PATTERNS, *_FORBIDDEN_DRAFT_COMMAND_PATTERNS):
                if pattern.search(packet_text):
                    reasons.append("instruction packet contains forbidden action language")
                    break
        else:
            reasons.append(f"instruction packet missing: {instruction_ref}")

    violations = assert_no_private_fields({"draft_ticket": draft})
    if violations:
        reasons.append("draft ticket blocked by private-field scan")

    if not draft.get("test_plan"):
        reasons.append("draft ticket missing test_plan commands")

    if not str(draft.get("rollback_plan") or "").strip():
        reasons.append("draft ticket missing rollback_plan")

    if not draft_path.is_file():
        reasons.append(f"draft ticket file missing: {draft_path}")

    return reasons


def validate_implementation_paths(
    paths: list[str],
    *,
    draft: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []
    expected = {
        str(item).replace("\\", "/")
        for item in (draft.get("expected_files") or [])
        if str(item).strip()
    }
    for raw in paths:
        normalized = raw.replace("\\", "/").strip()
        if not normalized:
            continue
        if normalized in _FORBIDDEN_IMPLEMENTATION_PATHS or any(
            normalized.startswith(prefix) for prefix in _FORBIDDEN_IMPLEMENTATION_PATHS
        ):
            reasons.append(f"forbidden implementation path: {normalized}")
            continue
        if expected and normalized not in expected:
            if not any(normalized.startswith(prefix) for prefix in _ALLOWED_IMPLEMENTATION_PREFIXES):
                reasons.append(f"path outside allowed implementation prefixes: {normalized}")
        elif not expected:
            if not any(normalized.startswith(prefix) for prefix in _ALLOWED_IMPLEMENTATION_PREFIXES):
                reasons.append(f"path outside allowed implementation prefixes: {normalized}")
    return reasons


def _touches_public_surface(paths: list[str]) -> bool:
    return any(
        path.replace("\\", "/").startswith(prefix)
        for path in paths
        for prefix in _PUBLIC_SURFACE_PREFIXES
    )


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
            raise Tier2ImplementationError("no draft ticket found (--latest)")
        path = root / str(discovery["draft_ticket_path"])
    else:
        raise Tier2ImplementationError("requires --draft-ticket PATH or --latest")
    payload = _load_json(path)
    if payload is None:
        raise Tier2ImplementationError(f"draft ticket unreadable: {path}")
    return path, payload


def run_test_plan_commands(
    commands: list[str],
    *,
    root: Path,
    command_runner: CommandRunner | None = None,
) -> dict[str, Any]:
    env = {**os.environ, "RGE_LLM_MODE": "mock", "RGE_ALLOW_LIVE_LLM": "0"}
    results: list[dict[str, Any]] = []
    for command in commands:
        if not str(command).strip():
            continue
        lowered = command.lower()
        if any(token in lowered for token in ("git push", "git merge", "export-public", "reset-circuit-breaker")):
            return {
                "passed": False,
                "commands": commands,
                "detail": f"forbidden test command: {command}",
                "results": results,
            }
        if command_runner is not None:
            argv = ["test-runner", command]
            completed = command_runner(argv, root, env)
        elif os.name == "nt":
            completed = run_captured(
                ["powershell", "-NoProfile", "-Command", command],
                cwd=str(root),
                env=env,
            )
        else:
            completed = run_captured(shlex.split(command), cwd=str(root), env=env)
        row = {
            "command": command,
            "returncode": completed.returncode,
            "passed": completed.returncode == 0,
        }
        results.append(row)
        if completed.returncode != 0:
            return {
                "passed": False,
                "commands": commands,
                "detail": f"test command failed: {command}",
                "results": results,
            }
    return {
        "passed": bool(results),
        "commands": commands,
        "detail": "all test_plan commands passed",
        "results": results,
    }


def inspect_tier2_implementation_status(
    *,
    root: Path | None = None,
    working_tree: WorkingTreeStatus | None = None,
    git_runner: GitCommandRunner | None = None,
) -> dict[str, Any]:
    project_root = root or repo_root()
    tree = working_tree or inspect_working_tree(project_root)
    tier = summarize_tier_policy()
    latest_draft = latest_draft_ticket(root=project_root)
    draft_id = latest_draft.get("draft_ticket_id")
    draft_path = latest_draft.get("draft_ticket_path")
    draft_available = latest_draft.get("status") == "available" and bool(draft_path)
    circuit = load_circuit_breaker(root=project_root)
    circuit_open = circuit.get("status") == "open"
    tree_assessment = assess_release_batch_working_tree(tree)
    tier_allowed, tier_reason = action_allowed("create_feature_branch")
    on_impl_branch = is_tier2_implementation_branch(tree.branch, draft_id)
    has_impl_commit = _branch_has_commits_ahead_of_main(
        root=project_root,
        branch=tree.branch,
        git_runner=git_runner,
    )
    batch_for_draft = discover_release_batch_for_draft(draft_id, root=project_root)
    blocked = bool(
        circuit_open
        or tree_assessment.get("blocks_batch_assembly")
        or not tier_allowed
    )
    block_reasons: list[str] = []
    if circuit_open:
        block_reasons.append("circuit breaker open")
    if not tier_allowed:
        block_reasons.append(tier_reason)
    if tree_assessment.get("unsafe_paths"):
        block_reasons.append("unsafe dirty paths present")

    return {
        "status": "available",
        "autonomy_tier": tier,
        "tier2_allowed": tier_allowed,
        "latest_draft_ticket_path": draft_path,
        "latest_draft_ticket_id": draft_id,
        "implementation_branch": tree.branch if on_impl_branch else None,
        "on_implementation_branch": on_impl_branch,
        "has_implementation_commit": has_impl_commit,
        "tier2_implementation_recommended": (
            draft_available and not on_impl_branch and tier_allowed and not blocked
        ),
        "tier2_continue_recommended": (
            draft_available and on_impl_branch and not has_impl_commit and not blocked
        ),
        "tier2_batch_refresh_recommended": (
            draft_available
            and on_impl_branch
            and has_impl_commit
            and batch_for_draft.get("status") != "available"
            and not blocked
        ),
        "tier2_blocked": blocked,
        "tier2_block_reasons": block_reasons,
        "operator_commands": {
            "run_tier2_latest": f"python {TIER2_CLI_SCRIPT} --latest",
            "run_tier2_dry_run": f"python {TIER2_CLI_SCRIPT} --latest --dry-run",
            "assemble_batch": "python scripts/run_release_batch_assembler.py --latest",
        },
    }


def run_tier2_local_implementation_command(
    *,
    draft_ticket: Path | None = None,
    latest: bool = False,
    dry_run: bool = False,
    branch_name: str | None = None,
    allow_controlled_dirty: bool = False,
    no_commit: bool = False,
    refresh_batch: bool = True,
    stage_only: bool = False,
    apply_staged: Path | None = None,
    require_staged_validation: bool = False,
    root: Path | None = None,
    git_runner: GitCommandRunner | None = None,
    command_runner: CommandRunner | None = None,
) -> tuple[dict[str, Any], int]:
    from rge.modules.tier2_patch_staging import (
        apply_staged_patch_bundle,
        load_patch_bundle,
        require_tier2_patch_staging_enabled,
        create_patch_bundle_from_working_tree,
        discover_latest_patch_bundle_for_draft,
    )

    project_root = root or repo_root()
    runner = git_runner or default_git_runner
    require_staged = require_staged_validation or require_tier2_patch_staging_enabled()
    draft_path, draft = _resolve_draft_ticket(
        draft_ticket=draft_ticket,
        latest=latest,
        root=project_root,
    )
    draft_id = str(draft.get("id") or draft_path.stem)
    rel_draft_path = _safe_rel(draft_path, project_root)

    payload: dict[str, Any] = {
        "schema_version": RUNNER_SCHEMA_VERSION,
        "status": "blocked",
        "verdict": "NO-GO",
        "draft_ticket_path": rel_draft_path,
        "draft_ticket_id": draft_id,
        "branch_name": None,
        "files_changed": [],
        "tests_run": [],
        "test_results_passed": None,
        "safety_audit_status": None,
        "commit_hash": None,
        "release_batch_path": None,
        "patch_bundle_path": None,
        "stop_reason": None,
        "dry_run": dry_run,
        "no_commit": no_commit,
        "stage_only": stage_only,
        "require_staged_validation": require_staged,
        "autonomy_tier_used": summarize_tier_policy().get("effective_tier"),
    }

    circuit = load_circuit_breaker(root=project_root)
    if circuit.get("status") == "open":
        payload["stop_reason"] = (
            "autonomy circuit breaker is open: "
            + str(circuit.get("latest_stop_reason") or "unknown")
        )
        return payload, 1

    tier_ok, tier_reason = action_allowed("create_feature_branch")
    if not tier_ok:
        payload["stop_reason"] = tier_reason
        return payload, 1

    draft_reasons = validate_draft_ticket_for_tier2(draft, draft_path=draft_path, root=project_root)
    if draft_reasons:
        payload["stop_reason"] = "; ".join(draft_reasons[:5])
        return payload, 1

    tree = inspect_working_tree(project_root)
    tree_assessment = assess_release_batch_working_tree(
        tree,
        allow_controlled_dirty=allow_controlled_dirty,
    )
    if tree_assessment.get("blocks_batch_assembly") and not dry_run and not allow_controlled_dirty:
        payload["stop_reason"] = "working tree blocked for tier2 implementation"
        if tree_assessment.get("unsafe_paths"):
            payload["stop_reason"] += ": " + ", ".join(tree_assessment["unsafe_paths"][:3])
        return payload, 1

    target_branch = build_tier2_branch_name(draft_id, override=branch_name)
    payload["branch_name"] = target_branch

    if stage_only:
        bundle_payload, bundle_path = create_patch_bundle_from_working_tree(
            draft_ticket=draft_path,
            branch_name=target_branch,
            root=project_root,
            working_tree=tree,
            git_runner=runner,
        )
        payload.update(
            {
                "status": "staged",
                "verdict": bundle_payload.get("validation_verdict"),
                "patch_bundle_path": _safe_rel(bundle_path, project_root),
                "files_changed": bundle_payload.get("proposed_changed_files") or [],
                "stop_reason": None if bundle_payload.get("validation_verdict") == "GO" else "; ".join(
                    bundle_payload.get("validation_reasons") or []
                )[:200],
            }
        )
        exit_code = 0 if bundle_payload.get("validation_verdict") == "GO" else 1
        return payload, exit_code

    if apply_staged is not None:
        bundle = load_patch_bundle(apply_staged, root=project_root)
        if bundle.get("validation_verdict") != "GO":
            payload["stop_reason"] = (
                "staged patch validation is not GO: " + str(bundle.get("validation_verdict"))
            )
            return payload, 1
        apply_staged_patch_bundle(bundle, root=project_root)
        payload["patch_bundle_path"] = bundle.get("_bundle_path")
        tree = inspect_working_tree(project_root)
        changed_files = collect_working_changed_files(tree, root=project_root, git_runner=runner)
    else:
        changed_files = collect_working_changed_files(tree, root=project_root, git_runner=runner)

    path_reasons = validate_implementation_paths(changed_files, draft=draft) if changed_files else []
    if path_reasons:
        payload["stop_reason"] = "; ".join(path_reasons[:5])
        return payload, 1

    if dry_run:
        payload.update(
            {
                "status": "dry_run",
                "verdict": "GO",
                "tests_run": list(draft.get("test_plan") or []),
                "stop_reason": None,
            }
        )
        return payload, 0

    on_target = tree.branch == target_branch
    if not on_target and tree.branch not in {None, "main", "master"} and not is_tier2_implementation_branch(tree.branch, draft_id):
        payload["stop_reason"] = (
            f"current branch {tree.branch!r} is unsafe for tier2; checkout main or pass --branch-name"
        )
        return payload, 1

    if not on_target:
        branch_exists = runner(["git", "show-ref", "--verify", f"refs/heads/{target_branch}"], project_root)
        if branch_exists.returncode == 0:
            checkout = runner(["git", "checkout", target_branch], project_root)
        else:
            checkout = runner(["git", "checkout", "-b", target_branch], project_root)
        if checkout.returncode != 0:
            payload["stop_reason"] = f"git checkout failed for {target_branch}"
            return payload, 1
        tree = inspect_working_tree(project_root)
        changed_files = collect_working_changed_files(tree, root=project_root, git_runner=runner)

    if not changed_files:
        payload["stop_reason"] = (
            "no implementation changes detected; apply draft work on the feature branch first"
        )
        payload["status"] = "pending_changes"
        payload["verdict"] = "PARTIAL"
        return payload, 1

    if require_staged:
        staged = discover_latest_patch_bundle_for_draft(draft_id, root=project_root)
        if staged.get("status") != "available" or staged.get("validation_verdict") != "GO":
            payload["stop_reason"] = (
                "tier2 patch staging validation GO required before commit "
                f"(RGE_REQUIRE_TIER2_PATCH_STAGING={require_tier2_patch_staging_enabled()})"
            )
            return payload, 1
        payload["patch_bundle_path"] = staged.get("bundle_path")

    test_results = run_test_plan_commands(
        [str(item) for item in (draft.get("test_plan") or []) if str(item).strip()],
        root=project_root,
        command_runner=command_runner,
    )
    payload["tests_run"] = test_results.get("commands") or []
    payload["test_results_passed"] = test_results.get("passed")
    if not test_results.get("passed"):
        payload["stop_reason"] = str(test_results.get("detail") or "tests failed")
        return payload, 1

    safety_status = "skipped"
    if _touches_public_surface(changed_files):
        audit = run_safety_audit(audit_type="full", root=project_root)
        safety_status = str(audit.get("status") or "fail")
        payload["safety_audit_status"] = safety_status
        if safety_status != "pass":
            payload["stop_reason"] = "safety audit failed after public-surface changes"
            return payload, 1
    else:
        payload["safety_audit_status"] = safety_status

    (project_root / DEFAULT_TEST_RESULTS_REL).parent.mkdir(parents=True, exist_ok=True)
    (project_root / DEFAULT_TEST_RESULTS_REL).write_text(
        json.dumps(test_results, indent=2) + "\n",
        encoding="utf-8",
    )
    safety_payload = {"status": safety_status, "detail": "tier2 local implementation runner"}
    (project_root / DEFAULT_SAFETY_RESULTS_REL).write_text(
        json.dumps(safety_payload, indent=2) + "\n",
        encoding="utf-8",
    )

    commit_hash: str | None = None
    if not no_commit:
        commit_ok, tier_commit_reason = action_allowed("local_commit")
        if not commit_ok:
            payload["stop_reason"] = tier_commit_reason
            return payload, 1
        commit_message = f"tier2: implement {draft_id}"
        add = runner(["git", "add", "--"] + changed_files, project_root)
        if add.returncode != 0:
            payload["stop_reason"] = "git add failed for allowed implementation files"
            return payload, 1
        commit = runner(["git", "commit", "-m", commit_message], project_root)
        if commit.returncode != 0:
            payload["stop_reason"] = "git commit failed"
            return payload, 1
        rev = runner(["git", "rev-parse", "HEAD"], project_root)
        commit_hash = rev.stdout.strip() if rev.returncode == 0 else None
        payload["commit_hash"] = commit_hash

    payload["files_changed"] = changed_files

    if refresh_batch and (commit_hash or no_commit):
        batch_payload, batch_code = run_release_batch_assembler_command(
            draft_ticket=draft_path,
            allow_controlled_dirty=True,
            test_results=project_root / DEFAULT_TEST_RESULTS_REL,
            safety_results=project_root / DEFAULT_SAFETY_RESULTS_REL,
            root=project_root,
        )
        if batch_code == 0:
            payload["release_batch_path"] = batch_payload.get("batch_path")

    payload.update({"status": "completed", "verdict": "GO", "stop_reason": None})
    violations = assert_no_private_fields({"tier2_summary": public_safe_summary(payload)})
    if violations:
        payload["verdict"] = "NO-GO"
        payload["stop_reason"] = "summary blocked by private-field scan"
        return payload, 1
    return payload, 0


def public_safe_summary(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "schema_version",
        "status",
        "verdict",
        "draft_ticket_path",
        "draft_ticket_id",
        "branch_name",
        "files_changed",
        "tests_run",
        "test_results_passed",
        "safety_audit_status",
        "commit_hash",
        "release_batch_path",
        "patch_bundle_path",
        "stop_reason",
        "dry_run",
        "no_commit",
        "stage_only",
        "require_staged_validation",
        "autonomy_tier_used",
    }
    return {key: payload[key] for key in allowed if key in payload}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tier 2 local branch implementation runner.")
    parser.add_argument("--draft-ticket", type=Path, default=None)
    parser.add_argument("--latest", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--branch-name", type=str, default=None)
    parser.add_argument("--allow-controlled-dirty", action="store_true")
    parser.add_argument("--no-commit", action="store_true")
    parser.add_argument("--no-refresh-batch", action="store_true")
    parser.add_argument("--stage-only", action="store_true")
    parser.add_argument("--apply-staged", type=Path, default=None)
    parser.add_argument("--require-staged-validation", action="store_true")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        payload, exit_code = run_tier2_local_implementation_command(
            draft_ticket=args.draft_ticket,
            latest=args.latest,
            dry_run=args.dry_run,
            branch_name=args.branch_name,
            allow_controlled_dirty=args.allow_controlled_dirty,
            no_commit=args.no_commit,
            refresh_batch=not args.no_refresh_batch,
            stage_only=args.stage_only,
            apply_staged=args.apply_staged,
            require_staged_validation=args.require_staged_validation,
            root=args.root,
        )
    except Tier2ImplementationError as exc:
        print(json.dumps({"status": "error", "verdict": "NO-GO", "stop_reason": str(exc)}, indent=2))
        return 1
    print(json.dumps(public_safe_summary(payload), indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
