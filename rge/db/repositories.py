"""Repository layer: the only place allowed to write accepted graph tables.

Invariants:
- Model output never reaches these writers without deterministic validation.
- Rejected claims are stored with rejection reasons, never discarded.
- Scores change only through append-only score events.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_source_id(raw_text_checksum: str) -> str:
    return f"src_{raw_text_checksum[:16]}"


def make_chunk_id(source_id: str, chunk_index: int, text_checksum: str) -> str:
    source_suffix = source_id.removeprefix("src_")
    return f"chk_{source_suffix}_{chunk_index}_{text_checksum[:8]}"


@dataclass(frozen=True)
class SourceRecord:
    id: str
    title: str
    source_type: str
    domain: str
    local_path: str
    raw_text_checksum: str
    status: str
    created_at: str
    updated_at: str
    authors_json: str = "[]"
    domain_metadata_json: str = "{}"


@dataclass(frozen=True)
class ChunkRecord:
    id: str
    source_id: str
    chunk_index: int
    chunk_text: str
    text_checksum: str
    created_at: str
    token_count: int | None = None


class SourceRepository:
    """Persist and read ``sources`` rows."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get_by_checksum(self, raw_text_checksum: str) -> SourceRecord | None:
        row = self._conn.execute(
            """
            SELECT id, title, source_type, domain, local_path, raw_text_checksum,
                   status, created_at, updated_at, authors_json, domain_metadata_json
            FROM sources
            WHERE raw_text_checksum = ?
            """,
            (raw_text_checksum,),
        ).fetchone()
        return _row_to_source(row) if row else None

    def get_by_id(self, source_id: str) -> SourceRecord | None:
        row = self._conn.execute(
            """
            SELECT id, title, source_type, domain, local_path, raw_text_checksum,
                   status, created_at, updated_at, authors_json, domain_metadata_json
            FROM sources
            WHERE id = ?
            """,
            (source_id,),
        ).fetchone()
        return _row_to_source(row) if row else None

    def insert(self, source: SourceRecord) -> SourceRecord:
        self._conn.execute(
            """
            INSERT INTO sources (
                id, title, authors_json, year, source_type, domain,
                domain_metadata_json, url, local_path, publisher, abstract,
                raw_text_checksum, quality_score, credibility_notes, status,
                created_at, updated_at
            ) VALUES (?, ?, ?, NULL, ?, ?, ?, NULL, ?, NULL, NULL, ?, NULL, NULL, ?, ?, ?)
            """,
            (
                source.id,
                source.title,
                source.authors_json,
                source.source_type,
                source.domain,
                source.domain_metadata_json,
                source.local_path,
                source.raw_text_checksum,
                source.status,
                source.created_at,
                source.updated_at,
            ),
        )
        self._conn.commit()
        return source


class ChunkRepository:
    """Persist and read ``chunks`` rows."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def list_for_source(self, source_id: str) -> list[ChunkRecord]:
        rows = self._conn.execute(
            """
            SELECT id, source_id, chunk_index, chunk_text, text_checksum,
                   created_at, token_count
            FROM chunks
            WHERE source_id = ?
            ORDER BY chunk_index
            """,
            (source_id,),
        ).fetchall()
        return [_row_to_chunk(row) for row in rows]

    def insert_many(self, chunks: list[ChunkRecord]) -> list[ChunkRecord]:
        self._conn.executemany(
            """
            INSERT INTO chunks (
                id, source_id, chunk_index, chunk_text, page, section,
                token_count, embedding_id, embedding_model, text_checksum, created_at
            ) VALUES (?, ?, ?, ?, NULL, NULL, ?, NULL, NULL, ?, ?)
            """,
            [
                (
                    chunk.id,
                    chunk.source_id,
                    chunk.chunk_index,
                    chunk.chunk_text,
                    chunk.token_count,
                    chunk.text_checksum,
                    chunk.created_at,
                )
                for chunk in chunks
            ],
        )
        self._conn.commit()
        return chunks


def ingest_local_source(
    conn: sqlite3.Connection,
    *,
    local_path: Path,
    domain: str,
    raw_text: str,
    title: str,
    source_type: str = "fixture",
) -> dict[str, Any]:
    """Fetch-parse-persist a local text source. Idempotent by content checksum."""
    from rge.modules.parser import parse_source_text

    checksum = sha256_hex(raw_text)
    source_repo = SourceRepository(conn)
    existing = source_repo.get_by_checksum(checksum)
    if existing is not None:
        chunk_repo = ChunkRepository(conn)
        return {
            "status": "already_ingested",
            "source_id": existing.id,
            "chunk_count": len(chunk_repo.list_for_source(existing.id)),
            "raw_text_checksum": existing.raw_text_checksum,
        }

    now = utc_now_iso()
    source_id = make_source_id(checksum)
    source = SourceRecord(
        id=source_id,
        title=title,
        source_type=source_type,
        domain=domain,
        local_path=str(local_path.resolve()),
        raw_text_checksum=checksum,
        status="ingested",
        created_at=now,
        updated_at=now,
    )
    source_repo.insert(source)

    chunk_dicts = parse_source_text(raw_text, source_id=source_id)
    chunk_records = [
        ChunkRecord(
            id=chunk["id"],
            source_id=source_id,
            chunk_index=chunk["chunk_index"],
            chunk_text=chunk["chunk_text"],
            text_checksum=chunk["text_checksum"],
            created_at=now,
            token_count=chunk.get("token_count"),
        )
        for chunk in chunk_dicts
    ]
    ChunkRepository(conn).insert_many(chunk_records)

    return {
        "status": "ingested",
        "source_id": source_id,
        "chunk_count": len(chunk_records),
        "raw_text_checksum": checksum,
        "domain": domain,
        "source_type": source_type,
        "created_at": now,
    }


def _row_to_source(row: sqlite3.Row) -> SourceRecord:
    return SourceRecord(
        id=row["id"],
        title=row["title"],
        source_type=row["source_type"],
        domain=row["domain"],
        local_path=row["local_path"],
        raw_text_checksum=row["raw_text_checksum"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        authors_json=row["authors_json"] or "[]",
        domain_metadata_json=row["domain_metadata_json"] or "{}",
    )


def _row_to_chunk(row: sqlite3.Row) -> ChunkRecord:
    return ChunkRecord(
        id=row["id"],
        source_id=row["source_id"],
        chunk_index=row["chunk_index"],
        chunk_text=row["chunk_text"],
        text_checksum=row["text_checksum"],
        created_at=row["created_at"],
        token_count=row["token_count"],
    )


def source_record_to_public_dict(source: SourceRecord) -> dict[str, Any]:
    """Return a JSON-serializable view without private chunk text."""
    return {
        "id": source.id,
        "title": source.title,
        "source_type": source.source_type,
        "domain": source.domain,
        "raw_text_checksum": source.raw_text_checksum,
        "status": source.status,
        "created_at": source.created_at,
        "updated_at": source.updated_at,
        "authors": json.loads(source.authors_json),
    }
