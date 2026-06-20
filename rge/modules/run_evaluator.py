"""Build run reports and failure summaries. Deterministic; no model use.

Every run produces a JSON-first run report with accepted/rejected counters
and machine-readable failure modes, queryable by ticket generation
(``docs/agents/08_REPORTING_SPEC.md`` section 6).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from rge.db.repositories import (
    ResearchContractRepository,
    ResearchRunRepository,
    RunReportRepository,
    utc_now_iso,
)
from rge.modules.research_planner import GOLDEN_CONTRACT_ID, ensure_golden_contract
from rge.modules.research_purpose import classify_research_purpose

GOLDEN_RUN_ID = "run_golden_test_19"
GOLDEN_TOPIC = "Does AI improve creative output while reducing diversity?"
GOLDEN_DOMAIN_PACK = "creativity"
REPORT_SCHEMA_VERSION = "0.1.0"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_report_dir(repo_root: Path | None = None) -> Path:
    return (repo_root or _repo_root()) / "data" / "reports"


def _scalar_count(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> int:
    row = conn.execute(query, params).fetchone()
    return int(row[0]) if row else 0


def aggregate_top_failure_modes(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Return rejection reasons sorted by frequency."""
    rows = conn.execute(
        """
        SELECT rejection_reason, COUNT(*) AS count
        FROM claims
        WHERE status = 'rejected' AND rejection_reason IS NOT NULL
        GROUP BY rejection_reason
        ORDER BY count DESC, rejection_reason
        """
    ).fetchall()
    return [
        {"reason": row["rejection_reason"], "count": int(row["count"])}
        for row in rows
    ]


def aggregate_run_metrics(conn: sqlite3.Connection) -> dict[str, int]:
    """Collect deterministic counters from the current database state."""
    claims_accepted = _scalar_count(
        conn, "SELECT COUNT(*) FROM claims WHERE status = 'accepted'"
    )
    claims_rejected = _scalar_count(
        conn, "SELECT COUNT(*) FROM claims WHERE status = 'rejected'"
    )
    return {
        "sources_discovered": _scalar_count(conn, "SELECT COUNT(*) FROM candidate_sources"),
        "sources_ingested": _scalar_count(
            conn,
            "SELECT COUNT(*) FROM sources WHERE status IN ('ingested', 'parsed')",
        ),
        "claims_extracted": claims_accepted + claims_rejected,
        "claims_accepted": claims_accepted,
        "claims_rejected": claims_rejected,
        "relationships_updated": _scalar_count(
            conn, "SELECT COUNT(*) FROM relationships WHERE status = 'active'"
        ),
        "score_events_created": _scalar_count(conn, "SELECT COUNT(*) FROM score_events"),
        "cards_exported": _scalar_count(
            conn, "SELECT COUNT(*) FROM public_cards WHERE is_public_safe = 1"
        ),
        "cluster_reports_created": _scalar_count(
            conn, "SELECT COUNT(*) FROM cluster_reports"
        ),
        "theory_candidates_created": _scalar_count(
            conn, "SELECT COUNT(*) FROM theory_candidates"
        ),
        "tickets_generated": _scalar_count(
            conn, "SELECT COUNT(*) FROM improvement_tickets"
        ),
        "evidence_atoms_created": _scalar_count(conn, "SELECT COUNT(*) FROM evidence_atoms"),
    }


def _purpose_for_report(
    conn: sqlite3.Connection,
    *,
    contract_id: str,
    topic: str,
    domain_pack: str,
) -> dict[str, Any]:
    contract = ResearchContractRepository(conn).get_by_id(contract_id)
    if contract and contract.get("purpose_metadata"):
        return dict(contract["purpose_metadata"])
    return classify_research_purpose(topic, domain=domain_pack, question_id=contract_id)


def _acquisition_quality_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    """Summarize acquisition and parser outcomes stored on source metadata."""
    from rge.modules.acquisition_quality import acquisition_quality_summary

    return acquisition_quality_summary(conn)


def build_run_report(
    conn: sqlite3.Connection,
    *,
    run_id: str,
    topic: str,
    domain_pack: str = GOLDEN_DOMAIN_PACK,
    contract_id: str | None = None,
) -> dict[str, Any]:
    """Build canonical run report JSON from aggregated DB metrics."""
    metrics = aggregate_run_metrics(conn)
    failure_modes = aggregate_top_failure_modes(conn)
    from rge.modules.atlas_trace import build_graph_connection_metrics

    graph_connection_metrics = build_graph_connection_metrics(
        conn,
        domain_pack=domain_pack,
        question=topic,
    )
    resolved_contract = contract_id or GOLDEN_CONTRACT_ID
    purpose = _purpose_for_report(
        conn,
        contract_id=resolved_contract,
        topic=topic,
        domain_pack=domain_pack,
    )
    return {
        "report_type": "run_report",
        "schema_version": REPORT_SCHEMA_VERSION,
        "run_id": run_id,
        "topic": topic,
        "domain_pack": domain_pack,
        "contract_id": resolved_contract,
        "purpose": purpose,
        "research_intent": purpose["research_intent"],
        "asset_affordance": purpose["asset_affordance"],
        "evidence_maturity": purpose["evidence_maturity"],
        "training_suitability": purpose["training_suitability"],
        "status": "informational",
        "created_at": utc_now_iso(),
        "sources_discovered": metrics["sources_discovered"],
        "sources_ingested": metrics["sources_ingested"],
        "claims_extracted": metrics["claims_extracted"],
        "claims_accepted": metrics["claims_accepted"],
        "claims_rejected": metrics["claims_rejected"],
        "relationships_updated": metrics["relationships_updated"],
        "score_events_created": metrics["score_events_created"],
        "cards_exported": metrics["cards_exported"],
        "cluster_reports_created": metrics["cluster_reports_created"],
        "theory_candidates_created": metrics["theory_candidates_created"],
        "evidence_atoms_created": metrics["evidence_atoms_created"],
        "acquisition_quality_summary": _acquisition_quality_summary(conn),
        "graph_connection_metrics": graph_connection_metrics,
        "top_failure_modes": failure_modes,
        "tickets_generated": metrics["tickets_generated"],
        "safety_audit_status": "not_run",
    }


def generate_run_report(
    conn: sqlite3.Connection,
    *,
    run_id: str = GOLDEN_RUN_ID,
    topic: str = GOLDEN_TOPIC,
    domain_pack: str = GOLDEN_DOMAIN_PACK,
    contract_id: str | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Ensure research run row, aggregate metrics, persist run report."""
    ensure_golden_contract(conn)
    run_repo = ResearchRunRepository(conn)
    report_repo = RunReportRepository(conn)
    resolved_contract = contract_id or GOLDEN_CONTRACT_ID

    run_repo.ensure(
        run_id=run_id,
        topic=topic,
        domain_pack=domain_pack,
        contract_id=resolved_contract,
        mode="fixture",
        status="completed",
    )

    existing = report_repo.get_by_run_id(run_id)
    if existing is not None:
        report = json.loads(existing.report_json)
        return {
            "status": "already_generated",
            "report_id": existing.id,
            "run_id": run_id,
            "report": report,
            "output_path": None,
        }

    report = build_run_report(
        conn,
        run_id=run_id,
        topic=topic,
        domain_pack=domain_pack,
        contract_id=resolved_contract,
    )
    record = report_repo.insert(
        run_id=run_id,
        topic=topic,
        domain_pack=domain_pack,
        report=report,
    )

    target_dir = output_dir or default_report_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / "run_report_latest.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return {
        "status": "generated",
        "report_id": record.id,
        "run_id": run_id,
        "report": report,
        "output_path": str(output_path),
    }


def evaluate_run(run_id: str) -> dict[str, Any]:
    """Legacy entry point for module contract checks."""
    return {
        "report_type": "run_report",
        "run_id": run_id,
        "topic": GOLDEN_TOPIC,
        "domain_pack": GOLDEN_DOMAIN_PACK,
        "top_failure_modes": [],
    }
