"""Mock arbitrary-source operator proof bundle (ticket-267)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rge.cli import (
    STAGED_FIXTURE_QUESTION_ID,
    STAGED_FIXTURE_RUN_ID,
    execute_staged_fixture_mode_run,
)
from rge.db.connection import connect, get_db_path
from rge.modules.card_exporter import FIXTURE_EXPORT_TIMESTAMP, export_public_cards

PROOF_BUNDLE_SCHEMA_VERSION = "1"
PIPELINE_MODE = "fixture_staged_rank1"
COMMAND = "prove-arbitrary-source-bundle"

REQUIRED_BUNDLE_FIELDS = (
    "status",
    "command",
    "pipeline_mode",
    "proof_bundle_schema_version",
    "source_id",
    "claim_count",
    "concept_link_count",
    "relationship_count",
    "qualification_count",
    "reconcile",
    "report_path",
    "export_path",
    "card_count",
    "database_path",
    "steps_completed",
    "usable_output",
)


def _failed_step_from_runtime_error(detail: str) -> str:
    marker = "research CLI step failed"
    if marker in detail:
        tail = detail.split(marker, 1)[-1]
        for token in ("extract-claims", "link-concepts", "build-relationships",
                      "detect-contradictions", "reconcile-scores",
                      "generate-run-report", "export-public", "ingest",
                      "discover-sources", "fetch-candidate", "ingest-staged"):
            if token in tail:
                return token
    if "staged fixture run counts mismatch" in detail:
        return "orchestrator_validation"
    return "orchestrator"


def collect_source_metrics(conn: Any, source_id: str) -> dict[str, int]:
    """Read per-source spine counts from the accepted graph DB."""
    claim_count = int(
        conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ?",
            (source_id,),
        ).fetchone()[0]
    )
    accepted_claim_count = int(
        conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ? AND status = 'accepted'",
            (source_id,),
        ).fetchone()[0]
    )
    concept_link_count = int(
        conn.execute(
            """
            SELECT COUNT(*) FROM claim_concepts cc
            JOIN claims c ON c.id = cc.claim_id
            WHERE c.source_id = ?
            """,
            (source_id,),
        ).fetchone()[0]
    )
    relationship_count = int(
        conn.execute(
            """
            SELECT COUNT(DISTINCT r.id)
            FROM relationships r
            JOIN relationship_evidence re ON re.relationship_id = r.id
            JOIN claims c ON c.id = re.claim_id
            WHERE c.source_id = ?
            """,
            (source_id,),
        ).fetchone()[0]
    )
    qualification_count = int(
        conn.execute(
            """
            SELECT COUNT(*) FROM relationship_evidence re
            JOIN claims c ON c.id = re.claim_id
            WHERE c.source_id = ? AND re.stance = 'qualifies'
            """,
            (source_id,),
        ).fetchone()[0]
    )
    reconcile_score_events = int(
        conn.execute(
            "SELECT COUNT(*) FROM score_events WHERE triggering_source_id = ?",
            (source_id,),
        ).fetchone()[0]
    )
    return {
        "claim_count": claim_count,
        "accepted_claim_count": accepted_claim_count,
        "concept_link_count": concept_link_count,
        "relationship_count": relationship_count,
        "qualification_count": qualification_count,
        "reconcile_score_events": reconcile_score_events,
    }


def compute_usable_output(
    *,
    metrics: dict[str, int],
    report_path: Path,
    export_path: Path,
    export_status: str,
) -> bool:
    return (
        metrics["accepted_claim_count"] >= 1
        and metrics["relationship_count"] >= 1
        and report_path.is_file()
        and export_path.is_file()
        and export_status == "success"
    )


def build_proof_bundle(
    *,
    orchestrator: dict[str, Any],
    metrics: dict[str, int],
    export_result: dict[str, Any],
    report_path: Path,
    export_path: Path,
    database_path: Path,
) -> dict[str, Any]:
    reconcile_events = metrics["reconcile_score_events"]
    reconcile_status = "completed" if reconcile_events > 0 else "no_score_changes"
    steps = list(orchestrator.get("steps_completed") or [])
    steps.append("export_public_cards")
    steps.append("operator_proof_bundle")

    return {
        "status": "completed",
        "command": COMMAND,
        "pipeline_mode": PIPELINE_MODE,
        "proof_bundle_schema_version": PROOF_BUNDLE_SCHEMA_VERSION,
        "source_id": orchestrator["rank1_source_id"],
        "claim_count": metrics["claim_count"],
        "concept_link_count": metrics["concept_link_count"],
        "relationship_count": metrics["relationship_count"],
        "qualification_count": metrics["qualification_count"],
        "reconcile": {
            "status": reconcile_status,
            "score_events_created": reconcile_events,
        },
        "report_path": str(report_path),
        "export_path": str(export_path),
        "card_count": int(export_result.get("card_count", 0)),
        "database_path": str(database_path),
        "steps_completed": steps,
        "usable_output": compute_usable_output(
            metrics=metrics,
            report_path=report_path,
            export_path=export_path,
            export_status=str(export_result.get("status", "")),
        ),
        "rank1_candidate_id": orchestrator.get("rank1_candidate_id"),
        "rank1_run_id": orchestrator.get("rank1_run_id"),
    }


def build_error_bundle(
    *,
    detail: str,
    failed_step: str,
    database_path: Path | None = None,
    partial_metrics: dict[str, int] | None = None,
) -> dict[str, Any]:
    bundle: dict[str, Any] = {
        "status": "error",
        "command": COMMAND,
        "pipeline_mode": PIPELINE_MODE,
        "proof_bundle_schema_version": PROOF_BUNDLE_SCHEMA_VERSION,
        "failed_step": failed_step,
        "detail": detail,
        "usable_output": False,
        "steps_completed": [],
    }
    if database_path is not None:
        bundle["database_path"] = str(database_path)
    if partial_metrics:
        bundle.update(
            {
                "source_id": partial_metrics.get("source_id"),
                "claim_count": partial_metrics.get("claim_count"),
                "concept_link_count": partial_metrics.get("concept_link_count"),
                "relationship_count": partial_metrics.get("relationship_count"),
                "qualification_count": partial_metrics.get("qualification_count"),
            }
        )
    return bundle


def write_proof_bundle(bundle: dict[str, Any], bundle_out: Path) -> None:
    bundle_out.parent.mkdir(parents=True, exist_ok=True)
    bundle_out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")


def execute_arbitrary_source_proof_bundle(
    *,
    topic: str,
    domain: str,
    db_path: Path,
    report_dir: Path,
    staging_dir: Path,
    export_dir: Path,
    bundle_out: Path | None = None,
    run_id: str = STAGED_FIXTURE_RUN_ID,
    question_id: str = STAGED_FIXTURE_QUESTION_ID,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Run mock staged spine, export cards, and assemble operator proof bundle."""
    import os

    from rge.cli import _REPO_ROOT

    resolved_db = get_db_path(db_path)
    root = repo_root or _REPO_ROOT
    prior_mode = os.environ.get("RGE_LLM_MODE")
    prior_live = os.environ.get("RGE_ALLOW_LIVE_LLM")
    os.environ["RGE_LLM_MODE"] = "mock"
    os.environ.pop("RGE_ALLOW_LIVE_LLM", None)

    try:
        orchestrator = execute_staged_fixture_mode_run(
            topic=topic,
            domain=domain,
            db_path=resolved_db,
            run_id=run_id,
            report_dir=report_dir,
            staging_dir=staging_dir,
            question_id=question_id,
        )
        rank1_source_id = orchestrator["rank1_source_id"]
        report_path = Path(
            orchestrator.get("artifacts", {}).get(
                "rank1_run_report",
                report_dir / "run_report_latest.json",
            )
        )
        export_path = export_dir / "public_cards.json"

        conn = connect(resolved_db)
        try:
            export_result = export_public_cards(
                conn,
                limit=100,
                output_dirs=[export_dir],
                repo_root=root,
                fixture_mode=True,
                export_timestamp=FIXTURE_EXPORT_TIMESTAMP,
                publish_public=False,
                snapshot_history=False,
            )
            metrics = collect_source_metrics(conn, rank1_source_id)
        finally:
            conn.close()

        bundle = build_proof_bundle(
            orchestrator=orchestrator,
            metrics=metrics,
            export_result=export_result,
            report_path=report_path,
            export_path=export_path,
            database_path=resolved_db,
        )
        if bundle_out is not None:
            write_proof_bundle(bundle, bundle_out)
            bundle["bundle_path"] = str(bundle_out)
        return bundle
    except (RuntimeError, ValueError) as exc:
        bundle = build_error_bundle(
            detail=str(exc),
            failed_step=_failed_step_from_runtime_error(str(exc)),
            database_path=resolved_db,
        )
        if bundle_out is not None:
            write_proof_bundle(bundle, bundle_out)
            bundle["bundle_path"] = str(bundle_out)
        return bundle
    finally:
        if prior_mode is None:
            os.environ.pop("RGE_LLM_MODE", None)
        else:
            os.environ["RGE_LLM_MODE"] = prior_mode
        if prior_live is None:
            os.environ.pop("RGE_ALLOW_LIVE_LLM", None)
        else:
            os.environ["RGE_ALLOW_LIVE_LLM"] = prior_live
