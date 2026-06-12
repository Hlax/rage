"""Create implementation tickets from actual failures. Deterministic; no model use.

Tickets are generated from run reports, rejection patterns, and audits, never
from vibes. Every ticket requires title, problem, evidence, affected modules,
expected files, acceptance criteria, test plan, non-goals, risk level, and a
rollback plan, so builder agents can consume it as a branch task.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from rge.db.repositories import ImprovementTicketRepository, RunReportRepository
from rge.modules.run_evaluator import GOLDEN_RUN_ID, default_report_dir

GOLDEN_MIN_FAILURE_COUNT = 1

# Failure modes that golden tests already prove via intentional fixture rejections.
# Run reports may still count these for observability; improvement drafts are suppressed.
GOLDEN_COVERED_IMPROVEMENT_FAILURE_MODES: frozenset[str] = frozenset(
    {
        "missing_quote_span",  # GT02 test_claims_without_quote_spans_are_rejected
    }
)

GOLDEN_COVERED_IMPROVEMENT_TITLE = "Improve claim quote span validation"

BUILDER_REQUIRED_TICKET_FIELDS: tuple[str, ...] = (
    "title",
    "problem",
    "evidence",
    "affected_modules",
    "expected_files",
    "acceptance_criteria",
    "test_plan",
    "non_goals",
    "risk_level",
    "rollback_plan",
)

BUILDER_RISK_LEVELS: frozenset[str] = frozenset({"low", "medium", "high"})

QUEUE_TICKET_ID_PATTERN = "ticket-"

PROMOTION_REVIEW_REQUIRED_MSG = (
    "promotion requires explicit --confirm review gate; "
    "generated tickets are never auto-promoted during pipeline runs"
)

VAGUE_TICKET_PHRASES: tuple[str, ...] = (
    "make it better",
    "improve things",
    "fix issues",
    "do better",
    "make improvements",
)

GOLDEN_FAILURE_TEMPLATES: dict[str, dict[str, Any]] = {
    "overgeneralized_scope": {
        "priority": "high",
        "title": "Improve claim extractor scope preservation",
        "problem": "High rejection rate caused by overgeneralized claims.",
        "affected_modules": [
            "claim_extractor",
            "claim_validator",
            "creativity_domain_pack",
        ],
        "expected_files": [
            "rge/modules/claim_extractor.py",
            "rge/modules/claim_validator.py",
            "domain_packs/creativity/claim_schema.yaml",
            "tests/golden/test_02_claim_extraction.py",
        ],
        "acceptance_criteria": [
            "Overgeneralized fixture claim is rejected or rewritten with preserved scope.",
            "No accepted claim lacks quote_span.",
        ],
        "test_plan": ["pytest tests/golden/test_02_claim_extraction.py"],
        "non_goals": ["Do not refactor the full orchestration graph."],
        "risk_level": "medium",
        "rollback_plan": (
            "Revert extractor prompt/schema changes and restore previous validator version."
        ),
    },
    "missing_quote_span": {
        "priority": "high",
        "title": "Improve claim quote span validation",
        "problem": "Rejected claims are missing required quote spans.",
        "affected_modules": ["claim_extractor", "claim_validator"],
        "expected_files": [
            "rge/modules/claim_extractor.py",
            "rge/modules/claim_validator.py",
            "tests/golden/test_02_claim_extraction.py",
        ],
        "acceptance_criteria": [
            "Claims without quote spans are rejected with machine-readable reasons.",
            "Accepted claims always include primary quote spans.",
        ],
        "test_plan": ["pytest tests/golden/test_02_claim_extraction.py"],
        "non_goals": ["Do not broaden claim extraction to live web sources."],
        "risk_level": "medium",
        "rollback_plan": "Revert claim validator quote-span checks.",
    },
    "weak_concept_mapping": {
        "priority": "medium",
        "title": "Improve concept mapping validation",
        "problem": "Concept links are rejected due to weak concept mapping.",
        "affected_modules": ["concept_linker", "creativity_domain_pack"],
        "expected_files": [
            "rge/modules/concept_linker.py",
            "domain_packs/creativity/ontology.yaml",
            "tests/golden/test_05_concept_linking.py",
        ],
        "acceptance_criteria": [
            "Weak concept mappings are rejected with machine-readable reasons.",
            "Valid fixture concept links persist to claim_concepts.",
        ],
        "test_plan": ["pytest tests/golden/test_05_concept_linking.py"],
        "non_goals": ["Do not auto-activate new ontology concepts."],
        "risk_level": "medium",
        "rollback_plan": "Revert concept linker validation rules.",
    },
}


def failure_mode_covered_by_golden_tests(failure_reason: str) -> bool:
    """Return True when golden tests already cover intentional fixture rejection."""
    return failure_reason in GOLDEN_COVERED_IMPROVEMENT_FAILURE_MODES


def improvement_draft_is_actionable(draft: dict[str, Any]) -> bool:
    """Return False for drafts that duplicate golden-covered validation work."""
    reason = draft.get("failure_reason")
    if isinstance(reason, str) and failure_mode_covered_by_golden_tests(reason):
        return False
    if draft.get("title") == GOLDEN_COVERED_IMPROVEMENT_TITLE:
        return False
    evidence = draft.get("evidence") or []
    if any(
        isinstance(item, str) and "missing_quote_span_count=" in item
        for item in evidence
    ):
        return False
    return True


def validate_builder_ticket(ticket: dict[str, Any]) -> list[str]:
    """Return machine-readable violations when a ticket is not builder-consumable."""
    violations: list[str] = []

    for field in BUILDER_REQUIRED_TICKET_FIELDS:
        if field not in ticket:
            violations.append(f"missing required field: {field}")
            continue
        value = ticket[field]
        if isinstance(value, str):
            if not value.strip():
                violations.append(f"empty required field: {field}")
        elif isinstance(value, list):
            if not value:
                violations.append(f"empty required list: {field}")
            elif not all(isinstance(item, str) and item.strip() for item in value):
                violations.append(f"non-string or blank entries in: {field}")
        else:
            violations.append(f"invalid type for field: {field}")

    title = ticket.get("title", "")
    if isinstance(title, str) and title.strip() and len(title.strip()) < 10:
        violations.append("title too short to convert into a branch task")

    problem = ticket.get("problem", "")
    if isinstance(problem, str) and problem.strip():
        lowered = problem.lower()
        if len(problem.strip()) < 20:
            violations.append("problem statement too vague")
        for phrase in VAGUE_TICKET_PHRASES:
            if phrase in lowered:
                violations.append(f"vague problem phrase: {phrase}")

    acceptance = ticket.get("acceptance_criteria", [])
    if isinstance(acceptance, list) and acceptance:
        for item in acceptance:
            if not isinstance(item, str):
                continue
            lowered = item.lower()
            if any(phrase in lowered for phrase in VAGUE_TICKET_PHRASES):
                violations.append(f"vague acceptance criterion: {item}")
            if len(item.strip()) < 10:
                violations.append(f"acceptance criterion not testable: {item}")

    test_plan = ticket.get("test_plan", [])
    if isinstance(test_plan, list) and test_plan:
        if not any(
            isinstance(item, str) and ("pytest" in item or "python -m" in item)
            for item in test_plan
        ):
            violations.append("test_plan lacks executable pytest command")

    expected_files = ticket.get("expected_files", [])
    if isinstance(expected_files, list) and expected_files:
        if not all(
            isinstance(item, str) and ("/" in item or item.endswith(".py"))
            for item in expected_files
        ):
            violations.append("expected_files must name concrete repo paths")

    risk_level = ticket.get("risk_level")
    if isinstance(risk_level, str) and risk_level not in BUILDER_RISK_LEVELS:
        violations.append(f"invalid risk_level: {risk_level}")

    return violations


def _normalize_queue_ticket_id(queue_ticket_id: str) -> str:
    ticket_id = queue_ticket_id.strip()
    if not ticket_id.startswith(QUEUE_TICKET_ID_PATTERN):
        raise ValueError(
            f"queue ticket id must start with {QUEUE_TICKET_ID_PATTERN!r}: "
            f"{queue_ticket_id!r}"
        )
    suffix = ticket_id[len(QUEUE_TICKET_ID_PATTERN) :]
    if not suffix.isdigit() or len(suffix) < 3:
        raise ValueError(
            f"queue ticket id must use numeric suffix (e.g. ticket-041): "
            f"{queue_ticket_id!r}"
        )
    return ticket_id


def improvement_ticket_to_queue_ticket(
    improvement: dict[str, Any],
    *,
    queue_ticket_id: str,
) -> dict[str, Any]:
    """Map a draft improvement ticket report into a builder queue ticket JSON dict."""
    normalized_id = _normalize_queue_ticket_id(queue_ticket_id)
    violations = validate_builder_ticket(improvement)
    if violations:
        raise ValueError(
            "improvement ticket is not builder-consumable: " + "; ".join(violations)
        )
    return {
        "id": normalized_id,
        "title": improvement["title"],
        "problem": improvement["problem"],
        "evidence": list(improvement["evidence"]),
        "affected_modules": list(improvement["affected_modules"]),
        "expected_files": list(improvement["expected_files"]),
        "acceptance_criteria": list(improvement["acceptance_criteria"]),
        "test_plan": list(improvement["test_plan"]),
        "non_goals": list(improvement["non_goals"]),
        "risk_level": improvement["risk_level"],
        "rollback_plan": improvement["rollback_plan"],
        "status": "proposed",
    }


def _load_improvement_ticket_from_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        if len(payload) != 1:
            raise ValueError(
                "from-json file must contain one improvement ticket or pass "
                "run-id + failure-reason to select from a list"
            )
        ticket = payload[0]
    elif isinstance(payload, dict):
        ticket = payload
    else:
        raise ValueError("from-json payload must be an object or single-item list")
    if not isinstance(ticket, dict):
        raise ValueError("improvement ticket payload must be a JSON object")
    return ticket


def _load_improvement_ticket_from_db(
    conn: sqlite3.Connection,
    *,
    run_id: str | None,
    failure_reason: str | None,
    improvement_ticket_id: str | None,
) -> dict[str, Any]:
    repo = ImprovementTicketRepository(conn)
    record: ImprovementTicketRecord | None
    if improvement_ticket_id:
        record = repo.get_by_id(improvement_ticket_id)
        if record is None:
            raise ValueError(
                f"No improvement ticket found for id={improvement_ticket_id}"
            )
    elif run_id and failure_reason:
        record = repo.get_for_run_and_reason(
            run_id=run_id,
            failure_reason=failure_reason,
        )
        if record is None:
            raise ValueError(
                f"No improvement ticket found for run_id={run_id} "
                f"failure_reason={failure_reason}"
            )
    else:
        raise ValueError(
            "provide --improvement-ticket-id or both --run-id and --failure-reason"
        )
    return json.loads(record.ticket_json)


def promote_improvement_ticket(
    *,
    queue_ticket_id: str,
    reviewed: bool,
    output_dir: Path,
    from_json: Path | None = None,
    conn: sqlite3.Connection | None = None,
    run_id: str | None = None,
    failure_reason: str | None = None,
    improvement_ticket_id: str | None = None,
) -> dict[str, Any]:
    """Promote a reviewed improvement ticket to a queue ticket JSON file.

    Never updates ``TICKET_QUEUE.md``; operators add queue rows manually after review.
    """
    if not reviewed:
        raise ValueError(PROMOTION_REVIEW_REQUIRED_MSG)

    has_db_source = conn is not None and (
        improvement_ticket_id is not None
        or (run_id is not None and failure_reason is not None)
    )
    sources = [from_json is not None, has_db_source]
    if sum(sources) != 1:
        raise ValueError(
            "provide exactly one source: --from-json or DB lookup via "
            "--improvement-ticket-id or (--run-id and --failure-reason)"
        )

    if from_json is not None:
        improvement = _load_improvement_ticket_from_json(from_json)
    else:
        assert conn is not None
        improvement = _load_improvement_ticket_from_db(
            conn,
            run_id=run_id,
            failure_reason=failure_reason,
            improvement_ticket_id=improvement_ticket_id,
        )

    queue_ticket = improvement_ticket_to_queue_ticket(
        improvement,
        queue_ticket_id=queue_ticket_id,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{queue_ticket['id']}.json"
    if output_path.exists():
        raise ValueError(
            f"queue ticket file already exists: {output_path}; "
            "refuse to overwrite without manual review"
        )
    output_path.write_text(json.dumps(queue_ticket, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "promoted",
        "command": "promote-improvement-ticket",
        "queue_ticket_id": queue_ticket["id"],
        "output_path": str(output_path),
        "source_failure_reason": improvement.get("failure_reason"),
        "reviewed": True,
        "ticket": queue_ticket,
    }


def _build_ticket_report(
    *,
    run_id: str,
    failure_reason: str,
    failure_count: int,
    template: dict[str, Any],
) -> dict[str, Any]:
    evidence = [
        f"run_report:{run_id}:{failure_reason}_count={failure_count}",
    ]
    return {
        "report_type": "improvement_ticket_report",
        "type": "improvement_ticket",
        "priority": template["priority"],
        "title": template["title"],
        "problem": template["problem"],
        "status": "draft",
        "failure_reason": failure_reason,
        "failure_count": failure_count,
        "evidence": evidence,
        "affected_modules": list(template["affected_modules"]),
        "expected_files": list(template["expected_files"]),
        "acceptance_criteria": list(template["acceptance_criteria"]),
        "test_plan": list(template["test_plan"]),
        "non_goals": list(template["non_goals"]),
        "risk_level": template["risk_level"],
        "rollback_plan": template["rollback_plan"],
    }


def write_improvement_tickets(run_report: dict[str, Any]) -> list[dict[str, Any]]:
    """Build improvement ticket reports from a run report failure-mode summary."""
    run_id = run_report.get("run_id", GOLDEN_RUN_ID)
    tickets: list[dict[str, Any]] = []
    for mode in run_report.get("top_failure_modes", []):
        reason = mode.get("reason")
        count = int(mode.get("count", 0))
        template = GOLDEN_FAILURE_TEMPLATES.get(reason or "")
        if template is None or count < GOLDEN_MIN_FAILURE_COUNT:
            continue
        if failure_mode_covered_by_golden_tests(reason or ""):
            continue
        tickets.append(
            _build_ticket_report(
                run_id=run_id,
                failure_reason=reason,
                failure_count=count,
                template=template,
            )
        )
    return tickets


def generate_improvement_tickets(
    conn: sqlite3.Connection,
    *,
    run_id: str = GOLDEN_RUN_ID,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Create draft improvement tickets from a persisted run report."""
    report_repo = RunReportRepository(conn)
    ticket_repo = ImprovementTicketRepository(conn)
    run_record = report_repo.get_by_run_id(run_id)
    if run_record is None:
        raise ValueError(f"No run report found for run_id={run_id}")

    run_report = json.loads(run_record.report_json)
    proposed = write_improvement_tickets(run_report)
    target_dir = output_dir or default_report_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / "improvement_ticket_latest.json"

    if not proposed:
        output_path.write_text(json.dumps([], indent=2) + "\n", encoding="utf-8")
        return {
            "status": "skipped_golden_covered",
            "run_id": run_id,
            "ticket_ids": [],
            "tickets": [],
            "output_path": str(output_path),
        }

    existing_count = ticket_repo.count_for_run(run_id)
    created_ids: list[str] = []
    ticket_reports: list[dict[str, Any]] = []

    for ticket in proposed:
        reason = ticket["failure_reason"]
        violations = validate_builder_ticket(ticket)
        if violations:
            raise ValueError(
                f"Improvement ticket for {reason} is not builder-consumable: "
                + "; ".join(violations)
            )
        existing = ticket_repo.get_for_run_and_reason(run_id=run_id, failure_reason=reason)
        if existing is not None:
            ticket_reports.append(json.loads(existing.ticket_json))
            created_ids.append(existing.id)
            continue
        record = ticket_repo.insert(
            run_id=run_id,
            failure_reason=reason,
            priority=ticket["priority"],
            title=ticket["title"],
            problem=ticket["problem"],
            evidence=ticket["evidence"],
            affected_modules=ticket["affected_modules"],
            expected_files=ticket["expected_files"],
            acceptance_criteria=ticket["acceptance_criteria"],
            test_plan=ticket["test_plan"],
            non_goals=ticket["non_goals"],
            risk_level=ticket["risk_level"],
            rollback_plan=ticket["rollback_plan"],
            ticket=ticket,
        )
        ticket["id"] = record.id
        created_ids.append(record.id)
        ticket_reports.append(ticket)

    status = (
        "generated"
        if ticket_repo.count_for_run(run_id) > existing_count
        else "already_generated"
    )

    output_path: Path | None = None
    target_dir = output_dir or default_report_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / "improvement_ticket_latest.json"
    output_path.write_text(json.dumps(ticket_reports, indent=2), encoding="utf-8")

    return {
        "status": status,
        "run_id": run_id,
        "ticket_ids": created_ids,
        "tickets": ticket_reports,
        "output_path": str(output_path),
    }
