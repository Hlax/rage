"""Acquisition and parser quality summaries for run and cluster reports."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from rge.db.repositories import sha256_hex, utc_now_iso


ACQUISITION_METADATA_FIELDS = (
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
)


def _clean_string(value: Any) -> str:
    return str(value or "").strip()


def _row_get(row: Any, key: str, default: Any = None) -> Any:
    if isinstance(row, dict):
        return row.get(key, default)
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return default


def _parser_backend_from_metadata(metadata: dict[str, Any]) -> str:
    parse = metadata.get("parse") if isinstance(metadata.get("parse"), dict) else {}
    return str(
        parse.get("parser_backend") or metadata.get("parser_backend") or ""
    ).strip()


def _acquisition_status_from_metadata(metadata: dict[str, Any]) -> str:
    return str(
        metadata.get("acquisition_status")
        or metadata.get("full_text_acquisition_status")
        or metadata.get("source_status")
        or ""
    ).strip()


def _source_status_from_metadata(metadata: dict[str, Any]) -> str:
    return _clean_string(
        metadata.get("source_status")
        or metadata.get("acquisition_status")
        or metadata.get("full_text_acquisition_status")
    )


def _availability_from_metadata(metadata: dict[str, Any]) -> dict[str, bool]:
    pdf_url = _clean_string(metadata.get("pdf_url"))
    tei_url = _clean_string(metadata.get("tei_url"))
    best_oa = _clean_string(metadata.get("best_oa_location_url"))
    location = metadata.get("location") if isinstance(metadata.get("location"), dict) else {}
    if not pdf_url and _clean_string(location.get("kind")).casefold() == "pdf":
        pdf_url = _clean_string(location.get("url"))
    if not tei_url and _clean_string(location.get("kind")).casefold() == "tei":
        tei_url = _clean_string(location.get("url"))
    return {
        "oa_available": bool(metadata.get("is_oa") or metadata.get("oa_status") == "open" or best_oa or pdf_url or tei_url),
        "pdf_available": bool(pdf_url),
        "tei_available": bool(tei_url),
    }


def acquisition_metadata_from_payload(
    payload: dict[str, Any],
    *,
    source_type: str | None = None,
    source_status: str | None = None,
    acquisition_status: str | None = None,
    parser_backend: str | None = None,
    failure_reason: str | None = None,
    resolver_source: str | None = None,
) -> dict[str, Any]:
    """Normalize resolver/acquisition/parser metadata for durable source rows."""
    parse = payload.get("parse") if isinstance(payload.get("parse"), dict) else {}
    quality_metrics = payload.get("quality_metrics") if isinstance(payload.get("quality_metrics"), dict) else {}
    availability = _availability_from_metadata(payload)
    normalized: dict[str, Any] = {
        "source_status": _clean_string(source_status or payload.get("source_status") or payload.get("acquisition_status")),
        "acquisition_status": _clean_string(acquisition_status or payload.get("acquisition_status") or payload.get("source_status")),
        "parser_backend": _clean_string(parser_backend or parse.get("parser_backend") or payload.get("parser_backend")),
        "source_type": _clean_string(source_type or payload.get("source_type") or payload.get("source_kind")),
        "quality_gate_status": _clean_string(payload.get("quality_gate_status") or parse.get("source_status") or payload.get("failure_class")),
        "extractable": bool(
            payload.get("extractable")
            if "extractable" in payload
            else quality_metrics.get("extractable")
            if "extractable" in quality_metrics
            else payload.get("clean_text")
        ),
        "failure_reason": _clean_string(failure_reason or payload.get("failure_reason") or payload.get("skip_reason") or payload.get("blocked_reason") or payload.get("reason")),
        "resolver_source": _clean_string(resolver_source or payload.get("resolver_source") or payload.get("resolver_backend") or payload.get("raw_provider") or payload.get("source_kind")),
        **availability,
    }
    for optional in ("is_oa", "oa_status", "best_oa_location_url", "pdf_url", "tei_url"):
        if payload.get(optional) not in (None, ""):
            normalized[optional] = payload[optional]
    if parse:
        normalized["parse"] = {
            key: value
            for key, value in parse.items()
            if key
            in {
                "source_status",
                "parser_backend",
                "readable_char_ratio",
                "sentence_count",
                "quoteable_span_count",
                "extracted_char_count",
                "detail",
                "page_count",
            }
        }
    if quality_metrics:
        normalized["quality_metrics"] = quality_metrics
    return {key: value for key, value in normalized.items() if value not in ("", None)}


def persist_source_acquisition_status(
    conn: sqlite3.Connection,
    *,
    source_id: str,
    title: str,
    domain: str,
    source_type: str,
    metadata: dict[str, Any],
    raw_text_checksum: str | None = None,
    local_path: str = "",
    status: str = "failed",
    authors: list[str] | None = None,
) -> dict[str, Any]:
    """Upsert a durable source row for acquisition/parser outcomes, including failures."""
    now = utc_now_iso()
    checksum = raw_text_checksum or sha256_hex(f"{source_id}:{title}:{metadata}")
    merged = dict(metadata)
    merged.setdefault("source_type", source_type)
    conn.execute(
        """
        INSERT INTO sources (
            id, title, authors_json, year, source_type, domain,
            domain_metadata_json, url, local_path, publisher, abstract,
            raw_text_checksum, quality_score, credibility_notes, status,
            created_at, updated_at
        ) VALUES (?, ?, ?, NULL, ?, ?, ?, NULL, ?, NULL, NULL, ?, NULL, NULL, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            source_type = excluded.source_type,
            domain = excluded.domain,
            domain_metadata_json = excluded.domain_metadata_json,
            raw_text_checksum = excluded.raw_text_checksum,
            status = excluded.status,
            updated_at = excluded.updated_at
        """,
        (
            source_id,
            title,
            json.dumps(authors or []),
            source_type,
            domain,
            json.dumps(merged, sort_keys=True),
            local_path,
            checksum,
            status,
            now,
            now,
        ),
    )
    conn.commit()
    return {
        "source_id": source_id,
        "status": status,
        "domain_metadata": merged,
    }


def merge_source_acquisition_metadata(
    conn: sqlite3.Connection,
    *,
    source_id: str,
    metadata: dict[str, Any],
    status: str | None = None,
) -> None:
    """Merge acquisition metadata onto an existing source row."""
    row = conn.execute(
        "SELECT domain_metadata_json, status FROM sources WHERE id = ?",
        (source_id,),
    ).fetchone()
    if row is None:
        return
    try:
        existing = json.loads(row["domain_metadata_json"] or "{}")
    except json.JSONDecodeError:
        existing = {}
    if not isinstance(existing, dict):
        existing = {}
    existing.update(metadata)
    conn.execute(
        """
        UPDATE sources
        SET domain_metadata_json = ?, status = COALESCE(?, status), updated_at = ?
        WHERE id = ?
        """,
        (json.dumps(existing, sort_keys=True), status, utc_now_iso(), source_id),
    )
    conn.commit()


def summarize_source_metadata_rows(
    rows: list[Any],
    *,
    source_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Aggregate acquisition/parser metrics from sources.domain_metadata_json rows."""
    status_counts: dict[str, int] = {}
    source_status_counts: dict[str, int] = {}
    parser_counts: dict[str, int] = {}
    source_type_counts: dict[str, int] = {}
    quality_gate_counts: dict[str, int] = {}
    extractable_counts: dict[str, int] = {}
    failure_reason_counts: dict[str, int] = {}
    resolver_source_counts: dict[str, int] = {}
    purpose_fit_counts: dict[str, int] = {}
    purpose_gate_decision_counts: dict[str, int] = {}
    availability_counts = {"oa_available": 0, "pdf_available": 0, "tei_available": 0}
    source_rows: list[dict[str, Any]] = []
    parsed_rows = 0

    for row in rows:
        try:
            metadata = json.loads(row["domain_metadata_json"] or "{}")
        except (json.JSONDecodeError, TypeError, KeyError):
            continue
        if not isinstance(metadata, dict):
            continue
        parsed_rows += 1

        status = _acquisition_status_from_metadata(metadata)
        if status:
            status_counts[status] = status_counts.get(status, 0) + 1

        source_status = _source_status_from_metadata(metadata)
        if source_status:
            source_status_counts[source_status] = source_status_counts.get(source_status, 0) + 1

        backend = _parser_backend_from_metadata(metadata)
        if backend:
            parser_counts[backend] = parser_counts.get(backend, 0) + 1

        source_type = str(metadata.get("source_type") or _row_get(row, "source_type") or "").strip()
        if source_type:
            source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1

        quality_gate = _clean_string(metadata.get("quality_gate_status"))
        if quality_gate:
            quality_gate_counts[quality_gate] = quality_gate_counts.get(quality_gate, 0) + 1

        if "extractable" in metadata:
            extractable_key = "true" if bool(metadata.get("extractable")) else "false"
            extractable_counts[extractable_key] = extractable_counts.get(extractable_key, 0) + 1

        failure_reason = _clean_string(metadata.get("failure_reason"))
        if failure_reason:
            failure_reason_counts[failure_reason] = failure_reason_counts.get(failure_reason, 0) + 1

        resolver_source = _clean_string(metadata.get("resolver_source"))
        if resolver_source:
            resolver_source_counts[resolver_source] = resolver_source_counts.get(resolver_source, 0) + 1

        purpose_fit = _clean_string(
            metadata.get("purpose_fit_status")
            or metadata.get("purpose_match_status")
        )
        if purpose_fit:
            purpose_fit_counts[purpose_fit] = purpose_fit_counts.get(purpose_fit, 0) + 1

        purpose_decision = _clean_string(metadata.get("purpose_gate_decision"))
        if purpose_decision:
            purpose_gate_decision_counts[purpose_decision] = (
                purpose_gate_decision_counts.get(purpose_decision, 0) + 1
            )

        availability = _availability_from_metadata(metadata)
        for key, available in availability.items():
            if available:
                availability_counts[key] += 1

        source_row: dict[str, Any] = {}
        for field in ACQUISITION_METADATA_FIELDS:
            if field in metadata:
                source_row[field] = metadata[field]
        if _row_get(row, "id"):
            source_row["source_id"] = _row_get(row, "id")
        if _row_get(row, "status"):
            source_row["db_status"] = _row_get(row, "status")
        if source_row:
            source_rows.append(source_row)

    return {
        "source_status_counts": source_status_counts,
        "acquisition_status_counts": status_counts,
        "parser_backend_counts": parser_counts,
        "source_type_counts": source_type_counts,
        "quality_gate_status_counts": quality_gate_counts,
        "extractable_counts": extractable_counts,
        "failure_reason_counts": failure_reason_counts,
        "resolver_source_counts": resolver_source_counts,
        "purpose_fit_status_counts": purpose_fit_counts,
        "purpose_gate_decision_counts": purpose_gate_decision_counts,
        "availability_counts": availability_counts,
        "sources_with_metadata": parsed_rows,
        "scoped_source_count": len(source_ids) if source_ids is not None else None,
        "source_status_rows": source_rows,
    }


def acquisition_quality_summary(
    conn: sqlite3.Connection,
    *,
    source_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Summarize acquisition/parser outcomes for all or selected sources."""
    if source_ids is not None:
        if not source_ids:
            return summarize_source_metadata_rows([], source_ids=source_ids)
        placeholders = ",".join("?" for _ in source_ids)
        rows = conn.execute(
            f"""
            SELECT id, status, source_type, domain_metadata_json
            FROM sources
            WHERE id IN ({placeholders})
              AND domain_metadata_json IS NOT NULL
            """,
            tuple(source_ids),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT id, status, source_type, domain_metadata_json
            FROM sources
            WHERE domain_metadata_json IS NOT NULL
            """
        ).fetchall()
    return summarize_source_metadata_rows(rows, source_ids=source_ids)


def cluster_source_ids(conn: sqlite3.Connection, *, domain: str) -> list[str]:
    """Return distinct source ids for accepted claims in a domain cluster scope."""
    rows = conn.execute(
        """
        SELECT DISTINCT source_id
        FROM claims
        WHERE domain = ? AND status = 'accepted'
        ORDER BY source_id
        """,
        (domain,),
    ).fetchall()
    return [str(row["source_id"]) for row in rows]


def cluster_acquisition_quality_summary(
    conn: sqlite3.Connection,
    *,
    domain: str,
) -> dict[str, Any]:
    """Parser/acquisition metrics scoped to cluster-linked sources."""
    source_ids = cluster_source_ids(conn, domain=domain)
    summary = acquisition_quality_summary(conn, source_ids=source_ids)
    summary["cluster_domain"] = domain
    summary["cluster_source_ids"] = source_ids
    return summary


ACQUISITION_STATUS_TO_FAILURE: dict[str, str] = {
    "dirty_text": "blocked_by_quality_gate",
    "parse_failed": "parse_failed",
    "full_text_parse_failed": "parse_failed",
    "download_failed": "download_failed",
    "full_text_available": "download_failed",
}


def staged_ingest_health_metadata(
    *,
    candidate: dict[str, Any] | None,
    source_type: str,
    raw_text: str,
    domain: str,
    artifact_path: Path,
    title: str,
    question: str | None = None,
) -> dict[str, Any]:
    """Build durable source-health metadata for staged ingest rows."""
    from rge.modules.purpose_gating import evaluate_text_purpose_fit
    from rge.modules.source_resolver.status import CLEAN_TEXT_READY

    suffix = artifact_path.suffix.casefold()
    parser_backend = "html_parser" if suffix in {".html", ".htm"} else "staged_text"
    resolver_source = "staged_fetch"
    if candidate:
        resolver_source = str(
            candidate.get("source_type")
            or candidate.get("provider")
            or resolver_source
        )
    purpose_question = question or str((candidate or {}).get("title") or title or domain)
    purpose_fit = evaluate_text_purpose_fit(
        f"{title} {raw_text[:500]}",
        question=purpose_question,
        domain_pack=domain,
        evidence_ref=title,
    )
    metadata = acquisition_metadata_from_payload(
        {
            "source_status": CLEAN_TEXT_READY,
            "acquisition_status": CLEAN_TEXT_READY,
            "parser_backend": parser_backend,
            "extractable": True,
            "quality_gate_status": "extractable",
        },
        source_type=source_type,
        source_status=CLEAN_TEXT_READY,
        acquisition_status=CLEAN_TEXT_READY,
        parser_backend=parser_backend,
        resolver_source=resolver_source,
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
        }
    )
    return metadata


def failure_modes_from_acquisition_summary(
    summary: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Derive improvement-ticket failure modes from acquisition/parser metrics."""
    if not summary:
        return []

    modes: list[dict[str, Any]] = []
    seen: set[str] = set()
    status_counts = summary.get("acquisition_status_counts") or {}
    source_types = summary.get("source_type_counts") or {}
    parser_counts = summary.get("parser_backend_counts") or {}

    for status, count in status_counts.items():
        reason = ACQUISITION_STATUS_TO_FAILURE.get(str(status))
        if reason and int(count) >= 1 and reason not in seen:
            modes.append({"reason": reason, "count": int(count)})
            seen.add(reason)

    dirty_count = int(status_counts.get("dirty_text") or 0)
    if source_types.get("webpage", 0) >= 1 and dirty_count >= 1:
        if "webpage_dirty_text" not in seen:
            modes.append({"reason": "webpage_dirty_text", "count": dirty_count})
            seen.add("webpage_dirty_text")

    pdf_unavailable = int(parser_counts.get("pdf_unavailable") or 0)
    if pdf_unavailable >= 1 and "pdf_parser_unavailable" not in seen:
        modes.append({"reason": "pdf_parser_unavailable", "count": pdf_unavailable})

    return modes
