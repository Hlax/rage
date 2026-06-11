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


def make_claim_id(source_id: str, chunk_id: str, claim_text: str) -> str:
    digest = sha256_hex(f"{source_id}:{chunk_id}:{claim_text}")
    return f"clm_{digest[:16]}"


def make_quote_id(claim_id: str, quote_text: str) -> str:
    digest = sha256_hex(f"{claim_id}:{quote_text}")
    return f"qt_{digest[:16]}"


@dataclass(frozen=True)
class ClaimRecord:
    id: str
    source_id: str
    chunk_id: str
    claim_text: str
    statement_type: str
    subject: str
    predicate: str
    object: str
    scope: str
    evidence_type: str
    confidence: float
    limitations_json: str
    domain: str
    status: str
    created_at: str
    updated_at: str
    rejection_reason: str | None = None
    domain_metadata_json: str = "{}"


class ClaimRepository:
    """Persist and read ``claims`` and ``claim_quotes`` rows."""

    VALIDATOR_VERSION = "0.1.0"

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get_by_id(self, claim_id: str) -> ClaimRecord | None:
        row = self._conn.execute(
            """
            SELECT id, source_id, chunk_id, claim_text, statement_type, subject,
                   predicate, object, scope, evidence_type, confidence,
                   limitations_json, domain, domain_metadata_json, status,
                   rejection_reason, created_at, updated_at
            FROM claims
            WHERE id = ?
            """,
            (claim_id,),
        ).fetchone()
        return _row_to_claim(row) if row else None

    def list_for_source(
        self, source_id: str, *, status: str | None = None
    ) -> list[ClaimRecord]:
        if status is None:
            rows = self._conn.execute(
                """
                SELECT id, source_id, chunk_id, claim_text, statement_type, subject,
                       predicate, object, scope, evidence_type, confidence,
                       limitations_json, domain, domain_metadata_json, status,
                       rejection_reason, created_at, updated_at
                FROM claims
                WHERE source_id = ?
                ORDER BY created_at
                """,
                (source_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT id, source_id, chunk_id, claim_text, statement_type, subject,
                       predicate, object, scope, evidence_type, confidence,
                       limitations_json, domain, domain_metadata_json, status,
                       rejection_reason, created_at, updated_at
                FROM claims
                WHERE source_id = ? AND status = ?
                ORDER BY created_at
                """,
                (source_id, status),
            ).fetchall()
        return [_row_to_claim(row) for row in rows]

    def count_for_source(self, source_id: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ?",
            (source_id,),
        ).fetchone()
        return int(row[0]) if row else 0

    def list_quotes_for_claim(self, claim_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT id, claim_id, source_id, chunk_id, quote_text, char_start,
                   char_end, page, is_primary, created_at
            FROM claim_quotes
            WHERE claim_id = ?
            """,
            (claim_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def insert_accepted(
        self,
        claim: dict[str, Any],
        *,
        extractor_provider: str,
        extractor_model: str,
        llm_schema_version: str,
    ) -> ClaimRecord:
        now = utc_now_iso()
        claim_id = make_claim_id(
            claim["source_id"], claim["chunk_id"], claim["claim_text"]
        )
        limitations = claim.get("limitations") or []
        domain_metadata = claim.get("domain_metadata") or {}

        self._conn.execute(
            """
            INSERT INTO claims (
                id, source_id, chunk_id, claim_text, statement_type, subject,
                predicate, object, scope, evidence_type, confidence,
                limitations_json, domain, domain_metadata_json, status,
                rejection_reason, rejection_details_json, extractor_model,
                extractor_provider, llm_schema_version, prompt_template_version,
                validator_version, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (
                claim_id,
                claim["source_id"],
                claim["chunk_id"],
                claim["claim_text"],
                "source_claim",
                claim["subject"],
                claim["predicate"],
                claim["object"],
                claim["scope"],
                claim["evidence_type"],
                float(claim["confidence"]),
                json.dumps(limitations),
                claim["domain"],
                json.dumps(domain_metadata),
                "accepted",
                extractor_model,
                extractor_provider,
                llm_schema_version,
                "0.1.0",
                self.VALIDATOR_VERSION,
                now,
                now,
            ),
        )

        quote_text = str(claim["quote_span"])
        quote_id = make_quote_id(claim_id, quote_text)
        self._conn.execute(
            """
            INSERT INTO claim_quotes (
                id, claim_id, source_id, chunk_id, quote_text, char_start,
                char_end, page, is_primary, created_at
            ) VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, 1, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (
                quote_id,
                claim_id,
                claim["source_id"],
                claim["chunk_id"],
                quote_text,
                now,
            ),
        )
        self._conn.commit()
        record = self.get_by_id(claim_id)
        assert record is not None
        return record

    def insert_rejected(
        self,
        claim: dict[str, Any],
        *,
        rejection_reason: str,
        extractor_provider: str,
        extractor_model: str,
        llm_schema_version: str,
    ) -> ClaimRecord:
        now = utc_now_iso()
        claim_text = claim.get("claim_text") or "(invalid claim)"
        source_id = claim.get("source_id") or "src_unknown"
        chunk_id = claim.get("chunk_id") or "chk_unknown"
        claim_id = make_claim_id(source_id, chunk_id, claim_text)
        limitations = claim.get("limitations") or []
        domain_metadata = claim.get("domain_metadata") or {}

        self._conn.execute(
            """
            INSERT INTO claims (
                id, source_id, chunk_id, claim_text, statement_type, subject,
                predicate, object, scope, evidence_type, confidence,
                limitations_json, domain, domain_metadata_json, status,
                rejection_reason, rejection_details_json, extractor_model,
                extractor_provider, llm_schema_version, prompt_template_version,
                validator_version, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (
                claim_id,
                source_id,
                chunk_id,
                claim_text,
                "source_claim",
                claim.get("subject"),
                claim.get("predicate"),
                claim.get("object"),
                claim.get("scope"),
                claim.get("evidence_type"),
                claim.get("confidence"),
                json.dumps(limitations),
                claim.get("domain"),
                json.dumps(domain_metadata),
                "rejected",
                rejection_reason,
                extractor_model,
                extractor_provider,
                llm_schema_version,
                "0.1.0",
                self.VALIDATOR_VERSION,
                now,
                now,
            ),
        )
        self._conn.commit()
        record = self.get_by_id(claim_id)
        assert record is not None
        return record


def ontology_id_to_concept_id(ontology_id: str) -> str:
    return f"cpt_{ontology_id.removeprefix('concept_')}"


def make_claim_concept_link_id(claim_id: str, concept_id: str, role: str) -> str:
    digest = sha256_hex(f"{claim_id}:{concept_id}:{role}")
    return f"ccl_{digest[:16]}"


@dataclass(frozen=True)
class ConceptRecord:
    id: str
    label: str
    definition: str
    domain: str
    status: str
    created_at: str
    updated_at: str
    domain_metadata_json: str = "{}"


class ConceptRepository:
    """Persist and read ``concepts`` rows seeded from domain packs."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get_by_label(self, domain: str, label: str) -> ConceptRecord | None:
        normalized = label.strip().casefold()
        rows = self._conn.execute(
            """
            SELECT id, label, definition, domain, status, domain_metadata_json,
                   created_at, updated_at
            FROM concepts
            WHERE domain = ?
            """,
            (domain,),
        ).fetchall()
        for row in rows:
            if row["label"].strip().casefold() == normalized:
                return _row_to_concept(row)
        return None

    def ensure_domain_concepts(self, domain_pack: str) -> list[ConceptRecord]:
        from rge.modules.concept_linker import load_domain_pack_concepts

        now = utc_now_iso()
        ensured: list[ConceptRecord] = []
        for concept in load_domain_pack_concepts(domain_pack):
            concept_id = ontology_id_to_concept_id(concept["id"])
            existing = self._conn.execute(
                "SELECT id FROM concepts WHERE id = ?",
                (concept_id,),
            ).fetchone()
            if existing is None:
                self._conn.execute(
                    """
                    INSERT INTO concepts (
                        id, label, definition, domain, domain_metadata_json,
                        status, parent_concept_id, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, '{}', ?, NULL, ?, ?)
                    """,
                    (
                        concept_id,
                        concept["label"],
                        concept.get("definition", ""),
                        domain_pack,
                        concept.get("status", "candidate"),
                        now,
                        now,
                    ),
                )
            record = self.get_by_label(domain_pack, concept["label"])
            if record is not None:
                ensured.append(record)
        self._conn.commit()
        return ensured


class ClaimConceptRepository:
    """Persist and read ``claim_concepts`` rows."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def count_for_source(self, source_id: str) -> int:
        row = self._conn.execute(
            """
            SELECT COUNT(*)
            FROM claim_concepts cc
            JOIN claims c ON c.id = cc.claim_id
            WHERE c.source_id = ?
            """,
            (source_id,),
        ).fetchone()
        return int(row[0]) if row else 0

    def list_for_source(self, source_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT cc.id, cc.claim_id, cc.concept_id, cc.role, cc.confidence,
                   cc.domain_metadata_json, cc.created_at, concepts.label AS concept_label
            FROM claim_concepts cc
            JOIN claims c ON c.id = cc.claim_id
            JOIN concepts ON concepts.id = cc.concept_id
            WHERE c.source_id = ?
            ORDER BY cc.created_at
            """,
            (source_id,),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "claim_id": row["claim_id"],
                "concept_id": row["concept_id"],
                "concept_label": row["concept_label"],
                "role": row["role"],
                "confidence": row["confidence"],
                "domain_metadata": json.loads(row["domain_metadata_json"] or "{}"),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def insert(
        self,
        *,
        claim_id: str,
        concept_id: str,
        role: str,
        confidence: float,
        domain_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        now = utc_now_iso()
        link_id = make_claim_concept_link_id(claim_id, concept_id, role)
        self._conn.execute(
            """
            INSERT INTO claim_concepts (
                id, claim_id, concept_id, role, confidence,
                domain_metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(claim_id, concept_id, role) DO NOTHING
            """,
            (
                link_id,
                claim_id,
                concept_id,
                role,
                confidence,
                json.dumps(domain_metadata),
                now,
            ),
        )
        self._conn.commit()
        return {
            "id": link_id,
            "claim_id": claim_id,
            "concept_id": concept_id,
            "role": role,
            "confidence": confidence,
            "domain_metadata": domain_metadata,
            "created_at": now,
        }


def _row_to_concept(row: sqlite3.Row) -> ConceptRecord:
    return ConceptRecord(
        id=row["id"],
        label=row["label"],
        definition=row["definition"] or "",
        domain=row["domain"],
        status=row["status"],
        domain_metadata_json=row["domain_metadata_json"] or "{}",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_claim(row: sqlite3.Row) -> ClaimRecord:
    return ClaimRecord(
        id=row["id"],
        source_id=row["source_id"],
        chunk_id=row["chunk_id"],
        claim_text=row["claim_text"],
        statement_type=row["statement_type"] or "source_claim",
        subject=row["subject"] or "",
        predicate=row["predicate"] or "",
        object=row["object"] or "",
        scope=row["scope"] or "",
        evidence_type=row["evidence_type"] or "",
        confidence=float(row["confidence"] or 0.0),
        limitations_json=row["limitations_json"] or "[]",
        domain=row["domain"] or "",
        domain_metadata_json=row["domain_metadata_json"] or "{}",
        status=row["status"],
        rejection_reason=row["rejection_reason"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def claim_record_to_public_dict(claim: ClaimRecord) -> dict[str, Any]:
    """Return a JSON-serializable claim view."""
    return {
        "id": claim.id,
        "source_id": claim.source_id,
        "chunk_id": claim.chunk_id,
        "claim_text": claim.claim_text,
        "subject": claim.subject,
        "predicate": claim.predicate,
        "object": claim.object,
        "scope": claim.scope,
        "evidence_type": claim.evidence_type,
        "confidence": claim.confidence,
        "limitations": json.loads(claim.limitations_json),
        "domain": claim.domain,
        "status": claim.status,
        "rejection_reason": claim.rejection_reason,
        "created_at": claim.created_at,
        "updated_at": claim.updated_at,
    }


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
