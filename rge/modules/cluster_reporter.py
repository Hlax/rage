"""Build evidence packets and cluster reports. Mixed; model-assisted synthesis.

Triggered at 15 claims + 3 sources per cluster. Evidence packets must be
balanced: supporting, contradicting, and qualifying claims, never
cherry-picked support (``docs/agents/08_REPORTING_SPEC.md`` sections 9-10).
Phase 0 stub.
"""

from __future__ import annotations

from typing import Any


def build_cluster_report(cluster_id: str) -> dict[str, Any]:
    """Build an evidence packet and cluster report. Not implemented in Phase 0."""
    raise NotImplementedError(
        "cluster_reporter.build_cluster_report arrives with Phase 3."
    )
