"""DB ingest and staged-spine wiring for MVP research-run (integration)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rge.modules.fulltext_evidence import FULLTEXT_EVIDENCE_BASIS, generate_fulltext_evidence_cards
from rge.modules.selective_fulltext import FULL_TEXT_CLEAN_TEXT_READY

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_STAGING = REPO_ROOT / "data" / "sources" / "research_spine"


def default_db_staging_dir() -> Path:
    return DEFAULT_DB_STAGING


def ingest_acquisition_to_db(
    conn: Any,
    acquisition: dict[str, Any],
    record: dict[str, Any],
    *,
    domain: str,
    staging_dir: Path | None = None,
) -> dict[str, Any]:
    """Persist selective full-text clean text as an ingested source + chunks."""
    from rge.db.repositories import ingest_local_source

    if acquisition.get("acquisition_status") != FULL_TEXT_CLEAN_TEXT_READY:
        return {
            "status": "skipped",
            "reason": "full_text_not_clean",
            "resolver_source_id": acquisition.get("source_id"),
        }

    clean_text = str(acquisition.get("clean_text") or "").strip()
    if not clean_text:
        return {
            "status": "skipped",
            "reason": "empty_clean_text",
            "resolver_source_id": acquisition.get("source_id"),
        }

    source_id = str(acquisition.get("source_id") or "unknown")
    safe_id = source_id.replace(":", "_")
    target_dir = staging_dir or default_db_staging_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = target_dir / f"{safe_id}.txt"
    artifact_path.write_text(clean_text, encoding="utf-8")

    ingest_result = ingest_local_source(
        conn,
        local_path=artifact_path,
        domain=domain,
        raw_text=clean_text,
        title=str(record.get("title") or source_id),
        source_type="selective_fulltext",
    )
    return {
        **ingest_result,
        "resolver_source_id": source_id,
        "artifact_path": str(artifact_path.resolve()),
        "parser_backend": (acquisition.get("parse") or {}).get("parser_backend"),
    }


def extract_fulltext_claims_to_db(
    conn: Any,
    db_source_id: str,
    *,
    fixture_name: str = "fulltext_quote_first_openalex.json",
    client: Any | None = None,
) -> dict[str, Any]:
    """Run mock extract-claims for one ingested selective full-text source."""
    from rge.modules.claim_extractor import extract_claims_for_source

    result = extract_claims_for_source(
        conn,
        db_source_id,
        fixture_name=fixture_name,
        client=client,
    )
    return {
        **result,
        "evidence_basis": FULLTEXT_EVIDENCE_BASIS,
        "db_source_id": db_source_id,
    }


def wire_selective_fulltext_to_db(
    conn: Any,
    *,
    acquisitions: list[dict[str, Any]],
    records_by_id: dict[str, dict[str, Any]],
    domain: str,
    persist_claims: bool = True,
    staging_dir: Path | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    """Ingest clean full-text acquisitions and optionally extract claims to DB."""
    ingest_rows: list[dict[str, Any]] = []
    extract_rows: list[dict[str, Any]] = []

    for acquisition in acquisitions:
        resolver_id = str(acquisition.get("source_id") or "")
        record = records_by_id.get(resolver_id, {"source_id": resolver_id, "title": resolver_id})
        ingest_row = ingest_acquisition_to_db(
            conn,
            acquisition,
            record,
            domain=domain,
            staging_dir=staging_dir,
        )
        ingest_rows.append(ingest_row)
        if not persist_claims:
            continue
        if ingest_row.get("status") not in {"completed", "already_ingested", "ingested"}:
            continue
        db_source_id = str(ingest_row.get("source_id") or "")
        if not db_source_id:
            continue
        extract_rows.append(
            extract_fulltext_claims_to_db(
                conn,
                db_source_id,
                client=client,
            )
        )

    accepted_total = sum(
        len(row.get("accepted_ids") or row.get("accepted_claim_ids") or [])
        for row in extract_rows
    )
    rejected_total = sum(
        len(row.get("rejected_ids") or row.get("rejected_claim_ids") or [])
        for row in extract_rows
    )
    return {
        "status": "completed",
        "ingest_rows": ingest_rows,
        "extract_rows": extract_rows,
        "accepted_claims_total": accepted_total,
        "rejected_claims_total": rejected_total,
    }


def wire_research_demo_to_db(
    conn: Any,
    demo: dict[str, Any],
    *,
    domain: str,
    persist_claims: bool = True,
    staging_dir: Path | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    """Attach DB ingest/extract results to a research-run payload."""
    fulltext = demo.get("selective_fulltext") or {}
    acquisitions = list(fulltext.get("acquisitions") or [])
    records = {}
    for item in demo.get("source_status_table") or []:
        records[str(item.get("source_id") or "")] = item
    for item in demo.get("ranked_sources") or []:
        records[str(item.get("source_id") or "")] = item

    spine = wire_selective_fulltext_to_db(
        conn,
        acquisitions=acquisitions,
        records_by_id=records,
        domain=domain,
        persist_claims=persist_claims,
        staging_dir=staging_dir,
        client=client,
    )
    fulltext_cards = generate_fulltext_evidence_cards(acquisitions, domain_pack=domain)
    return {
        **spine,
        "fulltext_evidence": fulltext_cards,
    }
