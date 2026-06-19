"""Bounded autocycle planner for RGE audit + run-next-ticket loop safety.

Combines principal gate inspection with operator_loop planning. Never implements
tickets, merges, pushes, or edits the queue. ``execute-safe`` may run the same
mock-only verification allowlist as ``operator_loop``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

from rge.modules.operator_loop import (
    WorkingTreeStatus,
    build_operator_plan,
    execute_safe_checks,
    inspect_working_tree,
    load_queue_ticket_json,
)
from rge.modules.principal_audit_gate import (
    _LOW_VALUE_CLASSIFICATIONS,
    classify_ticket_value,
    checkpoint_status,
    parse_queue_rows,
    repo_root,
)

MAX_CYCLES_HARD_CAP = 10
DEFAULT_MAX_CYCLES = 1

_DEFERRED_OPEN_TICKETS = frozenset({"ticket-059"})


def _resolve_autocycle_ticket_id(
    *,
    root: Path,
    explicit_next_ticket: str | None,
    plan: dict[str, Any],
) -> str | None:
    if explicit_next_ticket:
        return explicit_next_ticket
    queue_path = root / "tickets" / "TICKET_QUEUE.md"
    rows = parse_queue_rows(
        queue_path.read_text(encoding="utf-8") if queue_path.is_file() else ""
    )
    open_rows = [
        row
        for row in rows
        if row.status in {"proposed", "ready", "in_progress"}
        and row.ticket_id not in _DEFERRED_OPEN_TICKETS
    ]
    if open_rows:
        if any(row.status == "in_progress" for row in open_rows):
            active = min(
                (row for row in open_rows if row.status == "in_progress"),
                key=lambda row: row.order,
            )
            return active.ticket_id
        return max(open_rows, key=lambda row: row.order).ticket_id
    current = plan.get("current_ticket") or {}
    return current.get("ticket_id")


def _current_ticket_view(
    ticket_id: str | None,
    *,
    root: Path,
    plan: dict[str, Any],
) -> dict[str, Any]:
    if not ticket_id:
        return plan.get("current_ticket") or {}
    payload = load_queue_ticket_json(ticket_id, root=root)
    queue_path = root / "tickets" / "TICKET_QUEUE.md"
    rows = parse_queue_rows(
        queue_path.read_text(encoding="utf-8") if queue_path.is_file() else ""
    )
    row = next((item for item in rows if item.ticket_id == ticket_id), None)
    json_path = f"tickets/{ticket_id}.json"
    return {
        "ticket_id": ticket_id,
        "queue_status": row.status if row else None,
        "queue_order": row.order if row else None,
        "json_path": json_path if (root / json_path).is_file() else None,
        "json_status": payload.get("status") if payload else None,
        "risk_level": payload.get("risk_level") if payload else None,
        "title": payload.get("title") if payload else None,
    }


_DOCS_ONLY_CLASSES = frozenset(_LOW_VALUE_CLASSIFICATIONS)

_LIVE_REQUIREMENT_HINTS = (
    "live ollama",
    "live network",
    "openalex network",
    "browser automation",
    "cloud provider",
    "live_smoke",
    "rge_allow_live_llm",
    "rge_allow_source_network",
    "extract-claims-live",
    "ollama",
    "openrouter",
    "openai",
)

_PUBLIC_SURFACE_HINTS = (
    "apps/public-site",
    "export-public",
    "card_exporter",
    "public_export",
    "public-site",
)


def _clamp_max_cycles(value: int) -> int:
    return max(1, min(value, MAX_CYCLES_HARD_CAP))


def _ticket_payload_text(payload: dict[str, Any] | None, *, include_non_goals: bool = False) -> str:
    if not payload:
        return ""
    parts = [
        str(payload.get("title", "")),
        str(payload.get("problem", "")),
        " ".join(str(item) for item in payload.get("affected_modules", [])),
        " ".join(str(item) for item in payload.get("expected_files", [])),
        " ".join(str(item) for item in payload.get("acceptance_criteria", [])),
    ]
    if include_non_goals:
        parts.append(" ".join(str(item) for item in payload.get("non_goals", [])))
    return " ".join(parts).casefold()


def _requires_live_capabilities(payload: dict[str, Any] | None) -> bool:
    text = _ticket_payload_text(payload, include_non_goals=False)
    return any(hint in text for hint in _LIVE_REQUIREMENT_HINTS)


def _touches_public_surface(payload: dict[str, Any] | None) -> bool:
    if not payload:
        return False
    for path in payload.get("expected_files", []):
        normalized = str(path).replace("\\", "/").casefold()
        if any(hint in normalized for hint in _PUBLIC_SURFACE_HINTS):
            return True
    for module in payload.get("affected_modules", []):
        normalized = str(module).replace("\\", "/").casefold()
        if any(hint in normalized for hint in _PUBLIC_SURFACE_HINTS):
            return True
    return False


def _last_done_ticket_title(rows: list[Any]) -> str | None:
    done = [row for row in rows if row.status == "done"]
    if not done:
        return None
    return done[-1].title or None


def _is_docs_only_title(title: str | None) -> bool:
    if not title:
        return False
    return classify_ticket_value(title) in _DOCS_ONLY_CLASSES


def _queue_gate_disagreement(
    audit: dict[str, Any],
    resolved_ticket_id: str | None,
) -> str | None:
    audit_ticket = audit.get("next_ticket_id")
    if resolved_ticket_id and audit_ticket and resolved_ticket_id != audit_ticket:
        return (
            f"Resolved ticket {resolved_ticket_id!r} disagrees with gate next ticket "
            f"{audit_ticket!r}."
        )
    return None


def _shell_command(entry: dict[str, Any]) -> str:
    return str(entry.get("shell") or " ".join(entry.get("argv", [])))


def evaluate_autocycle_cycle(
    *,
    root: Path | None = None,
    working_tree: WorkingTreeStatus | None = None,
    allow_medium: bool = False,
    allow_high: bool = False,
    allow_docs_streak: bool = False,
    allow_live: bool = False,
    allow_public_surface: bool = False,
    explicit_next_ticket: str | None = None,
) -> dict[str, Any]:
    """Evaluate one autocycle iteration and return structured stop/proceed data."""
    project_root = root or repo_root()
    tree = working_tree or inspect_working_tree(project_root)
    plan = build_operator_plan(root=project_root, working_tree=tree)
    ticket_id = _resolve_autocycle_ticket_id(
        root=project_root,
        explicit_next_ticket=explicit_next_ticket,
        plan=plan,
    )
    current = _current_ticket_view(ticket_id, root=project_root, plan=plan)
    audit = checkpoint_status(root=project_root, next_ticket_id=ticket_id)
    ticket_json = (
        load_queue_ticket_json(ticket_id, root=project_root) if ticket_id else None
    )

    action = plan.get("next_recommended_action") or {}
    drift_warning = audit.get("drift_warning")
    audit_required = audit.get("cadence_status") == "overdue"
    pre_ticket_required = (
        audit.get("implementation_gate") == "blocked_missing_pre_ticket_audit"
    )
    value_class = classify_ticket_value(
        str((ticket_json or {}).get("title") or audit.get("next_ticket_title") or "")
    )

    result: dict[str, Any] = {
        "status": "proceed",
        "stop_reason": None,
        "current_ticket": current,
        "gate_status": audit.get("status"),
        "audit_required": audit_required,
        "pre_ticket_audit_required": pre_ticket_required,
        "drift_warning": drift_warning,
        "scratch_evidence_status": plan.get("scratch_evidence_status") or {},
        "autonomous_loop_scratch_status": plan.get("autonomous_loop_scratch_status")
        or {},
        "autonomous_loop_improvement_status": plan.get(
            "autonomous_loop_improvement_status"
        )
        or {},
        "arbitrary_source_proof_bundle_status": plan.get(
            "arbitrary_source_proof_bundle_status"
        )
        or {},
        "staged_rank2_scan_max": plan.get("staged_rank2_scan_max"),
        "scratch_evidence_review_recommended": False,
        "proof_bundle_recommended": False,
        "run_next_ticket_allowed": False,
        "next_command": None,
        "next_commands": [],
        "recommended_action": action,
        "ticket_value_class": value_class,
        "execute_safe_eligible": False,
    }

    def stop(
        reason: str,
        *,
        next_cmd: str | None = None,
        commands: list[str] | None = None,
    ) -> dict[str, Any]:
        result["status"] = "stopped"
        result["stop_reason"] = reason
        if next_cmd:
            result["next_command"] = next_cmd
        if commands:
            result["next_commands"] = commands
        return result

    if not tree.clean:
        return stop(
            "working_tree_dirty",
            next_cmd="git status --short",
            commands=["git status --short"],
        )

    if plan.get("documentation_git_drift", {}).get("detected"):
        violation = plan["documentation_git_drift"]["violations"][0]["message"]
        return stop(
            f"documentation_git_drift: {violation}",
            next_cmd="python -m rge.modules.operator_loop --mode plan",
        )

    disagreement = _queue_gate_disagreement(audit, ticket_id)
    if disagreement:
        return stop(f"queue_gate_disagreement: {disagreement}")

    if ticket_id and ticket_json is None:
        return stop(f"unknown_ticket_metadata: missing tickets/{ticket_id}.json")

    if ticket_id and not ticket_json.get("id"):
        return stop("unknown_ticket_metadata: ticket JSON missing id field")

    if audit_required:
        return stop(
            "principal_audit_cadence_overdue",
            next_cmd="/rge-principal-audit",
            commands=[
                "/rge-principal-audit",
                (
                    "python -m rge.modules.principal_audit_gate "
                    f"--next-ticket {ticket_id or '<id>'}"
                ),
            ],
        )

    if pre_ticket_required:
        return stop(
            f"pre_ticket_audit_missing for {ticket_id}",
            next_cmd=f"/rge-principal-audit (pre-ticket audit for {ticket_id})",
        )

    scratch_evidence = plan.get("scratch_evidence_status") or {}
    action = plan.get("next_recommended_action") or {}
    action_id = action.get("action_id")
    if (
        scratch_evidence.get("evidence_review_ready")
        and action_id == "run_scratch_evidence_review"
    ):
        commands = [_shell_command(cmd) for cmd in action.get("commands", [])]
        result["scratch_evidence_review_recommended"] = True
        result["recommended_action"] = action
        return stop(
            "operator_action_blocked_automation: run_scratch_evidence_review",
            next_cmd=commands[0] if commands else None,
            commands=commands,
        )

    proof_bundle_status = plan.get("arbitrary_source_proof_bundle_status") or {}
    if (
        proof_bundle_status.get("proof_bundle_recommended")
        and action_id == "run_arbitrary_source_proof_bundle"
    ):
        commands = [_shell_command(cmd) for cmd in action.get("commands", [])]
        result["proof_bundle_recommended"] = True
        result["recommended_action"] = action
        return stop(
            "operator_action_blocked_automation: run_arbitrary_source_proof_bundle",
            next_cmd=commands[0] if commands else None,
            commands=commands,
        )

    if drift_warning:
        return stop(
            f"drift_warning_active: {'; '.join(drift_warning)}",
            next_cmd=audit.get("recommended_override")
            or "/rge-principal-audit",
        )

    risk_level = str(
        (ticket_json or {}).get("risk_level")
        or audit.get("next_ticket_risk_level")
        or ""
    ).casefold()
    if risk_level == "high" and not allow_high:
        return stop(
            f"high_risk_ticket_requires_explicit_allow_high: {ticket_id}",
            next_cmd=f"/rge-principal-audit (pre-ticket audit for {ticket_id})",
        )
    if risk_level == "medium" and not allow_medium:
        return stop(
            f"medium_risk_ticket_requires_explicit_allow_medium: {ticket_id}",
            next_cmd=f"/rge-principal-audit (pre-ticket audit for {ticket_id})",
        )

    if ticket_json and _requires_live_capabilities(ticket_json) and not allow_live:
        return stop(
            f"live_capabilities_required: {ticket_id}",
            next_cmd=(
                "Review ticket non_goals and set explicit live env before agent run"
            ),
        )

    if ticket_json and _touches_public_surface(ticket_json) and not allow_public_surface:
        return stop(
            f"public_surface_mutation: {ticket_id}",
            next_cmd="/rge-principal-audit (pre-ticket audit for public surface ticket)",
        )

    queue_path = project_root / "tickets" / "TICKET_QUEUE.md"
    rows = parse_queue_rows(
        queue_path.read_text(encoding="utf-8") if queue_path.is_file() else ""
    )
    last_done_title = _last_done_ticket_title(rows)
    next_title = str(ticket_json.get("title") if ticket_json else "")
    if (
        not allow_docs_streak
        and _is_docs_only_title(next_title)
        and _is_docs_only_title(last_done_title)
    ):
        return stop(
            "docs_only_streak: consecutive docs/checkpoint tickets blocked",
            next_cmd=audit.get("recommended_override")
            or "/rge-principal-audit",
        )

    action = plan.get("next_recommended_action") or {}
    action_id = action.get("action_id")
    gate = action.get("gate")

    active_row = next((row for row in rows if row.ticket_id == ticket_id), None)
    if active_row and active_row.status in {"proposed", "ready"}:
        result["run_next_ticket_allowed"] = True
        return stop(
            "ticket_implementation_requires_agent: /rge-run-next-ticket is prompt-only",
            next_cmd="/rge-run-next-ticket",
            commands=["/rge-run-next-ticket"],
        )

    if active_row and active_row.status == "in_progress":
        return stop(
            "operator_action_blocked_automation: continue_ticket_implementation",
            next_cmd="Review latest agent report and resume ticket branch",
        )

    if action_id == "begin_ticket_implementation" and ticket_id:
        result["run_next_ticket_allowed"] = True
        commands = [_shell_command(cmd) for cmd in action.get("commands", [])]
        return stop(
            "ticket_implementation_requires_agent: /rge-run-next-ticket is prompt-only",
            next_cmd="/rge-run-next-ticket",
            commands=commands or ["/rge-run-next-ticket"],
        )

    if action_id in {
        "continue_ticket_implementation",
        "complete_pre_ticket_audit",
        "run_principal_audit",
        "review_improvement_ticket_promotion",
        "resolve_documentation_git_drift",
        "resolve_dirty_working_tree",
        "run_scratch_evidence_review",
        "run_arbitrary_source_proof_bundle",
    }:
        commands = [_shell_command(cmd) for cmd in action.get("commands", [])]
        return stop(
            f"operator_action_blocked_automation: {action_id}",
            next_cmd=commands[0] if commands else None,
            commands=commands,
        )

    if gate == "blocked":
        return stop(
            action.get("reason", "operator_loop_blocked"),
            next_cmd="python -m rge.modules.operator_loop --mode plan",
        )

    if action_id in {
        "run_deterministic_verification",
        "run_autonomous_researcher_loop",
    } and gate == "safe_autonomous":
        result["execute_safe_eligible"] = True
        result["next_command"] = (
            "python -m rge.modules.operator_autocycle --mode execute-safe"
        )
        result["next_commands"] = [
            _shell_command(cmd) for cmd in plan.get("safe_verification_commands", [])
        ]
        if action_id == "run_autonomous_researcher_loop":
            from rge.modules.operator_loop import autonomous_loop_safe_commands

            result["next_commands"].extend(
                _shell_command(cmd)
                for cmd in autonomous_loop_safe_commands(project_root)
            )
        return result

    return stop(
        action.get("reason", "no_automated_action_available"),
        next_cmd="python -m rge.modules.operator_loop --mode plan",
    )


def run_autocycle(
    *,
    mode: str,
    max_cycles: int = DEFAULT_MAX_CYCLES,
    root: Path | None = None,
    allow_medium: bool = False,
    allow_high: bool = False,
    allow_docs_streak: bool = False,
    allow_live: bool = False,
    allow_public_surface: bool = False,
    next_ticket: str | None = None,
    execute_runner: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run up to ``max_cycles`` bounded autocycle iterations."""
    project_root = root or repo_root()
    cycles_requested = _clamp_max_cycles(max_cycles)
    cycles: list[dict[str, Any]] = []
    cycles_completed = 0
    overall_status = "completed"
    final_stop_reason: str | None = None

    runner = execute_runner or execute_safe_checks

    for index in range(cycles_requested):
        evaluation = evaluate_autocycle_cycle(
            root=project_root,
            allow_medium=allow_medium,
            allow_high=allow_high,
            allow_docs_streak=allow_docs_streak,
            allow_live=allow_live,
            allow_public_surface=allow_public_surface,
            explicit_next_ticket=next_ticket,
        )
        evaluation["cycle_index"] = index + 1
        cycles.append(evaluation)
        cycles_completed = index + 1

        if evaluation["status"] == "stopped":
            overall_status = "stopped"
            final_stop_reason = evaluation.get("stop_reason")
            break

        if mode == "plan":
            overall_status = "planned"
            break

        if mode == "execute-safe":
            if not evaluation.get("execute_safe_eligible"):
                overall_status = "stopped"
                final_stop_reason = "execute_safe_not_eligible"
                break
            executed = runner(root=project_root)
            evaluation["execution"] = executed
            if executed.get("execution_status") == "pass":
                refreshed_scratch = executed.get("autonomous_loop_scratch_status")
                if refreshed_scratch:
                    evaluation["autonomous_loop_scratch_status"] = refreshed_scratch
                refreshed_improvement = executed.get("autonomous_loop_improvement_status")
                if refreshed_improvement:
                    evaluation["autonomous_loop_improvement_status"] = refreshed_improvement
                refreshed_action = executed.get("next_recommended_action")
                if refreshed_action:
                    evaluation["recommended_action"] = refreshed_action
            if executed.get("execution_status") != "pass":
                overall_status = "stopped"
                final_stop_reason = "verification_failed"
                break
            break

    last = cycles[-1] if cycles else {}
    return {
        "report_type": "operator_autocycle_status",
        "status": overall_status,
        "mode": mode,
        "cycles_requested": cycles_requested,
        "cycles_completed": cycles_completed,
        "current_ticket": last.get("current_ticket"),
        "gate_status": last.get("gate_status"),
        "audit_required": last.get("audit_required"),
        "pre_ticket_audit_required": last.get("pre_ticket_audit_required"),
        "drift_warning": last.get("drift_warning"),
        "scratch_evidence_status": last.get("scratch_evidence_status") or {},
        "autonomous_loop_scratch_status": last.get("autonomous_loop_scratch_status")
        or {},
        "autonomous_loop_improvement_status": last.get(
            "autonomous_loop_improvement_status"
        )
        or {},
        "recommended_action": last.get("recommended_action") or {},
        "arbitrary_source_proof_bundle_status": last.get(
            "arbitrary_source_proof_bundle_status"
        )
        or {},
        "staged_rank2_scan_max": last.get("staged_rank2_scan_max"),
        "scratch_evidence_review_recommended": last.get(
            "scratch_evidence_review_recommended", False
        ),
        "proof_bundle_recommended": last.get("proof_bundle_recommended", False),
        "run_next_ticket_allowed": last.get("run_next_ticket_allowed"),
        "stop_reason": final_stop_reason or last.get("stop_reason"),
        "next_command": last.get("next_command"),
        "next_commands": last.get("next_commands", []),
        "cycles": cycles,
        "forbidden_actions": [
            "git push",
            "git merge",
            "autonomous ticket implementation",
            "TICKET_QUEUE.md edits",
            "promote-improvement-ticket without --confirm",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Bounded autocycle planner for RGE audit + run-next-ticket safety. "
            "Never merges, pushes, or implements tickets."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("plan", "execute-safe"),
        default="plan",
        help="plan=read-only; execute-safe=mock verification when safe_autonomous only.",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=DEFAULT_MAX_CYCLES,
        help=(
            f"Maximum iterations (default {DEFAULT_MAX_CYCLES}, "
            f"hard cap {MAX_CYCLES_HARD_CAP})."
        ),
    )
    parser.add_argument(
        "--next-ticket",
        help="Optional ticket id override (e.g. ticket-167).",
    )
    parser.add_argument(
        "--allow-medium",
        action="store_true",
        help="Allow planning past medium-risk gate (still stops before implementation).",
    )
    parser.add_argument(
        "--allow-high",
        action="store_true",
        help="Allow planning past high-risk gate (still stops before implementation).",
    )
    parser.add_argument(
        "--allow-docs-streak",
        action="store_true",
        help="Allow consecutive docs/checkpoint tickets.",
    )
    parser.add_argument(
        "--allow-live",
        action="store_true",
        help="Allow tickets that require live network/Ollama/cloud capabilities.",
    )
    parser.add_argument(
        "--allow-public-surface",
        action="store_true",
        help="Allow tickets that touch public export/site surfaces.",
    )
    parser.add_argument("--root", type=Path, default=None, help="Repository root.")
    args = parser.parse_args(argv)

    payload = run_autocycle(
        mode=args.mode,
        max_cycles=args.max_cycles,
        root=args.root,
        allow_medium=args.allow_medium,
        allow_high=args.allow_high,
        allow_docs_streak=args.allow_docs_streak,
        allow_live=args.allow_live,
        allow_public_surface=args.allow_public_surface,
        next_ticket=args.next_ticket,
    )
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] in {"completed", "planned"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
