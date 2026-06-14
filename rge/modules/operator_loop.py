"""Bounded operator loop runner: inspect repo state and recommend or run safe checks.

Mock-only and deterministic. Never merges, pushes, promotes tickets, edits the
queue, enables live LLM mode, or runs live smoke tests.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from rge.modules.domain_pack_loader import inspect_domain_pack_load_health
from rge.modules.live_probe_scratch import get_scratch_db_path
from rge.modules.live_probe_scratch_summary import (
    REVIEWED_TABLE,
    LiveProbeScratchSummaryError,
    connect_scratch_readonly,
    validate_scratch_schema,
)
from rge.modules.principal_audit_gate import (
    QueueTicketRow,
    checkpoint_status,
    parse_queue_rows,
    repo_root,
)
from rge.modules.ticket_writer import improvement_draft_is_actionable
from rge.subprocess_capture import run_captured

_REPO_ROOT = repo_root()
_QUEUE_PATH = _REPO_ROOT / "tickets" / "TICKET_QUEUE.md"
_REPORTS_DIR = _REPO_ROOT / "agent_reports"
_TICKETS_DIR = _REPO_ROOT / "tickets"
_IMPROVEMENT_ARTIFACT = _REPO_ROOT / "data" / "tickets" / "improvement_ticket_latest.json"
_PUBLIC_SITE_DIR = _REPO_ROOT / "apps" / "public-site"

_OPEN_QUEUE_STATUSES = frozenset({"ready", "proposed"})
_STATUS_PRIORITY = {"ready": 0, "proposed": 1, "in_progress": -1}
_REPORT_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_")
_BUILD_REPORT_NAME_RE = re.compile(r"phase-\d+_ticket-\d+")
_TICKET_ID_RE = re.compile(r"ticket-(\d{3})", re.IGNORECASE)
_REPORT_BRANCH_RE = re.compile(
    r"(?:Branch|branch):\s*`([^`]+)`",
    re.IGNORECASE,
)
_PATH_TICKET_HINTS: dict[str, str] = {
    "operator_loop.py": "ticket-041",
    "principal_audit_gate.py": "ticket-040",
    "golden-gate.yml": "ticket-040",
    "rge-principal-audit.md": "ticket-040",
}

_MOCK_ENV = {"RGE_LLM_MODE": "mock", "RGE_ALLOW_LIVE_LLM": "0"}

_FORBIDDEN_EXECUTE_PATTERNS = (
    "git push",
    "git merge",
    "promote-improvement-ticket",
    "export-public",
    "live_smoke",
    "RGE_LLM_MODE=ollama",
    "RGE_ALLOW_LIVE_LLM=1",
)


@dataclass(frozen=True)
class WorkingTreeStatus:
    clean: bool
    branch: str | None
    dirty_paths: list[str]


@dataclass(frozen=True)
class RecommendedAction:
    action_id: str
    label: str
    gate: str  # safe_autonomous | review_gated | blocked
    reason: str
    commands: list[dict[str, Any]]


def default_improvement_artifact_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / "data" / "tickets" / "improvement_ticket_latest.json"


def public_site_applicable(root: Path | None = None) -> bool:
    site = (root or repo_root()) / "apps" / "public-site"
    return site.is_dir() and (site / "package.json").is_file()


def resolve_npm_executable() -> str | None:
    """Return the npm executable path for subprocess argv (Windows-safe)."""
    return shutil.which("npm")


def safe_verification_commands(root: Path | None = None) -> list[dict[str, Any]]:
    """Deterministic commands allowed in execute-safe mode."""
    project_root = root or repo_root()
    commands: list[dict[str, Any]] = [
        {
            "name": "golden_tests",
            "shell": "RGE_LLM_MODE=mock python -m pytest tests/golden",
            "argv": [sys.executable, "-m", "pytest", "tests/golden"],
            "cwd": str(project_root),
            "env": dict(_MOCK_ENV),
        },
        {
            "name": "full_pytest",
            "shell": "RGE_LLM_MODE=mock python -m pytest",
            "argv": [sys.executable, "-m", "pytest"],
            "cwd": str(project_root),
            "env": dict(_MOCK_ENV),
        },
        {
            "name": "safety_audit",
            "shell": "RGE_LLM_MODE=mock python -m rge.modules.safety_auditor --audit full",
            "argv": [
                sys.executable,
                "-m",
                "rge.modules.safety_auditor",
                "--audit",
                "full",
            ],
            "cwd": str(project_root),
            "env": dict(_MOCK_ENV),
        },
    ]
    npm_executable = resolve_npm_executable()
    if public_site_applicable(project_root) and npm_executable:
        commands.append(
            {
                "name": "public_site_build",
                "shell": "cd apps/public-site && npm run build",
                "argv": [npm_executable, "run", "build"],
                "cwd": str(project_root / "apps" / "public-site"),
                "env": dict(_MOCK_ENV),
            }
        )
    return commands


def inspect_working_tree(
    root: Path | None = None,
    *,
    status_runner: Callable[[list[str], Path], subprocess.CompletedProcess[str]] | None = None,
) -> WorkingTreeStatus:
    """Return git branch and cleanliness (read-only)."""
    project_root = root or repo_root()
    runner = status_runner or (lambda argv, cwd: run_captured(argv, cwd=cwd))
    porcelain = runner(["git", "status", "--porcelain"], project_root)
    dirty_paths = [
        line for line in porcelain.stdout.splitlines() if line.strip()
    ]
    branch_result = runner(["git", "branch", "--show-current"], project_root)
    branch = branch_result.stdout.strip() or None
    return WorkingTreeStatus(
        clean=len(dirty_paths) == 0,
        branch=branch,
        dirty_paths=dirty_paths,
    )


def load_queue_ticket_json(
    ticket_id: str,
    *,
    root: Path | None = None,
) -> dict[str, Any] | None:
    path = (root or repo_root()) / "tickets" / f"{ticket_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_ticket_json_files(*, root: Path | None = None) -> list[Path]:
    tickets_dir = (root or repo_root()) / "tickets"
    if not tickets_dir.is_dir():
        return []
    return sorted(tickets_dir.glob("ticket-*.json"))


def latest_agent_report(*, root: Path | None = None) -> str | None:
    reports_dir = (root or repo_root()) / "agent_reports"
    if not reports_dir.is_dir():
        return None
    reports = sorted(
        path
        for path in reports_dir.glob("*.md")
        if _REPORT_NAME_RE.match(path.name)
        and _BUILD_REPORT_NAME_RE.search(path.name)
    )
    if not reports:
        return None
    return str(reports[-1].relative_to(root or repo_root()))


def _find_active_queue_row(rows: list[QueueTicketRow]) -> QueueTicketRow | None:
    in_progress = [row for row in rows if row.status == "in_progress"]
    if in_progress:
        return min(in_progress, key=lambda row: row.order)
    open_rows = [row for row in rows if row.status in _OPEN_QUEUE_STATUSES]
    if not open_rows:
        return None
    return min(
        open_rows,
        key=lambda row: (_STATUS_PRIORITY.get(row.status, 99), row.order),
    )


def _ticket_ids_in_text(text: str) -> set[str]:
    return {f"ticket-{match.group(1)}" for match in _TICKET_ID_RE.finditer(text)}


def _ticket_ids_in_dirty_paths(dirty_paths: list[str]) -> set[str]:
    ticket_ids: set[str] = set()
    for line in dirty_paths:
        ticket_ids.update(_ticket_ids_in_text(line))
        normalized = line[3:].strip() if len(line) > 3 else line.strip()
        for hint, ticket_id in _PATH_TICKET_HINTS.items():
            if hint in normalized.replace("\\", "/"):
                ticket_ids.add(ticket_id)
    return ticket_ids


def _read_report_text(root: Path, relative_path: str | None) -> str:
    if not relative_path:
        return ""
    path = root / relative_path
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def is_audit_only_ticket(ticket_id: str, *, root: Path) -> bool:
    """Return True when a done ticket is audit/report-only (no code implementation)."""
    payload = load_queue_ticket_json(ticket_id, root=root)
    if not payload:
        return False
    affected = payload.get("affected_modules") or []
    expected = payload.get("expected_files") or []
    if affected:
        return False
    if expected and all(str(path).startswith("agent_reports/") for path in expected):
        return True
    title = str(payload.get("title", "")).lower()
    return "audit" in title and "checkpoint" in title


def _ticket_id_from_report_path(relative_path: str | None) -> str | None:
    if not relative_path:
        return None
    match = _TICKET_ID_RE.search(relative_path)
    return f"ticket-{match.group(1)}" if match else None


def _report_claims_positive_merge_to_main(report_text: str) -> bool:
    for line in report_text.splitlines():
        lowered = line.lower()
        if "merged to" not in lowered or "main" not in lowered:
            continue
        if "not merged" in lowered or ": no" in lowered or "awaiting" in lowered:
            continue
        if "yes" in lowered or "complete" in lowered or "at `" in lowered:
            return True
    return False


def ticket_has_implementation_commit(
    ticket_id: str,
    *,
    root: Path | None = None,
    log_runner: Callable[[list[str], Path], subprocess.CompletedProcess[str]] | None = None,
) -> bool:
    """Return whether main contains evidence the ticket was implemented.

    Checks commit messages for the ticket id and, when ``tickets/{id}.json``
    exists, whether that file appears in git history on main (covers commits
    whose messages omit the ticket id, e.g. ticket-043 on cc1c17c).
    """
    project_root = root or repo_root()
    runner = log_runner or (lambda argv, cwd: run_captured(argv, cwd=cwd))
    ticket_json_rel = f"tickets/{ticket_id}.json"
    ticket_json_on_disk = (project_root / ticket_json_rel).is_file()
    for ref in ("main", "HEAD"):
        result = runner(
            ["git", "log", ref, "--oneline", f"--grep={ticket_id}"],
            project_root,
        )
        if ticket_id in result.stdout:
            return True
        if ticket_json_on_disk:
            json_log = runner(
                ["git", "log", ref, "--oneline", "-1", "--", ticket_json_rel],
                project_root,
            )
            if json_log.stdout.strip():
                return True
    return False


def detect_documentation_git_drift(
    *,
    root: Path,
    working_tree: WorkingTreeStatus,
    rows: list[QueueTicketRow],
    active_row: QueueTicketRow | None,
    active_ticket_json: dict[str, Any] | None,
    latest_report_path: str | None,
    log_runner: Callable[[list[str], Path], subprocess.CompletedProcess[str]] | None = None,
) -> list[dict[str, str]]:
    """Detect documentation-ahead-of-git drift between queue, reports, and git."""
    violations: list[dict[str, str]] = []

    if active_row and active_row.status == "in_progress":
        ticket_id = active_row.ticket_id
        branch = working_tree.branch or ""
        if ticket_id not in branch.replace("_", "-"):
            violations.append(
                {
                    "kind": "branch_ticket_mismatch",
                    "message": (
                        f"Active ticket {ticket_id} is in_progress but current branch "
                        f"{branch!r} does not reference that ticket id."
                    ),
                }
            )

    report_text = _read_report_text(root, latest_report_path)
    report_ticket_id = _ticket_id_from_report_path(latest_report_path)
    if report_text and working_tree.branch:
        branch_match = _REPORT_BRANCH_RE.search(report_text)
        if branch_match:
            claimed_branch = branch_match.group(1).strip()
            merged_on_main = (
                working_tree.branch == "main"
                and report_ticket_id is not None
                and ticket_has_implementation_commit(
                    report_ticket_id,
                    root=root,
                    log_runner=log_runner,
                )
            )
            if (
                claimed_branch
                and claimed_branch != working_tree.branch
                and not merged_on_main
            ):
                violations.append(
                    {
                        "kind": "report_branch_mismatch",
                        "message": (
                            f"Latest report claims branch {claimed_branch!r} but git "
                            f"reports {working_tree.branch!r}."
                        ),
                    }
                )
        if _report_claims_positive_merge_to_main(report_text):
            merge_check = (
                log_runner(["git", "branch", "--show-current"], root)
                if log_runner is not None
                else run_captured(["git", "branch", "--show-current"], cwd=root)
            )
            current = merge_check.stdout.strip()
            if current and current != "main":
                violations.append(
                    {
                        "kind": "report_merge_claim_unverified",
                        "message": (
                            "Latest report claims a merge to main but the current "
                            f"branch is {current!r}."
                        ),
                    }
                )

    if (root / ".git").is_dir():
        for row in rows:
            if row.status != "done":
                continue
            if is_audit_only_ticket(row.ticket_id, root=root):
                continue
            if not ticket_has_implementation_commit(
                row.ticket_id,
                root=root,
                log_runner=log_runner,
            ):
                violations.append(
                    {
                        "kind": "done_without_implementation_commit",
                        "message": (
                            f"{row.ticket_id} is marked done in TICKET_QUEUE.md but "
                            "no matching implementation commit was found on main."
                        ),
                    }
                )

        if active_ticket_json and active_ticket_json.get("status") == "done":
            ticket_id = active_ticket_json.get("id")
            if isinstance(ticket_id, str) and not is_audit_only_ticket(
                ticket_id, root=root
            ) and not ticket_has_implementation_commit(
                ticket_id,
                root=root,
                log_runner=log_runner,
            ):
                violations.append(
                    {
                        "kind": "json_done_without_implementation_commit",
                        "message": (
                            f"{ticket_id} JSON status is done but git has no matching "
                            "implementation commit on main."
                        ),
                    }
                )

    dirty_ticket_ids = _ticket_ids_in_dirty_paths(working_tree.dirty_paths)
    if len(dirty_ticket_ids) > 1:
        violations.append(
            {
                "kind": "multi_ticket_dirty_tree",
                "message": (
                    "Working tree contains uncommitted changes spanning multiple "
                    f"tickets: {sorted(dirty_ticket_ids)}."
                ),
            }
        )

    return violations


def pending_improvement_tickets(
    *,
    root: Path | None = None,
    artifact_path: Path | None = None,
) -> dict[str, Any]:
    """Detect draft improvement tickets awaiting human promotion review."""
    project_root = root or repo_root()
    path = artifact_path or default_improvement_artifact_path(project_root)
    if not path.is_file():
        return {
            "pending": False,
            "artifact_path": str(path.relative_to(project_root)),
            "draft_count": 0,
            "draft_tickets": [],
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    tickets = payload if isinstance(payload, list) else [payload]
    drafts = [
        ticket
        for ticket in tickets
        if isinstance(ticket, dict)
        and ticket.get("status") == "draft"
        and improvement_draft_is_actionable(ticket)
    ]
    return {
        "pending": len(drafts) > 0,
        "artifact_path": str(path.relative_to(project_root)),
        "draft_count": len(drafts),
        "draft_tickets": [
            {
                "title": ticket.get("title"),
                "failure_reason": ticket.get("failure_reason"),
                "risk_level": ticket.get("risk_level"),
            }
            for ticket in drafts
        ],
    }


def _action_from_state(
    *,
    working_tree: WorkingTreeStatus,
    active_row: QueueTicketRow | None,
    active_ticket_json: dict[str, Any] | None,
    audit: dict[str, Any],
    improvement: dict[str, Any],
    drift_violations: list[dict[str, str]],
    scratch_evidence: dict[str, Any] | None = None,
    root: Path | None = None,
) -> RecommendedAction:
    safe_commands = safe_verification_commands(root)

    if drift_violations:
        return RecommendedAction(
            action_id="resolve_documentation_git_drift",
            label="Resolve documentation-ahead-of-git drift",
            gate="blocked",
            reason=drift_violations[0]["message"],
            commands=[
                {
                    "shell": "git status --short --branch",
                    "purpose": "inspect branch and dirty paths",
                },
                {
                    "shell": "python -m rge.modules.operator_loop --mode plan",
                    "purpose": "review drift findings",
                },
            ],
        )

    if not working_tree.clean:
        return RecommendedAction(
            action_id="resolve_dirty_working_tree",
            label="Resolve dirty working tree before operator actions",
            gate="blocked",
            reason=(
                f"Working tree has {len(working_tree.dirty_paths)} uncommitted "
                "change(s); operator loop refuses execute-safe until clean."
            ),
            commands=[
                {"shell": "git status --short", "purpose": "inspect dirty paths"}
            ],
        )

    if improvement["pending"]:
        return RecommendedAction(
            action_id="review_improvement_ticket_promotion",
            label="Review draft improvement ticket before promotion",
            gate="review_gated",
            reason=(
                f"{improvement['draft_count']} draft improvement ticket(s) in "
                f"{improvement['artifact_path']} require human review and explicit "
                "promote-improvement-ticket --confirm."
            ),
            commands=[
                {
                    "shell": (
                        "python -m rge.cli promote-improvement-ticket "
                        "--queue-ticket-id <id> --from-json "
                        f"{improvement['artifact_path']} --confirm"
                    ),
                    "purpose": "promote after human review",
                }
            ],
        )

    if audit.get("cadence_status") == "overdue":
        return RecommendedAction(
            action_id="run_principal_audit",
            label="Run principal audit checkpoint before next implementation",
            gate="review_gated",
            reason=audit.get("cadence_reason", "Principal audit cadence overdue."),
            commands=[
                {
                    "shell": "/rge-principal-audit",
                    "purpose": "principal audit checkpoint",
                },
                {
                    "shell": (
                        "python -m rge.modules.principal_audit_gate "
                        f"--next-ticket {active_row.ticket_id if active_row else '<id>'}"
                    ),
                    "purpose": "machine-readable audit status",
                },
            ],
        )

    next_ticket_id = active_row.ticket_id if active_row else None
    if (
        next_ticket_id
        and audit.get("implementation_gate") == "blocked_missing_pre_ticket_audit"
    ):
        return RecommendedAction(
            action_id="complete_pre_ticket_audit",
            label=f"Complete pre-ticket audit for {next_ticket_id}",
            gate="review_gated",
            reason=(
                f"{next_ticket_id} has risk_level "
                f"{audit.get('next_ticket_risk_level')} and requires a pre-ticket "
                "audit report in agent_reports/ before implementation."
            ),
            commands=[
                {
                    "shell": f"/rge-principal-audit (focused pre-ticket audit for {next_ticket_id})",
                    "purpose": "pre-ticket audit",
                }
            ],
        )

    if active_row and active_row.status in _OPEN_QUEUE_STATUSES:
        branch_hint = ""
        if active_ticket_json and active_ticket_json.get("title"):
            branch_hint = f": {active_ticket_json['title']}"
        return RecommendedAction(
            action_id="begin_ticket_implementation",
            label=f"Begin implementation for {active_row.ticket_id}{branch_hint}",
            gate="review_gated",
            reason=(
                f"{active_row.ticket_id} is {active_row.status} and passes audit "
                "gates; human or builder agent should create branch and implement."
            ),
            commands=[
                {
                    "shell": "/rge-run-next-ticket",
                    "purpose": "full ticket implementation workflow",
                },
                {
                    "shell": (
                        f"git checkout -b phase-<n>/{active_row.ticket_id}-<slug>"
                    ),
                    "purpose": "create implementation branch",
                },
            ],
        )

    if active_row and active_row.status == "in_progress":
        return RecommendedAction(
            action_id="continue_ticket_implementation",
            label=f"Continue in-progress ticket {active_row.ticket_id}",
            gate="review_gated",
            reason=(
                f"{active_row.ticket_id} is in_progress; finish implementation, "
                "tests, report, and merge checkpoint."
            ),
            commands=[
                {
                    "shell": f"Review tickets/{active_row.ticket_id}.json and latest agent report",
                    "purpose": "resume work",
                }
            ],
        )

    scratch = scratch_evidence or {}
    if scratch.get("evidence_review_ready"):
        evidence_command = scratch.get("operator_commands", {}).get(
            "evidence_review",
            "python -m rge.cli probe-scratch-evidence-review",
        )
        return RecommendedAction(
            action_id="run_scratch_evidence_review",
            label="Run scratch evidence review for operator/principal sign-off",
            gate="review_gated",
            reason=(
                f"Scratch DB at {scratch.get('scratch_db_path')} has "
                f"{scratch.get('total_reviewed_reports')} reviewed report(s); "
                "generate a deterministic evidence review artifact before seeding "
                "improvement tickets."
            ),
            commands=[
                {
                    "shell": evidence_command,
                    "purpose": "compose read-only evidence review from scratch DB",
                },
                {
                    "shell": (
                        "python -m rge.cli probe-scratch-evidence-review "
                        "--out agent_reports/YYYY-MM-DD_scratch-evidence-review.md"
                    ),
                    "purpose": "archive review markdown under agent_reports/",
                },
            ],
        )

    return RecommendedAction(
        action_id="run_deterministic_verification",
        label="Run deterministic mock-only verification checks",
        gate="safe_autonomous",
        reason=(
            "No open queue ticket requires immediate human action; safe to run "
            "mock-only golden tests, pytest, safety audit, and public-site build."
        ),
        commands=safe_commands,
    )


def inspect_scratch_evidence_status(
    *,
    root: Path | None = None,
    scratch_db: Path | None = None,
) -> dict[str, Any]:
    """Read-only scratch DB presence and reviewed-row counts for operator plan mode."""
    project_root = root or repo_root()
    scratch_path = get_scratch_db_path(scratch_db)
    if not scratch_path.is_absolute():
        scratch_path = project_root / scratch_path
    scratch_path = scratch_path.resolve()
    try:
        rel_path = scratch_path.relative_to(project_root.resolve()).as_posix()
    except ValueError:
        rel_path = scratch_path.as_posix()

    status: dict[str, Any] = {
        "scratch_db_path": rel_path,
        "scratch_db_exists": scratch_path.is_file(),
        "readable": False,
        "total_reviewed_reports": None,
        "evidence_review_ready": False,
        "summary_ready": False,
        "status": "missing",
        "error": None,
        "operator_commands": {
            "summary": "python -m rge.cli probe-scratch-summary --allow-empty",
            "evidence_review": (
                "python -m rge.cli probe-scratch-evidence-review --allow-empty"
            ),
        },
    }

    if not scratch_path.is_file():
        status["error"] = f"scratch DB not found: {rel_path}"
        return status

    try:
        conn = connect_scratch_readonly(scratch_path)
        try:
            validate_scratch_schema(conn)
            row = conn.execute(
                f"SELECT COUNT(*) AS total FROM {REVIEWED_TABLE}"
            ).fetchone()
            total = int(row["total"]) if row is not None else 0
        finally:
            conn.close()
    except LiveProbeScratchSummaryError as exc:
        status["status"] = "invalid"
        status["error"] = str(exc)
        return status
    except (OSError, sqlite3.Error) as exc:
        status["status"] = "error"
        status["error"] = str(exc)
        return status

    status["readable"] = True
    status["total_reviewed_reports"] = total
    status["summary_ready"] = True
    status["evidence_review_ready"] = total > 0
    status["status"] = "ok" if total > 0 else "empty"
    return status


def inspect_domain_pack_status(
    *,
    root: Path | None = None,
    pack_id: str = "creativity",
) -> dict[str, Any]:
    """Read-only creativity domain pack load health for operator plan mode."""
    return inspect_domain_pack_load_health(pack_id, root=root or repo_root())


def inspect_nm4_evidence_spine_status(
    *,
    root: Path | None = None,
    evidence_db: Path | None = None,
) -> dict[str, Any]:
    """Read-only NM-4 gitignored evidence DB spine counts for operator plan mode."""
    project_root = root or repo_root()
    db_path = evidence_db if evidence_db is not None else Path(
        "data/db/live_research_evidence.sqlite"
    )
    if not db_path.is_absolute():
        db_path = project_root / db_path
    db_path = db_path.resolve()
    try:
        rel_path = db_path.relative_to(project_root.resolve()).as_posix()
    except ValueError:
        rel_path = db_path.as_posix()

    status: dict[str, Any] = {
        "evidence_db_path": rel_path,
        "evidence_db_exists": db_path.is_file(),
        "readable": False,
        "source_count": None,
        "manual_text_source_count": None,
        "accepted_claim_count": None,
        "concept_link_count": None,
        "active_relationship_count": None,
        "relationship_evidence_count": None,
        "qualification_link_count": None,
        "score_event_count": None,
        "spine_milestones": {
            "sources": False,
            "accepted_claims": False,
            "concept_links": False,
            "active_relationships": False,
            "relationship_evidence": False,
            "qualification_links": False,
            "score_events": False,
        },
        "spine_stage": "missing",
        "status": "missing",
        "error": None,
        "operator_commands": {
            "ingest": (
                "python -m rge.cli ingest <manual_text> --domain creativity "
                "--source-type manual_text --db data/db/live_research_evidence.sqlite"
            ),
            "live_extract": (
                "python -m rge.cli extract-claims --source <id> "
                "--db data/db/live_research_evidence.sqlite --live-manual-fallthrough"
            ),
            "reconcile": (
                "python -m rge.cli reconcile-scores --source <followup_id> "
                "--db data/db/live_research_evidence.sqlite --evidence-db-reconcile"
            ),
        },
    }

    if not db_path.is_file():
        status["error"] = f"evidence DB not found: {rel_path}"
        return status

    try:
        conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            source_count = int(
                conn.execute("SELECT COUNT(*) AS n FROM sources").fetchone()["n"]
            )
            manual_text_source_count = int(
                conn.execute(
                    "SELECT COUNT(*) AS n FROM sources WHERE source_type = 'manual_text'"
                ).fetchone()["n"]
            )
            accepted_claim_count = int(
                conn.execute(
                    "SELECT COUNT(*) AS n FROM claims WHERE status = 'accepted'"
                ).fetchone()["n"]
            )
            concept_link_count = int(
                conn.execute("SELECT COUNT(*) AS n FROM claim_concepts").fetchone()["n"]
            )
            active_relationship_count = int(
                conn.execute(
                    "SELECT COUNT(*) AS n FROM relationships WHERE status = 'active'"
                ).fetchone()["n"]
            )
            relationship_evidence_count = int(
                conn.execute("SELECT COUNT(*) AS n FROM relationship_evidence").fetchone()[
                    "n"
                ]
            )
            qualification_link_count = int(
                conn.execute(
                    "SELECT COUNT(*) AS n FROM relationship_evidence "
                    "WHERE stance = 'qualifies'"
                ).fetchone()["n"]
            )
            score_event_count = int(
                conn.execute("SELECT COUNT(*) AS n FROM score_events").fetchone()["n"]
            )
        finally:
            conn.close()
    except (OSError, sqlite3.Error) as exc:
        status["status"] = "error"
        status["spine_stage"] = "error"
        status["error"] = str(exc)
        return status

    milestones = {
        "sources": source_count > 0,
        "accepted_claims": accepted_claim_count > 0,
        "concept_links": concept_link_count > 0,
        "active_relationships": active_relationship_count > 0,
        "relationship_evidence": relationship_evidence_count > 0,
        "qualification_links": qualification_link_count > 0,
        "score_events": score_event_count > 0,
    }
    status["readable"] = True
    status["source_count"] = source_count
    status["manual_text_source_count"] = manual_text_source_count
    status["accepted_claim_count"] = accepted_claim_count
    status["concept_link_count"] = concept_link_count
    status["active_relationship_count"] = active_relationship_count
    status["relationship_evidence_count"] = relationship_evidence_count
    status["qualification_link_count"] = qualification_link_count
    status["score_event_count"] = score_event_count
    status["spine_milestones"] = milestones

    if source_count == 0:
        status["spine_stage"] = "empty"
        status["status"] = "empty"
    elif score_event_count > 0:
        status["spine_stage"] = "reconciled"
        status["status"] = "ok"
    else:
        status["spine_stage"] = "partial"
        status["status"] = "partial"
    return status


def build_operator_plan(
    *,
    root: Path | None = None,
    working_tree: WorkingTreeStatus | None = None,
    improvement_artifact: Path | None = None,
    log_runner: Callable[[list[str], Path], subprocess.CompletedProcess[str]] | None = None,
) -> dict[str, Any]:
    """Inspect repo state and return machine-readable operator loop plan."""
    project_root = root or repo_root()
    queue_path = project_root / "tickets" / "TICKET_QUEUE.md"
    queue_text = queue_path.read_text(encoding="utf-8") if queue_path.is_file() else ""
    rows = parse_queue_rows(queue_text)
    active_row = _find_active_queue_row(rows)
    active_ticket_json = (
        load_queue_ticket_json(active_row.ticket_id, root=project_root)
        if active_row
        else None
    )
    tree = working_tree or inspect_working_tree(project_root)
    next_ticket_id = active_row.ticket_id if active_row else None
    audit = checkpoint_status(root=project_root, next_ticket_id=next_ticket_id)
    improvement = pending_improvement_tickets(
        root=project_root,
        artifact_path=improvement_artifact,
    )
    latest_report = latest_agent_report(root=project_root)
    drift_violations = detect_documentation_git_drift(
        root=project_root,
        working_tree=tree,
        rows=rows,
        active_row=active_row,
        active_ticket_json=active_ticket_json,
        latest_report_path=latest_report,
        log_runner=log_runner,
    )
    scratch_evidence = inspect_scratch_evidence_status(root=project_root)
    domain_pack_status = inspect_domain_pack_status(root=project_root)
    nm4_evidence_spine_status = inspect_nm4_evidence_spine_status(root=project_root)
    action = _action_from_state(
        working_tree=tree,
        active_row=active_row,
        active_ticket_json=active_ticket_json,
        audit=audit,
        improvement=improvement,
        drift_violations=drift_violations,
        scratch_evidence=scratch_evidence,
        root=project_root,
    )

    ticket_json_index = {
        path.stem: str(path.relative_to(project_root))
        for path in list_ticket_json_files(root=project_root)
    }

    return {
        "report_type": "operator_loop_status",
        "mode": "plan",
        "working_tree": {
            "clean": tree.clean,
            "branch": tree.branch,
            "dirty_paths": tree.dirty_paths,
        },
        "current_ticket": {
            "ticket_id": active_row.ticket_id if active_row else None,
            "queue_status": active_row.status if active_row else None,
            "queue_order": active_row.order if active_row else None,
            "json_path": (
                ticket_json_index.get(active_row.ticket_id)
                if active_row and active_row.ticket_id in ticket_json_index
                else None
            ),
            "json_status": (
                active_ticket_json.get("status") if active_ticket_json else None
            ),
            "risk_level": (
                active_ticket_json.get("risk_level") if active_ticket_json else None
            ),
            "title": active_ticket_json.get("title") if active_ticket_json else None,
        },
        "queue_summary": {
            "total_rows": len(rows),
            "open_ticket_ids": [
                row.ticket_id
                for row in rows
                if row.status in _OPEN_QUEUE_STATUSES or row.status == "in_progress"
            ],
            "ticket_json_files": ticket_json_index,
        },
        "latest_agent_report": latest_report,
        "documentation_git_drift": {
            "detected": len(drift_violations) > 0,
            "violations": drift_violations,
        },
        "audit_cadence": audit,
        "scratch_evidence_status": scratch_evidence,
        "domain_pack_status": domain_pack_status,
        "nm4_evidence_spine_status": nm4_evidence_spine_status,
        "pending_improvement_tickets": improvement,
        "next_recommended_action": {
            "action_id": action.action_id,
            "label": action.label,
            "gate": action.gate,
            "reason": action.reason,
            "commands": action.commands,
        },
        "safe_verification_commands": safe_verification_commands(project_root),
        "execute_safe_eligible": tree.clean and action.gate != "blocked",
        "forbidden_operator_actions": [
            "merge to main",
            "git push",
            "promote improvement tickets without --confirm",
            "edit TICKET_QUEUE.md",
            "export-public --publish",
            "enable live LLM mode",
            "run live_smoke tests",
        ],
    }


def _assert_safe_command(command: dict[str, Any]) -> None:
    shell_repr = command.get("shell", "")
    name = command.get("name", "")
    allowed_names = {item["name"] for item in safe_verification_commands()}
    if name and name not in allowed_names:
        raise ValueError(f"command {name!r} is not in the safe verification allowlist")
    combined = shell_repr.lower()
    for pattern in _FORBIDDEN_EXECUTE_PATTERNS:
        if pattern.lower() in combined:
            raise ValueError(f"forbidden pattern in command: {pattern}")


def execute_safe_checks(
    *,
    root: Path | None = None,
    working_tree: WorkingTreeStatus | None = None,
    command_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> dict[str, Any]:
    """Run deterministic safe checks when the working tree is clean."""
    project_root = root or repo_root()
    plan = build_operator_plan(root=project_root, working_tree=working_tree)
    plan["mode"] = "execute-safe"

    if not plan["execute_safe_eligible"]:
        plan["execution_results"] = []
        plan["execution_status"] = "blocked"
        return plan

    runner = command_runner or run_captured
    results: list[dict[str, Any]] = []
    all_passed = True
    for command in plan["safe_verification_commands"]:
        _assert_safe_command(command)
        env = os.environ.copy()
        env.update(command.get("env", {}))
        completed = runner(
            command["argv"],
            cwd=command["cwd"],
            env=env,
        )
        passed = completed.returncode == 0
        all_passed = all_passed and passed
        results.append(
            {
                "name": command["name"],
                "shell": command["shell"],
                "exit_code": completed.returncode,
                "passed": passed,
                "stdout_tail": completed.stdout[-500:] if completed.stdout else "",
                "stderr_tail": completed.stderr[-500:] if completed.stderr else "",
            }
        )

    plan["execution_results"] = results
    plan["execution_status"] = "pass" if all_passed else "fail"
    return plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Bounded operator loop: inspect repo state (plan) or run safe "
            "deterministic checks (execute-safe). Mock-only; no merge/push/promote."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("plan", "execute-safe"),
        default="plan",
        help="plan=read-only JSON status; execute-safe=run allowlisted mock checks.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root (defaults to package parent).",
    )
    args = parser.parse_args(argv)
    if args.mode == "plan":
        payload = build_operator_plan(root=args.root)
    else:
        payload = execute_safe_checks(root=args.root)
    print(json.dumps(payload, indent=2))
    if args.mode == "execute-safe":
        if payload.get("execution_status") == "blocked":
            return 2
        if payload.get("execution_status") == "fail":
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
