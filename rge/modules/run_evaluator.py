"""Build run reports and failure summaries. Mostly deterministic.

Every run produces a JSON-first run report with accepted/rejected counters
and machine-readable failure modes, queryable by ticket generation
(``docs/agents/08_REPORTING_SPEC.md`` section 6). Phase 0 stub.
"""

from __future__ import annotations

from typing import Any


def evaluate_run(run_id: str) -> dict[str, Any]:
    """Build the run report for a completed run. Not implemented in Phase 0."""
    raise NotImplementedError("run_evaluator.evaluate_run arrives with Phase 3.")
