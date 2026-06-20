"""DB ingest and staged-spine wiring for MVP research-run (integration)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rge.db.repositories import sha256_hex
from rge.modules.acquisition_quality import (
    acquisition_metadata_from_payload,
    merge_source_acquisition_metadata,
    persist_source_acquisition_status,
)
from rge.modules.fulltext_evidence import FULLTEXT_EVIDENCE_BASIS, generate_fulltext_evidence_cards
from rge.modules.selective_fulltext import FULL_TEXT_CLEAN_TEXT_READY, acquire_selective_fulltext

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_STAGING = REPO_ROOT / "data" / "sources" / "research_spine"
MANUAL_RESOLVER_FIXTURES = REPO_ROOT / "fixtures" / "source_providers" / "manual_resolver_fixtures.json"

# Mock staged candidate ids → manual resolver fixture ids for fixture-mode wiring.
STAGED_SELECTIVE_FULLTEXT_FIXTURE_ALIASES: dict[str, str] = {
    "disc_openalex_W2741809807": "manual_oa_tei",
    "disc_openalex_W1234567890": "manual_oa_pdf",
}


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

    resolver_source_id = str(acquisition.get("source_id") or record.get("source_id") or "unknown")
    metadata = {
        **{
            key: record.get(key)
            for key in (
                "is_oa",
                "oa_status",
                "best_oa_location_url",
                "pdf_url",
                "tei_url",
                "source_status",
                "resolver_backend",
                "raw_provider",
            )
            if record.get(key) not in (None, "")
        },
        **acquisition_metadata_from_payload(
            {**record, **acquisition},
            source_type="selective_fulltext",
            source_status=record.get("source_status"),
            acquisition_status=acquisition.get("acquisition_status"),
            parser_backend=(acquisition.get("parse") or {}).get("parser_backend"),
            failure_reason=acquisition.get("skip_reason")
            or acquisition.get("blocked_reason")
            or acquisition.get("failure_class"),
            resolver_source=record.get("resolver_backend") or record.get("raw_provider"),
        ),
    }

    if acquisition.get("acquisition_status") != FULL_TEXT_CLEAN_TEXT_READY:
        persist_source_acquisition_status(
            conn,
            source_id=resolver_source_id,
            title=str(record.get("title") or resolver_source_id),
            domain=domain,
            source_type="selective_fulltext",
            raw_text_checksum=sha256_hex(
                f"{resolver_source_id}:{acquisition.get('acquisition_status')}:{metadata}"
            ),
            status="failed",
            metadata=metadata,
        )
        return {
            "status": "skipped",
            "reason": "full_text_not_clean",
            "resolver_source_id": resolver_source_id,
        }

    clean_text = str(acquisition.get("clean_text") or "").strip()
    if not clean_text:
        return {
            "status": "skipped",
            "reason": "empty_clean_text",
            "resolver_source_id": resolver_source_id,
        }

    source_id = resolver_source_id
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
    db_source_id = str(ingest_result["source_id"])
    metadata["resolver_source"] = source_id
    merge_source_acquisition_metadata(
        conn,
        source_id=db_source_id,
        metadata=metadata,
        status="parsed",
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


def _load_manual_fixture_entry(fixture_id: str) -> dict[str, Any] | None:
    if not MANUAL_RESOLVER_FIXTURES.is_file():
        return None
    payload = json.loads(MANUAL_RESOLVER_FIXTURES.read_text(encoding="utf-8"))
    for entry in payload.get("records") or []:
        if str(entry.get("fixture_id") or "") == fixture_id:
            return dict(entry)
    return None


def candidate_source_to_fulltext_record(
    candidate: dict[str, Any],
    *,
    fixture_mode: bool = False,
) -> dict[str, Any]:
    """Map a candidate_sources row to a selective full-text resolver record."""
    from rge.modules.fetcher import parse_url_candidates
    from rge.modules.source_resolver.records import resolved_record_from_manual_fixture

    candidate_id = str(candidate.get("id") or candidate.get("candidate_id") or "")
    if fixture_mode and candidate_id in STAGED_SELECTIVE_FULLTEXT_FIXTURE_ALIASES:
        entry = _load_manual_fixture_entry(
            STAGED_SELECTIVE_FULLTEXT_FIXTURE_ALIASES[candidate_id]
        )
        if entry is not None:
            return resolved_record_from_manual_fixture(entry)

    record: dict[str, Any] = {
        "source_id": candidate_id,
        "title": str(candidate.get("title") or candidate_id),
    }
    for route in parse_url_candidates(candidate):
        kind = str(route.get("kind") or "").casefold()
        url = str(route.get("url") or "").strip()
        if not url:
            continue
        if "tei" in kind or url.casefold().endswith((".xml", ".tei")):
            record["tei_url"] = url
        elif "pdf" in kind or url.casefold().endswith(".pdf"):
            record["pdf_url"] = url
    fallback_url = candidate.get("url")
    if fallback_url and not record.get("tei_url") and not record.get("pdf_url"):
        url = str(fallback_url)
        if url.casefold().endswith((".xml", ".tei")):
            record["tei_url"] = url
        elif url.casefold().endswith(".pdf"):
            record["pdf_url"] = url
    return record


def wire_staged_orchestrator_selective_fulltext(
    conn: Any,
    *,
    candidate_ids: list[str],
    domain: str,
    staging_dir: Path | None = None,
    fixture_mode: bool = False,
    persist_claims: bool = True,
    force_top_n: bool = True,
    client: Any | None = None,
) -> dict[str, Any]:
    """Run selective full-text acquisition for staged candidates and persist to DB."""
    from rge.db.repositories import CandidateSourceRepository

    repo = CandidateSourceRepository(conn)
    records: list[dict[str, Any]] = []
    records_by_id: dict[str, dict[str, Any]] = {}
    for candidate_id in candidate_ids:
        candidate = repo.get_by_id(candidate_id)
        if candidate is None:
            continue
        record = candidate_source_to_fulltext_record(candidate, fixture_mode=fixture_mode)
        records.append(record)
        resolver_id = str(record.get("source_id") or candidate_id)
        records_by_id[resolver_id] = {
            "source_id": resolver_id,
            "title": record.get("title") or candidate.get("title"),
        }

    fulltext = acquire_selective_fulltext(
        records,
        top_n=max(len(records), 1),
        fixture_mode=fixture_mode,
        force_top_n=force_top_n,
    )
    spine = wire_selective_fulltext_to_db(
        conn,
        acquisitions=list(fulltext.get("acquisitions") or []),
        records_by_id=records_by_id,
        domain=domain,
        persist_claims=persist_claims,
        staging_dir=staging_dir,
        client=client,
    )
    fulltext_cards = generate_fulltext_evidence_cards(
        list(fulltext.get("acquisitions") or []),
        domain_pack=domain,
    )
    return {
        "status": "completed",
        "candidate_ids": candidate_ids,
        "selective_fulltext": fulltext,
        "db_spine": spine,
        "fulltext_evidence": fulltext_cards,
    }
