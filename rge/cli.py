"""``research`` CLI entry point."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from rge import __version__

_NOT_IMPLEMENTED_EXIT_CODE = 2
_REPO_ROOT = Path(__file__).resolve().parents[1]

FIXTURE_RUN_ID = "run_golden_fixture_mvp"
GOLDEN_MVP_TOPIC = (
    "Does AI improve creative output while reducing diversity?"
)

_FIXTURE_SOURCE_PATHS = {
    "base": _REPO_ROOT
    / "fixtures"
    / "sources"
    / "creativity_ai_diversity_short.txt",
    "followup": _REPO_ROOT
    / "fixtures"
    / "sources"
    / "creativity_ai_diversity_followup_short.txt",
    "contradiction": _REPO_ROOT
    / "fixtures"
    / "sources"
    / "creativity_ai_diversity_contradiction.txt",
}

_FIXTURE_LLM = {
    "base_extract": "claim_extraction_valid_and_missing_quote.json",
    "followup_extract": "claim_extraction_creativity_diversity_followup.json",
    "contradiction_extract": "claim_extraction_creativity_diversity_contradiction.json",
    "contradiction_link": "concept_linking_creativity_diversity_contradiction.json",
    "contradiction_relationship": (
        "relationship_drafting_creativity_diversity_contradiction.json"
    ),
    "contradiction_detect": "contradiction_detection_creativity_diversity.json",
}

_SOURCE_TITLE_BY_KEY = {
    "base": "creativity_ai_diversity_short.txt",
    "followup": "creativity_ai_diversity_followup_short.txt",
    "contradiction": "creativity_ai_diversity_contradiction.txt",
}


def _not_implemented(command: str, phase_hint: str) -> int:
    payload = {
        "status": "not_implemented",
        "command": command,
        "phase": "0",
        "detail": f"'{command}' is a Phase 0 placeholder. {phase_hint}",
    }
    print(json.dumps(payload, indent=2))
    return _NOT_IMPLEMENTED_EXIT_CODE


def _db_cli_args(db_path: Path | None) -> list[str]:
    return ["--db", str(db_path)] if db_path is not None else []


def _run_cli_step(argv: list[str]) -> None:
    exit_code = main(argv)
    if exit_code != 0:
        raise RuntimeError(
            f"research CLI step failed (exit {exit_code}): {' '.join(argv)}"
        )


def _source_id_by_title(conn: Any, title: str) -> str:
    row = conn.execute(
        "SELECT id FROM sources WHERE title = ?",
        (title,),
    ).fetchone()
    if row is None:
        raise ValueError(f"ingested source not found for title: {title}")
    return row[0]


def execute_fixture_mode_run(
    *,
    topic: str,
    domain: str,
    db_path: Path | None = None,
    run_id: str = FIXTURE_RUN_ID,
    report_dir: Path | None = None,
    ticket_dir: Path | None = None,
    export_dirs: list[Path] | None = None,
) -> dict[str, Any]:
    """Run the deterministic fixture-mode MVP pipeline end to end."""
    from rge.db.connection import ensure_database, get_db_path
    from rge.modules.card_exporter import (
        FIXTURE_EXPORT_TIMESTAMP,
        default_export_dirs,
        default_ticket_output_dir,
        export_public_cards,
    )
    from rge.modules.cluster_reporter import generate_cluster_report
    from rge.modules.research_planner import ensure_golden_contract, generate_followup_questions
    from rge.modules.research_queue import queue_sources_from_fixture
    from rge.modules.run_evaluator import generate_run_report
    from rge.modules.safety_auditor import run_safety_audit
    from rge.modules.theory_generator import generate_theory_candidates
    from rge.modules.ticket_writer import generate_improvement_tickets

    prior_mode = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    root = _REPO_ROOT
    resolved_db = get_db_path(db_path)
    resolved_reports = report_dir or (root / "data" / "reports")
    resolved_tickets = ticket_dir or default_ticket_output_dir(root)
    resolved_exports = (
        export_dirs if export_dirs is not None else default_export_dirs(root)
    )
    db_args = _db_cli_args(db_path)
    steps_completed: list[str] = []

    try:
        conn = ensure_database(db_path)
        try:
            contract = ensure_golden_contract(conn)
            steps_completed.append("create_research_contract")

            queue_result = queue_sources_from_fixture(conn)
            queue_count = int(queue_result.get("queue_count", 0))
            if queue_count < 3:
                raise ValueError(
                    f"fixture queue must include at least three sources; got {queue_count}"
                )
            steps_completed.append("queue_fixture_sources")

            _run_cli_step(
                [
                    "ingest",
                    str(_FIXTURE_SOURCE_PATHS["base"]),
                    "--domain",
                    domain,
                    *db_args,
                ]
            )
            base_id = _source_id_by_title(conn, _SOURCE_TITLE_BY_KEY["base"])
            _run_cli_step(
                [
                    "extract-claims",
                    "--source",
                    base_id,
                    "--fixture",
                    _FIXTURE_LLM["base_extract"],
                    *db_args,
                ]
            )
            _run_cli_step(["link-concepts", "--source", base_id, *db_args])
            _run_cli_step(
                ["build-relationships", "--source", base_id, *db_args]
            )
            _run_cli_step(["reconcile-scores", "--source", base_id, *db_args])
            steps_completed.append("process_base_source")

            _run_cli_step(
                [
                    "ingest",
                    str(_FIXTURE_SOURCE_PATHS["followup"]),
                    "--domain",
                    domain,
                    *db_args,
                ]
            )
            followup_id = _source_id_by_title(conn, _SOURCE_TITLE_BY_KEY["followup"])
            _run_cli_step(
                [
                    "extract-claims",
                    "--source",
                    followup_id,
                    "--fixture",
                    _FIXTURE_LLM["followup_extract"],
                    *db_args,
                ]
            )
            _run_cli_step(["link-concepts", "--source", followup_id, *db_args])
            _run_cli_step(
                ["build-relationships", "--source", followup_id, *db_args]
            )
            _run_cli_step(
                ["reconcile-scores", "--source", followup_id, *db_args]
            )
            steps_completed.append("process_followup_source")

            _run_cli_step(
                [
                    "ingest",
                    str(_FIXTURE_SOURCE_PATHS["contradiction"]),
                    "--domain",
                    domain,
                    *db_args,
                ]
            )
            contradiction_id = _source_id_by_title(
                conn, _SOURCE_TITLE_BY_KEY["contradiction"]
            )
            _run_cli_step(
                [
                    "extract-claims",
                    "--source",
                    contradiction_id,
                    "--fixture",
                    _FIXTURE_LLM["contradiction_extract"],
                    *db_args,
                ]
            )
            _run_cli_step(
                [
                    "link-concepts",
                    "--source",
                    contradiction_id,
                    "--fixture",
                    _FIXTURE_LLM["contradiction_link"],
                    *db_args,
                ]
            )
            _run_cli_step(
                [
                    "build-relationships",
                    "--source",
                    contradiction_id,
                    "--fixture",
                    _FIXTURE_LLM["contradiction_relationship"],
                    *db_args,
                ]
            )
            _run_cli_step(
                [
                    "detect-contradictions",
                    "--source",
                    contradiction_id,
                    "--fixture",
                    _FIXTURE_LLM["contradiction_detect"],
                    *db_args,
                ]
            )
            _run_cli_step(
                ["reconcile-scores", "--source", contradiction_id, *db_args]
            )
            steps_completed.append("process_contradiction_source")

            generate_followup_questions(conn)
            steps_completed.append("generate_followup_questions")

            cluster_result = generate_cluster_report(
                conn,
                domain=domain,
                output_dir=resolved_reports,
                pad_golden=True,
            )
            steps_completed.append("generate_cluster_report")

            theory_result = generate_theory_candidates(
                conn,
                domain=domain,
                output_dir=resolved_reports,
            )
            steps_completed.append("generate_theory_candidates")

            export_result = export_public_cards(
                conn,
                output_dirs=resolved_exports,
                repo_root=root,
                fixture_mode=True,
                export_timestamp=FIXTURE_EXPORT_TIMESTAMP,
            )
            steps_completed.append("export_public_cards")

            generate_run_report(
                conn,
                run_id=run_id,
                topic=topic,
                domain_pack=domain,
                output_dir=resolved_reports,
            )
            steps_completed.append("generate_run_report")

            ticket_result = generate_improvement_tickets(
                conn,
                run_id=run_id,
                output_dir=resolved_tickets,
            )
            steps_completed.append("generate_improvement_tickets")

            safety_report = run_safety_audit("full", root=root)
            if safety_report["status"] != "pass":
                blocked = safety_report.get("blocked_reasons", [])
                raise ValueError(
                    "safety audit failed after fixture run: "
                    + "; ".join(blocked[:3])
                    + (f"; and {len(blocked) - 3} more" if len(blocked) > 3 else "")
                )
            steps_completed.append("safety_audit_full")

            accepted = int(
                conn.execute(
                    "SELECT COUNT(*) FROM claims WHERE status = 'accepted'"
                ).fetchone()[0]
            )
            rejected = int(
                conn.execute(
                    "SELECT COUNT(*) FROM claims WHERE status = 'rejected'"
                ).fetchone()[0]
            )
            relationships = int(
                conn.execute(
                    "SELECT COUNT(*) FROM relationships WHERE status = 'active'"
                ).fetchone()[0]
            )
            score_events = int(
                conn.execute("SELECT COUNT(*) FROM score_events").fetchone()[0]
            )
            tickets = int(
                conn.execute("SELECT COUNT(*) FROM improvement_tickets").fetchone()[0]
            )
            qualifies = int(
                conn.execute(
                    """
                    SELECT COUNT(*) FROM relationship_evidence
                    WHERE stance = 'qualifies'
                    """
                ).fetchone()[0]
            )
            supports = int(
                conn.execute(
                    """
                    SELECT COUNT(*) FROM relationship_evidence
                    WHERE stance = 'supports'
                    """
                ).fetchone()[0]
            )

            if accepted < 1 or rejected < 1:
                raise ValueError("fixture run requires accepted and rejected claims")
            if relationships < 1:
                raise ValueError("fixture run requires active relationships")
            if score_events < 1:
                raise ValueError("fixture run requires score events")
            if export_result.get("card_count", 0) < 2:
                raise ValueError("fixture run requires at least two public cards")
            if qualifies < 1 or supports < 1:
                raise ValueError(
                    "fixture run requires support and qualification evidence"
                )

            export_primary = resolved_exports[0] / "public_cards.json"
            return {
                "status": "completed",
                "command": "run",
                "mode": "fixture",
                "topic": topic,
                "domain": domain,
                "run_id": run_id,
                "contract_id": contract["id"],
                "database_path": str(resolved_db),
                "steps_completed": steps_completed,
                "queue_count": queue_count,
                "sources_ingested": int(
                    conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
                ),
                "claims_accepted": accepted,
                "claims_rejected": rejected,
                "relationships_active": relationships,
                "score_events": score_events,
                "card_count": export_result.get("card_count"),
                "cluster_report_id": cluster_result.get("cluster_report_id"),
                "theory_candidate_ids": theory_result.get("theory_candidate_ids"),
                "ticket_ids": ticket_result.get("ticket_ids"),
                "artifacts": {
                    "database": str(resolved_db),
                    "run_report": str(resolved_reports / "run_report_latest.json"),
                    "cluster_report": str(
                        resolved_reports / "cluster_report_latest.json"
                    ),
                    "public_cards_export": str(export_primary),
                    "public_memos_export": str(
                        resolved_exports[0] / "public_memos.json"
                    ),
                    "improvement_tickets": str(
                        resolved_tickets / "improvement_ticket_latest.json"
                    ),
                },
                "safety_audit_status": safety_report["status"],
            }
        finally:
            conn.close()
    finally:
        if prior_mode is None:
            os.environ.pop("RGE_LLM_MODE", None)
        else:
            os.environ["RGE_LLM_MODE"] = prior_mode


def _cmd_run(args: argparse.Namespace) -> int:
    if not args.fixture_mode:
        return _not_implemented(
            "run",
            "Live discovery runs are not implemented. Use --fixture-mode for the "
            "deterministic MVP pipeline.",
        )
    if not args.topic:
        payload = {
            "status": "error",
            "command": "run",
            "detail": "--topic is required for fixture-mode runs.",
        }
        print(json.dumps(payload, indent=2))
        return 1
    if not args.domain:
        payload = {
            "status": "error",
            "command": "run",
            "detail": "--domain is required for fixture-mode runs.",
        }
        print(json.dumps(payload, indent=2))
        return 1

    try:
        db_path = Path(args.db) if args.db else None
        report_dir = Path(args.output_dir) if args.output_dir else None
        ticket_dir = Path(args.ticket_dir) if args.ticket_dir else None
        export_dirs = (
            [Path(args.export_dir)]
            if getattr(args, "export_dir", None)
            else None
        )
        result = execute_fixture_mode_run(
            topic=args.topic,
            domain=args.domain,
            db_path=db_path,
            run_id=args.run_id or FIXTURE_RUN_ID,
            report_dir=report_dir,
            ticket_dir=ticket_dir,
            export_dirs=export_dirs,
        )
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        payload = {
            "status": "error",
            "command": "run",
            "detail": str(exc),
        }
        print(json.dumps(payload, indent=2))
        return 1


def _cmd_generate_cluster_report(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import ClusterReportRepository
    from rge.modules.cluster_reporter import generate_cluster_report

    db_path = Path(args.db) if args.db else None
    conn = ensure_database(db_path)
    try:
        output_dir = Path(args.output_dir) if args.output_dir else None
        result = generate_cluster_report(
            conn,
            domain=args.domain,
            output_dir=output_dir,
            pad_golden=not args.no_pad,
        )
        reports = ClusterReportRepository(conn).count()
        payload = {
            "status": result["status"],
            "command": "generate-cluster-report",
            "domain": args.domain,
            "cluster_report_id": result.get("cluster_report_id"),
            "cluster_report_count": reports,
            "readiness": result.get("readiness"),
            "padding": result.get("padding"),
            "output_path": result.get("output_path"),
            "report": result.get("report"),
        }
        print(json.dumps(payload, indent=2))
        return 0
    except ValueError as exc:
        payload = {
            "status": "error",
            "command": "generate-cluster-report",
            "detail": str(exc),
        }
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_generate_theory_candidates(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import TheoryCandidateRepository
    from rge.modules.theory_generator import generate_theory_candidates

    db_path = Path(args.db) if args.db else None
    conn = ensure_database(db_path)
    try:
        output_dir = Path(args.output_dir) if args.output_dir else None
        result = generate_theory_candidates(
            conn,
            domain=args.domain,
            cluster_report_id=args.cluster_report,
            fixture_name=args.fixture,
            output_dir=output_dir,
        )
        payload = {
            "status": result["status"],
            "command": "generate-theory-candidates",
            "domain": args.domain,
            "cluster_report_id": result.get("cluster_report_id"),
            "theory_candidate_count": TheoryCandidateRepository(conn).count(),
            "theory_candidate_ids": result.get("theory_candidate_ids"),
            "rejected_count": result.get("rejected_count", 0),
            "output_path": result.get("output_path"),
            "report": result.get("report"),
            "candidates": result.get("candidates"),
        }
        if result.get("rejected"):
            payload["rejected"] = result["rejected"]
        print(json.dumps(payload, indent=2))
        return 0
    except ValueError as exc:
        payload = {
            "status": "error",
            "command": "generate-theory-candidates",
            "detail": str(exc),
        }
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_generate_followup_questions(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.modules.research_planner import (
        GOLDEN_CONTRACT_ID,
        generate_followup_questions,
    )

    db_path = Path(args.db) if args.db else None
    conn = ensure_database(db_path)
    try:
        contract_id = args.contract or GOLDEN_CONTRACT_ID
        result = generate_followup_questions(
            conn,
            contract_id=contract_id,
            cluster_report_id=args.cluster_report,
            fixture_name=args.fixture,
            include_golden_batch=not args.no_golden_batch,
        )
        payload = {
            "status": result["status"],
            "command": "generate-followup-questions",
            "contract_id": contract_id,
            "candidate_count": result.get("candidate_count", 0),
            "queued_count": result.get("queued_count", 0),
            "parked_count": result.get("parked_count", 0),
            "queued": result.get("queued"),
            "parked": result.get("parked"),
            "evaluations": result.get("evaluations"),
            "followups": result.get("followups"),
        }
        print(json.dumps(payload, indent=2))
        return 0
    except ValueError as exc:
        payload = {
            "status": "error",
            "command": "generate-followup-questions",
            "detail": str(exc),
        }
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_generate_ontology_pressure(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import OntologyProposalRepository
    from rge.modules.ontology_pressure import generate_ontology_pressure_report

    db_path = Path(args.db) if args.db else None
    conn = ensure_database(db_path)
    try:
        output_dir = Path(args.output_dir) if args.output_dir else None
        result = generate_ontology_pressure_report(
            conn,
            domain=args.domain,
            output_dir=output_dir,
            pad_golden=not args.no_pad,
        )
        payload = {
            "status": result["status"],
            "command": "generate-ontology-pressure",
            "domain": args.domain,
            "proposal_id": result.get("proposal_id"),
            "proposal_count": OntologyProposalRepository(conn).count(),
            "readiness": result.get("readiness"),
            "padding": result.get("padding"),
            "output_path": result.get("output_path"),
            "report": result.get("report"),
        }
        print(json.dumps(payload, indent=2))
        return 0
    except ValueError as exc:
        payload = {
            "status": "error",
            "command": "generate-ontology-pressure",
            "detail": str(exc),
        }
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_generate_domain_proposal(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import DomainProposalRepository
    from rge.modules.domain_proposer import generate_domain_proposal

    db_path = Path(args.db) if args.db else None
    conn = ensure_database(db_path)
    try:
        output_dir = Path(args.output_dir) if args.output_dir else None
        result = generate_domain_proposal(
            conn,
            domain=args.domain,
            output_dir=output_dir,
            pad_golden=not args.no_pad,
        )
        payload = {
            "status": result["status"],
            "command": "generate-domain-proposal",
            "domain": args.domain,
            "proposal_id": result.get("proposal_id"),
            "proposal_count": DomainProposalRepository(conn).count(),
            "readiness": result.get("readiness"),
            "padding": result.get("padding"),
            "output_path": result.get("output_path"),
            "report": result.get("report"),
        }
        print(json.dumps(payload, indent=2))
        return 0
    except ValueError as exc:
        payload = {
            "status": "error",
            "command": "generate-domain-proposal",
            "detail": str(exc),
        }
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_generate_run_report(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import RunReportRepository
    from rge.modules.run_evaluator import GOLDEN_RUN_ID, generate_run_report

    db_path = Path(args.db) if args.db else None
    conn = ensure_database(db_path)
    try:
        output_dir = Path(args.output_dir) if args.output_dir else None
        result = generate_run_report(
            conn,
            run_id=args.run_id or GOLDEN_RUN_ID,
            topic=args.topic,
            domain_pack=args.domain,
            contract_id=args.contract,
            output_dir=output_dir,
        )
        payload = {
            "status": result["status"],
            "command": "generate-run-report",
            "run_id": result["run_id"],
            "report_id": result.get("report_id"),
            "report_count": RunReportRepository(conn).count(),
            "output_path": result.get("output_path"),
            "report": result.get("report"),
        }
        print(json.dumps(payload, indent=2))
        return 0
    except ValueError as exc:
        payload = {
            "status": "error",
            "command": "generate-run-report",
            "detail": str(exc),
        }
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_generate_improvement_tickets(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import ImprovementTicketRepository
    from rge.modules.run_evaluator import GOLDEN_RUN_ID
    from rge.modules.ticket_writer import generate_improvement_tickets

    db_path = Path(args.db) if args.db else None
    conn = ensure_database(db_path)
    try:
        output_dir = Path(args.output_dir) if args.output_dir else None
        result = generate_improvement_tickets(
            conn,
            run_id=args.run_id or GOLDEN_RUN_ID,
            output_dir=output_dir,
        )
        payload = {
            "status": result["status"],
            "command": "generate-improvement-tickets",
            "run_id": result["run_id"],
            "ticket_ids": result["ticket_ids"],
            "ticket_count": ImprovementTicketRepository(conn).count_for_run(
                result["run_id"]
            ),
            "output_path": result.get("output_path"),
            "tickets": result.get("tickets"),
        }
        print(json.dumps(payload, indent=2))
        return 0
    except ValueError as exc:
        payload = {
            "status": "error",
            "command": "generate-improvement-tickets",
            "detail": str(exc),
        }
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_promote_improvement_ticket(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.modules.ticket_writer import promote_improvement_ticket

    from_json = Path(args.from_json) if args.from_json else None
    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else _REPO_ROOT / "tickets"
    )
    conn = None
    try:
        if from_json is None:
            db_path = Path(args.db) if args.db else None
            conn = ensure_database(db_path)
        result = promote_improvement_ticket(
            queue_ticket_id=args.queue_ticket_id,
            reviewed=bool(args.confirm),
            output_dir=output_dir,
            from_json=from_json,
            conn=conn,
            run_id=args.run_id,
            failure_reason=args.failure_reason,
            improvement_ticket_id=args.improvement_ticket_id,
        )
        print(json.dumps(result, indent=2))
        return 0
    except ValueError as exc:
        payload = {
            "status": "error",
            "command": "promote-improvement-ticket",
            "detail": str(exc),
        }
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        if conn is not None:
            conn.close()


def _cmd_export_public(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.modules.card_exporter import export_public_cards

    db_path = Path(args.db) if args.db else None
    output_dirs = [Path(args.output_dir)] if args.output_dir else None
    conn = ensure_database(db_path)
    try:
        result = export_public_cards(
            conn,
            limit=args.limit,
            output_dirs=output_dirs,
            publish_public=bool(getattr(args, "publish", False)),
            snapshot_history=not bool(getattr(args, "no_snapshot_history", False)),
        )
        print(json.dumps(result, indent=2))
        return 0
    except ValueError as exc:
        payload = {
            "status": "error",
            "command": "export-public",
            "detail": str(exc),
        }
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_model_health(_args: argparse.Namespace) -> int:
    from rge.config import load_config
    from rge.llm.mode import effective_llm_mode, live_llm_enabled
    from rge.llm.registry import get_model_client

    config = load_config()
    client = get_model_client(config, mode="ollama")
    report = client.health_check()
    payload = {
        "command": "model-health",
        "status": "ok",
        **report,
        "live_llm_enabled": live_llm_enabled(config),
        "effective_llm_mode": effective_llm_mode(config),
    }
    print(json.dumps(payload, indent=2))
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    from rge.modules.verify_runner import run_verification

    result = run_verification(
        root=_REPO_ROOT,
        skip_site=bool(getattr(args, "skip_site", False)),
    )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 1


def _cmd_extract_claims(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import ClaimRepository, claim_record_to_public_dict
    from rge.modules.claim_extractor import extract_claims_for_source

    db_path = Path(args.db) if args.db else None
    conn = ensure_database(db_path)
    try:
        result = extract_claims_for_source(
            conn,
            args.source,
            fixture_name=args.fixture,
        )
        claim_repo = ClaimRepository(conn)
        accepted = claim_repo.list_for_source(args.source, status="accepted")
        rejected = claim_repo.list_for_source(args.source, status="rejected")
        payload = {
            "status": result["status"],
            "command": "extract-claims",
            "source_id": args.source,
            "accepted_count": result["accepted_count"],
            "rejected_count": result["rejected_count"],
            "accepted_claims": [
                claim_record_to_public_dict(claim) for claim in accepted
            ],
            "rejected_claims": [
                claim_record_to_public_dict(claim) for claim in rejected
            ],
        }
        print(json.dumps(payload, indent=2))
        return 0
    except ValueError as exc:
        payload = {"status": "error", "command": "extract-claims", "detail": str(exc)}
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_link_concepts(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import ClaimConceptRepository
    from rge.modules.concept_linker import link_concepts_for_source

    db_path = Path(args.db) if args.db else None
    conn = ensure_database(db_path)
    try:
        result = link_concepts_for_source(
            conn,
            args.source,
            fixture_name=args.fixture,
        )
        links = ClaimConceptRepository(conn).list_for_source(args.source)
        payload = {
            "status": result["status"],
            "command": "link-concepts",
            "source_id": args.source,
            "link_count": result["link_count"],
            "links": links,
            "rejected_link_count": result.get("rejected_link_count", 0),
        }
        print(json.dumps(payload, indent=2))
        return 0
    except ValueError as exc:
        payload = {"status": "error", "command": "link-concepts", "detail": str(exc)}
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_build_relationships(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import (
        RelationshipEvidenceRepository,
        RelationshipRepository,
    )
    from rge.modules.relationship_builder import build_relationships_for_source

    db_path = Path(args.db) if args.db else None
    conn = ensure_database(db_path)
    try:
        result = build_relationships_for_source(
            conn,
            args.source,
            fixture_name=args.fixture,
        )
        relationships = RelationshipRepository(conn).list_for_source(args.source)
        evidence = RelationshipEvidenceRepository(conn).list_for_source(args.source)
        payload = {
            "status": result["status"],
            "command": "build-relationships",
            "source_id": args.source,
            "relationship_count": result.get(
                "relationship_count", len(relationships)
            ),
            "relationships": relationships,
            "evidence_count": len(evidence),
            "evidence": evidence,
            "rejected_relationship_count": result.get(
                "rejected_relationship_count", 0
            ),
        }
        if result.get("rejected_relationships"):
            payload["rejected_relationships"] = result["rejected_relationships"]
        print(json.dumps(payload, indent=2))
        return 0
    except ValueError as exc:
        payload = {
            "status": "error",
            "command": "build-relationships",
            "detail": str(exc),
        }
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_detect_contradictions(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import RelationshipEvidenceRepository, RelationshipRepository
    from rge.modules.contradiction_detector import detect_contradictions_for_source

    db_path = Path(args.db) if args.db else None
    conn = ensure_database(db_path)
    try:
        result = detect_contradictions_for_source(
            conn,
            args.source,
            fixture_name=args.fixture,
        )
        relationships = RelationshipRepository(conn).list_active()
        qualifications = [
            row
            for row in RelationshipEvidenceRepository(conn).list_for_source(args.source)
            if row["stance"] == "qualifies"
        ]
        payload = {
            "status": result["status"],
            "command": "detect-contradictions",
            "source_id": args.source,
            "qualification_count": result.get("qualification_count", 0),
            "qualifications": qualifications,
            "active_relationships": relationships,
        }
        if result.get("rejected"):
            payload["rejected"] = result["rejected"]
        print(json.dumps(payload, indent=2))
        return 0
    except ValueError as exc:
        payload = {
            "status": "error",
            "command": "detect-contradictions",
            "detail": str(exc),
        }
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_validate_contract(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import ResearchQueueRepository
    from rge.modules.research_planner import (
        GOLDEN_CONTRACT_ID,
        ensure_golden_contract,
        validate_followup_for_contract,
    )

    db_path = Path(args.db) if args.db else None
    conn = ensure_database(db_path)
    try:
        contract_id = args.contract or GOLDEN_CONTRACT_ID
        ensure_golden_contract(conn)
        result = validate_followup_for_contract(
            conn,
            contract_id,
            args.follow_up,
        )
        followups = ResearchQueueRepository(conn).list_followups_for_contract(
            contract_id
        )
        payload = {
            "status": result["status"],
            "command": "validate-contract",
            "contract_id": contract_id,
            "follow_up": args.follow_up,
            "evaluation": result.get("evaluation"),
            "queue_item": result.get("queue_item"),
            "followups": followups,
        }
        print(json.dumps(payload, indent=2))
        return 0
    except ValueError as exc:
        payload = {
            "status": "error",
            "command": "validate-contract",
            "detail": str(exc),
        }
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_queue_sources(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import CandidateSourceRepository, ResearchQueueRepository
    from rge.modules.research_queue import (
        DEFAULT_RESEARCH_QUESTION_ID,
        queue_sources_from_fixture,
    )

    db_path = Path(args.db) if args.db else None
    conn = ensure_database(db_path)
    try:
        fixture_path = Path(args.fixture) if args.fixture else None
        if fixture_path is not None and not fixture_path.is_absolute():
            fixture_path = Path(__file__).resolve().parents[2] / fixture_path
        question_id = args.question or DEFAULT_RESEARCH_QUESTION_ID
        result = queue_sources_from_fixture(
            conn,
            fixture_path=fixture_path,
            research_question_id=question_id,
        )
        queue_items = ResearchQueueRepository(conn).list_for_question(question_id)
        candidates = CandidateSourceRepository(conn).list_for_question(question_id)
        payload = {
            "status": result["status"],
            "command": "queue-sources",
            "research_question_id": question_id,
            "queue_count": result.get("queue_count", len(queue_items)),
            "queue_items": queue_items,
            "candidate_sources": candidates,
        }
        if result.get("ranked_candidates"):
            payload["ranked_candidates"] = result["ranked_candidates"]
        print(json.dumps(payload, indent=2))
        return 0
    except (ValueError, FileNotFoundError) as exc:
        payload = {
            "status": "error",
            "command": "queue-sources",
            "detail": str(exc),
        }
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_reconcile_scores(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import RelationshipRepository, ScoreEventRepository
    from rge.modules.score_reconciler import reconcile_scores_for_source

    db_path = Path(args.db) if args.db else None
    conn = ensure_database(db_path)
    try:
        result = reconcile_scores_for_source(conn, args.source)
        relationships = RelationshipRepository(conn).list_active()
        score_events = ScoreEventRepository(conn).list_for_source(args.source)
        payload = {
            "status": result["status"],
            "command": "reconcile-scores",
            "source_id": args.source,
            "score_events_created": result.get("score_events_created", 0),
            "relationships_updated": result.get("relationships_updated", 0),
            "score_events": score_events,
            "active_relationships": relationships,
        }
        if result.get("skipped"):
            payload["skipped"] = result["skipped"]
        print(json.dumps(payload, indent=2))
        return 0
    except ValueError as exc:
        payload = {
            "status": "error",
            "command": "reconcile-scores",
            "detail": str(exc),
        }
        print(json.dumps(payload, indent=2))
        return 1
    finally:
        conn.close()


def _cmd_ingest(args: argparse.Namespace) -> int:
    from rge.db.connection import ensure_database
    from rge.db.repositories import (
        ChunkRepository,
        SourceRepository,
        ingest_local_source,
        source_record_to_public_dict,
    )
    from rge.modules.fetcher import FetchError, fetch_local_text_file

    source_path = Path(args.source_path)
    db_path = Path(args.db) if args.db else None

    try:
        fetched = fetch_local_text_file(source_path)
    except FetchError as exc:
        payload = {"status": "error", "command": "ingest", "detail": str(exc)}
        print(json.dumps(payload, indent=2))
        return 1

    conn = ensure_database(db_path)
    try:
        result = ingest_local_source(
            conn,
            local_path=fetched["local_path"],
            domain=args.domain,
            raw_text=fetched["raw_text"],
            title=fetched["title"],
            source_type=fetched["source_type"],
        )
        source = SourceRepository(conn).get_by_id(result["source_id"])
        chunks = ChunkRepository(conn).list_for_source(result["source_id"])
        payload = {
            "status": result["status"],
            "command": "ingest",
            "source": source_record_to_public_dict(source) if source else None,
            "chunk_count": len(chunks),
            "chunk_ids": [chunk.id for chunk in chunks],
            "raw_text_checksum": result["raw_text_checksum"],
        }
        print(json.dumps(payload, indent=2))
        return 0
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="research",
        description=(
            "Research Graph Engine CLI. Local-first research infrastructure: "
            "sources -> scoped claims -> concept graph -> evidence graph -> "
            "reports/cards -> improvement tickets."
        ),
    )
    parser.add_argument("--version", action="version", version=f"research {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run",
        help="Run a research workflow for a topic.",
        description=(
            "Run a fixture-mode research workflow from contract through public "
            "export and improvement tickets. Live discovery is not implemented."
        ),
    )
    run_parser.add_argument("--topic", help="Root research topic.")
    run_parser.add_argument("--domain", help="Domain pack ID (e.g. creativity).")
    run_parser.add_argument(
        "--fixture-mode",
        action="store_true",
        help="Use deterministic fixture sources instead of live discovery.",
    )
    run_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    run_parser.add_argument(
        "--run-id",
        help=f"Research run ID (defaults to {FIXTURE_RUN_ID}).",
    )
    run_parser.add_argument(
        "--output-dir",
        help="Optional report output directory (defaults to data/reports/).",
    )
    run_parser.add_argument(
        "--ticket-dir",
        help="Optional improvement ticket output directory (defaults to data/tickets/).",
    )
    run_parser.add_argument(
        "--export-dir",
        help="Optional single export directory (for tests; skips default export paths).",
    )
    run_parser.set_defaults(func=_cmd_run)

    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Ingest a local text source into SQLite.",
        description="Ingest a local plain-text source and persist source + chunk records.",
    )
    ingest_parser.add_argument(
        "source_path",
        help="Path to a local plain-text source file.",
    )
    ingest_parser.add_argument(
        "--domain",
        required=True,
        help="Primary domain pack ID (e.g. creativity).",
    )
    ingest_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    ingest_parser.set_defaults(func=_cmd_ingest)

    extract_parser = subparsers.add_parser(
        "extract-claims",
        help="Extract scoped claims from an ingested source (mock LLM).",
        description=(
            "Extract candidate claims via the mock model client, validate them "
            "deterministically, and persist accepted/rejected claim records."
        ),
    )
    extract_parser.add_argument(
        "--source",
        required=True,
        help="Stable source ID to extract claims from.",
    )
    extract_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    extract_parser.add_argument(
        "--fixture",
        help="Optional mock LLM fixture filename for deterministic extraction tests.",
    )
    extract_parser.set_defaults(func=_cmd_extract_claims)

    link_parser = subparsers.add_parser(
        "link-concepts",
        help="Link accepted claims to domain concepts (mock LLM).",
        description=(
            "Propose concept links via the mock model client, validate them "
            "deterministically, and persist claim_concepts rows."
        ),
    )
    link_parser.add_argument(
        "--source",
        required=True,
        help="Stable source ID whose accepted claims should be linked.",
    )
    link_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    link_parser.add_argument(
        "--fixture",
        help="Optional mock LLM fixture filename for deterministic linking tests.",
    )
    link_parser.set_defaults(func=_cmd_link_concepts)

    build_parser = subparsers.add_parser(
        "build-relationships",
        help="Build evidence relationships from linked claims (mock LLM).",
        description=(
            "Propose concept relationships via the mock model client, validate them "
            "deterministically, and persist relationships plus relationship_evidence rows."
        ),
    )
    build_parser.add_argument(
        "--source",
        required=True,
        help="Stable source ID whose accepted claims should drive relationships.",
    )
    build_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    build_parser.add_argument(
        "--fixture",
        help="Optional mock LLM fixture filename for deterministic relationship tests.",
    )
    build_parser.set_defaults(func=_cmd_build_relationships)

    reconcile_parser = subparsers.add_parser(
        "reconcile-scores",
        help="Reconcile relationship scores from new supporting evidence.",
        description=(
            "Apply deterministic score updates when new accepted claims support "
            "existing relationships, writing append-only score_events history."
        ),
    )
    reconcile_parser.add_argument(
        "--source",
        required=True,
        help="Stable source ID whose accepted claims may trigger score updates.",
    )
    reconcile_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    reconcile_parser.set_defaults(func=_cmd_reconcile_scores)

    detect_parser = subparsers.add_parser(
        "detect-contradictions",
        help="Detect contradictions and preserve qualification links (mock LLM).",
        description=(
            "Propose contradiction/qualification links via the mock model client, "
            "validate them deterministically, and persist qualifies evidence without "
            "deleting or flattening opposing claims."
        ),
    )
    detect_parser.add_argument(
        "--source",
        required=True,
        help="Stable source ID whose accepted claims should trigger contradiction detection.",
    )
    detect_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    detect_parser.add_argument(
        "--fixture",
        help="Optional mock LLM fixture filename for deterministic contradiction tests.",
    )
    detect_parser.set_defaults(func=_cmd_detect_contradictions)

    queue_parser = subparsers.add_parser(
        "queue-sources",
        help="Rank and queue fixture candidate sources (deterministic).",
        description=(
            "Load fixture candidate sources, rank them with a deterministic "
            "queue-priority formula, and persist candidate_sources plus "
            "research_queue rows."
        ),
    )
    queue_parser.add_argument(
        "--domain",
        default="creativity",
        help="Domain pack ID used for queue context (default: creativity).",
    )
    queue_parser.add_argument(
        "--question",
        help="Research question ID for queue grouping.",
    )
    queue_parser.add_argument(
        "--fixture",
        help=(
            "Optional candidate-source fixture path "
            "(defaults to fixtures/candidate_sources/source_ranking_fixture.json)."
        ),
    )
    queue_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    queue_parser.set_defaults(func=_cmd_queue_sources)

    validate_parser = subparsers.add_parser(
        "validate-contract",
        help="Validate follow-up questions against a research contract.",
        description=(
            "Evaluate a follow-up question against an active research contract, "
            "persisting parked or queued follow-up items with machine-readable reasons."
        ),
    )
    validate_parser.add_argument(
        "--follow-up",
        required=True,
        help="Follow-up question text to evaluate against the contract.",
    )
    validate_parser.add_argument(
        "--contract",
        help="Research contract ID (defaults to Golden Test 10 contract).",
    )
    validate_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    validate_parser.set_defaults(func=_cmd_validate_contract)

    cluster_report_parser = subparsers.add_parser(
        "generate-cluster-report",
        help="Generate cluster report when claim/source thresholds are met.",
        description=(
            "Evaluate cluster maturity thresholds, build a balanced evidence "
            "packet, persist a cluster report, and write cluster_report_latest.json."
        ),
    )
    cluster_report_parser.add_argument(
        "--domain",
        default="creativity",
        help="Domain pack ID for cluster evaluation (default: creativity).",
    )
    cluster_report_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    cluster_report_parser.add_argument(
        "--output-dir",
        help="Optional output directory for cluster_report_latest.json (for tests).",
    )
    cluster_report_parser.add_argument(
        "--no-pad",
        action="store_true",
        help="Skip deterministic golden threshold padding (for negative tests).",
    )
    cluster_report_parser.set_defaults(func=_cmd_generate_cluster_report)

    theory_parser = subparsers.add_parser(
        "generate-theory-candidates",
        help="Generate candidate theories from cluster evidence packets.",
        description=(
            "Load a cluster report evidence packet, propose candidate theories "
            "via mock fixture, validate deterministically, and persist candidates."
        ),
    )
    theory_parser.add_argument(
        "--domain",
        default="creativity",
        help="Domain pack ID for cluster lookup (default: creativity).",
    )
    theory_parser.add_argument(
        "--cluster-report",
        help="Optional cluster report ID (defaults to latest golden cluster report).",
    )
    theory_parser.add_argument(
        "--fixture",
        default="theory_generation_creativity_diversity.json",
        help="Mock theory fixture filename.",
    )
    theory_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    theory_parser.add_argument(
        "--output-dir",
        help="Optional output directory for theory_candidate_latest.json (for tests).",
    )
    theory_parser.set_defaults(func=_cmd_generate_theory_candidates)

    followup_parser = subparsers.add_parser(
        "generate-followup-questions",
        help="Generate contract-gated follow-up questions from cluster context.",
        description=(
            "Propose follow-up questions from cluster/theory context, validate "
            "each against the research contract, and queue or park with reasons."
        ),
    )
    followup_parser.add_argument(
        "--contract",
        help="Research contract ID (defaults to Golden Test 10 contract).",
    )
    followup_parser.add_argument(
        "--cluster-report",
        help="Optional cluster report ID (defaults to latest golden cluster report).",
    )
    followup_parser.add_argument(
        "--fixture",
        default="followup_question_generation_golden_test_16.json",
        help="Mock follow-up question fixture filename.",
    )
    followup_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    followup_parser.add_argument(
        "--no-golden-batch",
        action="store_true",
        help="Skip built-in Golden Test 16 question batch.",
    )
    followup_parser.set_defaults(func=_cmd_generate_followup_questions)

    ontology_parser = subparsers.add_parser(
        "generate-ontology-pressure",
        help="Generate ontology pressure report when vocabulary thresholds are met.",
        description=(
            "Detect recurring uncaptured vocabulary, build a draft ontology "
            "proposal, persist it, and write ontology_pressure_latest.json."
        ),
    )
    ontology_parser.add_argument(
        "--domain",
        default="creativity",
        help="Domain pack ID for ontology evaluation (default: creativity).",
    )
    ontology_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    ontology_parser.add_argument(
        "--output-dir",
        help="Optional output directory for ontology_pressure_latest.json (for tests).",
    )
    ontology_parser.add_argument(
        "--no-pad",
        action="store_true",
        help="Skip deterministic golden threshold padding (for negative tests).",
    )
    ontology_parser.set_defaults(func=_cmd_generate_ontology_pressure)

    domain_proposal_parser = subparsers.add_parser(
        "generate-domain-proposal",
        help="Generate draft domain proposal when strict thresholds are met.",
        description=(
            "Evaluate domain proposal thresholds, build a draft subdomain "
            "proposal, persist it, and write domain_proposal_latest.json."
        ),
    )
    domain_proposal_parser.add_argument(
        "--domain",
        default="creativity",
        help="Parent domain pack ID for evaluation (default: creativity).",
    )
    domain_proposal_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    domain_proposal_parser.add_argument(
        "--output-dir",
        help="Optional output directory for domain_proposal_latest.json (for tests).",
    )
    domain_proposal_parser.add_argument(
        "--no-pad",
        action="store_true",
        help="Skip deterministic golden threshold padding (for negative tests).",
    )
    domain_proposal_parser.set_defaults(func=_cmd_generate_domain_proposal)

    run_report_parser = subparsers.add_parser(
        "generate-run-report",
        help="Generate machine-readable research run report from DB metrics.",
        description=(
            "Aggregate accepted/rejected counters, failure modes, and spine "
            "metrics into a run report, persist it, and write run_report_latest.json."
        ),
    )
    run_report_parser.add_argument(
        "--run-id",
        help="Research run ID (defaults to golden Test 19 run ID).",
    )
    run_report_parser.add_argument(
        "--topic",
        default="Does AI improve creative output while reducing diversity?",
        help="Research topic stored on the run report.",
    )
    run_report_parser.add_argument(
        "--domain",
        default="creativity",
        help="Domain pack ID for the run report (default: creativity).",
    )
    run_report_parser.add_argument(
        "--contract",
        help="Research contract ID (defaults to golden Test 10 contract).",
    )
    run_report_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    run_report_parser.add_argument(
        "--output-dir",
        help="Optional output directory for run_report_latest.json (for tests).",
    )
    run_report_parser.set_defaults(func=_cmd_generate_run_report)

    improvement_parser = subparsers.add_parser(
        "generate-improvement-tickets",
        help="Generate improvement tickets from run report failure modes.",
        description=(
            "Read a persisted run report, map top_failure_modes to actionable "
            "draft improvement tickets, persist them, and write "
            "improvement_ticket_latest.json."
        ),
    )
    improvement_parser.add_argument(
        "--run-id",
        help="Research run ID (defaults to golden Test 19 run ID).",
    )
    improvement_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    improvement_parser.add_argument(
        "--output-dir",
        help="Optional output directory for improvement_ticket_latest.json (for tests).",
    )
    improvement_parser.set_defaults(func=_cmd_generate_improvement_tickets)

    promote_parser = subparsers.add_parser(
        "promote-improvement-ticket",
        help="Promote a reviewed improvement ticket to tickets/<id>.json.",
        description=(
            "Convert a draft improvement ticket into a builder queue ticket JSON "
            "file after explicit human/audit review. Does not edit TICKET_QUEUE.md."
        ),
    )
    promote_parser.add_argument(
        "--queue-ticket-id",
        required=True,
        help="Target queue ticket id (e.g. ticket-041).",
    )
    promote_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required review gate; promotion fails without this flag.",
    )
    promote_parser.add_argument(
        "--from-json",
        help="Path to improvement_ticket_latest.json or a single ticket object.",
    )
    promote_parser.add_argument(
        "--run-id",
        help="Run id when loading an improvement ticket from the database.",
    )
    promote_parser.add_argument(
        "--failure-reason",
        help="Failure reason key when loading by run id (e.g. overgeneralized_scope).",
    )
    promote_parser.add_argument(
        "--improvement-ticket-id",
        help="Improvement ticket row id (imp_*) when loading from the database.",
    )
    promote_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    promote_parser.add_argument(
        "--output-dir",
        help="Directory for the promoted queue ticket JSON (defaults to tickets/).",
    )
    promote_parser.set_defaults(func=_cmd_promote_improvement_ticket)

    export_parser = subparsers.add_parser(
        "export-public",
        help="Export public-safe card JSON with safety filtering.",
        description=(
            "Export public-safe card JSON after deterministic safety validation. "
            "Mock mode writes scratch exports to data/exports/ (with snapshot "
            "history by default). Use --publish for live-mode public-site updates."
        ),
    )
    export_parser.add_argument(
        "--limit", type=int, default=100, help="Maximum records to export."
    )
    export_parser.add_argument(
        "--db",
        help="Optional SQLite database path (defaults to data/db/creative_research.sqlite).",
    )
    export_parser.add_argument(
        "--output-dir",
        help="Optional single output directory (for tests; skips default export paths).",
    )
    export_parser.add_argument(
        "--publish",
        action="store_true",
        help=(
            "Allow writing to apps/public-site/public/data/. Required for live-mode "
            "exports when RGE_ALLOW_LIVE_LLM=1 and RGE_LLM_MODE=ollama."
        ),
    )
    export_parser.add_argument(
        "--no-snapshot-history",
        action="store_true",
        help=(
            "Skip writing data/exports/snapshot_manifest.json and history copies "
            "under data/exports/history/."
        ),
    )
    export_parser.set_defaults(func=_cmd_export_public)

    model_health_parser = subparsers.add_parser(
        "model-health",
        help="Report local Ollama reachability without raising.",
        description=(
            "Probe the configured Ollama endpoint and model availability. "
            "Always exits 0 with a JSON report; does not run structured tasks."
        ),
    )
    model_health_parser.set_defaults(func=_cmd_model_health)

    verify_parser = subparsers.add_parser(
        "verify",
        help="Run deterministic mock-only verification checks.",
        description=(
            "Run mock-only golden tests, pytest, safety audit, and public-site "
            "build. Does not require Ollama or a clean git tree."
        ),
    )
    verify_parser.add_argument(
        "--skip-site",
        action="store_true",
        help="Skip npm public-site build (Python checks only).",
    )
    verify_parser.set_defaults(func=_cmd_verify)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
