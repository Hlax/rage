"""Acquisition and parser quality summaries for run and cluster reports."""

from __future__ import annotations

import json
import sqlite3
from typing import Any


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


def summarize_source_metadata_rows(
    rows: list[Any],
    *,
    source_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Aggregate acquisition/parser metrics from sources.domain_metadata_json rows."""
    status_counts: dict[str, int] = {}
    parser_counts: dict[str, int] = {}
    source_type_counts: dict[str, int] = {}
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

        backend = _parser_backend_from_metadata(metadata)
        if backend:
            parser_counts[backend] = parser_counts.get(backend, 0) + 1

        source_type = str(metadata.get("source_type") or "").strip()
        if source_type:
            source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1

    return {
        "acquisition_status_counts": status_counts,
        "parser_backend_counts": parser_counts,
        "source_type_counts": source_type_counts,
        "sources_with_metadata": parsed_rows,
        "scoped_source_count": len(source_ids) if source_ids is not None else None,
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
            SELECT domain_metadata_json
            FROM sources
            WHERE id IN ({placeholders})
              AND domain_metadata_json IS NOT NULL
            """,
            tuple(source_ids),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT domain_metadata_json
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
}


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
