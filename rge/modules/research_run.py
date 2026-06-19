"""Single-command MVP research demo loop (MVP-P7)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rge.modules.abstract_evidence import generate_abstract_evidence_cards
from rge.modules.failure_recommender import recommend_from_abstract_evidence_run
from rge.modules.field_map import (
    build_field_clusters,
    rank_field_map_records,
    synthesize_field_report,
)
from rge.modules.selective_fulltext import acquire_selective_fulltext
from rge.modules.source_resolver import resolve_work_candidates

RESEARCH_RUN_COMMAND = "research-run"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "reports" / "research_runs"


def run_research_demo(
    *,
    topic: str,
    domain_pack: str = "creativity",
    max_candidates: int = 20,
    top_sources: int = 5,
    full_text_top_n: int = 3,
    fixture_mode: bool = False,
    mode: str = "abstract-first",
    enrich_unpaywall: bool = False,
    db_conn: Any | None = None,
    persist_claims: bool = False,
    staging_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the MVP research loop: resolve → rank → abstract evidence → selective full text → report."""
    resolved = resolve_work_candidates(
        query=topic,
        domain_pack=domain_pack,
        limit=max_candidates,
        fixture_mode=fixture_mode,
        enrich_unpaywall=enrich_unpaywall and not fixture_mode,
    )
    records = list(resolved.get("records") or [])
    clusters = build_field_clusters(records, query=topic)
    ranked = rank_field_map_records(records, query=topic, top_n=top_sources)
    abstract_evidence = generate_abstract_evidence_cards(ranked, domain_pack=domain_pack)

    fulltext_result = None
    if mode in {"abstract-first", "full-text-augmented"}:
        fulltext_result = acquire_selective_fulltext(
            ranked,
            abstract_evidence=abstract_evidence,
            top_n=full_text_top_n,
            fixture_mode=fixture_mode,
            force_top_n=mode == "full-text-augmented",
        )

    statuses = [str(record.get("source_status") or "") for record in records]
    improvement = recommend_from_abstract_evidence_run(
        abstract_evidence,
        source_statuses=statuses,
    )
    if fulltext_result:
        parse_failed = int(fulltext_result.get("status_counts", {}).get("full_text_parse_failed", 0))
        if parse_failed > 0 and improvement.get("recommended_packet", "").endswith("P1"):
            from rge.modules.failure_recommender import PACKET_PDF_PARSER

            improvement = {
                **improvement,
                "recommended_packet": PACKET_PDF_PARSER,
                "rationale": (
                    "Selective full-text acquisition hit parse failures; prioritize PDF/TEI "
                    "parser milestone before ranking or resolver expansion."
                ),
                "dominant_signal": "parse_failed",
            }

    field_report = synthesize_field_report(
        query=topic,
        domain_pack=domain_pack,
        records=records,
        ranked_sources=ranked,
        clusters=clusters,
        abstract_evidence=abstract_evidence,
        improvement_recommendation=improvement,
    )
    if fulltext_result:
        field_report["selective_fulltext"] = {
            "status_counts": fulltext_result.get("status_counts"),
            "acquisition_count": fulltext_result.get("acquisition_count"),
        }

    db_spine = None
    if db_conn is not None:
        from rge.modules.research_spine import wire_research_demo_to_db

        db_spine = wire_research_demo_to_db(
            db_conn,
            {
                "selective_fulltext": fulltext_result,
                "source_status_table": [
                    {
                        "source_id": record.get("source_id"),
                        "title": record.get("title"),
                        "source_status": record.get("source_status"),
                    }
                    for record in records
                ],
                "ranked_sources": field_report.get("top_sources"),
            },
            domain=domain_pack,
            persist_claims=persist_claims,
            staging_dir=staging_dir,
        )

    return {
        "command": RESEARCH_RUN_COMMAND,
        "status": "ok",
        "mode": mode,
        "topic": topic,
        "domain_pack": domain_pack,
        "fixture_mode": fixture_mode,
        "resolver_summary": {
            "resolved_count": resolved.get("resolved_count", 0),
            "backend_counts": resolved.get("backend_counts", {}),
        },
        "source_status_table": [
            {
                "source_id": record.get("source_id"),
                "title": record.get("title"),
                "source_status": record.get("source_status"),
            }
            for record in records
        ],
        "ranked_sources": field_report.get("top_sources"),
        "abstract_evidence": abstract_evidence,
        "selective_fulltext": fulltext_result,
        "field_map_report": field_report,
        "improvement_recommendation": improvement,
        "db_spine": db_spine,
    }


def run_research_run_command(
    *,
    topic: str | None,
    domain_pack: str,
    max_candidates: int,
    top_sources: int,
    full_text_top_n: int,
    fixture_mode: bool,
    mode: str,
    output_dir: Path | None = None,
    db_path: Path | None = None,
    persist_claims: bool = False,
    staging_dir: Path | None = None,
) -> tuple[dict[str, Any], int]:
    if not topic and not fixture_mode:
        return {
            "command": RESEARCH_RUN_COMMAND,
            "status": "error",
            "reason": "missing_query",
            "detail": "--topic is required unless --fixture-mode is set.",
        }, 1

    effective_topic = topic or "AI assisted creativity and idea diversity"
    db_conn = None
    if db_path is not None:
        from rge.db.connection import ensure_database

        db_conn = ensure_database(db_path)

    try:
        payload = run_research_demo(
            topic=effective_topic,
            domain_pack=domain_pack,
            max_candidates=max_candidates,
            top_sources=top_sources,
            full_text_top_n=full_text_top_n,
            fixture_mode=fixture_mode,
            mode=mode,
            db_conn=db_conn,
            persist_claims=persist_claims,
            staging_dir=staging_dir,
        )
    finally:
        if db_conn is not None:
            db_conn.close()
    target_dir = output_dir or DEFAULT_OUTPUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / "latest.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    payload["output_path"] = str(out_path.resolve())
    return payload, 0
