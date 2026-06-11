"""Update confidence scores and write score events. Deterministic; no model use.

Scores are derived, never manually overwritten. Every change writes an
append-only ``score_events`` row preserving old score, new score, triggering
claim/source, reason, and formula version. Phase 0 stub.
"""

from __future__ import annotations

from typing import Any


def reconcile_scores(new_claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reconcile scores after new evidence; emit score events. Not implemented in Phase 0."""
    raise NotImplementedError(
        "score_reconciler.reconcile_scores arrives with Phase 1."
    )
