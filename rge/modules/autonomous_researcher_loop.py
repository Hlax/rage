"""Closed autonomous researcher loop proof orchestrator (ticket-332).

Fixture-mode default: seed question → research pipeline → private atlas export →
coherence report → research quality evaluation → recommended improvement ticket.

Staged-spine path (ticket-337): mock discover→report orchestrator → same inspection
tail without live Ollama or public export.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from rge.cli import FIXTURE_RUN_ID, GOLDEN_MVP_TOPIC, execute_fixture_mode_run
from rge.db.connection import connect
from rge.modules.atlas_coherence_report import write_atlas_coherence_report
from rge.modules.atlas_snapshot_builder import export_atlas_snapshot_to_path
from rge.modules.research_quality_evaluator import (
    evaluate_research_quality,
    recommend_improvement_ticket,
    refresh_research_quality_after_ticket_seeding,
)

LOOP_SCHEMA_VERSION = "autonomous_researcher_loop_v0"
COMMAND = "autonomous-researcher-loop"
ResearchPath = Literal["fixture_mode", "staged_spine"]
RESEARCH_PATHS: tuple[ResearchPath, ...] = ("fixture_mode", "staged_spine")


def _normalize_staged_run_for_quality(staged_result: dict[str, Any]) -> dict[str, Any]:
    """Map staged orchestrator counts to fixture run_result fields for quality eval."""
    return {
        "status": staged_result.get("status"),
        "mode": staged_result.get("mode"),
        "claims_accepted": int(staged_result.get("rank1_accepted") or 0)
        + int(staged_result.get("rank2_accepted") or 0),
        "claims_rejected": int(staged_result.get("rank1_rejected") or 0)
        + int(staged_result.get("rank2_rejected") or 0),
        "relationships_active": int(staged_result.get("rank1_relationships") or 0)
        + int(staged_result.get("rank2_relationships") or 0),
        "card_count": 0,
        "ticket_ids": [],
        "rank1_run_id": staged_result.get("rank1_run_id"),
        "rank2_run_id": staged_result.get("rank2_run_id"),
    }


def _execute_research_step(
    *,
    research_path: ResearchPath,
    topic: str,
    domain: str,
    db_path: Path,
    run_id: str,
    report_dir: Path,
    ticket_dir: Path,
    export_dir: Path,
    staging_dir: Path | None,
    question_id: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run the research orchestrator for the selected path."""
    if research_path == "staged_spine":
        from rge.cli import (
            STAGED_FIXTURE_QUESTION_ID,
            execute_staged_fixture_mode_run,
        )

        staged_result = execute_staged_fixture_mode_run(
            topic=topic,
            domain=domain,
            db_path=db_path,
            run_id=run_id,
            report_dir=report_dir,
            staging_dir=staging_dir,
            question_id=question_id or STAGED_FIXTURE_QUESTION_ID,
        )
        return staged_result, _normalize_staged_run_for_quality(staged_result)

    fixture_result = execute_fixture_mode_run(
        topic=topic,
        domain=domain,
        db_path=db_path,
        run_id=run_id,
        report_dir=report_dir,
        ticket_dir=ticket_dir,
        export_dirs=[export_dir],
    )
    return fixture_result, fixture_result


def execute_autonomous_researcher_loop(
    *,
    topic: str | None = None,
    domain: str = "creativity",
    db_path: Path,
    artifact_dir: Path,
    run_id: str = FIXTURE_RUN_ID,
    recommended_ticket_id: str = "ticket-333",
    research_path: ResearchPath = "fixture_mode",
    staging_dir: Path | None = None,
    question_id: str | None = None,
) -> dict[str, Any]:
    """Run one mock-safe autonomous researcher loop and write inspection artifacts."""
    if research_path not in RESEARCH_PATHS:
        return {
            "status": "failed",
            "command": COMMAND,
            "loop_schema_version": LOOP_SCHEMA_VERSION,
            "detail": f"Unsupported research_path: {research_path}",
        }

    resolved_topic = topic or GOLDEN_MVP_TOPIC
    artifact_dir.mkdir(parents=True, exist_ok=True)
    export_dir = artifact_dir / "export"
    report_dir = artifact_dir / "reports"
    ticket_dir = artifact_dir / "tickets"
    resolved_staging = staging_dir or (artifact_dir / "staging")
    for directory in (export_dir, report_dir, ticket_dir, resolved_staging):
        directory.mkdir(parents=True, exist_ok=True)

    raw_run_result, run_result = _execute_research_step(
        research_path=research_path,
        topic=resolved_topic,
        domain=domain,
        db_path=db_path,
        run_id=run_id,
        report_dir=report_dir,
        ticket_dir=ticket_dir,
        export_dir=export_dir,
        staging_dir=resolved_staging,
        question_id=question_id,
    )
    if raw_run_result.get("status") != "completed":
        return {
            "status": "failed",
            "command": COMMAND,
            "loop_schema_version": LOOP_SCHEMA_VERSION,
            "research_path": research_path,
            "detail": (
                "Staged-spine research run did not complete."
                if research_path == "staged_spine"
                else "Fixture-mode research run did not complete."
            ),
            "run_result": raw_run_result,
        }

    atlas_path = artifact_dir / "atlas_snapshot.json"
    coherence_json = artifact_dir / "atlas_coherence_report.json"
    coherence_md = artifact_dir / "atlas_coherence_report.md"
    loop_report_path = artifact_dir / "autonomous_loop_report.json"
    recommended_ticket_path = artifact_dir / "recommended_improvement_ticket.json"

    atlas_fixture_mode = research_path == "fixture_mode"
    quality_run_id = run_id
    if research_path == "staged_spine":
        quality_run_id = str(raw_run_result.get("rank1_run_id") or run_id)

    conn = connect(db_path)
    try:
        atlas_export = export_atlas_snapshot_to_path(
            conn,
            atlas_path,
            topic=resolved_topic,
            domain_pack=domain,
            fixture_mode=atlas_fixture_mode,
        )
        snapshot = json.loads(atlas_path.read_text(encoding="utf-8"))
        coherence_result = write_atlas_coherence_report(
            snapshot,
            json_path=coherence_json,
            markdown_path=coherence_md,
        )
        coherence_report = json.loads(coherence_json.read_text(encoding="utf-8"))
    finally:
        conn.close()

    if research_path == "staged_spine":
        run_report_path = Path(raw_run_result["artifacts"]["rank1_run_report"])
        improvement_path = ticket_dir / "improvement_ticket_latest.json"
    else:
        run_report_path = Path(run_result["artifacts"]["run_report"])
        improvement_path = Path(run_result["artifacts"]["improvement_tickets"])

    run_report = json.loads(run_report_path.read_text(encoding="utf-8"))
    improvement_payload: list[dict[str, Any]] | dict[str, Any] = []
    if improvement_path.is_file():
        raw = json.loads(improvement_path.read_text(encoding="utf-8"))
        improvement_payload = raw if isinstance(raw, list) else raw

    improvement_result = {
        "status": (
            "skipped_staged_spine_no_improvement_step"
            if research_path == "staged_spine"
            else (
                "skipped_golden_covered"
                if not run_result.get("ticket_ids")
                and isinstance(improvement_payload, list)
                and len(improvement_payload) == 0
                else "generated"
            )
        ),
        "ticket_ids": run_result.get("ticket_ids") or [],
        "output_path": str(improvement_path),
    }

    quality_initial = evaluate_research_quality(
        run_result=run_result,
        run_report=run_report,
        atlas_snapshot=snapshot,
        coherence_report=coherence_report,
        improvement_result=improvement_result,
    )

    evidence = [
        f"autonomous_loop:{quality_run_id}:quality_verdict={quality_initial['research_quality_verdict']}",
        f"autonomous_loop:{quality_run_id}:weakest={quality_initial['weakest_dimension']}",
        f"autonomous_loop:research_path={research_path}",
        f"coherence:{coherence_report.get('overall_coherence_verdict')}",
        f"run_report:{quality_run_id}:tickets_generated={run_report.get('tickets_generated', 0)}",
    ]
    for mode in run_report.get("top_failure_modes") or []:
        evidence.append(
            f"run_report:{quality_run_id}:{mode.get('reason')}_count={mode.get('count')}"
        )

    quality_driven_result: dict[str, Any] | None = None
    if not run_result.get("ticket_ids"):
        from rge.modules.ticket_writer import generate_quality_driven_improvement_tickets

        conn = connect(db_path)
        try:
            quality_driven_result = generate_quality_driven_improvement_tickets(
                conn,
                run_id=quality_run_id,
                quality=quality_initial,
                output_dir=ticket_dir,
                supplemental_evidence=evidence,
            )
        finally:
            conn.close()
        improvement_path = Path(
            (quality_driven_result or {}).get("output_path") or improvement_path
        )

    quality = refresh_research_quality_after_ticket_seeding(
        run_result=run_result,
        run_report=run_report,
        atlas_snapshot=snapshot,
        coherence_report=coherence_report,
        improvement_result=improvement_result,
        quality_driven_result=quality_driven_result,
        initial_quality=quality_initial,
    )

    recommended_ticket = recommend_improvement_ticket(
        quality,
        queue_ticket_id=recommended_ticket_id,
        evidence=evidence,
    )
    recommended_ticket_path.write_text(
        json.dumps(recommended_ticket, indent=2) + "\n",
        encoding="utf-8",
    )

    research_step = (
        "execute_staged_fixture_mode_run"
        if research_path == "staged_spine"
        else "execute_fixture_mode_run"
    )
    loop_report = {
        "status": "completed",
        "command": COMMAND,
        "loop_schema_version": LOOP_SCHEMA_VERSION,
        "research_path": research_path,
        "topic": resolved_topic,
        "domain": domain,
        "run_id": run_id,
        "quality_run_id": quality_run_id,
        "database_path": str(db_path),
        "artifact_dir": str(artifact_dir),
        "staging_dir": str(resolved_staging) if research_path == "staged_spine" else None,
        "steps_completed": [
            research_step,
            "export_atlas_snapshot",
            "atlas_coherence_report",
            "evaluate_research_quality",
            "generate_quality_driven_improvement_tickets",
            "refresh_research_quality_after_ticket_seeding",
            "recommend_improvement_ticket",
        ],
        "artifacts": {
            "atlas_snapshot": str(atlas_path),
            "coherence_json": str(coherence_json),
            "coherence_md": str(coherence_md),
            "run_report": str(run_report_path),
            "improvement_tickets": str(improvement_path),
            "loop_report": str(loop_report_path),
            "recommended_improvement_ticket": str(recommended_ticket_path),
        },
        "run_summary": {
            "claims_accepted": run_result.get("claims_accepted"),
            "claims_rejected": run_result.get("claims_rejected"),
            "relationships_active": run_result.get("relationships_active"),
            "card_count": run_result.get("card_count"),
            "ticket_ids": run_result.get("ticket_ids") or [],
            "quality_driven_ticket_ids": (
                (quality_driven_result or {}).get("ticket_ids") or []
            ),
            "quality_driven_status": (
                (quality_driven_result or {}).get("status")
            ),
            "rank1_run_id": raw_run_result.get("rank1_run_id"),
            "rank2_run_id": raw_run_result.get("rank2_run_id"),
        },
        "quality_driven_improvement": quality_driven_result,
        "atlas_export": atlas_export,
        "coherence": {
            "overall_coherence_verdict": coherence_report.get("overall_coherence_verdict"),
            "population": coherence_report.get("population"),
        },
        "research_quality": quality,
        "research_quality_initial": quality_initial,
        "recommended_improvement_ticket_id": recommended_ticket_id,
        "drift_note": (
            "Research Atlas / frontend contract is parked; next work should improve "
            "autonomous research behavior beyond fixture-mode and staged-spine mock paths."
        ),
    }
    loop_report_path.write_text(json.dumps(loop_report, indent=2) + "\n", encoding="utf-8")
    return loop_report
