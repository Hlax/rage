"""Local-safe arbitrary-source purpose gate + Atlas health proof.

This packet deliberately stays mock/local-safe by default. It resolves fixture
records for an arbitrary question, persists source health, skips unextractable
records before extraction, purpose-gates abstract evidence, and emits an
Atlas-safe run artifact.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from rge.db.repositories import (
    ChunkRecord,
    ClaimRepository,
    sha256_hex,
    utc_now_iso,
)
from rge.modules.abstract_evidence import (
    abstract_chunk_id,
    extract_abstract_evidence_card,
)
from rge.modules.acquisition_quality import (
    acquisition_metadata_from_payload,
    acquisition_quality_summary,
    persist_source_acquisition_status,
)
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.failure_recommender import recommend_from_run_report
from rge.modules.purpose_gating import evaluate_text_purpose_fit
from rge.modules.research_purpose import classify_research_purpose
from rge.modules.run_evaluator import generate_run_report
from rge.modules.source_resolver import resolve_work_candidates
from rge.modules.source_resolver.evidence import explain_source_evidence
from rge.modules.source_resolver.status import (
    ABSTRACT_AVAILABLE,
    CLEAN_TEXT_READY,
    EXTRACTABLE,
    OA_PDF_AVAILABLE,
    OA_TEI_AVAILABLE,
)

LOCAL_SAFE_ARBITRARY_QUESTION = "How does AI affect human creativity?"
LOCAL_SAFE_RUN_ID = "run_local_safe_ai_human_creativity"
LIVE_NETWORK_RUN_ID = "run_live_network_ai_human_creativity"
LOCAL_SAFE_ATLAS_ARTIFACT_SCHEMA_VERSION = "atlas_source_health_run_v0.1.0"
LIVE_NETWORK_SOURCE_LIMIT = 5
LIVE_NETWORK_BACKENDS = ("openalex", "arxiv")
LIVE_NETWORK_RESOLVER_QUERY = "human AI creativity"
LIVE_SOURCE_HEALTH_ARTIFACT_NAME = "atlas_source_health_run_latest.json"

_EXTRACTABLE_STATUSES = frozenset(
    {
        ABSTRACT_AVAILABLE,
        OA_PDF_AVAILABLE,
        OA_TEI_AVAILABLE,
        CLEAN_TEXT_READY,
        EXTRACTABLE,
    }
)


def _source_id(record: dict[str, Any]) -> str:
    return str(record.get("source_id") or record.get("provider_id") or "src_unknown")


def _source_title(record: dict[str, Any]) -> str:
    return str(record.get("title") or _source_id(record) or "Untitled source")


def _source_type(record: dict[str, Any]) -> str:
    return str(record.get("source_type") or record.get("source_kind") or "resolver_record")


def _purpose_fit_for_record(
    record: dict[str, Any],
    *,
    question: str,
    domain_pack: str,
) -> dict[str, Any]:
    text = " ".join(
        str(record.get(key) or "")
        for key in ("title", "abstract_text", "source_status")
    )
    return evaluate_text_purpose_fit(
        text,
        question=question,
        domain_pack=domain_pack,
        evidence_ref=_source_id(record),
    )


def _health_metadata_for_record(
    record: dict[str, Any],
    *,
    question: str,
    domain_pack: str,
) -> dict[str, Any]:
    evidence = explain_source_evidence(record)
    purpose_fit = _purpose_fit_for_record(
        record,
        question=question,
        domain_pack=domain_pack,
    )
    status = str(record.get("source_status") or "")
    extractable = bool(
        status in _EXTRACTABLE_STATUSES
        and evidence.get("can_extract_abstract_claims")
        and str(record.get("abstract_text") or "").strip()
    )
    failure_reason = ""
    if not extractable:
        failure_reason = str(evidence.get("extraction_recommendation") or "not_extractable")
    if purpose_fit["decision"] == "rejected":
        failure_reason = "purpose_mismatch"

    metadata = acquisition_metadata_from_payload(
        {
            **record,
            "source_status": status,
            "acquisition_status": status,
            "parser_backend": "abstract_record"
            if extractable
            else str(record.get("parser_backend") or "none"),
            "extractable": extractable,
            "quality_gate_status": "extractable"
            if extractable and purpose_fit["decision"] != "rejected"
            else "blocked",
            "failure_reason": failure_reason,
            "resolver_source": str(record.get("source_kind") or "manual_fixture"),
        },
        source_type=_source_type(record),
        source_status=status,
        acquisition_status=status,
        parser_backend="abstract_record" if extractable else "none",
        failure_reason=failure_reason,
        resolver_source=str(record.get("source_kind") or "manual_fixture"),
    )
    metadata.update(
        {
            "purpose_fit_status": str(purpose_fit["purpose_match_status"]),
            "purpose_fit_reason": str(
                purpose_fit.get("why_purpose_match")
                or purpose_fit.get("why_evidence_downgraded_or_rejected")
                or ""
            ),
            "purpose_gate_decision": str(purpose_fit["decision"]),
            "purpose_required_families": list(
                purpose_fit.get("required_concept_families") or []
            ),
        }
    )
    return metadata


def persist_resolved_source_health(
    conn: sqlite3.Connection,
    records: list[dict[str, Any]],
    *,
    question: str = LOCAL_SAFE_ARBITRARY_QUESTION,
    domain_pack: str = "creativity",
) -> list[dict[str, Any]]:
    """Persist source-health rows for resolved records, including skipped sources."""
    persisted: list[dict[str, Any]] = []
    for record in records:
        source_id = _source_id(record)
        metadata = _health_metadata_for_record(
            record,
            question=question,
            domain_pack=domain_pack,
        )
        extractable = bool(metadata.get("extractable"))
        persisted.append(
            persist_source_acquisition_status(
                conn,
                source_id=source_id,
                title=_source_title(record),
                domain=domain_pack,
                source_type=_source_type(record),
                metadata=metadata,
                raw_text_checksum=str(record.get("raw_text_checksum") or ""),
                local_path="",
                status="parsed" if extractable else "failed",
                authors=list(record.get("authors") or []),
            )
        )
    return persisted


def _ensure_abstract_chunk(
    conn: sqlite3.Connection,
    record: dict[str, Any],
    *,
    domain_pack: str,
) -> ChunkRecord | None:
    abstract = str(record.get("abstract_text") or "").strip()
    if not abstract:
        return None
    source_id = _source_id(record)
    chunk_id = abstract_chunk_id(source_id)
    now = utc_now_iso()
    checksum = sha256_hex(f"{source_id}:{abstract}")
    conn.execute(
        """
        INSERT OR IGNORE INTO chunks (
            id, source_id, chunk_index, chunk_text, page, section,
            token_count, embedding_id, embedding_model, text_checksum, created_at
        ) VALUES (?, ?, 0, ?, NULL, 'abstract', ?, NULL, NULL, ?, ?)
        """,
        (
            chunk_id,
            source_id,
            abstract,
            len(abstract.split()),
            checksum,
            now,
        ),
    )
    conn.commit()
    return ChunkRecord(
        id=chunk_id,
        source_id=source_id,
        chunk_index=0,
        chunk_text=abstract,
        text_checksum=checksum,
        created_at=now,
        token_count=len(abstract.split()),
    )


def _insert_purpose_mismatch_rejection(
    conn: sqlite3.Connection,
    record: dict[str, Any],
    *,
    domain_pack: str,
    reason: str,
) -> str | None:
    chunk = _ensure_abstract_chunk(conn, record, domain_pack=domain_pack)
    if chunk is None:
        return None
    claim = ClaimRepository(conn).insert_rejected(
        {
            "source_id": _source_id(record),
            "chunk_id": chunk.id,
            "claim_text": f"Purpose-mismatched source skipped before extraction: {_source_title(record)}",
            "quote_span": "",
            "subject": "source",
            "predicate": "blocked_by",
            "object": "purpose_gate",
            "scope": LOCAL_SAFE_ARBITRARY_QUESTION,
            "evidence_type": "blocked",
            "confidence": 0.0,
            "limitations": [reason],
            "domain": domain_pack,
            "domain_metadata": {
                "purpose_fit_status": "mismatch",
                "purpose_gate_decision": "rejected",
                "purpose_gate_reason": reason,
            },
        },
        rejection_reason="purpose_mismatch",
        extractor_provider="purpose_gate",
        extractor_model="deterministic",
        llm_schema_version="0.1.0",
    )
    return claim.id


def persist_abstract_evidence_outcomes(
    conn: sqlite3.Connection,
    records: list[dict[str, Any]],
    *,
    question: str = LOCAL_SAFE_ARBITRARY_QUESTION,
    domain_pack: str = "creativity",
    client: Any | None = None,
) -> dict[str, Any]:
    """Purpose-gate abstract evidence and persist accepted/rejected claim rows."""
    claim_repo = ClaimRepository(conn)
    accepted_ids: list[str] = []
    rejected_ids: list[str] = []
    cards: list[dict[str, Any]] = []
    skipped_before_extraction = 0
    purpose_mismatch_sources = 0

    for record in records:
        source_id = _source_id(record)
        metadata = _health_metadata_for_record(
            record,
            question=question,
            domain_pack=domain_pack,
        )
        if not metadata.get("extractable"):
            skipped_before_extraction += 1
            cards.append(
                {
                    "source_ref": f"source_{len(cards) + 1:03d}",
                    "status": "skipped",
                    "source_status": metadata.get("source_status"),
                    "skip_reason": metadata.get("failure_reason") or "not_extractable",
                    "purpose_fit_status": metadata.get("purpose_fit_status"),
                    "purpose_gate_decision": metadata.get("purpose_gate_decision"),
                }
            )
            continue

        card = extract_abstract_evidence_card(
            record,
            domain_pack=domain_pack,
            question=question,
            client=client,
        )
        cards.append(card)
        if card.get("skip_reason") == "purpose_mismatch":
            purpose_mismatch_sources += 1
            rejection_id = _insert_purpose_mismatch_rejection(
                conn,
                record,
                domain_pack=domain_pack,
                reason=str(card.get("purpose_gate_reason") or "purpose_mismatch"),
            )
            if rejection_id:
                rejected_ids.append(rejection_id)
            continue
        if card.get("status") != "completed":
            skipped_before_extraction += 1
            continue

        _ensure_abstract_chunk(conn, record, domain_pack=domain_pack)
        for claim in card.get("accepted_claims") or []:
            stored = claim_repo.insert_accepted(
                claim,
                extractor_provider="mock",
                extractor_model="abstract_fixture",
                llm_schema_version="0.1.0",
            )
            accepted_ids.append(stored.id)
        for claim in card.get("rejected_claims") or []:
            stored = claim_repo.insert_rejected(
                claim,
                rejection_reason=str(claim.get("rejection_reason") or "invalid_claim"),
                extractor_provider="mock",
                extractor_model="abstract_fixture",
                llm_schema_version="0.1.0",
            )
            rejected_ids.append(stored.id)

    return {
        "status": "completed",
        "accepted_claim_ids": sorted(set(accepted_ids)),
        "rejected_claim_ids": sorted(set(rejected_ids)),
        "accepted_count": len(set(accepted_ids)),
        "rejected_count": len(set(rejected_ids)),
        "skipped_before_extraction": skipped_before_extraction,
        "purpose_mismatch_source_count": purpose_mismatch_sources,
        "cards": cards,
    }


def _source_health_preview(summary: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    allowed_fields = (
        "source_status",
        "acquisition_status",
        "parser_backend",
        "source_type",
        "quality_gate_status",
        "extractable",
        "failure_reason",
        "resolver_source",
        "oa_available",
        "pdf_available",
        "tei_available",
        "is_oa",
        "oa_status",
        "purpose_fit_status",
        "purpose_fit_reason",
        "purpose_gate_decision",
        "db_status",
    )
    for index, row in enumerate(summary.get("source_status_rows") or [], start=1):
        rows.append(
            {
                "source_ref": f"source_{index:03d}",
                **{field: row[field] for field in allowed_fields if field in row},
            }
        )
    return {
        "source_status_counts": summary.get("source_status_counts") or {},
        "acquisition_status_counts": summary.get("acquisition_status_counts") or {},
        "parser_backend_counts": summary.get("parser_backend_counts") or {},
        "source_type_counts": summary.get("source_type_counts") or {},
        "quality_gate_status_counts": summary.get("quality_gate_status_counts") or {},
        "extractable_counts": summary.get("extractable_counts") or {},
        "failure_reason_counts": summary.get("failure_reason_counts") or {},
        "resolver_source_counts": summary.get("resolver_source_counts") or {},
        "availability_counts": summary.get("availability_counts") or {},
        "purpose_fit_status_counts": summary.get("purpose_fit_status_counts") or {},
        "purpose_gate_decision_counts": summary.get("purpose_gate_decision_counts") or {},
        "sources_with_metadata": summary.get("sources_with_metadata") or 0,
        "source_rows": rows,
    }


def build_atlas_safe_run_artifact(
    conn: sqlite3.Connection,
    *,
    question: str = LOCAL_SAFE_ARBITRARY_QUESTION,
    domain_pack: str = "creativity",
    run_report: dict[str, Any] | None = None,
    question_id: str = "local_safe_arbitrary_run",
) -> dict[str, Any]:
    """Build public-safe run artifact for Atlas/operator inspection."""
    summary = acquisition_quality_summary(conn)
    report = run_report or {}
    recommendation = recommend_from_run_report(report) if report else {
        "recommended_packet": "source-health-persistence",
        "rationale": "Run report was not available.",
    }
    graph_metrics = report.get("graph_connection_metrics") or {}
    artifact = {
        "schema_version": LOCAL_SAFE_ATLAS_ARTIFACT_SCHEMA_VERSION,
        "status": "completed",
        "question": question,
        "domain_pack": domain_pack,
        "purpose": classify_research_purpose(
            question,
            domain=domain_pack,
            question_id=question_id,
        ),
        "source_health_summary": _source_health_preview(summary),
        "purpose_fit_summary": {
            "source_counts": summary.get("purpose_fit_status_counts") or {},
            "gate_decision_counts": summary.get("purpose_gate_decision_counts") or {},
            "accepted_evidence_count": int(report.get("claims_accepted") or 0),
            "rejected_evidence_count": int(report.get("claims_rejected") or 0),
        },
        "graph_summary": {
            "claims": int(report.get("claims_extracted") or 0),
            "atoms": (graph_metrics.get("totals") or {}).get("atoms", 0),
            "relationships": int(report.get("relationships_updated") or 0),
            "connection_metrics": graph_metrics,
        },
        "readiness_warnings": _readiness_warnings(
            source_health=_source_health_preview(summary),
            run_report=report,
        ),
        "next_recommended_packet": recommendation.get("recommended_packet"),
        "next_recommended_reason": recommendation.get("rationale"),
    }
    violations = assert_no_private_fields({"atlas_safe_run_artifact": artifact})
    if violations:
        raise ValueError(
            "Atlas-safe run artifact blocked by private-field policy: "
            + "; ".join(violations[:5])
        )
    return artifact


def _readiness_warnings(
    *,
    source_health: dict[str, Any],
    run_report: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if int(source_health.get("sources_with_metadata") or 0) == 0:
        warnings.append("Source health metadata is missing.")
    extractable_counts = source_health.get("extractable_counts") or {}
    if int(extractable_counts.get("true") or 0) == 0:
        warnings.append("No extractable sources reached quote-grounded evidence.")
    failure_counts = source_health.get("failure_reason_counts") or {}
    if failure_counts:
        warnings.append(
            "Acquisition or purpose blockers present: "
            + ", ".join(sorted(str(key) for key in failure_counts))
        )
    graph_totals = (run_report.get("graph_connection_metrics") or {}).get("totals") or {}
    if int(graph_totals.get("relationships") or 0) == 0:
        warnings.append("No relationship graph was produced for this run.")
    return warnings


def assert_live_source_health_smoke_env() -> dict[str, str]:
    """Fail closed unless operator explicitly opts into live source-health smoke."""
    import os

    allow_smoke = os.environ.get("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "0").strip().casefold()
    if allow_smoke not in {"1", "true", "yes"}:
        raise RuntimeError(
            "Live source-health smoke requires RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE=1."
        )
    allow_network = os.environ.get("RGE_ALLOW_SOURCE_NETWORK", "0").strip().casefold()
    if allow_network not in {"1", "true", "yes"}:
        raise RuntimeError(
            "Live source-health smoke requires RGE_ALLOW_SOURCE_NETWORK=1."
        )
    mailto = os.environ.get("OPENALEX_MAILTO", "").strip()
    if not mailto:
        raise RuntimeError("Live source-health smoke requires OPENALEX_MAILTO.")
    return {
        "RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE": allow_smoke,
        "RGE_ALLOW_SOURCE_NETWORK": allow_network,
        "OPENALEX_MAILTO": mailto,
    }


def assert_live_combined_source_health_smoke_env() -> dict[str, str]:
    """Fail closed unless both live source-health and query-expansion smokes are opted in."""
    from rge.modules.source_resolver.query_expansion import (
        assert_live_query_expansion_smoke_env,
    )

    combined = assert_live_source_health_smoke_env()
    combined.update(assert_live_query_expansion_smoke_env())
    return combined


def resolve_live_network_source_records(
    *,
    question: str = LOCAL_SAFE_ARBITRARY_QUESTION,
    resolver_query: str = LIVE_NETWORK_RESOLVER_QUERY,
    domain_pack: str = "creativity",
    limit: int = LIVE_NETWORK_SOURCE_LIMIT,
    backends: tuple[str, ...] = LIVE_NETWORK_BACKENDS,
) -> dict[str, Any]:
    """Resolve a bounded live OpenAlex/arXiv source set (metadata/abstracts only)."""
    assert_live_source_health_smoke_env()
    resolved = resolve_work_candidates(
        query=resolver_query,
        domain_pack=domain_pack,
        limit=limit,
        backends=list(backends),
        fixture_mode=False,
        enrich_unpaywall=False,
    )
    records = list(resolved.get("records") or [])
    if len(records) > limit:
        resolved["records"] = records[:limit]
        resolved["resolved_count"] = limit
    resolved["research_question"] = question
    resolved["resolver_query"] = resolver_query
    return resolved


def _write_atlas_safe_artifact(
    artifact: dict[str, Any],
    *,
    output_dir: Path | None,
) -> str | None:
    if output_dir is None:
        return None
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / LIVE_SOURCE_HEALTH_ARTIFACT_NAME
    path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return str(path)


def _execute_source_health_proof_pipeline(
    conn: sqlite3.Connection,
    *,
    resolved: dict[str, Any],
    question: str,
    domain_pack: str,
    run_id: str,
    output_dir: Path | None = None,
    client: Any | None = None,
    include_graph_proof: bool = True,
    resolver_mode: str,
) -> dict[str, Any]:
    """Shared source-health persistence, abstract evidence, report, and artifact path."""
    records = list(resolved.get("records") or [])
    if not records:
        raise ValueError("Source resolver returned zero records.")

    persist_resolved_source_health(
        conn,
        records,
        question=question,
        domain_pack=domain_pack,
    )
    evidence = persist_abstract_evidence_outcomes(
        conn,
        records,
        question=question,
        domain_pack=domain_pack,
        client=client,
    )

    graph_result: dict[str, Any] = {"status": "skipped", "reason": "no_accepted_claims"}
    accepted_claim_ids = list(evidence.get("accepted_claim_ids") or [])
    if include_graph_proof and accepted_claim_ids:
        from rge.modules.concept_linker import link_concepts_for_source
        from rge.modules.relationship_density_proof import (
            ensure_purpose_gated_relationship_density_proof,
        )

        source_ids = sorted(
            {
                str(row["source_id"])
                for row in conn.execute(
                    """
                    SELECT DISTINCT source_id
                    FROM claims
                    WHERE status = 'accepted'
                    ORDER BY source_id
                    """
                ).fetchall()
            }
        )
        link_results = []
        for source_id in source_ids:
            try:
                link_results.append(link_concepts_for_source(conn, source_id))
            except ValueError as exc:
                link_results.append(
                    {"status": "skipped", "source_ref": "source", "reason": str(exc)}
                )
        density = ensure_purpose_gated_relationship_density_proof(
            conn,
            domain=domain_pack,
            question=question,
            claim_ids=accepted_claim_ids,
        )
        graph_result = {
            "status": "completed",
            "link_results": link_results,
            "density_proof": density,
        }

    report_result = generate_run_report(
        conn,
        run_id=run_id,
        topic=question,
        domain_pack=domain_pack,
        output_dir=output_dir,
    )
    run_report = dict(report_result["report"])
    artifact = build_atlas_safe_run_artifact(
        conn,
        question=question,
        domain_pack=domain_pack,
        run_report=run_report,
    )
    artifact_path = _write_atlas_safe_artifact(artifact, output_dir=output_dir)
    source_health = acquisition_quality_summary(conn)
    resolver_breakdown = {
        backend: int((resolved.get("backend_counts") or {}).get(backend) or 0)
        for backend in resolved.get("backends") or []
    }
    return {
        "status": "completed",
        "question": question,
        "resolver_mode": resolver_mode,
        "resolver_query": resolved.get("resolver_query") or question,
        "resolved_count": int(resolved.get("resolved_count") or len(records)),
        "backend_counts": dict(resolved.get("backend_counts") or {}),
        "resolver_breakdown": resolver_breakdown,
        "source_health": source_health,
        "evidence": evidence,
        "graph": graph_result,
        "run_report": run_report,
        "atlas_safe_artifact": artifact,
        "artifact_path": artifact_path,
    }


def run_local_safe_arbitrary_source_health_proof(
    conn: sqlite3.Connection,
    *,
    question: str = LOCAL_SAFE_ARBITRARY_QUESTION,
    domain_pack: str = "creativity",
    output_dir: Path | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    """Execute the local-safe arbitrary question proof and optionally write artifacts."""
    resolved = resolve_work_candidates(
        query=question,
        domain_pack=domain_pack,
        limit=10,
        fixture_mode=True,
    )
    return _execute_source_health_proof_pipeline(
        conn,
        resolved=resolved,
        question=question,
        domain_pack=domain_pack,
        run_id=LOCAL_SAFE_RUN_ID,
        output_dir=output_dir,
        client=client,
        include_graph_proof=True,
        resolver_mode="manual_fixture",
    )


def run_live_network_source_health_smoke(
    conn: sqlite3.Connection,
    *,
    question: str = LOCAL_SAFE_ARBITRARY_QUESTION,
    resolver_query: str = LIVE_NETWORK_RESOLVER_QUERY,
    domain_pack: str = "creativity",
    output_dir: Path | None = None,
    limit: int = LIVE_NETWORK_SOURCE_LIMIT,
    backends: tuple[str, ...] = LIVE_NETWORK_BACKENDS,
    client: Any | None = None,
) -> dict[str, Any]:
    """Operator-gated live OpenAlex/arXiv source-health smoke on a temp DB."""
    resolved = resolve_live_network_source_records(
        question=question,
        resolver_query=resolver_query,
        domain_pack=domain_pack,
        limit=limit,
        backends=backends,
    )
    return _execute_source_health_proof_pipeline(
        conn,
        resolved=resolved,
        question=question,
        domain_pack=domain_pack,
        run_id=LIVE_NETWORK_RUN_ID,
        output_dir=output_dir,
        client=client,
        include_graph_proof=False,
        resolver_mode="live_network",
    )


def run_live_combined_source_health_query_expansion_smoke(
    conn: sqlite3.Connection,
    *,
    question: str = LOCAL_SAFE_ARBITRARY_QUESTION,
    domain_pack: str = "creativity",
    output_dir: Path | None = None,
    limit: int = LIVE_NETWORK_SOURCE_LIMIT,
    backends: tuple[str, ...] = LIVE_NETWORK_BACKENDS,
    client: Any | None = None,
) -> dict[str, Any]:
    """Operator-gated live smoke chaining query expansion with source-health persistence."""
    assert_live_combined_source_health_smoke_env()
    expansion_resolved = resolve_work_candidates(
        query=question,
        domain_pack=domain_pack,
        limit=limit,
        backends=list(backends),
        fixture_mode=False,
    )
    health_result = run_live_network_source_health_smoke(
        conn,
        question=question,
        domain_pack=domain_pack,
        output_dir=output_dir,
        limit=limit,
        backends=backends,
        client=client,
    )
    return {
        "status": "completed",
        "question": question,
        "discovery_query": expansion_resolved.get("discovery_query"),
        "query_expansion": dict(expansion_resolved.get("query_expansion") or {}),
        "expansion_resolved_count": int(expansion_resolved.get("resolved_count") or 0),
        "expansion_records": list(expansion_resolved.get("records") or []),
        **health_result,
    }
