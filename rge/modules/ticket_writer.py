"""Create implementation tickets from actual failures. Model-assisted, validated.

Tickets are generated from run reports, rejection patterns, and audits, never
from vibes. Every ticket requires title, problem, evidence, affected modules,
expected files, acceptance criteria, test plan, non-goals, risk level, and a
rollback plan, so builder agents can consume it as a branch task. Phase 0 stub.
"""

from __future__ import annotations

from typing import Any


def write_improvement_tickets(run_report: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate improvement tickets from a run report. Not implemented in Phase 0."""
    raise NotImplementedError(
        "ticket_writer.write_improvement_tickets arrives with Phase 5."
    )
