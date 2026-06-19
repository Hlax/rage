"""Webpage source adapter: normalize public HTML into source artifacts.

Scrapling-compatible boundary: acquisition and clean-text normalization only.
No claim extraction, paywall bypass, or network calls in default tests.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from rge.db.repositories import sha256_hex, utc_now_iso
from rge.modules.fetcher import html_to_text
from rge.modules.text_quality_gate import assess_chunk_extractability

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WEB_STAGING_DIR = REPO_ROOT / "data" / "sources" / "web"

ACQUISITION_CLEAN = "clean_text_ready"
ACQUISITION_DIRTY = "dirty_text"
WEBPAGE_EVIDENCE_BASIS = "webpage_clean_text_quote_first"

def build_webpage_quality_metrics(clean_text: str) -> dict[str, Any]:
    """Return deterministic quality metrics for a normalized webpage body."""
    assessment = assess_chunk_extractability(clean_text)
    return {
        "quoteable_span_count": assessment["quoteable_span_count"],
        "is_clean": assessment["is_clean"],
        "extractable": assessment["extractable"],
        "text_length": len(clean_text),
    }


def normalize_webpage_artifact(
    *,
    html: str,
    url: str,
    title: str,
    authors: list[str] | None = None,
    published_date: str | None = None,
    source_id: str | None = None,
) -> dict[str, Any]:
    """Normalize HTML into the shared source artifact shape for webpage ingestion."""
    raw_text = html
    clean_text = html_to_text(html)
    checksum = sha256_hex(clean_text)
    resolved_source_id = source_id or f"src_{checksum[:16]}"
    metrics = build_webpage_quality_metrics(clean_text)
    acquisition_status = (
        ACQUISITION_CLEAN if metrics["extractable"] else ACQUISITION_DIRTY
    )
    return {
        "source_id": resolved_source_id,
        "source_type": "webpage",
        "url": url,
        "title": title,
        "authors": authors or [],
        "published_date": published_date,
        "raw_text": raw_text,
        "clean_text": clean_text,
        "quality_metrics": metrics,
        "acquisition_status": acquisition_status,
        "raw_text_checksum": checksum,
        "created_at": utc_now_iso(),
    }


def acquire_webpage_from_path(
    path: Path,
    *,
    url: str | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    """Load a local HTML fixture and return a normalized webpage artifact."""
    html = path.read_text(encoding="utf-8")
    inferred_title = title
    if not inferred_title:
        for line in html.splitlines():
            if "<title>" in line.casefold():
                inferred_title = (
                    line.split("<title>", 1)[-1]
                    .split("</title>", 1)[0]
                    .strip()
                )
                break
    return normalize_webpage_artifact(
        html=html,
        url=url or f"file://{path.as_posix()}",
        title=inferred_title or path.stem,
    )


def persist_webpage_artifact_staging(
    artifact: dict[str, Any],
    *,
    staging_dir: Path,
) -> dict[str, Any]:
    """Write a normalized webpage artifact JSON for operator inspection."""
    staging_dir.mkdir(parents=True, exist_ok=True)
    source_id = str(artifact["source_id"])
    out_path = staging_dir / f"{source_id}.webpage.json"
    out_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return {
        "status": "staged",
        "source_id": source_id,
        "artifact_path": str(out_path),
        "acquisition_status": artifact["acquisition_status"],
    }


def default_web_staging_dir() -> Path:
    return DEFAULT_WEB_STAGING_DIR


def load_webpage_artifact_from_path(path: Path) -> dict[str, Any]:
    """Load a staged webpage artifact JSON written by persist_webpage_artifact_staging."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Webpage artifact JSON must be an object.")
    required = ("source_id", "source_type", "clean_text", "acquisition_status")
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"Webpage artifact missing required fields: {', '.join(missing)}")
    if str(payload.get("source_type")) != "webpage":
        raise ValueError("Webpage artifact source_type must be webpage.")
    return payload


def _attach_webpage_source_metadata(
    conn: sqlite3.Connection,
    *,
    source_id: str,
    artifact: dict[str, Any],
) -> None:
    domain_metadata = {
        "url": artifact.get("url"),
        "published_date": artifact.get("published_date"),
        "acquisition_status": artifact.get("acquisition_status"),
        "quality_metrics": artifact.get("quality_metrics") or {},
        "parser_backend": "html_to_text",
        "source_adapter": "web_source_adapter",
    }
    conn.execute(
        """
        UPDATE sources
        SET domain_metadata_json = ?, authors_json = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            json.dumps(domain_metadata),
            json.dumps(artifact.get("authors") or []),
            utc_now_iso(),
            source_id,
        ),
    )
    conn.commit()


def ingest_webpage_artifact_to_db(
    conn: sqlite3.Connection,
    artifact: dict[str, Any],
    *,
    domain: str,
    staging_dir: Path | None = None,
) -> dict[str, Any]:
    """Persist normalized webpage clean text as an ingested source + chunks."""
    from rge.db.repositories import ChunkRepository, ingest_local_source

    acquisition_status = str(artifact.get("acquisition_status") or "")
    if acquisition_status != ACQUISITION_CLEAN:
        return {
            "status": "blocked_dirty_text",
            "reason": acquisition_status or ACQUISITION_DIRTY,
            "source_id": str(artifact.get("source_id") or ""),
            "quality_metrics": artifact.get("quality_metrics") or {},
        }

    clean_text = str(artifact.get("clean_text") or "").strip()
    if not clean_text:
        return {
            "status": "skipped",
            "reason": "empty_clean_text",
            "source_id": str(artifact.get("source_id") or ""),
        }

    source_id = str(artifact.get("source_id") or "unknown")
    target_dir = staging_dir or default_web_staging_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_id = source_id.replace(":", "_")
    artifact_path = target_dir / f"{safe_id}.txt"
    artifact_path.write_text(clean_text, encoding="utf-8")

    ingest_result = ingest_local_source(
        conn,
        local_path=artifact_path,
        domain=domain,
        raw_text=clean_text,
        title=str(artifact.get("title") or source_id),
        source_type="webpage",
    )
    db_source_id = str(ingest_result["source_id"])
    _attach_webpage_source_metadata(conn, source_id=db_source_id, artifact=artifact)
    chunks = ChunkRepository(conn).list_for_source(db_source_id)
    return {
        **ingest_result,
        "artifact_path": str(artifact_path.resolve()),
        "chunk_ids": [chunk.id for chunk in chunks],
        "quality_metrics": artifact.get("quality_metrics") or {},
        "acquisition_status": acquisition_status,
        "url": artifact.get("url"),
    }


def extract_webpage_claims_to_db(
    conn: sqlite3.Connection,
    db_source_id: str,
    *,
    fixture_name: str | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    """Run quote-first extract-claims for one ingested webpage source."""
    from rge.modules.claim_extractor import extract_claims_for_source

    result = extract_claims_for_source(
        conn,
        db_source_id,
        fixture_name=fixture_name,
        client=client,
    )
    return {
        **result,
        "evidence_basis": WEBPAGE_EVIDENCE_BASIS,
        "db_source_id": db_source_id,
    }


def run_ingest_webpage_pipeline(
    conn: sqlite3.Connection,
    artifact: dict[str, Any],
    *,
    domain: str,
    staging_dir: Path | None = None,
    persist_claims: bool = True,
    fixture_name: str | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    """Ingest a webpage artifact and optionally run quote-first claim extraction."""
    ingest_row = ingest_webpage_artifact_to_db(
        conn,
        artifact,
        domain=domain,
        staging_dir=staging_dir,
    )
    if ingest_row.get("status") not in {"ingested", "already_ingested"}:
        return {
            "status": ingest_row.get("status", "error"),
            "command": "ingest-webpage",
            "ingest": ingest_row,
            "extract": None,
        }

    extract_row: dict[str, Any] | None = None
    db_source_id = str(ingest_row["source_id"])
    if persist_claims:
        extract_row = extract_webpage_claims_to_db(
            conn,
            db_source_id,
            fixture_name=fixture_name,
            client=client,
        )

    return {
        "status": "completed",
        "command": "ingest-webpage",
        "ingest": ingest_row,
        "extract": extract_row,
        "source_id": db_source_id,
    }
