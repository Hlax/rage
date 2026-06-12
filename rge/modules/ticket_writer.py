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
    if not proposed:
        raise ValueError(
            "No improvement tickets generated: run report has no qualifying failure modes."
        )

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
