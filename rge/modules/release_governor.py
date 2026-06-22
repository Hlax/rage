"""Deterministic release governor for batch promotion and mainline autonomy gates."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Callable

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.autonomy_tier_policy import (
    action_allowed,
    summarize_tier_policy,
)
from rge.modules.autonomous_synthesis_governor import (
    FORBIDDEN_ACTION_PATTERNS,
    SAFE_DIRTY_PREFIXES,
    _safe_rel,
    dirty_paths_in_unsafe_paths,
    load_circuit_breaker,
    load_governor_ledger,
    update_circuit_breaker,
    utc_now_iso,
)
from rge.modules.instruction_packet_ticket_draft import latest_draft_ticket
from rge.modules.operator_loop import WorkingTreeStatus, inspect_working_tree
from rge.modules.principal_audit_gate import repo_root
from rge.modules.safety_auditor import run_safety_audit
from rge.modules.verify_runner import run_verification

RELEASE_GOVERNOR_SCHEMA_VERSION = "release_governor_v0.1.0"
BATCH_SCHEMA_VERSION = "release_batch_v0.1.0"
DEFAULT_BATCH_DIR_REL = Path("data/operator/release_batches")
DEFAULT_REPORT_REL = Path("data/operator/release_governor_report_latest.json")
DEFAULT_AUDIT_REL = Path("data/operator/release_governor_audit.jsonl")
DEFAULT_CANDIDATE_DIR_REL = Path("data/operator/canonical_ticket_candidates")
ATLAS_ARTIFACT_REL = Path("apps/public-site/public/data/atlas_release_governor_latest.json")
ATLAS_ARTIFACT_SCHEMA = "atlas_release_governor_v0.1.0"
RELEASE_CLI_SCRIPT = "scripts/run_release_governor.py"
BATCH_ASSEMBLER_CLI_SCRIPT = "scripts/run_release_batch_assembler.py"

PUBLIC_ARTIFACT_PREFIXES = (
    "apps/public-site/public/data/",
    "apps/public-site/app/",
    "apps/public-site/lib/",
)

DEFAULT_BATCH_MAX_ITEMS = 5
DEFAULT_CHANGED_FILE_ALLOWLIST = (
    "rge/",
    "tests/",
    "scripts/",
    "agent_reports/",
    "data/operator/",
    "apps/public-site/",
    "tickets/",
    "docs/",
    ".env.example",
)

FORBIDDEN_BATCH_PATHS = (
    ".env",
    ".env.local",
    "credentials",
    "secret",
    "private_key",
)


class ReleaseGovernorError(RuntimeError):
    """Raised when release governor inputs or gates are invalid."""


def release_batch_dir(*, root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_BATCH_DIR_REL


def release_report_path(*, root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_REPORT_REL


def release_audit_path(*, root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_AUDIT_REL


def canonical_candidate_dir(*, root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_CANDIDATE_DIR_REL


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _batch_max_items() -> int:
    raw = os.environ.get("RGE_RELEASE_BATCH_MAX_ITEMS", str(DEFAULT_BATCH_MAX_ITEMS)).strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_BATCH_MAX_ITEMS


def _changed_file_allowlist() -> tuple[str, ...]:
    raw = os.environ.get("RGE_RELEASE_CHANGED_FILE_ALLOWLIST", "").strip()
    if not raw:
        return DEFAULT_CHANGED_FILE_ALLOWLIST
    return tuple(item.strip() for item in raw.split(",") if item.strip())


def validate_batch_schema(batch: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if batch.get("schema_version") != BATCH_SCHEMA_VERSION:
        reasons.append(f"schema_version must be {BATCH_SCHEMA_VERSION!r}")
    if not batch.get("batch_id"):
        reasons.append("batch_id is required")
    for field in (
        "draft_ticket_ids",
        "instruction_packet_refs",
        "branch_names",
        "commit_hashes",
        "reports",
        "changed_files",
    ):
        if not isinstance(batch.get(field), list):
            reasons.append(f"{field} must be a list")
    if not str(batch.get("rollback_plan") or "").strip():
        reasons.append("rollback_plan is required")
    return reasons


def load_release_batch(path: Path, *, root: Path | None = None) -> dict[str, Any]:
    project_root = root or repo_root()
    candidate = path if path.is_absolute() else project_root / path
    if not candidate.is_file():
        raise ReleaseGovernorError(f"release batch not found: {path}")
    batch = _load_json(candidate)
    if batch is None:
        raise ReleaseGovernorError(f"release batch is not valid JSON: {path}")
    errors = validate_batch_schema(batch)
    if errors:
        raise ReleaseGovernorError("invalid release batch: " + "; ".join(errors[:5]))
    batch["_path"] = _safe_rel(candidate, project_root)
    return batch


def discover_latest_release_batch(*, root: Path | None = None) -> dict[str, Any]:
    project_root = root or repo_root()
    batch_dir = release_batch_dir(root=project_root)
    if not batch_dir.is_dir():
        return {"status": "missing", "batch_path": None}
    candidates = sorted(
        batch_dir.glob("*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        return {"status": "missing", "batch_path": None}
    latest = candidates[0]
    return {
        "status": "available",
        "batch_path": _safe_rel(latest, project_root),
        "batch_id": _load_json(latest).get("batch_id") if _load_json(latest) else None,
    }


def _normalize_dirty_path(raw: str) -> str:
    path = raw[3:].strip() if len(raw) > 3 and raw[:2].strip() else raw.strip()
    return path.replace("\\", "/")


def non_safe_dirty_paths(dirty_paths: list[str]) -> list[str]:
    """Dirty paths outside operator-safe generated artifact prefixes."""
    blocked: list[str] = []
    for raw in dirty_paths:
        normalized = _normalize_dirty_path(raw)
        if not normalized:
            continue
        if any(normalized.startswith(prefix) for prefix in SAFE_DIRTY_PREFIXES):
            continue
        blocked.append(normalized)
    return blocked


def assess_release_batch_working_tree(
    working_tree: WorkingTreeStatus,
    *,
    allow_controlled_dirty: bool = False,
) -> dict[str, Any]:
    """Classify working tree for release batch assembly and plan recommendations."""
    if working_tree.clean:
        return {
            "status": "clean",
            "blocks_batch_assembly": False,
            "blocks_plan_recommendations": False,
            "unsafe_paths": [],
            "non_safe_dirty_paths": [],
            "controlled_dirty": False,
        }
    unsafe = dirty_paths_in_unsafe_paths(working_tree.dirty_paths)
    non_safe = non_safe_dirty_paths(working_tree.dirty_paths)
    if unsafe:
        return {
            "status": "unsafe_dirty",
            "blocks_batch_assembly": True,
            "blocks_plan_recommendations": True,
            "unsafe_paths": unsafe,
            "non_safe_dirty_paths": non_safe,
            "controlled_dirty": False,
        }
    if non_safe and not allow_controlled_dirty:
        return {
            "status": "dirty",
            "blocks_batch_assembly": True,
            "blocks_plan_recommendations": True,
            "unsafe_paths": [],
            "non_safe_dirty_paths": non_safe,
            "controlled_dirty": False,
        }
    return {
        "status": "controlled_dirty",
        "blocks_batch_assembly": False,
        "blocks_plan_recommendations": False,
        "unsafe_paths": [],
        "non_safe_dirty_paths": non_safe,
        "controlled_dirty": True,
    }


def discover_release_batch_for_draft(
    draft_ticket_id: str | None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Find the newest release batch JSON that references a draft ticket id."""
    project_root = root or repo_root()
    if not draft_ticket_id:
        return {"status": "missing", "batch_path": None, "batch_id": None}
    batch_dir = release_batch_dir(root=project_root)
    if not batch_dir.is_dir():
        return {"status": "missing", "batch_path": None, "batch_id": None}
    for path in sorted(
        batch_dir.glob("*.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    ):
        payload = _load_json(path)
        if not isinstance(payload, dict):
            continue
        draft_ids = payload.get("draft_ticket_ids") or []
        if draft_ticket_id in draft_ids:
            return {
                "status": "available",
                "batch_path": _safe_rel(path, project_root),
                "batch_id": payload.get("batch_id"),
            }
    return {"status": "missing", "batch_path": None, "batch_id": None}


def resolve_next_release_action(
    *,
    draft_available: bool,
    batch_for_draft_available: bool,
    batch_assembly_blocked: bool,
    circuit_open: bool,
    dry_run_recommended: bool,
) -> tuple[str, int]:
    """Return (next_action_label, min_autonomy_tier) for operator/Atlas surfaces."""
    if circuit_open:
        return "inspect_circuit_breaker", 0
    if batch_assembly_blocked:
        return "resolve_working_tree", 0
    if draft_available and not batch_for_draft_available:
        return "assemble_release_batch", 1
    if batch_for_draft_available and dry_run_recommended:
        return "release_governor_dry_run", 0
    if batch_for_draft_available:
        return "release_governor_inspect", 0
    return "none", 0


def _check_working_tree(
    working_tree: WorkingTreeStatus | None,
    *,
    root: Path,
    allow_controlled_dirty: bool,
) -> list[str]:
    tree = working_tree or inspect_working_tree(root)
    reasons: list[str] = []
    if not tree.clean and not allow_controlled_dirty:
        reasons.append("working tree is not clean")
    unsafe = dirty_paths_in_unsafe_paths(tree.dirty_paths)
    if unsafe:
        reasons.append("unsafe dirty paths: " + ", ".join(unsafe[:5]))
    return reasons


def _check_secrets_and_private_fields(*, root: Path) -> list[str]:
    reasons: list[str] = []
    audit = run_safety_audit(audit_type="full", root=root)
    if audit.get("status") != "pass":
        reasons.extend(audit.get("blocked_reasons") or ["safety audit failed"])
    return reasons


def _check_verify(*, root: Path, skip_site: bool) -> list[str]:
    report = run_verification(root=root, skip_site=skip_site)
    if report.get("status") != "pass":
        failed = [
            row["name"]
            for row in report.get("results") or []
            if not row.get("passed")
        ]
        reasons = [f"verify failed: {', '.join(failed)}"] if failed else ["verify failed"]
        return reasons
    return []


def _check_agent_reports(batch: dict[str, Any], *, root: Path) -> list[str]:
    reasons: list[str] = []
    reports = batch.get("reports") or []
    if not reports:
        reasons.append("batch missing agent report paths")
        return reasons
    has_md = False
    has_json = False
    for rel in reports:
        path = root / str(rel)
        if not path.is_file():
            reasons.append(f"agent report missing: {rel}")
            continue
        if str(rel).endswith(".md"):
            has_md = True
        if str(rel).endswith("-latest.json"):
            has_json = True
    if not has_md:
        reasons.append("batch missing agent report markdown")
    if not has_json:
        reasons.append("batch missing agent report latest JSON")
    return reasons


def _check_circuit_breaker(*, root: Path) -> list[str]:
    circuit = load_circuit_breaker(root=root)
    if circuit.get("status") == "open":
        return [
            "autonomy circuit breaker is open: "
            + str(circuit.get("latest_stop_reason") or "unknown")
        ]
    return []


def _check_synthesis_governor(*, root: Path) -> list[str]:
    reasons: list[str] = []
    ledger = load_governor_ledger(root=root)
    for review in ledger.get("reviews") or []:
        if not isinstance(review, dict):
            continue
        verdict = review.get("governor_verdict")
        if verdict in {"PARTIAL", "NO-GO"}:
            reasons.append(
                f"synthesis governor {verdict} review present: {review.get('review_id')}"
            )
    return reasons


def _check_forbidden_synthesis_instructions(batch: dict[str, Any], *, root: Path) -> list[str]:
    reasons: list[str] = []
    for ref in batch.get("instruction_packet_refs") or []:
        path = root / str(ref)
        text = ""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            reasons.append(f"instruction packet unreadable: {ref}")
            continue
        for pattern in FORBIDDEN_ACTION_PATTERNS:
            if pattern.search(text):
                reasons.append(f"instruction packet {ref} contains forbidden action language")
    return reasons


def _check_batch_size(batch: dict[str, Any]) -> list[str]:
    limit = _batch_max_items()
    count = max(
        len(batch.get("draft_ticket_ids") or []),
        len(batch.get("branch_names") or []),
        len(batch.get("commit_hashes") or []),
    )
    if count > limit:
        return [f"batch size {count} exceeds limit {limit}"]
    return []


def _check_changed_file_allowlist(batch: dict[str, Any]) -> list[str]:
    allowlist = _changed_file_allowlist()
    reasons: list[str] = []
    for rel in batch.get("changed_files") or []:
        normalized = str(rel).replace("\\", "/")
        if any(marker in normalized.casefold() for marker in FORBIDDEN_BATCH_PATHS):
            reasons.append(f"changed file blocked: {rel}")
            continue
        if not any(normalized.startswith(prefix) for prefix in allowlist):
            reasons.append(f"changed file outside allowlist: {rel}")
    return reasons


def _check_batch_test_results(batch: dict[str, Any]) -> list[str]:
    results = batch.get("test_results")
    if not isinstance(results, dict):
        return ["batch missing test_results object"]
    if results.get("passed") is not True:
        return ["batch test_results.passed is not true"]
    return []


def _check_batch_safety_results(batch: dict[str, Any]) -> list[str]:
    results = batch.get("safety_results")
    if not isinstance(results, dict):
        return ["batch missing safety_results object"]
    if results.get("status") != "pass":
        return ["batch safety_results.status is not pass"]
    return []


def _public_artifacts_changed(batch: dict[str, Any]) -> bool:
    for rel in batch.get("changed_files") or []:
        normalized = str(rel).replace("\\", "/")
        if any(normalized.startswith(prefix) for prefix in PUBLIC_ARTIFACT_PREFIXES):
            return True
    return False


def _check_tier2_patch_staging(batch: dict[str, Any], *, root: Path) -> list[str]:
    from rge.modules.tier2_patch_staging import require_tier2_patch_staging_enabled
    from rge.modules.tier2_local_implementation import is_tier2_implementation_branch

    if not require_tier2_patch_staging_enabled():
        return []
    branches = batch.get("branch_names") or []
    if not any(is_tier2_implementation_branch(str(branch)) for branch in branches):
        return []
    meta = batch.get("candidate_metadata") or {}
    patch = meta.get("patch_staging") if isinstance(meta.get("patch_staging"), dict) else {}
    if patch.get("validation_verdict") != "GO":
        return ["tier2 patch staging validation GO required (RGE_REQUIRE_TIER2_PATCH_STAGING=1)"]
    return []


def evaluate_release_governor(
    batch: dict[str, Any],
    *,
    root: Path | None = None,
    working_tree: WorkingTreeStatus | None = None,
    skip_site: bool = False,
    run_verify: bool = True,
    run_safety: bool = True,
) -> dict[str, Any]:
    """Run deterministic release governor checks; returns verdict payload."""
    project_root = root or repo_root()
    reasons: list[str] = []
    checks: dict[str, Any] = {}

    def _run(name: str, fn: Callable[[], list[str]]) -> None:
        result = fn()
        checks[name] = {"passed": not result, "reasons": result}
        reasons.extend(result)

    _run(
        "working_tree",
        lambda: _check_working_tree(
            working_tree,
            root=project_root,
            allow_controlled_dirty=bool(batch.get("allow_controlled_dirty")),
        ),
    )
    _run("rollback_plan", lambda: [] if batch.get("rollback_plan") else ["rollback_plan missing"])
    _run("batch_schema", lambda: validate_batch_schema(batch))
    _run("batch_size", lambda: _check_batch_size(batch))
    _run("changed_file_allowlist", lambda: _check_changed_file_allowlist(batch))
    _run("batch_test_results", lambda: _check_batch_test_results(batch))
    _run("batch_safety_results", lambda: _check_batch_safety_results(batch))
    _run("agent_reports", lambda: _check_agent_reports(batch, root=project_root))
    _run("circuit_breaker", lambda: _check_circuit_breaker(root=project_root))
    _run("synthesis_governor", lambda: _check_synthesis_governor(root=project_root))
    _run("forbidden_synthesis_instructions", lambda: _check_forbidden_synthesis_instructions(batch, root=project_root))
    _run("tier2_patch_staging", lambda: _check_tier2_patch_staging(batch, root=project_root))
    if run_safety:
        _run("safety_audit", lambda: _check_secrets_and_private_fields(root=project_root))
    if run_verify:
        _run(
            "verify",
            lambda: _check_verify(
                root=project_root,
                skip_site=skip_site or not _public_artifacts_changed(batch),
            ),
        )

    verdict = "GO" if not reasons else ("PARTIAL" if len(reasons) <= 2 else "NO-GO")
    if any(
        marker in reason
        for reason in reasons
        for marker in ("circuit breaker", "secret", "safety audit", "forbidden action")
    ):
        verdict = "NO-GO"

    return {
        "schema_version": RELEASE_GOVERNOR_SCHEMA_VERSION,
        "evaluated_at": utc_now_iso(),
        "batch_id": batch.get("batch_id"),
        "batch_path": batch.get("_path"),
        "governor_verdict": verdict,
        "failure_reasons": reasons,
        "checks": checks,
        "autonomy_tier": summarize_tier_policy(),
        "public_artifacts_changed": _public_artifacts_changed(batch),
    }


def append_release_audit_record(record: dict[str, Any], *, root: Path | None = None) -> Path:
    project_root = root or repo_root()
    path = release_audit_path(root=project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(record)
    payload.setdefault("recorded_at", utc_now_iso())
    payload.setdefault("schema_version", RELEASE_GOVERNOR_SCHEMA_VERSION)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return path


def write_release_report(payload: dict[str, Any], *, root: Path | None = None) -> Path:
    project_root = root or repo_root()
    path = release_report_path(root=project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    safe = dict(payload)
    violations = assert_no_private_fields({"release_governor_report": safe})
    if violations:
        raise ReleaseGovernorError(
            "release governor report blocked: " + "; ".join(violations[:5])
        )
    path.write_text(json.dumps(safe, indent=2) + "\n", encoding="utf-8")
    return path


def promote_draft_tickets_to_candidates(
    batch: dict[str, Any],
    *,
    root: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    project_root = root or repo_root()
    allowed, reason = action_allowed("promote_canonical_ticket")
    if not allowed:
        return {"status": "blocked", "detail": reason, "promoted": []}
    out_dir = canonical_candidate_dir(root=project_root)
    promoted: list[str] = []
    for draft_id in batch.get("draft_ticket_ids") or []:
        draft_dir = project_root / "data/operator/draft_tickets"
        matches = [
            path
            for path in draft_dir.glob("draft_*.json")
            if path.is_file()
            and (
                draft_id in path.name
                or (_load_json(path) or {}).get("id") == draft_id
            )
        ]
        for match in matches[:1]:
            payload = _load_json(match)
            if payload is None:
                continue
            candidate = dict(payload)
            candidate["status"] = "proposed"
            candidate["promoted_from_batch"] = batch.get("batch_id")
            candidate["promotion_path"] = f"tickets/{candidate.get('id', 'candidate')}.json"
            rel = _safe_rel(out_dir / f"{candidate.get('id', 'candidate')}.json", project_root)
            if not dry_run:
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / f"{candidate.get('id', 'candidate')}.json").write_text(
                    json.dumps(candidate, indent=2) + "\n",
                    encoding="utf-8",
                )
            promoted.append(rel)
    return {"status": "completed" if promoted else "skipped", "promoted": promoted, "dry_run": dry_run}


def _gate_irreversible_action(
    *,
    action: str,
    evaluation: dict[str, Any],
    confirm: bool,
) -> tuple[bool, str]:
    if evaluation.get("governor_verdict") != "GO":
        return False, "release governor verdict is not GO"
    allowed, reason = action_allowed(action)
    if not allowed:
        return False, reason
    if not confirm:
        return False, f"{action} requires --confirm flag"
    return True, "allowed"


def run_release_governor_command(
    *,
    candidate: Path | None = None,
    inspect_only: bool = False,
    dry_run: bool = False,
    promote_tickets: bool = False,
    push_branches: bool = False,
    merge_batch: bool = False,
    publish: bool = False,
    confirm: bool = False,
    skip_site: bool = False,
    root: Path | None = None,
    working_tree: WorkingTreeStatus | None = None,
) -> tuple[dict[str, Any], int]:
    project_root = root or repo_root()

    if inspect_only:
        payload = {
            "status": "completed",
            "command": "inspect",
            "autonomy_tier": summarize_tier_policy(),
            "latest_batch": discover_latest_release_batch(root=project_root),
            "latest_draft_ticket": latest_draft_ticket(root=project_root),
            "circuit_breaker": load_circuit_breaker(root=project_root),
        }
        write_release_report(payload, root=project_root)
        sync_public_release_governor_artifact(root=project_root)
        return payload, 0

    if candidate is None:
        latest = discover_latest_release_batch(root=project_root)
        if latest.get("status") != "available":
            return (
                {"status": "error", "detail": "requires --candidate PATH or existing batch"},
                2,
            )
        candidate = project_root / str(latest["batch_path"])

    batch = load_release_batch(candidate, root=project_root)
    evaluation = evaluate_release_governor(
        batch,
        root=project_root,
        working_tree=working_tree,
        skip_site=skip_site,
        run_verify=not dry_run or bool(batch.get("test_results")),
        run_safety=not dry_run or bool(batch.get("safety_results")),
    )
    payload: dict[str, Any] = {
        "status": "completed",
        "command": "dry_run" if dry_run else "evaluate",
        "dry_run": dry_run,
        "evaluation": evaluation,
        "autonomy_tier": evaluation.get("autonomy_tier"),
        "governor_verdict": evaluation.get("governor_verdict"),
        "failure_reasons": evaluation.get("failure_reasons") or [],
    }

    if evaluation.get("governor_verdict") != "GO" and not dry_run:
        update_circuit_breaker(
            verdict="NO-GO",
            failure_reasons=evaluation.get("failure_reasons") or ["release governor rejected"],
            root=project_root,
        )
        payload["circuit_breaker_advanced"] = True

    actions_attempted: list[dict[str, Any]] = []
    if promote_tickets:
        ok, detail = _gate_irreversible_action(
            action="promote_canonical_ticket",
            evaluation=evaluation,
            confirm=confirm,
        )
        result = (
            promote_draft_tickets_to_candidates(batch, root=project_root, dry_run=dry_run or not ok)
            if ok
            else {"status": "blocked", "detail": detail}
        )
        actions_attempted.append({"action": "promote_tickets", **result})

    for action_name, enabled, tier_action, recommended in (
        (
            "push_branches",
            push_branches,
            "push_feature_branch",
            "git push -u origin HEAD",
        ),
        (
            "merge_batch",
            merge_batch,
            "batch_merge",
            "git merge --no-ff <integration-branch>",
        ),
        (
            "publish",
            publish,
            "publish_public_export",
            "research export-public --publish",
        ),
    ):
        if not enabled:
            continue
        ok, detail = _gate_irreversible_action(
            action=tier_action,
            evaluation=evaluation,
            confirm=confirm,
        )
        actions_attempted.append(
            {
                "action": action_name,
                "status": "approved" if ok else "blocked",
                "detail": detail if not ok else "gated; operator must run manually",
                "recommended_command": recommended if ok else None,
                "executed": False,
            }
        )

    if actions_attempted:
        payload["actions"] = actions_attempted

    report_path = write_release_report(payload, root=project_root)
    payload["report_path"] = _safe_rel(report_path, project_root)
    sync_public_release_governor_artifact(root=project_root)
    if confirm and payload.get("governor_verdict") == "GO":
        append_release_audit_record(
            {
                "event": "release_governor_action",
                "batch_id": batch.get("batch_id"),
                "actions": actions_attempted,
                "governor_verdict": payload.get("governor_verdict"),
            },
            root=project_root,
        )

    exit_code = 0 if payload.get("governor_verdict") == "GO" else 1
    if dry_run and payload.get("governor_verdict") == "GO":
        exit_code = 0
    return payload, exit_code


def atlas_artifact_path(*, root: Path | None = None) -> Path:
    return (root or repo_root()) / ATLAS_ARTIFACT_REL


def build_atlas_safe_release_governor_artifact(*, root: Path | None = None) -> dict[str, Any]:
    """Build public-safe Atlas operator artifact for release governor visibility."""
    project_root = root or repo_root()
    plan = inspect_release_governor_plan_status(root=project_root)
    tier = plan.get("autonomy_tier") or summarize_tier_policy()
    latest_batch = discover_latest_release_batch(root=project_root)
    report = _load_json(release_report_path(root=project_root)) or {}
    evaluation = report.get("evaluation") if isinstance(report.get("evaluation"), dict) else {}
    governor_verdict = (
        evaluation.get("governor_verdict")
        or report.get("governor_verdict")
        or "UNKNOWN"
    )
    artifact = {
        "schema_version": ATLAS_ARTIFACT_SCHEMA,
        "status": "available",
        "autonomy_tier": {
            "configured_tier": tier.get("configured_tier"),
            "effective_tier": tier.get("effective_tier"),
            "tier_name": tier.get("tier_name"),
        },
        "latest_batch_path": plan.get("latest_batch_for_draft_path") or plan.get("latest_batch_path"),
        "latest_batch_id": plan.get("latest_batch_for_draft_id") or latest_batch.get("batch_id"),
        "batch_status": (
            "available"
            if plan.get("latest_batch_for_draft_path") or latest_batch.get("status") == "available"
            else "missing"
        ),
        "governor_verdict": governor_verdict,
        "release_governor_dry_run_recommended": plan.get("release_governor_dry_run_recommended"),
        "batch_candidate_recommended": plan.get("batch_candidate_recommended"),
        "implementation_branch_recommended": plan.get("implementation_branch_recommended"),
        "release_push_recommended": plan.get("release_push_recommended"),
        "release_merge_recommended": plan.get("release_merge_recommended"),
        "release_publish_recommended": plan.get("release_publish_recommended"),
        "circuit_breaker_status": plan.get("circuit_breaker_status"),
        "latest_draft_ticket_path": plan.get("latest_draft_ticket_path"),
        "next_release_action": plan.get("next_release_action"),
        "autonomy_tier_required_for_next_action": plan.get(
            "autonomy_tier_required_for_next_action"
        ),
        "batch_assembly_block_reasons": list(plan.get("batch_assembly_block_reasons") or [])[:5],
        "failure_reasons": list(evaluation.get("failure_reasons") or report.get("failure_reasons") or [])[:5],
        "forbidden_actions": [
            "auto_merge",
            "auto_push",
            "auto_publish",
            "auto_promote_ticket_without_governor_go",
        ],
        "operator_commands": plan.get("operator_commands") or {},
        "updated_at": utc_now_iso(),
    }
    violations = assert_no_private_fields({"release_governor_artifact": artifact})
    if violations:
        raise ReleaseGovernorError(
            "Atlas release governor artifact blocked: " + "; ".join(violations[:5])
        )
    return artifact


def sync_public_release_governor_artifact(*, root: Path | None = None) -> dict[str, Any]:
    project_root = root or repo_root()
    artifact = build_atlas_safe_release_governor_artifact(root=project_root)
    path = atlas_artifact_path(root=project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "completed",
        "public_artifact_path": _safe_rel(path, project_root),
        "governor_verdict": artifact.get("governor_verdict"),
    }


def refresh_release_governor_dry_run_if_batch(*, root: Path | None = None) -> dict[str, Any] | None:
    """Read-only release governor dry-run when a batch exists; writes public-safe report."""
    project_root = root or repo_root()
    latest = discover_latest_release_batch(root=project_root)
    if latest.get("status") != "available":
        sync_public_release_governor_artifact(root=project_root)
        return None
    try:
        batch = load_release_batch(project_root / str(latest["batch_path"]), root=project_root)
        evaluation = evaluate_release_governor(
            batch,
            root=project_root,
            skip_site=True,
            run_verify=False,
            run_safety=False,
        )
        write_release_report(
            {"status": "completed", "command": "dry_run", "evaluation": evaluation},
            root=project_root,
        )
        sync_public_release_governor_artifact(root=project_root)
        return evaluation
    except ReleaseGovernorError as exc:
        return {"status": "error", "detail": str(exc)}


def build_safe_fixture_batch(*, batch_id: str = "batch_fixture_safe_001") -> dict[str, Any]:
    """Deterministic safe batch fixture for tests and dry-run proofs."""
    return {
        "schema_version": BATCH_SCHEMA_VERSION,
        "batch_id": batch_id,
        "status": "candidate",
        "created_at": utc_now_iso(),
        "draft_ticket_ids": ["draft-from-syn-packet-fixture"],
        "instruction_packet_refs": [],
        "branch_names": ["phase-3/release-governor-fixture"],
        "commit_hashes": ["deadbeef00000000000000000000000000000000"],
        "test_results": {"passed": True, "commands": ["python -m pytest tests/unit/test_release_governor.py -q"]},
        "safety_results": {"status": "pass"},
        "reports": [
            "agent_reports/2026-06-22_autonomous-release-governor-batch-promotion.md",
            "agent_reports/2026-06-22_autonomous-release-governor-batch-promotion-latest.json",
        ],
        "rollback_plan": "Revert batch branch and delete canonical ticket candidates.",
        "proposed_release_summary": "Fixture-safe release governor dry-run batch.",
        "changed_files": ["rge/modules/release_governor.py", "tests/unit/test_release_governor.py"],
        "allow_controlled_dirty": True,
    }


def inspect_release_governor_plan_status(
    *,
    root: Path | None = None,
    working_tree: WorkingTreeStatus | None = None,
) -> dict[str, Any]:
    project_root = root or repo_root()
    tier = summarize_tier_policy()
    latest_draft = latest_draft_ticket(root=project_root)
    draft_path = latest_draft.get("draft_ticket_path")
    draft_id = latest_draft.get("draft_ticket_id")
    draft_available = latest_draft.get("status") == "available" and bool(draft_path)
    batch_for_draft = discover_release_batch_for_draft(draft_id, root=project_root)
    latest_batch = discover_latest_release_batch(root=project_root)
    batch_path = batch_for_draft.get("batch_path") or latest_batch.get("batch_path")
    tree = working_tree or inspect_working_tree(project_root)
    tree_assessment = assess_release_batch_working_tree(tree)
    branch_exists = bool(tree.branch and tree.branch not in {"main", "master"})
    circuit = load_circuit_breaker(root=project_root)
    circuit_open = circuit.get("status") == "open"

    batch_assembly_blocked = bool(
        tree_assessment.get("blocks_batch_assembly")
        or circuit_open
    )
    batch_assembly_block_reasons: list[str] = []
    if circuit_open:
        batch_assembly_block_reasons.append(
            "autonomy circuit breaker is open: "
            + str(circuit.get("latest_stop_reason") or "unknown")
        )
    if tree_assessment.get("unsafe_paths"):
        batch_assembly_block_reasons.append(
            "unsafe dirty paths: " + ", ".join(tree_assessment["unsafe_paths"][:5])
        )
    if tree_assessment.get("non_safe_dirty_paths") and tree_assessment.get("status") != "controlled_dirty":
        batch_assembly_block_reasons.append(
            "non-operator dirty paths: "
            + ", ".join(tree_assessment["non_safe_dirty_paths"][:5])
        )

    dry_run_recommended = batch_for_draft.get("status") == "available"
    push_recommended = False
    merge_recommended = False
    publish_recommended = False
    implementation_branch_recommended = (
        draft_available and not branch_exists and tier.get("effective_tier", 0) >= 2
    )
    tier2_status: dict[str, Any] = {"status": "missing"}
    patch_staging_status: dict[str, Any] = {"status": "missing"}
    patch_preview_status: dict[str, Any] = {"status": "missing"}
    has_impl_commit = False
    try:
        from rge.modules.tier2_local_implementation import inspect_tier2_implementation_status
        from rge.modules.tier2_patch_staging import inspect_tier2_patch_staging_status
        from rge.modules.tier2_patch_staging_preview import inspect_tier2_patch_staging_preview_status

        tier2_status = inspect_tier2_implementation_status(
            root=project_root,
            working_tree=tree,
        )
        patch_staging_status = inspect_tier2_patch_staging_status(
            root=project_root,
            working_tree=tree,
        )
        patch_preview_status = inspect_tier2_patch_staging_preview_status(root=project_root)
        has_impl_commit = bool(tier2_status.get("has_implementation_commit"))
    except ImportError:
        has_impl_commit = branch_exists

    batch_candidate_recommended = (
        draft_available
        and batch_for_draft.get("status") != "available"
        and has_impl_commit
        and not batch_assembly_blocked
    )

    if batch_for_draft.get("batch_path") and batch_for_draft.get("status") == "available":
        try:
            batch = load_release_batch(
                project_root / str(batch_for_draft["batch_path"]),
                root=project_root,
            )
            evaluation = evaluate_release_governor(
                batch,
                root=project_root,
                working_tree=tree,
                skip_site=True,
                run_verify=False,
                run_safety=False,
            )
            if evaluation.get("governor_verdict") == "GO":
                push_recommended = action_allowed("push_feature_branch")[0]
                merge_recommended = action_allowed("batch_merge")[0]
                publish_recommended = action_allowed("publish_public_export")[0]
        except ReleaseGovernorError:
            dry_run_recommended = True

    next_action, next_action_tier = resolve_next_release_action(
        draft_available=draft_available,
        batch_for_draft_available=batch_for_draft.get("status") == "available",
        batch_assembly_blocked=batch_assembly_blocked,
        circuit_open=circuit_open,
        dry_run_recommended=dry_run_recommended,
    )

    return {
        "status": "available",
        "autonomy_tier": tier,
        "latest_draft_ticket_path": draft_path,
        "latest_draft_ticket_id": draft_id,
        "latest_batch_path": batch_path,
        "latest_batch_for_draft_path": batch_for_draft.get("batch_path"),
        "latest_batch_for_draft_id": batch_for_draft.get("batch_id"),
        "working_tree_assessment": tree_assessment,
        "batch_assembly_blocked": batch_assembly_blocked,
        "batch_assembly_block_reasons": batch_assembly_block_reasons,
        "implementation_branch_recommended": implementation_branch_recommended,
        "batch_candidate_recommended": batch_candidate_recommended,
        "tier2_implementation_status": tier2_status,
        "tier2_implementation_recommended": tier2_status.get("tier2_implementation_recommended"),
        "tier2_continue_recommended": tier2_status.get("tier2_continue_recommended"),
        "tier2_batch_refresh_recommended": tier2_status.get("tier2_batch_refresh_recommended"),
        "tier2_patch_staging_status": patch_staging_status,
        "tier2_patch_staging_recommended": patch_staging_status.get("tier2_patch_staging_recommended"),
        "tier2_patch_validation_recommended": patch_staging_status.get("tier2_patch_validation_recommended"),
        "tier2_patch_apply_recommended": patch_staging_status.get("tier2_patch_apply_recommended"),
        "tier2_patch_fix_recommended": patch_staging_status.get("tier2_patch_fix_recommended"),
        "tier2_patch_staging_preview_status": patch_preview_status,
        "tier2_patch_staging_preview_refresh_recommended": patch_preview_status.get(
            "tier2_patch_staging_preview_refresh_recommended"
        ),
        "release_governor_dry_run_recommended": dry_run_recommended and not circuit_open,
        "release_push_recommended": push_recommended,
        "release_merge_recommended": merge_recommended,
        "release_publish_recommended": publish_recommended,
        "circuit_breaker_status": circuit.get("status"),
        "next_release_action": next_action,
        "autonomy_tier_required_for_next_action": next_action_tier,
        "operator_commands": {
            "assemble_batch": f"python {BATCH_ASSEMBLER_CLI_SCRIPT} --latest",
            "inspect": f"python {RELEASE_CLI_SCRIPT} --inspect",
            "dry_run": f"python {RELEASE_CLI_SCRIPT} --candidate {batch_path or 'PATH'} --dry-run",
            "promote_tickets": (
                f"python {RELEASE_CLI_SCRIPT} --candidate {batch_path or 'PATH'} "
                "--promote-tickets --confirm"
            ),
            "push_branches": (
                f"python {RELEASE_CLI_SCRIPT} --candidate {batch_path or 'PATH'} "
                "--push-branches --confirm"
            ),
            "merge_batch": (
                f"python {RELEASE_CLI_SCRIPT} --candidate {batch_path or 'PATH'} "
                "--merge-batch --confirm"
            ),
            "publish": (
                f"python {RELEASE_CLI_SCRIPT} --candidate {batch_path or 'PATH'} "
                "--publish --confirm"
            ),
            "tier2_implementation": f"python scripts/run_tier2_local_implementation.py --latest",
            "tier2_dry_run": f"python scripts/run_tier2_local_implementation.py --latest --dry-run",
            "tier2_patch_stage": "python scripts/run_tier2_patch_staging.py --latest",
            "tier2_patch_validate": "python scripts/run_tier2_patch_staging.py --bundle PATH --validate",
            "tier2_patch_apply": (
                "python scripts/run_tier2_local_implementation.py --latest "
                "--apply-staged PATH --require-staged-validation"
            ),
            "tier2_patch_preview_refresh": (
                "python scripts/refresh_tier2_patch_staging_preview.py --latest --sync-public"
            ),
        },
    }


def public_safe_summary(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "status",
        "command",
        "dry_run",
        "governor_verdict",
        "failure_reasons",
        "report_path",
        "autonomy_tier",
        "actions",
        "evaluation",
        "detail",
    }
    safe = {key: payload[key] for key in allowed if key in payload}
    if "autonomy_tier" in safe and isinstance(safe["autonomy_tier"], dict):
        tier = safe["autonomy_tier"]
        safe["autonomy_tier"] = {
            "effective_tier": tier.get("effective_tier"),
            "tier_name": tier.get("tier_name"),
            "configured_tier": tier.get("configured_tier"),
        }
    if "evaluation" in safe and isinstance(safe["evaluation"], dict):
        ev = safe["evaluation"]
        safe["evaluation"] = {
            "batch_id": ev.get("batch_id"),
            "governor_verdict": ev.get("governor_verdict"),
            "failure_reasons": ev.get("failure_reasons"),
        }
    return safe


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Release governor for batch promotion gates.")
    parser.add_argument("--inspect", action="store_true", help="Read-only inspect mode.")
    parser.add_argument("--candidate", type=Path, default=None, help="Release batch JSON path.")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate without irreversible actions.")
    parser.add_argument("--promote-tickets", action="store_true")
    parser.add_argument("--push-branches", action="store_true")
    parser.add_argument("--merge-batch", action="store_true")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--confirm", action="store_true", help="Confirm irreversible gated action.")
    parser.add_argument("--skip-site", action="store_true")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args(argv)

    payload, exit_code = run_release_governor_command(
        candidate=args.candidate,
        inspect_only=args.inspect,
        dry_run=args.dry_run
        or not any(
            (
                args.promote_tickets,
                args.push_branches,
                args.merge_batch,
                args.publish,
            )
        ),
        promote_tickets=args.promote_tickets,
        push_branches=args.push_branches,
        merge_batch=args.merge_batch,
        publish=args.publish,
        confirm=args.confirm,
        skip_site=args.skip_site,
        root=args.root,
    )
    print(json.dumps(public_safe_summary(payload), indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
