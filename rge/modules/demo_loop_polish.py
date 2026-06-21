"""Demo loop polish: one-command research-run → Atlas-safe product summary.

Operator-gated proof that the fixture-mode research demo loop produces source
resolution, abstract evidence, selective full-text status, improvement
recommendation, and optional DB spine/trace reporting in a public-safe artifact.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from rge.db.connection import ensure_database
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.principal_audit_gate import repo_root
from rge.modules.research_run import run_research_demo

PACKET_ID = "demo-loop-polish"
DEMO_LOOP_SCHEMA_VERSION = "atlas_demo_loop_polish_v0.1.0"
DEMO_LOOP_ARTIFACT_NAME = "atlas_demo_loop_polish_latest.json"
DEMO_LOOP_RUN_ID = "run_demo_loop_polish"
DEFAULT_TOPIC = "AI assisted creativity and idea diversity"

NEXT_RECOMMENDED_PACKET = {
    "id": "operator-loop-full-atlas-refresh-checklist",
    "title": "Operator Loop Full Atlas Refresh Checklist",
}


class DemoLoopPolishGateError(RuntimeError):
    """Raised when operator env gates for demo loop polish are missing."""


def assert_demo_loop_polish_env() -> dict[str, str]:
    """Fail closed unless operator opts into demo loop polish proof."""
    allow = os.environ.get("RGE_ALLOW_DEMO_LOOP_POLISH", "0").strip().casefold()
    if allow not in {"1", "true", "yes"}:
        raise DemoLoopPolishGateError(
            "Demo loop polish requires RGE_ALLOW_DEMO_LOOP_POLISH=1."
        )
    return {"RGE_ALLOW_DEMO_LOOP_POLISH": allow}


def required_env_setup_commands() -> list[str]:
    return [
        '$env:RGE_ALLOW_DEMO_LOOP_POLISH = "1"',
        '$env:RGE_LLM_MODE = "mock"',
        "python scripts/run_demo_loop_polish.py --sync-public",
        "# With DB persist + run report:",
        "python scripts/run_demo_loop_polish.py --persist-claims --sync-public",
    ]


def summarize_source_status_counts(source_status_table: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in source_status_table:
        status = str(row.get("source_status") or "unknown")
        counts[status] += 1
    return dict(sorted(counts.items()))


def summarize_abstract_evidence(abstract_evidence: dict[str, Any] | None) -> dict[str, Any]:
    evidence = abstract_evidence or {}
    return {
        "card_count": int(evidence.get("card_count") or 0),
        "completed_count": int(evidence.get("completed_count") or 0),
        "accepted_claims_total": int(evidence.get("accepted_claims_total") or 0),
        "rejected_claims_total": int(evidence.get("rejected_claims_total") or 0),
        "skipped_count": int(evidence.get("skipped_count") or 0),
    }


def summarize_selective_fulltext(selective_fulltext: dict[str, Any] | None) -> dict[str, Any]:
    fulltext = selective_fulltext or {}
    return {
        "acquisition_count": int(fulltext.get("acquisition_count") or 0),
        "status_counts": dict(fulltext.get("status_counts") or {}),
    }


def summarize_improvement_recommendation(
    improvement: dict[str, Any] | None,
) -> dict[str, Any]:
    rec = improvement or {}
    return {
        "recommended_packet": str(rec.get("recommended_packet") or "unknown"),
        "dominant_signal": str(rec.get("dominant_signal") or "unknown"),
        "rationale": str(rec.get("rationale") or ""),
    }


def summarize_db_spine(db_spine: dict[str, Any] | None) -> dict[str, Any]:
    spine = db_spine or {}
    return {
        "status": spine.get("status", "skipped"),
        "accepted_claims_total": int(spine.get("accepted_claims_total") or 0),
        "rejected_claims_total": int(spine.get("rejected_claims_total") or 0),
        "fulltext_completed_count": int(
            (spine.get("fulltext_evidence") or {}).get("completed_count") or 0
        ),
        "fulltext_accepted_total": int(
            (spine.get("fulltext_evidence") or {}).get("accepted_claims_total") or 0
        ),
    }


def classify_demo_loop_verdict(
    *,
    demo_status: str,
    abstract_summary: dict[str, Any],
    fulltext_summary: dict[str, Any],
    field_report: dict[str, Any] | None,
    improvement: dict[str, Any],
    db_spine_summary: dict[str, Any],
    trace_summary: dict[str, Any] | None,
) -> tuple[str, str]:
    """Return (verdict, rationale) for demo loop polish."""
    if demo_status != "ok":
        return "NO-GO", "Research demo loop did not complete successfully."

    accepted = int(abstract_summary.get("accepted_claims_total") or 0)
    trace_count = int((trace_summary or {}).get("trace_count") or 0)
    recommended = str(improvement.get("recommended_packet") or "")

    if accepted >= 1 and field_report and recommended:
        fulltext_clean = int(
            fulltext_summary.get("status_counts", {}).get("full_text_clean_text_ready", 0)
        )
        if trace_count >= 1 or int(db_spine_summary.get("accepted_claims_total") or 0) >= 1:
            return (
                "GO",
                "Fixture demo loop produced quote-grounded abstract evidence, "
                f"selective full-text status ({fulltext_clean} clean), improvement "
                f"recommendation ({recommended}), and DB/trace spine rows.",
            )
        return (
            "GO",
            "Fixture demo loop produced quote-grounded abstract evidence, selective "
            f"full-text acquisition summary, and improvement recommendation ({recommended}).",
        )

    if accepted >= 1:
        return (
            "PARTIAL",
            "Demo loop ran but field report or improvement recommendation is thin.",
        )

    return (
        "PARTIAL",
        "Demo loop completed but abstract evidence acceptance is thin on fixtures.",
    )


def build_atlas_safe_demo_loop_artifact(
    *,
    topic: str,
    domain_pack: str,
    mode: str,
    fixture_mode: bool,
    resolver_summary: dict[str, Any],
    source_status_counts: dict[str, int],
    ranked_source_count: int,
    abstract_summary: dict[str, Any],
    fulltext_summary: dict[str, Any],
    improvement: dict[str, Any],
    field_report_summary: dict[str, Any],
    db_spine_summary: dict[str, Any],
    trace_summary: dict[str, Any] | None,
    verdict: str,
    rationale: str,
) -> dict[str, Any]:
    """Build public-safe Atlas bundle for demo loop polish."""
    trace = trace_summary or {}
    artifact: dict[str, Any] = {
        "schema_version": DEMO_LOOP_SCHEMA_VERSION,
        "status": "completed",
        "packet_id": PACKET_ID,
        "run_id": DEMO_LOOP_RUN_ID,
        "demo_loop_verdict": verdict,
        "demo_loop_rationale": rationale,
        "evaluation_only": False,
        "topic": topic,
        "domain_pack": domain_pack,
        "mode": mode,
        "fixture_mode": fixture_mode,
        "resolver_summary": {
            "resolved_count": int(resolver_summary.get("resolved_count") or 0),
            "backend_counts": dict(resolver_summary.get("backend_counts") or {}),
        },
        "source_status_counts": source_status_counts,
        "ranked_source_count": ranked_source_count,
        "abstract_evidence_summary": abstract_summary,
        "selective_fulltext_summary": fulltext_summary,
        "field_report_summary": field_report_summary,
        "improvement_recommendation": improvement,
        "db_spine_summary": db_spine_summary,
        "trace_summary": {
            "trace_count": int(trace.get("trace_count") or 0),
            "atom_count": int(trace.get("atom_count") or 0),
            "preview_row_count": len(trace.get("atlas_trace_preview") or []),
        },
        "next_recommended_packet": NEXT_RECOMMENDED_PACKET,
    }
    violations = assert_no_private_fields({"artifact": artifact})
    if violations:
        raise ValueError(
            "Demo loop artifact blocked by private-field policy: "
            + "; ".join(violations[:5])
        )
    return artifact


def sync_demo_loop_artifact_to_public_site(
    artifact: dict[str, Any],
    *,
    public_path: Path,
) -> dict[str, Any]:
    """Copy validated demo loop artifact into public-site preview data."""
    if artifact.get("schema_version") != DEMO_LOOP_SCHEMA_VERSION:
        raise ValueError(
            f"schema_version must be {DEMO_LOOP_SCHEMA_VERSION!r}."
        )
    verdict = str(artifact.get("demo_loop_verdict") or "")
    if verdict in {"", "PENDING"}:
        raise ValueError("demo_loop_verdict must be set before public sync.")
    abstract = artifact.get("abstract_evidence_summary") or {}
    if int(abstract.get("accepted_claims_total") or 0) < 1:
        raise ValueError("abstract_evidence_summary.accepted_claims_total must be >= 1.")
    violations = assert_no_private_fields({"artifact": artifact})
    if violations:
        raise ValueError(
            "Demo loop artifact failed public-safe validation: "
            + "; ".join(violations[:5])
        )
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return {
        "status": "completed",
        "output_path": str(public_path),
        "demo_loop_verdict": verdict,
        "accepted_claims_total": abstract.get("accepted_claims_total"),
        "trace_count": (artifact.get("trace_summary") or {}).get("trace_count"),
    }


def summarize_field_report(field_report: dict[str, Any] | None) -> dict[str, Any]:
    report = field_report or {}
    abstract = report.get("abstract_evidence_summary") or {}
    return {
        "report_type": str(report.get("report_type") or "field_map"),
        "metadata_record_count": int(report.get("metadata_record_count") or 0),
        "cluster_count": int(report.get("cluster_count") or 0),
        "weak_evidence_area_count": len(report.get("weak_evidence_areas") or []),
        "accepted_claims_total": int(abstract.get("accepted_claims_total") or 0),
        "rejected_claims_total": int(abstract.get("rejected_claims_total") or 0),
    }


def run_demo_loop_polish_smoke(
    conn: Any | None = None,
    *,
    topic: str = DEFAULT_TOPIC,
    domain_pack: str = "creativity",
    max_candidates: int = 20,
    top_sources: int = 5,
    full_text_top_n: int = 3,
    mode: str = "abstract-first",
    persist_claims: bool = False,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Operator-gated fixture research demo loop with Atlas-safe summary."""
    env_gates = assert_demo_loop_polish_env()
    os.environ.setdefault("RGE_LLM_MODE", "mock")

    demo = run_research_demo(
        topic=topic,
        domain_pack=domain_pack,
        max_candidates=max_candidates,
        top_sources=top_sources,
        full_text_top_n=full_text_top_n,
        fixture_mode=True,
        mode=mode,
        db_conn=conn,
        persist_claims=persist_claims and conn is not None,
        staging_dir=output_dir,
    )

    trace_summary: dict[str, Any] | None = None
    if conn is not None and persist_claims:
        from rge.modules.live_arbitrary_source_health import build_atlas_safe_run_artifact
        from rge.modules.run_evaluator import generate_run_report

        report_result = generate_run_report(
            conn,
            run_id=DEMO_LOOP_RUN_ID,
            topic=topic,
            domain_pack=domain_pack,
            output_dir=output_dir,
        )
        run_report = dict(report_result.get("report") or {})
        atlas_run = build_atlas_safe_run_artifact(
            conn,
            question=topic,
            domain_pack=domain_pack,
            run_report=run_report,
            question_id="demo_loop_polish",
        )
        trace_summary = dict(atlas_run.get("trace_summary") or {})

    abstract_summary = summarize_abstract_evidence(demo.get("abstract_evidence"))
    fulltext_summary = summarize_selective_fulltext(demo.get("selective_fulltext"))
    improvement = summarize_improvement_recommendation(
        demo.get("improvement_recommendation")
    )
    db_spine_summary = summarize_db_spine(demo.get("db_spine"))
    field_report_summary = summarize_field_report(demo.get("field_map_report"))

    verdict, rationale = classify_demo_loop_verdict(
        demo_status=str(demo.get("status") or ""),
        abstract_summary=abstract_summary,
        fulltext_summary=fulltext_summary,
        field_report=demo.get("field_map_report"),
        improvement=improvement,
        db_spine_summary=db_spine_summary,
        trace_summary=trace_summary,
    )

    atlas_artifact = build_atlas_safe_demo_loop_artifact(
        topic=topic,
        domain_pack=domain_pack,
        mode=str(demo.get("mode") or mode),
        fixture_mode=True,
        resolver_summary=dict(demo.get("resolver_summary") or {}),
        source_status_counts=summarize_source_status_counts(
            list(demo.get("source_status_table") or [])
        ),
        ranked_source_count=len(demo.get("ranked_sources") or []),
        abstract_summary=abstract_summary,
        fulltext_summary=fulltext_summary,
        improvement=improvement,
        field_report_summary=field_report_summary,
        db_spine_summary=db_spine_summary,
        trace_summary=trace_summary,
        verdict=verdict,
        rationale=rationale,
    )

    root = repo_root()
    out_dir = output_dir or (root / "data" / "exports" / "demo_loop_polish")
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = out_dir / DEMO_LOOP_ARTIFACT_NAME
    artifact_path.write_text(json.dumps(atlas_artifact, indent=2), encoding="utf-8")

    demo_output = out_dir / "research_run_latest.json"
    demo_output.write_text(json.dumps(demo, indent=2), encoding="utf-8")

    try:
        operator_artifact_ref = artifact_path.relative_to(root).as_posix()
    except ValueError:
        operator_artifact_ref = f"{out_dir.name}/{DEMO_LOOP_ARTIFACT_NAME}"

    try:
        research_run_output_ref = demo_output.relative_to(root).as_posix()
    except ValueError:
        research_run_output_ref = demo_output.name

    return {
        "packet_id": PACKET_ID,
        "demo_loop_verdict": verdict,
        "demo_loop_rationale": rationale,
        "env_gates": env_gates,
        "artifact_path": str(artifact_path),
        "operator_artifact_ref": operator_artifact_ref,
        "research_run_output_ref": research_run_output_ref,
        "atlas_safe_artifact": atlas_artifact,
        "next_recommended_packet": NEXT_RECOMMENDED_PACKET,
    }


def run_demo_loop_polish_with_fresh_db(
    *,
    output_dir: Path | None = None,
    persist_claims: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    root = repo_root()
    out_dir = output_dir or (root / "data" / "exports" / "demo_loop_polish")
    out_dir.mkdir(parents=True, exist_ok=True)
    db_path = out_dir / "demo_loop_polish.sqlite"
    if db_path.exists():
        db_path.unlink()
    conn = ensure_database(db_path)
    try:
        return run_demo_loop_polish_smoke(
            conn,
            persist_claims=persist_claims,
            output_dir=out_dir,
            **kwargs,
        )
    finally:
        conn.close()
