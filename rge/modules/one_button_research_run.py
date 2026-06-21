"""One-button mock-safe research run (operator packet v1).

Collapses staged-spine research → private atlas export → research quality JSON
into a single CLI invocation. Defaults: mock LLM, no network, scratch paths.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from rge.cli import (
    FIXTURE_RUN_ID,
    STAGED_FIXTURE_QUESTION_ID,
    STAGED_FIXTURE_RUN_ID,
    execute_fixture_mode_run,
    execute_staged_fixture_mode_run,
)
from rge.db.connection import connect
from rge.modules.atlas_coherence_report import write_atlas_coherence_report
from rge.modules.atlas_snapshot_builder import export_atlas_snapshot_to_path
from rge.modules.autonomous_researcher_loop import _normalize_staged_run_for_quality
from rge.modules.principal_audit_gate import repo_root
from rge.modules.research_quality_evaluator import (
    evaluate_research_quality,
    recommend_improvement_ticket,
)

COMMAND = "run"
SCHEMA_VERSION = "one_button_research_run_v0.1.0"
DEFAULT_DB_REL = Path("data/db/scratch_research.sqlite")
DEFAULT_ARTIFACT_DIR_REL = Path("data/reports/scratch_research")

NEXT_RECOMMENDED_PACKET = {
    "id": "local-scheduled-research-loop",
    "title": "Local Scheduled Research Loop (Windows Task Scheduler profile)",
}


class OneButtonResearchRunGateError(RuntimeError):
    """Raised when live opt-in gates are missing for one-button research run."""


def _truthy(name: str) -> bool:
    return os.environ.get(name, "0").strip().casefold() in {"1", "true", "yes"}


def assert_live_network_gates() -> dict[str, str]:
    """Fail closed unless live network gates are set."""
    missing: list[str] = []
    gates: dict[str, str] = {}
    for name in ("RGE_ALLOW_SOURCE_NETWORK",):
        value = os.environ.get(name, "").strip()
        if not _truthy(name):
            missing.append(f"{name}=1")
        else:
            gates[name] = value
    mailto = os.environ.get("OPENALEX_MAILTO", "").strip()
    if not mailto:
        missing.append("OPENALEX_MAILTO=<operator email>")
    else:
        gates["OPENALEX_MAILTO"] = mailto
    if missing:
        raise OneButtonResearchRunGateError(
            "Live network requires: " + ", ".join(missing)
        )
    return gates


def assert_live_llm_extract_gates() -> dict[str, str]:
    """Fail closed unless live Ollama extract gates are set."""
    missing: list[str] = []
    gates: dict[str, str] = {}
    if not _truthy("RGE_ALLOW_LIVE_LLM"):
        missing.append("RGE_ALLOW_LIVE_LLM=1")
    llm_mode = os.environ.get("RGE_LLM_MODE", "mock").strip().casefold()
    if llm_mode != "ollama":
        missing.append("RGE_LLM_MODE=ollama")
    else:
        gates["RGE_LLM_MODE"] = llm_mode
    if not _truthy("RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM"):
        missing.append("RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM=1")
    if missing:
        raise OneButtonResearchRunGateError(
            "Live LLM extract requires: " + ", ".join(missing)
        )
    gates["RGE_ALLOW_LIVE_LLM"] = os.environ.get("RGE_ALLOW_LIVE_LLM", "1")
    gates["RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM"] = os.environ.get(
        "RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM", "1"
    )
    return gates


def resolve_scratch_paths(
    *,
    db_path: Path | None,
    artifact_dir: Path | None,
    root: Path | None = None,
) -> tuple[Path, Path]:
    project_root = root or repo_root()
    resolved_db = db_path or (project_root / DEFAULT_DB_REL)
    resolved_artifact = artifact_dir or (project_root / DEFAULT_ARTIFACT_DIR_REL)
    if not resolved_db.is_absolute():
        resolved_db = project_root / resolved_db
    if not resolved_artifact.is_absolute():
        resolved_artifact = project_root / resolved_artifact
    return resolved_db, resolved_artifact


def execute_one_button_research_run(
    *,
    topic: str,
    domain: str = "creativity",
    db_path: Path | None = None,
    artifact_dir: Path | None = None,
    export_atlas: bool = True,
    quality_report_path: Path | None = None,
    live_network: bool = False,
    live_llm_extract: bool = False,
    sync_atlas_public: bool = False,
    skip_site_build: bool = False,
    source_limit: int | None = None,
    run_id: str = STAGED_FIXTURE_RUN_ID,
    question_id: str | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Run mock-safe one-button research workflow on scratch paths."""
    project_root = root or repo_root()
    resolved_db, resolved_artifact = resolve_scratch_paths(
        db_path=db_path,
        artifact_dir=artifact_dir,
        root=project_root,
    )
    resolved_artifact.mkdir(parents=True, exist_ok=True)
    resolved_db.parent.mkdir(parents=True, exist_ok=True)

    prior_llm = os.environ.get("RGE_LLM_MODE")
    prior_network = os.environ.get("RGE_ALLOW_SOURCE_NETWORK")
    gates_applied: dict[str, str] = {}

    try:
        if live_network:
            gates_applied.update(assert_live_network_gates())
        else:
            os.environ["RGE_LLM_MODE"] = "mock"
            os.environ.pop("RGE_ALLOW_SOURCE_NETWORK", None)

        if live_llm_extract:
            gates_applied.update(assert_live_llm_extract_gates())
        elif not live_network:
            os.environ["RGE_LLM_MODE"] = "mock"

        report_dir = resolved_artifact / "reports"
        staging_dir = resolved_artifact / "staging"
        ticket_dir = resolved_artifact / "tickets"
        export_dir = resolved_artifact / "export"
        for directory in (report_dir, staging_dir, ticket_dir, export_dir):
            directory.mkdir(parents=True, exist_ok=True)

        research_path = "staged_spine" if live_network else "fixture_mode"
        atlas_fixture_mode = not live_network

        if live_network:
            pipeline_result = execute_staged_fixture_mode_run(
                topic=topic,
                domain=domain,
                db_path=resolved_db,
                run_id=run_id,
                report_dir=report_dir,
                staging_dir=staging_dir,
                question_id=question_id or STAGED_FIXTURE_QUESTION_ID,
            )
            if pipeline_result.get("status") != "completed":
                return {
                    "status": "failed",
                    "command": COMMAND,
                    "schema_version": SCHEMA_VERSION,
                    "detail": "Staged-spine research run did not complete.",
                    "run_result": pipeline_result,
                    "research_path": research_path,
                    "gates_applied": gates_applied,
                    "no_auto_promotion": True,
                    "no_public_publish": True,
                }
            run_result = _normalize_staged_run_for_quality(pipeline_result)
            quality_run_id = str(pipeline_result.get("rank1_run_id") or run_id)
            run_report_path = Path(pipeline_result["artifacts"]["rank1_run_report"])
        else:
            fixture_run_id = run_id if run_id != STAGED_FIXTURE_RUN_ID else FIXTURE_RUN_ID
            pipeline_result = execute_fixture_mode_run(
                topic=topic,
                domain=domain,
                db_path=resolved_db,
                run_id=fixture_run_id,
                report_dir=report_dir,
                ticket_dir=ticket_dir,
                export_dirs=[export_dir],
            )
            if pipeline_result.get("status") != "completed":
                return {
                    "status": "failed",
                    "command": COMMAND,
                    "schema_version": SCHEMA_VERSION,
                    "detail": "Fixture-mode research run did not complete.",
                    "run_result": pipeline_result,
                    "research_path": research_path,
                    "gates_applied": gates_applied,
                    "no_auto_promotion": True,
                    "no_public_publish": True,
                }
            run_result = pipeline_result
            quality_run_id = fixture_run_id
            run_report_path = Path(pipeline_result["artifacts"]["run_report"])

        run_report = json.loads(run_report_path.read_text(encoding="utf-8"))

        atlas_path = resolved_artifact / "atlas_snapshot.json"
        coherence_json = resolved_artifact / "atlas_coherence_report.json"
        coherence_md = resolved_artifact / "atlas_coherence_report.md"
        atlas_export: dict[str, Any] | None = None
        snapshot: dict[str, Any] = {}
        coherence_report: dict[str, Any] = {}

        if export_atlas:
            conn = connect(resolved_db)
            try:
                atlas_export = export_atlas_snapshot_to_path(
                    conn,
                    atlas_path,
                    topic=topic,
                    domain_pack=domain,
                    fixture_mode=atlas_fixture_mode,
                )
                snapshot = json.loads(atlas_path.read_text(encoding="utf-8"))
                write_atlas_coherence_report(
                    snapshot,
                    json_path=coherence_json,
                    markdown_path=coherence_md,
                )
                coherence_report = json.loads(coherence_json.read_text(encoding="utf-8"))
            finally:
                conn.close()

        improvement_result = {
            "status": "skipped_staged_spine_no_improvement_step",
            "ticket_ids": [],
        }
        quality = evaluate_research_quality(
            run_result=run_result,
            run_report=run_report,
            atlas_snapshot=snapshot,
            coherence_report=coherence_report,
            improvement_result=improvement_result,
        )

        quality_path = quality_report_path or (resolved_artifact / "research_quality.json")
        if not quality_path.is_absolute():
            quality_path = project_root / quality_path
        quality_path.parent.mkdir(parents=True, exist_ok=True)
        quality_path.write_text(json.dumps(quality, indent=2) + "\n", encoding="utf-8")

        recommended_ticket = recommend_improvement_ticket(
            quality,
            queue_ticket_id="ticket-next",
            evidence=[f"one_button_run:{quality_run_id}"],
        )
        recommended_path = resolved_artifact / "recommended_improvement_ticket.json"
        recommended_path.write_text(
            json.dumps(recommended_ticket, indent=2) + "\n",
            encoding="utf-8",
        )

        sync_result: dict[str, Any] | None = None
        if sync_atlas_public:
            from rge.modules.full_atlas_refresh_checklist import (
                refresh_fixture_operator_packets,
            )

            export_dir = resolved_artifact / "public_sync"
            sync_result = refresh_fixture_operator_packets(
                root=project_root,
                export_dir=export_dir,
            )
            if not skip_site_build:
                import subprocess

                site_dir = project_root / "apps" / "public-site"
                if site_dir.is_dir():
                    subprocess.run(
                        ["npm", "run", "build"],
                        cwd=site_dir,
                        check=False,
                    )

        return {
            "status": "completed",
            "command": COMMAND,
            "schema_version": SCHEMA_VERSION,
            "mode": "one_button_research_run_v1",
            "research_path": research_path,
            "topic": topic,
            "domain": domain,
            "db_path": str(resolved_db.relative_to(project_root)),
            "artifact_dir": str(resolved_artifact.relative_to(project_root)),
            "llm_mode": os.environ.get("RGE_LLM_MODE", "mock"),
            "live_network": live_network,
            "live_llm_extract": live_llm_extract,
            "source_limit": source_limit,
            "gates_applied": gates_applied,
            "run_result": pipeline_result,
            "research_quality_verdict": quality.get("research_quality_verdict"),
            "weakest_dimension": quality.get("weakest_dimension"),
            "artifacts": {
                "run_report": str(run_report_path),
                "atlas_snapshot": str(atlas_path) if export_atlas else None,
                "coherence_report": str(coherence_json) if export_atlas else None,
                "research_quality": str(quality_path),
                "recommended_improvement_ticket": str(recommended_path),
            },
            "atlas_export": atlas_export,
            "public_sync": sync_result,
            "next_recommended_packet": NEXT_RECOMMENDED_PACKET,
            "no_auto_promotion": True,
            "no_merge": True,
            "no_push": True,
            "no_public_publish": not sync_atlas_public,
        }
    finally:
        if prior_llm is None:
            os.environ.pop("RGE_LLM_MODE", None)
        else:
            os.environ["RGE_LLM_MODE"] = prior_llm
        if prior_network is None:
            os.environ.pop("RGE_ALLOW_SOURCE_NETWORK", None)
        else:
            os.environ["RGE_ALLOW_SOURCE_NETWORK"] = prior_network
