"""Principal audit checkpoint status for builder agents (read-only, no side effects)."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_QUEUE_PATH = _REPO_ROOT / "tickets" / "TICKET_QUEUE.md"
_REPORTS_DIR = _REPO_ROOT / "agent_reports"

_CONSECUTIVE_DONE_THRESHOLD = 3
_QUEUE_ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|\s*(ticket-\d{3})\s*\|\s*(\w+)\s*\|\s*([^|]+?)\s*\|",
    re.MULTILINE,
)
_PRINCIPAL_AUDIT_RE = re.compile(
    r"pre-phase-\d+-principal-audit|principal-audit",
    re.IGNORECASE,
)
_PRE_TICKET_RE = re.compile(r"pre-ticket-(\d{3})", re.IGNORECASE)
_POST_TICKET_RE = re.compile(r"post-ticket-(\d{3})", re.IGNORECASE)
_PRE_PHASE_RE = re.compile(r"pre-phase-(\d+)[-_]principal-audit", re.IGNORECASE)

# Phase boundary ticket numbers: principal audits at phase start reference this ticket.
_PHASE_BOUNDARY_TICKET = {2: 33}

_LEGACY_PRINCIPAL_ORDER_CUTOFF = 33


@dataclass(frozen=True)
class CheckpointReport:
    path: Path
    kind: str  # principal | pre_ticket
    ticket_number: int | None


@dataclass(frozen=True)
class QueueTicketRow:
    order: int
    ticket_id: str
    status: str
    title: str = ""


def repo_root() -> Path:
    return _REPO_ROOT


def parse_queue_rows(queue_text: str) -> list[QueueTicketRow]:
    rows: list[QueueTicketRow] = []
    for match in _QUEUE_ROW_RE.finditer(queue_text):
        title = match.group(4).strip() if match.lastindex and match.lastindex >= 4 else ""
        rows.append(
            QueueTicketRow(
                order=int(match.group(1)),
                ticket_id=match.group(2),
                status=match.group(3).strip().lower(),
                title=title,
            )
        )
    return rows


def _ticket_number_from_id(ticket_id: str) -> int:
    return int(ticket_id.split("-")[1])


def _parse_checkpoint_report(path: Path) -> CheckpointReport | None:
    name = path.name.lower()
    pre_match = _PRE_TICKET_RE.search(name)
    if pre_match:
        return CheckpointReport(
            path=path,
            kind="pre_ticket",
            ticket_number=int(pre_match.group(1)),
        )
    if not _PRINCIPAL_AUDIT_RE.search(name):
        return None

    post_match = _POST_TICKET_RE.search(name)
    if post_match:
        return CheckpointReport(
            path=path,
            kind="principal",
            ticket_number=int(post_match.group(1)),
        )

    phase_match = _PRE_PHASE_RE.search(name)
    if phase_match:
        phase = int(phase_match.group(1))
        return CheckpointReport(
            path=path,
            kind="principal",
            ticket_number=_PHASE_BOUNDARY_TICKET.get(phase),
        )

    return CheckpointReport(path=path, kind="principal", ticket_number=None)


def _checkpoint_reports(root: Path) -> list[CheckpointReport]:
    reports: list[CheckpointReport] = []
    if not (root / "agent_reports").is_dir():
        return reports
    for path in sorted((root / "agent_reports").glob("*.md")):
        parsed = _parse_checkpoint_report(path)
        if parsed is not None:
            reports.append(parsed)
    reports.sort(key=lambda item: item.path.name)
    return reports


def _checkpoint_is_valid(
    checkpoint: CheckpointReport, rows: list[QueueTicketRow]
) -> bool:
    """Reject premature principal audits that reference tickets not yet done."""
    if checkpoint.ticket_number is None:
        return True
    if checkpoint.kind == "pre_ticket":
        return True

    ticket_id = f"ticket-{checkpoint.ticket_number:03d}"
    status_by_id = {row.ticket_id: row.status for row in rows}
    return status_by_id.get(ticket_id) == "done"


def _latest_checkpoint(
    reports: list[CheckpointReport], rows: list[QueueTicketRow]
) -> CheckpointReport | None:
    valid = [report for report in reports if _checkpoint_is_valid(report, rows)]
    if not valid:
        return None
    numbered = [report for report in valid if report.ticket_number is not None]
    if numbered:
        return max(numbered, key=lambda report: report.ticket_number)
    return valid[-1]


def _done_since_checkpoint(
    rows: list[QueueTicketRow],
    checkpoint: CheckpointReport | None,
) -> list[QueueTicketRow]:
    if checkpoint is None:
        return [row for row in rows if row.status == "done"]
    if checkpoint.ticket_number is not None:
        cutoff = checkpoint.ticket_number
        return [
            row
            for row in rows
            if row.status == "done" and _ticket_number_from_id(row.ticket_id) > cutoff
        ]
    return [
        row
        for row in rows
        if row.status == "done" and row.order > _LEGACY_PRINCIPAL_ORDER_CUTOFF
    ]


_VALUE_CLASSIFICATIONS = (
    "product_risk_reduction",
    "live_research_proof",
    "test_proof",
    "safety_hardening",
    "infrastructure",
    "docs_corrective",
    "docs_crosslink",
    "checkpoint_only",
)

_LOW_VALUE_CLASSIFICATIONS = frozenset(
    {"docs_crosslink", "checkpoint_only", "docs_corrective"}
)

_CORRECTIVE_OVERRIDE_HINTS = (
    "nm-1",
    "live extraction",
    "extract-claims-live",
    "real live",
    "arbitrary source",
    "nm-4",
)


def classify_ticket_value(title: str) -> str:
    """Deterministic product-value classification from a ticket title."""
    lowered = title.casefold()
    if "principal audit checkpoint" in lowered or lowered.startswith("post-ticket-"):
        return "checkpoint_only"
    if "cross-link" in lowered or "crosslink" in lowered:
        return "docs_crosslink"
    if any(
        phrase in lowered
        for phrase in (
            "alignment audit",
            "maturity",
            "relabel",
            "honest status",
            "third-party",
        )
    ):
        return "docs_corrective"
    if any(
        phrase in lowered
        for phrase in (
            "live extraction write",
            "extract-claims-live",
            "real live",
            "live validated",
            "non-checksum",
            "non-fixture",
        )
    ):
        return "live_research_proof"
    if any(
        phrase in lowered
        for phrase in (
            "e2e",
            "idempotency",
            "pipeline proof test",
            "golden test",
            "builder golden",
        )
    ):
        return "test_proof"
    if any(
        phrase in lowered
        for phrase in ("safety audit", "safety auditor", "prompt-injection", "export policy")
    ):
        return "safety_hardening"
    if any(
        phrase in lowered
        for phrase in (
            "operator loop",
            "verify",
            "ci golden",
            "windows",
            "npm subprocess",
            "model-health",
            "scratch db",
            "principal audit gate",
            "cadence gate",
        )
    ):
        return "infrastructure"
    if any(
        phrase in lowered
        for phrase in (
            "real manual source",
            "manual source ingestion",
            "domain pack loader",
            "claim extraction proof",
            "concept linking proof",
            "relationship proof",
            "contradiction detection proof",
            "score reconciliation proof",
            "pipeline e2e",
            "pipeline idempotency",
            "ollama",
            "live probe",
            "live claim",
        )
    ):
        return "product_risk_reduction"
    return "infrastructure"


def _recent_done_tickets(rows: list[QueueTicketRow], *, limit: int = 8) -> list[QueueTicketRow]:
    done = [row for row in rows if row.status == "done"]
    return done[-limit:]


def evaluate_value_drift(
    rows: list[QueueTicketRow],
    *,
    next_ticket_id: str | None = None,
    next_ticket_title: str | None = None,
) -> dict[str, Any]:
    """Detect low-value ticket streaks and recommend corrective overrides."""
    recent = _recent_done_tickets(rows, limit=8)
    classifications = [
        {
            "ticket_id": row.ticket_id,
            "title": row.title,
            "value_class": classify_ticket_value(row.title),
        }
        for row in recent
    ]
    class_values = [item["value_class"] for item in classifications]

    drift_warnings: list[str] = []
    consecutive_low = 0
    for value in reversed(class_values):
        if value in _LOW_VALUE_CLASSIFICATIONS:
            consecutive_low += 1
        else:
            break
    if consecutive_low >= 3:
        drift_warnings.append(
            f"{consecutive_low} consecutive completed tickets are docs/checkpoint work "
            f"({', '.join(class_values[-consecutive_low:])})."
        )

    low_in_recent = sum(1 for value in class_values if value in _LOW_VALUE_CLASSIFICATIONS)
    if low_in_recent >= 5:
        drift_warnings.append(
            f"{low_in_recent} of the last {len(class_values)} completed tickets are "
            "docs/checkpoint work."
        )

    high_value_recent = any(
        value in {"product_risk_reduction", "live_research_proof", "test_proof"}
        for value in class_values[-3:]
    )
    if not high_value_recent and len(class_values) >= 3:
        drift_warnings.append(
            "No product-risk or live-research proof advanced in the last 3 completed tickets."
        )

    recommended_override: str | None = None
    if next_ticket_id and next_ticket_title:
        next_class = classify_ticket_value(next_ticket_title)
        if next_class in _LOW_VALUE_CLASSIFICATIONS and drift_warnings:
            recommended_override = (
                "Prefer corrective product work (live validated extraction, arbitrary-source "
                "pipeline, or honest maturity relabel) over the queued doc/checkpoint ticket."
            )

    return {
        "recent_ticket_classifications": classifications,
        "drift_warning": drift_warnings or None,
        "recommended_override": recommended_override,
    }


def _pre_ticket_report_for(
    reports: list[CheckpointReport], ticket_number: int
) -> CheckpointReport | None:
    matches = [
        report
        for report in reports
        if report.kind == "pre_ticket" and report.ticket_number == ticket_number
    ]
    return matches[-1] if matches else None


def checkpoint_status(
    *,
    root: Path | None = None,
    next_ticket_id: str | None = None,
) -> dict[str, Any]:
    """Return whether the principal audit checkpoint is satisfied, overdue, or not due."""
    project_root = root or repo_root()
    queue_path = project_root / "tickets" / "TICKET_QUEUE.md"
    queue_text = queue_path.read_text(encoding="utf-8") if queue_path.is_file() else ""
    rows = parse_queue_rows(queue_text)
    reports = _checkpoint_reports(project_root)
    latest = _latest_checkpoint(reports, rows)
    done_since = _done_since_checkpoint(rows, latest)
    done_count = len(done_since)

    cadence_status = "not_due"
    cadence_reason = (
        f"{done_count} done ticket(s) since latest checkpoint "
        f"(threshold {_CONSECUTIVE_DONE_THRESHOLD})."
    )
    if done_count >= _CONSECUTIVE_DONE_THRESHOLD:
        cadence_status = "overdue"
        cadence_reason = (
            f"{done_count} consecutive done ticket(s) since latest checkpoint "
            f"meet or exceed threshold {_CONSECUTIVE_DONE_THRESHOLD}; "
            "run /rge-principal-audit or a focused pre-ticket audit before "
            "the next implementation ticket."
        )
    elif latest is not None:
        cadence_status = "satisfied"
        cadence_reason = (
            f"Latest checkpoint report is {latest.path.name}; only {done_count} "
            f"done ticket(s) since then (below threshold {_CONSECUTIVE_DONE_THRESHOLD})."
        )
    else:
        cadence_reason = "No principal or pre-ticket audit report found in agent_reports/."

    next_ticket_number: int | None = None
    next_ticket_risk: str | None = None
    next_ticket_title: str | None = None
    pre_ticket_path: str | None = None
    implementation_gate = "not_applicable"

    if next_ticket_id:
        ticket_json = project_root / "tickets" / f"{next_ticket_id}.json"
        if ticket_json.is_file():
            payload = json.loads(ticket_json.read_text(encoding="utf-8"))
            next_ticket_risk = payload.get("risk_level")
            next_ticket_title = payload.get("title")
        for row in rows:
            if row.ticket_id == next_ticket_id and row.title:
                next_ticket_title = row.title
                break
        match = re.match(r"ticket-(\d{3})", next_ticket_id)
        if match:
            next_ticket_number = int(match.group(1))
            pre = _pre_ticket_report_for(reports, next_ticket_number)
            pre_ticket_path = str(pre.path.relative_to(project_root)) if pre else None
            if next_ticket_risk in {"medium", "high"}:
                implementation_gate = (
                    "satisfied" if pre is not None else "blocked_missing_pre_ticket_audit"
                )
            else:
                implementation_gate = "satisfied"

    overall = cadence_status
    if implementation_gate == "blocked_missing_pre_ticket_audit":
        overall = "blocked"
    elif cadence_status == "overdue":
        overall = "overdue"
    elif cadence_status in {"satisfied", "not_due"}:
        overall = "satisfied" if implementation_gate != "blocked_missing_pre_ticket_audit" else "blocked"

    value_drift = evaluate_value_drift(
        rows,
        next_ticket_id=next_ticket_id,
        next_ticket_title=next_ticket_title,
    )

    return {
        "report_type": "principal_audit_checkpoint_status",
        "status": overall,
        "cadence_status": cadence_status,
        "cadence_reason": cadence_reason,
        "done_tickets_since_latest_checkpoint": done_count,
        "done_ticket_ids_since_latest_checkpoint": [row.ticket_id for row in done_since],
        "consecutive_done_threshold": _CONSECUTIVE_DONE_THRESHOLD,
        "latest_checkpoint_report": (
            str(latest.path.relative_to(project_root)) if latest else None
        ),
        "latest_checkpoint_kind": latest.kind if latest else None,
        "latest_checkpoint_ticket_number": (
            latest.ticket_number if latest else None
        ),
        "next_ticket_id": next_ticket_id,
        "next_ticket_title": next_ticket_title,
        "next_ticket_risk_level": next_ticket_risk,
        "next_ticket_value_class": (
            classify_ticket_value(next_ticket_title) if next_ticket_title else None
        ),
        "implementation_gate": implementation_gate,
        "pre_ticket_audit_report": pre_ticket_path,
        "drift_warning": value_drift["drift_warning"],
        "recommended_override": value_drift["recommended_override"],
        "recent_ticket_classifications": value_drift["recent_ticket_classifications"],
        "milestone_triggers": [
            "public export or card_exporter changes",
            "public site or committed public JSON changes",
            "schema migrations",
            "theory / inference generation changes",
            "live Ollama or live smoke constraint changes",
        ],
        "operator_command": "/rge-principal-audit",
        "ci_workflow": ".github/workflows/golden-gate.yml",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report principal audit checkpoint status (read-only)."
    )
    parser.add_argument(
        "--next-ticket",
        help="Optional ticket id (e.g. ticket-040) to evaluate implementation gate.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root (defaults to package parent).",
    )
    args = parser.parse_args(argv)
    payload = checkpoint_status(root=args.root, next_ticket_id=args.next_ticket)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
