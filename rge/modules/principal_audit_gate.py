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
    r"^\|\s*(\d+)\s*\|\s*(ticket-\d{3})\s*\|\s*(\w+)\s*\|",
    re.MULTILINE,
)
_PRINCIPAL_AUDIT_RE = re.compile(
    r"pre-phase-\d+-principal-audit|principal-audit",
    re.IGNORECASE,
)
_PRE_TICKET_RE = re.compile(r"pre-ticket-(\d{3})", re.IGNORECASE)


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


def repo_root() -> Path:
    return _REPO_ROOT


def parse_queue_rows(queue_text: str) -> list[QueueTicketRow]:
    rows: list[QueueTicketRow] = []
    for match in _QUEUE_ROW_RE.finditer(queue_text):
        rows.append(
            QueueTicketRow(
                order=int(match.group(1)),
                ticket_id=match.group(2),
                status=match.group(3).strip().lower(),
            )
        )
    return rows


def _checkpoint_reports(root: Path) -> list[CheckpointReport]:
    reports: list[CheckpointReport] = []
    if not (root / "agent_reports").is_dir():
        return reports
    for path in sorted((root / "agent_reports").glob("*.md")):
        name = path.name.lower()
        pre_match = _PRE_TICKET_RE.search(name)
        if pre_match:
            reports.append(
                CheckpointReport(
                    path=path,
                    kind="pre_ticket",
                    ticket_number=int(pre_match.group(1)),
                )
            )
            continue
        if _PRINCIPAL_AUDIT_RE.search(name):
            reports.append(
                CheckpointReport(
                    path=path,
                    kind="principal",
                    ticket_number=None,
                )
            )
    reports.sort(key=lambda item: item.path.name)
    return reports


def _latest_checkpoint(reports: list[CheckpointReport]) -> CheckpointReport | None:
    return reports[-1] if reports else None


def _done_since_checkpoint(
    rows: list[QueueTicketRow],
    checkpoint: CheckpointReport | None,
) -> list[QueueTicketRow]:
    if checkpoint is None:
        return [row for row in rows if row.status == "done"]
    if checkpoint.kind == "pre_ticket" and checkpoint.ticket_number is not None:
        cutoff = checkpoint.ticket_number
        return [
            row
            for row in rows
            if row.status == "done"
            and int(row.ticket_id.split("-")[1]) > cutoff
        ]
    # Principal audit: count all implementation tickets done after ticket-033.
    return [row for row in rows if row.status == "done" and row.order > 33]


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
    latest = _latest_checkpoint(reports)
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
    pre_ticket_path: str | None = None
    implementation_gate = "not_applicable"

    if next_ticket_id:
        ticket_json = project_root / "tickets" / f"{next_ticket_id}.json"
        if ticket_json.is_file():
            payload = json.loads(ticket_json.read_text(encoding="utf-8"))
            next_ticket_risk = payload.get("risk_level")
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
        "next_ticket_id": next_ticket_id,
        "next_ticket_risk_level": next_ticket_risk,
        "implementation_gate": implementation_gate,
        "pre_ticket_audit_report": pre_ticket_path,
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
