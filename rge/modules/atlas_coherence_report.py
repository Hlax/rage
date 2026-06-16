"""Human-readable Research Atlas coherence report from private snapshots (ticket-289).

Read-only analysis of an ``atlas_snapshot_v0.1.0`` payload for operator product validation.
Does not mutate graph state or write public exports.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rge.contracts.atlas_snapshot_v0 import (
    ATLAS_FOLLOW_UP_QUESTION_FIELDS,
    ATLAS_RUN_LINEAGE_OPTIONAL_FIELDS,
    ATLAS_SNAPSHOT_SCHEMA_VERSION,
    validate_atlas_snapshot,
)
from rge.modules.atlas_snapshot_builder import assert_no_private_fields

REPORT_SCHEMA_VERSION = "atlas_coherence_report_v0.1.0"


def _population_audit(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "runs": len(snapshot.get("runs") or []),
        "nodes": len(snapshot.get("nodes") or []),
        "edges": len(snapshot.get("edges") or []),
        "cards": len(snapshot.get("cards") or []),
        "reports": len(snapshot.get("reports") or []),
        "follow_up_questions": len(snapshot.get("follow_up_questions") or []),
        "domains": len(snapshot.get("domains") or []),
        "clusters": len(snapshot.get("clusters") or []),
    }


def _lineage_audit(snapshot: dict[str, Any]) -> dict[str, Any]:
    runs = snapshot.get("runs") or []
    per_run: list[dict[str, Any]] = []
    for run in runs:
        present = {
            field: field in run and run.get(field) is not None
            for field in ATLAS_RUN_LINEAGE_OPTIONAL_FIELDS
        }
        per_run.append(
            {
                "run_id": run.get("run_id"),
                "lineage_fields_present": present,
            }
        )
    runs_with_question = sum(
        1 for item in per_run if item["lineage_fields_present"].get("research_question_id")
    )
    return {
        "run_count": len(runs),
        "runs_with_research_question_id": runs_with_question,
        "per_run": per_run,
    }


def _domain_audit(snapshot: dict[str, Any]) -> dict[str, Any]:
    domains = snapshot.get("domains") or []
    nodes = snapshot.get("nodes") or []
    root_domain = (snapshot.get("root") or {}).get("domain_pack")
    nodes_with_domain = sum(1 for node in nodes if node.get("domain_pack"))
    return {
        "root_domain_pack": root_domain,
        "domain_entries": [
            {"id": item.get("id"), "role": item.get("role")} for item in domains
        ],
        "nodes_with_domain_pack": nodes_with_domain,
        "node_domain_coverage_ratio": (
            nodes_with_domain / len(nodes) if nodes else 0.0
        ),
    }


def _linkage_audit(snapshot: dict[str, Any]) -> dict[str, Any]:
    node_ids = {str(item.get("id")) for item in (snapshot.get("nodes") or []) if item.get("id")}
    cards = snapshot.get("cards") or []
    edges = snapshot.get("edges") or []
    reports = snapshot.get("reports") or []

    cards_with_concepts = sum(
        1 for card in cards if isinstance(card.get("concepts"), list) and card["concepts"]
    )
    cards_with_source_metadata = sum(
        1
        for card in cards
        if isinstance(card.get("public_source_metadata"), list)
        and card["public_source_metadata"]
    )
    valid_edges = sum(
        1
        for edge in edges
        if str(edge.get("source_node_id")) in node_ids
        and str(edge.get("target_node_id")) in node_ids
    )
    reports_with_run = sum(1 for report in reports if report.get("run_id"))

    return {
        "cards_with_concepts": cards_with_concepts,
        "cards_with_public_source_metadata": cards_with_source_metadata,
        "edges_with_valid_node_endpoints": valid_edges,
        "edge_endpoint_coverage_ratio": (valid_edges / len(edges) if edges else 0.0),
        "reports_with_run_id": reports_with_run,
    }


def _follow_up_field_audit(snapshot: dict[str, Any]) -> dict[str, Any]:
    questions = snapshot.get("follow_up_questions") or []
    complete = 0
    for item in questions:
        if all(field in item for field in ATLAS_FOLLOW_UP_QUESTION_FIELDS):
            complete += 1
    return {
        "count": len(questions),
        "with_full_contract_fields": complete,
    }


def _refactor_risk_notes(
    population: dict[str, Any],
    lineage: dict[str, Any],
    linkage: dict[str, Any],
    follow_up: dict[str, Any],
) -> list[str]:
    notes: list[str] = []
    if population["edges"] == 0:
        notes.append("No relationship edges — graph UI would show isolated concept nodes.")
    if population["reports"] == 0 and population["runs"] >= 1:
        notes.append("Runs exist but reports[] empty — run narrative panel would be blank.")
    if population["follow_up_questions"] == 0:
        notes.append(
            "follow_up_questions[] empty — research queue panel deferred or unpopulated on live runs."
        )
    if lineage["run_count"] >= 1 and lineage["runs_with_research_question_id"] == 0:
        notes.append("runs[] missing research_question_id — question lineage UI at risk.")
    if population["cards"] >= 1 and linkage["cards_with_concepts"] == 0:
        notes.append("cards[] lack concepts — card-to-graph linking weak for frontend.")
    if population["edges"] >= 1 and linkage["edge_endpoint_coverage_ratio"] < 1.0:
        notes.append("Some edges reference unknown node ids — graph render validation needed.")
    if follow_up["count"] > 0 and follow_up["with_full_contract_fields"] < follow_up["count"]:
        notes.append("follow_up_questions[] missing contract fields — shape drift risk.")
    if population["clusters"] == 0:
        notes.append("clusters[] empty — cluster navigation may rely on cards only.")
    return notes


def _verdict_section(
    population: dict[str, Any],
    linkage: dict[str, Any],
    lineage: dict[str, Any],
    safety: dict[str, Any],
    refactor_risk_notes: list[str],
) -> dict[str, Any]:
    contract_valid = safety.get("contract_valid") is True
    private_clean = not safety.get("private_field_violations")

    meaningful = (
        contract_valid
        and private_clean
        and population["cards"] >= 1
        and population["nodes"] >= 1
        and population["runs"] >= 1
    )
    claims_linked = (
        population["cards"] == 0
        or (
            linkage["cards_with_concepts"] >= 1
            and (
                population["edges"] == 0
                or linkage["edges_with_valid_node_endpoints"] >= 1
            )
        )
    )
    reports_ready = population["runs"] == 0 or (
        population["reports"] >= 1 and linkage["reports_with_run_id"] >= 1
    )
    refactor_risk = len(refactor_risk_notes) > 0

    return {
        "meaningful_atlas_data_from_research_loop": {
            "verdict": "pass" if meaningful else "fail",
            "detail": (
                "Snapshot has cards, nodes, and runs under a valid contract."
                if meaningful
                else "Minimum graph population or contract validation not met."
            ),
        },
        "claims_linked_to_sources_and_concepts": {
            "verdict": "pass" if claims_linked else "fail",
            "detail": (
                "Cards expose concept labels and edges connect known concept nodes."
                if claims_linked
                else "Card concept linkage or edge endpoints insufficient."
            ),
        },
        "reports_and_hypotheses_frontend_ready": {
            "verdict": "pass" if reports_ready else "partial",
            "detail": (
                "Report summaries include run_id for run-scoped UI panels."
                if reports_ready
                else "Run reports missing or lack run_id — narrative UI needs enrichment."
            ),
        },
        "missing_fields_create_refactor_risk": {
            "verdict": "warn" if refactor_risk else "pass",
            "detail": (
                "; ".join(refactor_risk_notes)
                if refactor_risk
                else "No major optional-field gaps detected for v0 frontend planning."
            ),
            "notes": refactor_risk_notes,
        },
        "lineage_fields_actionable": {
            "verdict": (
                "pass"
                if lineage["runs_with_research_question_id"] >= 1
                else "partial"
            ),
            "detail": (
                f"{lineage['runs_with_research_question_id']}/{lineage['run_count']} runs "
                "include research_question_id."
            ),
        },
    }


def build_atlas_coherence_report(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Build structured coherence report JSON from a validated atlas snapshot dict."""
    leak_violations = assert_no_private_fields(snapshot)
    contract_valid = True
    contract_error: str | None = None
    try:
        validate_atlas_snapshot(snapshot)
    except Exception as exc:  # noqa: BLE001 — operator report captures validation failure
        contract_valid = False
        contract_error = str(exc)

    population = _population_audit(snapshot)
    lineage = _lineage_audit(snapshot)
    domain = _domain_audit(snapshot)
    linkage = _linkage_audit(snapshot)
    follow_up = _follow_up_field_audit(snapshot)
    refactor_risk_notes = _refactor_risk_notes(population, lineage, linkage, follow_up)

    safety = {
        "contract_valid": contract_valid,
        "contract_error": contract_error,
        "private_field_violations": leak_violations,
        "public_safe_flag": (snapshot.get("safety") or {}).get("public_safe"),
    }

    verdict = _verdict_section(
        population, linkage, lineage, safety, refactor_risk_notes
    )

    overall = "pass"
    if not contract_valid or leak_violations:
        overall = "fail"
    elif any(section.get("verdict") == "fail" for section in verdict.values()):
        overall = "fail"
    elif any(section.get("verdict") in {"partial", "warn"} for section in verdict.values()):
        overall = "partial"

    return {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "atlas_schema_version": snapshot.get("schema_version"),
        "snapshot_id": snapshot.get("snapshot_id"),
        "generated_at": snapshot.get("generated_at"),
        "overall_coherence_verdict": overall,
        "population": population,
        "lineage": lineage,
        "domain": domain,
        "linkage": linkage,
        "follow_up_questions_audit": follow_up,
        "safety": safety,
        "verdict": verdict,
    }


def format_atlas_coherence_report_markdown(report: dict[str, Any]) -> str:
    """Render operator-readable markdown from a coherence report dict."""
    population = report.get("population") or {}
    verdict = report.get("verdict") or {}
    lines = [
        "# Research Atlas Coherence Report",
        "",
        f"- Report schema: `{report.get('report_schema_version')}`",
        f"- Atlas schema: `{report.get('atlas_schema_version')}`",
        f"- Snapshot id: `{report.get('snapshot_id')}`",
        f"- Overall verdict: **{report.get('overall_coherence_verdict')}**",
        "",
        "## Population",
        "",
        "| Field | Count |",
        "|-------|------:|",
    ]
    for key in (
        "runs",
        "nodes",
        "edges",
        "cards",
        "reports",
        "follow_up_questions",
        "domains",
        "clusters",
    ):
        lines.append(f"| `{key}[]` | {population.get(key, 0)} |")

    lines.extend(["", "## Coherence verdicts", ""])
    for title, section in verdict.items():
        lines.append(f"### {title.replace('_', ' ')}")
        lines.append(f"- **Verdict:** {section.get('verdict')}")
        lines.append(f"- {section.get('detail')}")
        lines.append("")

    safety = report.get("safety") or {}
    lines.extend(
        [
            "## Safety",
            "",
            f"- Contract valid: `{safety.get('contract_valid')}`",
            f"- Private-field violations: {len(safety.get('private_field_violations') or [])}",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_atlas_coherence_report(
    snapshot: dict[str, Any],
    *,
    json_path: Path,
    markdown_path: Path | None = None,
) -> dict[str, Any]:
    """Write coherence report JSON (and optional markdown) to operator-private paths."""
    report = build_atlas_coherence_report(snapshot)
    json_path = Path(json_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    json_path.write_text(json_payload, encoding="utf-8")

    md_path: Path | None = None
    if markdown_path is not None:
        md_path = Path(markdown_path)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(
            format_atlas_coherence_report_markdown(report),
            encoding="utf-8",
        )

    return {
        "status": "completed",
        "command": "atlas-coherence-report",
        "overall_coherence_verdict": report["overall_coherence_verdict"],
        "json_path": str(json_path),
        "markdown_path": str(md_path) if md_path else None,
        "atlas_schema_version": report.get("atlas_schema_version"),
    }
