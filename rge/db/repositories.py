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

    def list_accepted_for_domain(self, domain: str) -> list[ClaimRecord]:
        rows = self._conn.execute(
            """
            SELECT id, source_id, chunk_id, claim_text, statement_type, subject,
                   predicate, object, scope, evidence_type, confidence,
                   limitations_json, domain, domain_metadata_json, status,
                   rejection_reason, created_at, updated_at
            FROM claims
            WHERE domain = ? AND status = 'accepted'
            ORDER BY created_at
            """,
            (domain,),
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

    def list_for_domain(self, domain: str) -> list[ConceptRecord]:
        rows = self._conn.execute(
            """
            SELECT id, label, definition, domain, status, domain_metadata_json,
                   created_at, updated_at
            FROM concepts
            WHERE domain = ?
            ORDER BY label
            """,
            (domain,),
        ).fetchall()
        return [_row_to_concept(row) for row in rows]


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


def make_relationship_id(
    subject_concept_id: str, predicate: str, object_concept_id: str, scope: str
) -> str:
    digest = sha256_hex(
        f"{subject_concept_id}:{predicate}:{object_concept_id}:{scope}"
    )
    return f"rel_{digest[:16]}"


def make_relationship_evidence_id(
    relationship_id: str, claim_id: str, stance: str
) -> str:
    digest = sha256_hex(f"{relationship_id}:{claim_id}:{stance}")
    return f"rev_{digest[:16]}"


class RelationshipRepository:
    """Persist and read ``relationships`` rows."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def count_for_source(self, source_id: str) -> int:
        row = self._conn.execute(
            """
            SELECT COUNT(DISTINCT re.relationship_id)
            FROM relationship_evidence re
            JOIN claims c ON c.id = re.claim_id
            WHERE c.source_id = ?
            """,
            (source_id,),
        ).fetchone()
        return int(row[0]) if row else 0

    def list_for_source(self, source_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT DISTINCT r.id, r.subject_concept_id, r.predicate,
                   r.object_concept_id, r.scope, r.confidence,
                   r.evidence_strength, r.domain, r.domain_metadata_json,
                   r.status, r.created_at, r.updated_at,
                   sub.label AS subject_label, obj.label AS object_label
            FROM relationships r
            JOIN relationship_evidence re ON re.relationship_id = r.id
            JOIN claims c ON c.id = re.claim_id
            JOIN concepts sub ON sub.id = r.subject_concept_id
            JOIN concepts obj ON obj.id = r.object_concept_id
            WHERE c.source_id = ?
            ORDER BY r.created_at
            """,
            (source_id,),
        ).fetchall()
        return [_row_to_relationship(row) for row in rows]

    def get_by_id(self, relationship_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            """
            SELECT r.id, r.subject_concept_id, r.predicate, r.object_concept_id,
                   r.scope, r.confidence, r.evidence_strength, r.domain,
                   r.domain_metadata_json, r.status, r.created_at, r.updated_at,
                   sub.label AS subject_label, obj.label AS object_label
            FROM relationships r
            JOIN concepts sub ON sub.id = r.subject_concept_id
            JOIN concepts obj ON obj.id = r.object_concept_id
            WHERE r.id = ?
            """,
            (relationship_id,),
        ).fetchone()
        return _row_to_relationship(row) if row else None

    def insert(
        self,
        *,
        subject_concept_id: str,
        predicate: str,
        object_concept_id: str,
        scope: str,
        confidence: float,
        domain: str,
        status: str,
        evidence_strength: float | None = None,
        domain_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        now = utc_now_iso()
        relationship_id = make_relationship_id(
            subject_concept_id, predicate, object_concept_id, scope
        )
        self._conn.execute(
            """
            INSERT INTO relationships (
                id, subject_concept_id, predicate, object_concept_id, scope,
                confidence, evidence_strength, domain, domain_metadata_json,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (
                relationship_id,
                subject_concept_id,
                predicate,
                object_concept_id,
                scope,
                confidence,
                evidence_strength,
                domain,
                json.dumps(domain_metadata or {}),
                status,
                now,
                now,
            ),
        )
        self._conn.commit()
        record = self.get_by_id(relationship_id)
        assert record is not None
        return record

    def list_active(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT r.id, r.subject_concept_id, r.predicate, r.object_concept_id,
                   r.scope, r.confidence, r.evidence_strength, r.domain,
                   r.domain_metadata_json, r.status, r.created_at, r.updated_at,
                   sub.label AS subject_label, obj.label AS object_label
            FROM relationships r
            JOIN concepts sub ON sub.id = r.subject_concept_id
            JOIN concepts obj ON obj.id = r.object_concept_id
            WHERE r.status = 'active'
            ORDER BY r.created_at
            """
        ).fetchall()
        return [_row_to_relationship(row) for row in rows]

    def merge_domain_metadata(
        self,
        relationship_id: str,
        patch: dict[str, Any],
    ) -> dict[str, Any]:
        existing = self.get_by_id(relationship_id)
        if existing is None:
            raise ValueError(f"Relationship not found: {relationship_id}")
        metadata = json.loads(existing.get("domain_metadata_json") or "{}")
        metadata.update(patch)
        now = utc_now_iso()
        self._conn.execute(
            """
            UPDATE relationships
            SET domain_metadata_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (json.dumps(metadata), now, relationship_id),
        )
        self._conn.commit()
        updated = self.get_by_id(relationship_id)
        assert updated is not None
        return updated

    def find_active_by_triple(
        self,
        *,
        subject_concept: str,
        predicate: str,
        object_concept: str,
    ) -> dict[str, Any] | None:
        subject_norm = subject_concept.strip().casefold()
        predicate_norm = predicate.strip().casefold()
        object_norm = object_concept.strip().casefold()
        for relationship in self.list_active():
            if (
                relationship["subject_concept"].strip().casefold() == subject_norm
                and relationship["predicate"].strip().casefold() == predicate_norm
                and relationship["object_concept"].strip().casefold() == object_norm
            ):
                return relationship
        return None


class RelationshipEvidenceRepository:
    """Persist and read ``relationship_evidence`` rows."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def list_for_relationship(self, relationship_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT id, relationship_id, claim_id, stance, relevance_score, created_at
            FROM relationship_evidence
            WHERE relationship_id = ?
            ORDER BY created_at
            """,
            (relationship_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_for_source(self, source_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT re.id, re.relationship_id, re.claim_id, re.stance,
                   re.relevance_score, re.created_at
            FROM relationship_evidence re
            JOIN claims c ON c.id = re.claim_id
            WHERE c.source_id = ?
            ORDER BY re.created_at
            """,
            (source_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def insert(
        self,
        *,
        relationship_id: str,
        claim_id: str,
        stance: str,
        relevance_score: float | None = None,
    ) -> dict[str, Any]:
        now = utc_now_iso()
        evidence_id = make_relationship_evidence_id(relationship_id, claim_id, stance)
        self._conn.execute(
            """
            INSERT INTO relationship_evidence (
                id, relationship_id, claim_id, stance, relevance_score, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(relationship_id, claim_id, stance) DO NOTHING
            """,
            (
                evidence_id,
                relationship_id,
                claim_id,
                stance,
                relevance_score,
                now,
            ),
        )
        self._conn.commit()
        row = self._conn.execute(
            """
            SELECT id, relationship_id, claim_id, stance, relevance_score, created_at
            FROM relationship_evidence
            WHERE id = ?
            """,
            (evidence_id,),
        ).fetchone()
        assert row is not None
        return dict(row)

    def has_link(
        self, *, relationship_id: str, claim_id: str, stance: str
    ) -> bool:
        row = self._conn.execute(
            """
            SELECT 1 FROM relationship_evidence
            WHERE relationship_id = ? AND claim_id = ? AND stance = ?
            """,
            (relationship_id, claim_id, stance),
        ).fetchone()
        return row is not None


def make_score_event_id(
    entity_type: str,
    entity_id: str,
    triggering_claim_id: str,
    old_score: float,
    new_score: float,
) -> str:
    digest = sha256_hex(
        f"{entity_type}:{entity_id}:{triggering_claim_id}:{old_score}:{new_score}"
    )
    return f"sce_{digest[:16]}"


class ScoreEventRepository:
    """Persist and read append-only ``score_events`` rows."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def has_triggering_claim(
        self, *, entity_type: str, entity_id: str, triggering_claim_id: str
    ) -> bool:
        row = self._conn.execute(
            """
            SELECT 1 FROM score_events
            WHERE entity_type = ? AND entity_id = ? AND triggering_claim_id = ?
            """,
            (entity_type, entity_id, triggering_claim_id),
        ).fetchone()
        return row is not None

    def list_for_entity(self, entity_type: str, entity_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT id, entity_type, entity_id, old_score, new_score,
                   triggering_claim_id, triggering_source_id, reason,
                   formula_version, created_at
            FROM score_events
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY created_at
            """,
            (entity_type, entity_id),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_for_source(self, source_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT id, entity_type, entity_id, old_score, new_score,
                   triggering_claim_id, triggering_source_id, reason,
                   formula_version, created_at
            FROM score_events
            WHERE triggering_source_id = ?
            ORDER BY created_at
            """,
            (source_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_all(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT id, entity_type, entity_id, old_score, new_score,
                   triggering_claim_id, triggering_source_id, reason,
                   formula_version, created_at
            FROM score_events
            ORDER BY created_at DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]


def make_cluster_report_id(cluster_id: str, cluster_label: str) -> str:
    digest = sha256_hex(f"{cluster_id}:{cluster_label}")
    return f"crpt_{digest[:16]}"


@dataclass(frozen=True)
class ClusterReportRecord:
    id: str
    run_id: str | None
    cluster_label: str
    included_concepts_json: str
    evidence_packet_json: str
    report_json: str
    prose_summary: str | None
    created_at: str


class ClusterReportRepository:
    """Persist and read ``cluster_reports`` rows."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get_by_id(self, report_id: str) -> ClusterReportRecord | None:
        row = self._conn.execute(
            """
            SELECT id, run_id, cluster_label, included_concepts_json,
                   evidence_packet_json, report_json, prose_summary, created_at
            FROM cluster_reports
            WHERE id = ?
            """,
            (report_id,),
        ).fetchone()
        return _row_to_cluster_report(row) if row else None

    def get_latest_for_label(self, cluster_label: str) -> ClusterReportRecord | None:
        row = self._conn.execute(
            """
            SELECT id, run_id, cluster_label, included_concepts_json,
                   evidence_packet_json, report_json, prose_summary, created_at
            FROM cluster_reports
            WHERE cluster_label = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (cluster_label,),
        ).fetchone()
        return _row_to_cluster_report(row) if row else None

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM cluster_reports").fetchone()
        return int(row[0]) if row else 0

    def insert(
        self,
        *,
        cluster_id: str,
        cluster_label: str,
        included_concepts: list[str],
        evidence_packet: dict[str, Any],
        report: dict[str, Any],
        prose_summary: str | None = None,
        run_id: str | None = None,
    ) -> ClusterReportRecord:
        now = utc_now_iso()
        report_id = make_cluster_report_id(cluster_id, cluster_label)
        self._conn.execute(
            """
            INSERT INTO cluster_reports (
                id, run_id, cluster_label, included_concepts_json,
                evidence_packet_json, report_json, prose_summary, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (
                report_id,
                run_id,
                cluster_label,
                json.dumps(included_concepts),
                json.dumps(evidence_packet),
                json.dumps(report),
                prose_summary,
                now,
            ),
        )
        self._conn.commit()
        record = self.get_by_id(report_id)
        assert record is not None
        return record


def _row_to_cluster_report(row: sqlite3.Row) -> ClusterReportRecord:
    return ClusterReportRecord(
        id=row["id"],
        run_id=row["run_id"],
        cluster_label=row["cluster_label"],
        included_concepts_json=row["included_concepts_json"],
        evidence_packet_json=row["evidence_packet_json"],
        report_json=row["report_json"],
        prose_summary=row["prose_summary"],
        created_at=row["created_at"],
    )


def make_theory_candidate_id(cluster_report_id: str, theory_text: str) -> str:
    digest = sha256_hex(f"{cluster_report_id}:{theory_text}")
    return f"thc_{digest[:16]}"


@dataclass(frozen=True)
class TheoryCandidateRecord:
    id: str
    run_id: str | None
    cluster_report_id: str | None
    theory_text: str
    confidence: str
    supporting_claims_json: str
    contradicting_or_qualifying_claims_json: str
    boundary_conditions_json: str
    weakening_evidence_json: str
    next_questions_json: str
    status: str
    report_json: str
    created_at: str
    updated_at: str


class TheoryCandidateRepository:
    """Persist and read ``theory_candidates`` rows."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get_by_id(self, theory_id: str) -> TheoryCandidateRecord | None:
        row = self._conn.execute(
            """
            SELECT id, run_id, cluster_report_id, theory_text, confidence,
                   supporting_claims_json, contradicting_or_qualifying_claims_json,
                   boundary_conditions_json, weakening_evidence_json,
                   next_questions_json, status, report_json, created_at, updated_at
            FROM theory_candidates
            WHERE id = ?
            """,
            (theory_id,),
        ).fetchone()
        return _row_to_theory_candidate(row) if row else None

    def list_for_cluster_report(
        self, cluster_report_id: str
    ) -> list[TheoryCandidateRecord]:
        rows = self._conn.execute(
            """
            SELECT id, run_id, cluster_report_id, theory_text, confidence,
                   supporting_claims_json, contradicting_or_qualifying_claims_json,
                   boundary_conditions_json, weakening_evidence_json,
                   next_questions_json, status, report_json, created_at, updated_at
            FROM theory_candidates
            WHERE cluster_report_id = ?
            ORDER BY created_at
            """,
            (cluster_report_id,),
        ).fetchall()
        return [_row_to_theory_candidate(row) for row in rows]

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM theory_candidates").fetchone()
        return int(row[0]) if row else 0

    def insert(
        self,
        *,
        cluster_report_id: str,
        theory_text: str,
        confidence: str,
        supporting_claims: list[str],
        contradicting_or_qualifying_claims: list[str],
        boundary_conditions: list[str],
        weakening_evidence: list[str],
        next_questions: list[str],
        report: dict[str, Any],
        run_id: str | None = None,
        status: str = "candidate",
    ) -> TheoryCandidateRecord:
        now = utc_now_iso()
        theory_id = make_theory_candidate_id(cluster_report_id, theory_text)
        self._conn.execute(
            """
            INSERT INTO theory_candidates (
                id, run_id, cluster_report_id, theory_text, confidence,
                supporting_claims_json, contradicting_or_qualifying_claims_json,
                boundary_conditions_json, weakening_evidence_json,
                next_questions_json, status, report_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (
                theory_id,
                run_id,
                cluster_report_id,
                theory_text,
                confidence,
                json.dumps(supporting_claims),
                json.dumps(contradicting_or_qualifying_claims),
                json.dumps(boundary_conditions),
                json.dumps(weakening_evidence),
                json.dumps(next_questions),
                status,
                json.dumps(report),
                now,
                now,
            ),
        )
        self._conn.commit()
        record = self.get_by_id(theory_id)
        assert record is not None
        return record


def _row_to_theory_candidate(row: sqlite3.Row) -> TheoryCandidateRecord:
    return TheoryCandidateRecord(
        id=row["id"],
        run_id=row["run_id"],
        cluster_report_id=row["cluster_report_id"],
        theory_text=row["theory_text"],
        confidence=row["confidence"],
        supporting_claims_json=row["supporting_claims_json"],
        contradicting_or_qualifying_claims_json=row[
            "contradicting_or_qualifying_claims_json"
        ],
        boundary_conditions_json=row["boundary_conditions_json"],
        weakening_evidence_json=row["weakening_evidence_json"],
        next_questions_json=row["next_questions_json"],
        status=row["status"],
        report_json=row["report_json"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def make_ontology_proposal_id(candidate_concept: str, proposal_type: str) -> str:
    digest = sha256_hex(f"{candidate_concept}:{proposal_type}")
    return f"ont_{digest[:16]}"


@dataclass(frozen=True)
class OntologyProposalRecord:
    id: str
    proposal_type: str
    candidate_concept: str | None
    status: str
    evidence_claims_json: str
    reason: str
    proposal_json: str
    created_at: str
    updated_at: str


class OntologyProposalRepository:
    """Persist and read ``ontology_proposals`` rows."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get_by_id(self, proposal_id: str) -> OntologyProposalRecord | None:
        row = self._conn.execute(
            """
            SELECT id, proposal_type, candidate_concept, status,
                   evidence_claims_json, reason, proposal_json,
                   created_at, updated_at
            FROM ontology_proposals
            WHERE id = ?
            """,
            (proposal_id,),
        ).fetchone()
        return _row_to_ontology_proposal(row) if row else None

    def get_latest_for_candidate(
        self, candidate_concept: str
    ) -> OntologyProposalRecord | None:
        row = self._conn.execute(
            """
            SELECT id, proposal_type, candidate_concept, status,
                   evidence_claims_json, reason, proposal_json,
                   created_at, updated_at
            FROM ontology_proposals
            WHERE candidate_concept = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (candidate_concept,),
        ).fetchone()
        return _row_to_ontology_proposal(row) if row else None

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM ontology_proposals").fetchone()
        return int(row[0]) if row else 0

    def insert(
        self,
        *,
        proposal_type: str,
        candidate_concept: str,
        status: str,
        evidence_claims: list[str],
        reason: str,
        proposal: dict[str, Any],
    ) -> OntologyProposalRecord:
        now = utc_now_iso()
        proposal_id = make_ontology_proposal_id(candidate_concept, proposal_type)
        self._conn.execute(
            """
            INSERT INTO ontology_proposals (
                id, proposal_type, candidate_concept, status,
                evidence_claims_json, reason, proposal_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (
                proposal_id,
                proposal_type,
                candidate_concept,
                status,
                json.dumps(evidence_claims),
                reason,
                json.dumps(proposal),
                now,
                now,
            ),
        )
        self._conn.commit()
        record = self.get_by_id(proposal_id)
        assert record is not None
        return record


def _row_to_ontology_proposal(row: sqlite3.Row) -> OntologyProposalRecord:
    return OntologyProposalRecord(
        id=row["id"],
        proposal_type=row["proposal_type"],
        candidate_concept=row["candidate_concept"],
        status=row["status"],
        evidence_claims_json=row["evidence_claims_json"],
        reason=row["reason"],
        proposal_json=row["proposal_json"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def make_domain_proposal_id(domain_id: str) -> str:
    digest = sha256_hex(domain_id)
    return f"dpr_{digest[:16]}"


@dataclass(frozen=True)
class DomainProposalRecord:
    id: str
    domain_id: str
    status: str
    parent_domains_json: str
    overlap_domains_json: str
    specialized_terms_json: str
    scoring_overlay_proposals_json: str
    evidence_claims_json: str
    threshold_report_json: str
    proposal_json: str
    created_at: str
    updated_at: str


class DomainProposalRepository:
    """Persist and read ``domain_proposals`` rows."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get_by_id(self, proposal_id: str) -> DomainProposalRecord | None:
        row = self._conn.execute(
            """
            SELECT id, domain_id, status, parent_domains_json, overlap_domains_json,
                   specialized_terms_json, scoring_overlay_proposals_json,
                   evidence_claims_json, threshold_report_json, created_at, updated_at
            FROM domain_proposals
            WHERE id = ?
            """,
            (proposal_id,),
        ).fetchone()
        return _row_to_domain_proposal(row) if row else None

    def get_latest_for_domain(self, domain_id: str) -> DomainProposalRecord | None:
        row = self._conn.execute(
            """
            SELECT id, domain_id, status, parent_domains_json, overlap_domains_json,
                   specialized_terms_json, scoring_overlay_proposals_json,
                   evidence_claims_json, threshold_report_json, created_at, updated_at
            FROM domain_proposals
            WHERE domain_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (domain_id,),
        ).fetchone()
        return _row_to_domain_proposal(row) if row else None

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM domain_proposals").fetchone()
        return int(row[0]) if row else 0

    def insert(
        self,
        *,
        domain_id: str,
        status: str,
        parent_domains: list[str],
        overlap_domains: list[str],
        specialized_terms: list[str],
        scoring_overlay_proposals: list[str],
        evidence_claims: list[str],
        threshold_report: dict[str, Any],
        proposal: dict[str, Any],
    ) -> DomainProposalRecord:
        now = utc_now_iso()
        proposal_id = make_domain_proposal_id(domain_id)
        self._conn.execute(
            """
            INSERT INTO domain_proposals (
                id, domain_id, status, parent_domains_json, overlap_domains_json,
                specialized_terms_json, scoring_overlay_proposals_json,
                evidence_claims_json, threshold_report_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (
                proposal_id,
                domain_id,
                status,
                json.dumps(parent_domains),
                json.dumps(overlap_domains),
                json.dumps(specialized_terms),
                json.dumps(scoring_overlay_proposals),
                json.dumps(evidence_claims),
                json.dumps(threshold_report),
                now,
                now,
            ),
        )
        self._conn.commit()
        record = self.get_by_id(proposal_id)
        assert record is not None
        return record


def _row_to_domain_proposal(row: sqlite3.Row) -> DomainProposalRecord:
    threshold_report = json.loads(row["threshold_report_json"])
    proposal = {
        "report_type": "domain_proposal_report",
        "domain_id": row["domain_id"],
        "status": row["status"],
        "thresholds": threshold_report.get("thresholds", threshold_report),
        "parent_domains": json.loads(row["parent_domains_json"]),
        "overlap_domains": json.loads(row["overlap_domains_json"]),
        "specialized_terms": json.loads(row["specialized_terms_json"]),
        "scoring_overlay_proposals": json.loads(
            row["scoring_overlay_proposals_json"]
        ),
        "evidence_claims": json.loads(row["evidence_claims_json"]),
        "reason_parent_domain_is_underspecified": threshold_report.get(
            "reason_parent_domain_is_underspecified", ""
        ),
        "ontology_rationale": threshold_report.get("ontology_rationale", ""),
    }
    return DomainProposalRecord(
        id=row["id"],
        domain_id=row["domain_id"],
        status=row["status"],
        parent_domains_json=row["parent_domains_json"],
        overlap_domains_json=row["overlap_domains_json"],
        specialized_terms_json=row["specialized_terms_json"],
        scoring_overlay_proposals_json=row["scoring_overlay_proposals_json"],
        evidence_claims_json=row["evidence_claims_json"],
        threshold_report_json=row["threshold_report_json"],
        proposal_json=json.dumps(proposal),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def persist_relationship_score_update(
    conn: sqlite3.Connection,
    *,
    relationship_id: str,
    old_score: float,
    new_score: float,
    triggering_claim_id: str,
    triggering_source_id: str,
    reason: str,
    formula_version: str,
    add_evidence: bool,
    evidence_relevance_score: float | None = None,
) -> dict[str, Any]:
    """Atomically append score history and update relationship confidence."""
    now = utc_now_iso()
    event_id = make_score_event_id(
        "relationship",
        relationship_id,
        triggering_claim_id,
        old_score,
        new_score,
    )
    conn.execute(
        """
        INSERT INTO score_events (
            id, entity_type, entity_id, old_score, new_score,
            triggering_claim_id, triggering_source_id, reason,
            formula_version, created_at
        ) VALUES (?, 'relationship', ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            relationship_id,
            old_score,
            new_score,
            triggering_claim_id,
            triggering_source_id,
            reason,
            formula_version,
            now,
        ),
    )
    conn.execute(
        """
        UPDATE relationships
        SET confidence = ?, updated_at = ?
        WHERE id = ?
        """,
        (new_score, now, relationship_id),
    )
    if add_evidence:
        evidence_id = make_relationship_evidence_id(
            relationship_id, triggering_claim_id, "supports"
        )
        conn.execute(
            """
            INSERT INTO relationship_evidence (
                id, relationship_id, claim_id, stance, relevance_score, created_at
            ) VALUES (?, ?, ?, 'supports', ?, ?)
            ON CONFLICT(relationship_id, claim_id, stance) DO NOTHING
            """,
            (
                evidence_id,
                relationship_id,
                triggering_claim_id,
                evidence_relevance_score,
                now,
            ),
        )
    conn.commit()
    row = conn.execute(
        """
        SELECT id, entity_type, entity_id, old_score, new_score,
               triggering_claim_id, triggering_source_id, reason,
               formula_version, created_at
        FROM score_events
        WHERE id = ?
        """,
        (event_id,),
    ).fetchone()
    assert row is not None
    return dict(row)


def _row_to_relationship(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "subject_concept_id": row["subject_concept_id"],
        "object_concept_id": row["object_concept_id"],
        "subject_concept": row["subject_label"],
        "object_concept": row["object_label"],
        "predicate": row["predicate"],
        "scope": row["scope"],
        "confidence": row["confidence"],
        "evidence_strength": row["evidence_strength"],
        "domain": row["domain"],
        "domain_metadata": json.loads(row["domain_metadata_json"] or "{}"),
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
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


def make_research_queue_id(
    candidate_source_id: str, research_question_id: str
) -> str:
    digest = sha256_hex(f"{candidate_source_id}:{research_question_id}")
    return f"que_{digest[:16]}"


def make_followup_queue_id(contract_id: str, question_text: str) -> str:
    digest = sha256_hex(f"{contract_id}:{question_text.strip().casefold()}")
    return f"que_{digest[:16]}"


class ResearchContractRepository:
    """Persist and read ``research_contracts`` rows."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get_by_id(self, contract_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            """
            SELECT id, root_topic, primary_question, domain_pack,
                   allowed_concepts_json, adjacent_concepts_json,
                   out_of_scope_concepts_json, source_budget, search_budget,
                   follow_up_depth, drift_threshold, success_criteria_json,
                   source_strategy_json, evidence_requirements_json,
                   queue_priority_formula, topic_drift_formula, status,
                   created_at, updated_at
            FROM research_contracts
            WHERE id = ?
            """,
            (contract_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "root_topic": row["root_topic"],
            "primary_question": row["primary_question"],
            "domain_pack": row["domain_pack"],
            "allowed_concepts": json.loads(row["allowed_concepts_json"] or "[]"),
            "adjacent_concepts": json.loads(row["adjacent_concepts_json"] or "[]"),
            "out_of_scope_concepts": json.loads(
                row["out_of_scope_concepts_json"] or "[]"
            ),
            "source_budget": row["source_budget"],
            "search_budget": row["search_budget"],
            "follow_up_depth": row["follow_up_depth"],
            "drift_threshold": row["drift_threshold"],
            "success_criteria": json.loads(row["success_criteria_json"] or "[]"),
            "source_strategy": json.loads(row["source_strategy_json"] or "{}"),
            "evidence_requirements": json.loads(
                row["evidence_requirements_json"] or "{}"
            ),
            "queue_priority_formula": row["queue_priority_formula"],
            "topic_drift_formula": row["topic_drift_formula"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def insert(self, contract: dict[str, Any]) -> dict[str, Any]:
        now = utc_now_iso()
        contract_id = contract["id"]
        self._conn.execute(
            """
            INSERT INTO research_contracts (
                id, root_topic, primary_question, domain_pack,
                allowed_concepts_json, adjacent_concepts_json,
                out_of_scope_concepts_json, source_budget, search_budget,
                follow_up_depth, drift_threshold, success_criteria_json,
                source_strategy_json, evidence_requirements_json,
                queue_priority_formula, topic_drift_formula, status,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (
                contract_id,
                contract.get("root_topic"),
                contract.get("primary_question"),
                contract.get("domain_pack"),
                json.dumps(contract.get("allowed_concepts", [])),
                json.dumps(contract.get("adjacent_concepts", [])),
                json.dumps(contract.get("out_of_scope_concepts", [])),
                contract.get("source_budget", 5),
                contract.get("search_budget", 10),
                contract.get("follow_up_depth", 1),
                contract.get("drift_threshold", 0.35),
                json.dumps(contract.get("success_criteria", [])),
                json.dumps(contract.get("source_strategy", {})),
                json.dumps(contract.get("evidence_requirements", {})),
                contract.get("queue_priority_formula", "golden_v0.1.0"),
                contract.get("topic_drift_formula", "golden_v0.1.0"),
                contract.get("status", "active"),
                now,
                now,
            ),
        )
        self._conn.commit()
        record = self.get_by_id(contract_id)
        assert record is not None
        return record


class CandidateSourceRepository:
    """Persist and read ``candidate_sources`` rows."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(
        self,
        *,
        candidate_id: str,
        research_question_id: str,
        contract_id: str | None,
        title: str,
        source_type: str,
        reason: str,
        relevance_score: float,
        credibility_prior: float,
        gap_fill_score: float,
        recency_score: float,
        source_diversity_score: float,
        novelty_score: float,
        drift_risk: float,
        priority_score: float,
        status: str,
        url: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now_iso()
        self._conn.execute(
            """
            INSERT INTO candidate_sources (
                id, research_question_id, contract_id, title, url, source_type,
                reason, relevance_score, credibility_prior, gap_fill_score,
                recency_score, source_diversity_score, novelty_score, drift_risk,
                priority_score, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (
                candidate_id,
                research_question_id,
                contract_id,
                title,
                url,
                source_type,
                reason,
                relevance_score,
                credibility_prior,
                gap_fill_score,
                recency_score,
                source_diversity_score,
                novelty_score,
                drift_risk,
                priority_score,
                status,
                now,
            ),
        )
        self._conn.commit()
        row = self._conn.execute(
            "SELECT * FROM candidate_sources WHERE id = ?",
            (candidate_id,),
        ).fetchone()
        assert row is not None
        return dict(row)

    def list_for_question(self, research_question_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT *
            FROM candidate_sources
            WHERE research_question_id = ?
            ORDER BY priority_score DESC
            """,
            (research_question_id,),
        ).fetchall()
        return [dict(row) for row in rows]


class ResearchQueueRepository:
    """Persist and read ``research_queue`` rows."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def count_for_question(self, research_question_id: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM research_queue WHERE research_question_id = ?",
            (research_question_id,),
        ).fetchone()
        return int(row[0]) if row else 0

    def insert(
        self,
        *,
        candidate_source_id: str,
        research_question_id: str,
        contract_id: str | None,
        priority_score: float,
        reason: str,
        status: str,
        item_type: str = "source",
    ) -> dict[str, Any]:
        now = utc_now_iso()
        queue_id = make_research_queue_id(candidate_source_id, research_question_id)
        self._conn.execute(
            """
            INSERT INTO research_queue (
                id, candidate_source_id, research_question_id, contract_id,
                item_type, priority_score, reason, status, attempt_count,
                last_error, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (
                queue_id,
                candidate_source_id,
                research_question_id,
                contract_id,
                item_type,
                priority_score,
                reason,
                status,
                now,
                now,
            ),
        )
        self._conn.commit()
        row = self._conn.execute(
            "SELECT * FROM research_queue WHERE id = ?",
            (queue_id,),
        ).fetchone()
        assert row is not None
        return dict(row)

    def get_followup(
        self, contract_id: str, question_text: str
    ) -> dict[str, Any] | None:
        queue_id = make_followup_queue_id(contract_id, question_text)
        row = self._conn.execute(
            "SELECT * FROM research_queue WHERE id = ?",
            (queue_id,),
        ).fetchone()
        return dict(row) if row else None

    def insert_followup(
        self,
        *,
        contract_id: str,
        question_text: str,
        priority_score: float,
        reason: str,
        status: str,
        research_question_id: str,
    ) -> dict[str, Any]:
        now = utc_now_iso()
        queue_id = make_followup_queue_id(contract_id, question_text)
        self._conn.execute(
            """
            INSERT INTO research_queue (
                id, candidate_source_id, research_question_id, contract_id,
                item_type, priority_score, reason, status, attempt_count,
                last_error, created_at, updated_at
            ) VALUES (?, NULL, ?, ?, 'question', ?, ?, ?, 0, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (
                queue_id,
                research_question_id,
                contract_id,
                priority_score,
                reason,
                status,
                question_text,
                now,
                now,
            ),
        )
        self._conn.commit()
        row = self._conn.execute(
            "SELECT * FROM research_queue WHERE id = ?",
            (queue_id,),
        ).fetchone()
        assert row is not None
        return dict(row)

    def list_followups_for_contract(self, contract_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT id, candidate_source_id, research_question_id, contract_id,
                   item_type, priority_score, reason, status, attempt_count,
                   last_error, created_at, updated_at
            FROM research_queue
            WHERE contract_id = ? AND item_type = 'question'
            ORDER BY priority_score DESC, created_at
            """,
            (contract_id,),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "candidate_source_id": row["candidate_source_id"],
                "research_question_id": row["research_question_id"],
                "contract_id": row["contract_id"],
                "item_type": row["item_type"],
                "priority_score": row["priority_score"],
                "reason": row["reason"],
                "status": row["status"],
                "attempt_count": row["attempt_count"],
                "question_text": row["last_error"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def count_followups_by_status(self, contract_id: str) -> dict[str, int]:
        rows = self._conn.execute(
            """
            SELECT status, COUNT(*) AS count
            FROM research_queue
            WHERE contract_id = ? AND item_type = 'question'
            GROUP BY status
            """,
            (contract_id,),
        ).fetchall()
        return {row["status"]: int(row["count"]) for row in rows}

    def list_for_question(self, research_question_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT q.id, q.candidate_source_id, q.research_question_id,
                   q.contract_id, q.item_type, q.priority_score, q.reason,
                   q.status, q.attempt_count, q.last_error, q.created_at,
                   q.updated_at, c.source_type, c.relevance_score,
                   c.credibility_prior, c.gap_fill_score, c.title
            FROM research_queue q
            JOIN candidate_sources c ON c.id = q.candidate_source_id
            WHERE q.research_question_id = ?
            ORDER BY q.priority_score DESC
            """,
            (research_question_id,),
        ).fetchall()
        return [
            {
                "id": row["id"],
                "candidate_source_id": row["candidate_source_id"],
                "research_question_id": row["research_question_id"],
                "contract_id": row["contract_id"],
                "item_type": row["item_type"],
                "priority_score": row["priority_score"],
                "reason": row["reason"],
                "status": row["status"],
                "attempt_count": row["attempt_count"],
                "last_error": row["last_error"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "source_type": row["source_type"],
                "relevance_score": row["relevance_score"],
                "credibility_prior": row["credibility_prior"],
                "gap_fill_score": row["gap_fill_score"],
                "title": row["title"],
            }
            for row in rows
        ]


@dataclass(frozen=True)
class PublicCardRecord:
    id: str
    type: str
    title: str
    summary: str
    confidence: str
    concepts_json: str
    source_count: int
    claim_ids_json: str
    public_detail_level: str
    is_public_safe: int
    private_fields_json: str
    created_at: str
    updated_at: str


class PublicCardRepository:
    """Persist and read ``public_cards`` rows."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def count_public_safe(self) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) FROM public_cards WHERE is_public_safe = 1"
        ).fetchone()
        return int(row[0]) if row else 0

    def get_by_id(self, card_id: str) -> PublicCardRecord | None:
        row = self._conn.execute(
            """
            SELECT id, type, title, summary, confidence, concepts_json,
                   source_count, claim_ids_json, public_detail_level,
                   is_public_safe, private_fields_json, created_at, updated_at
            FROM public_cards
            WHERE id = ?
            """,
            (card_id,),
        ).fetchone()
        return _row_to_public_card(row) if row else None

    def insert(
        self,
        *,
        card_id: str,
        card_type: str,
        title: str,
        summary: str,
        confidence: str,
        concepts: list[str],
        source_count: int,
        claim_ids: list[str],
        public_detail_level: str,
        is_public_safe: bool,
        private_fields: dict[str, Any] | None = None,
    ) -> PublicCardRecord:
        now = utc_now_iso()
        self._conn.execute(
            """
            INSERT INTO public_cards (
                id, type, title, summary, confidence, concepts_json,
                source_count, claim_ids_json, public_detail_level,
                is_public_safe, private_fields_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (
                card_id,
                card_type,
                title,
                summary,
                confidence,
                json.dumps(concepts),
                source_count,
                json.dumps(claim_ids),
                public_detail_level,
                1 if is_public_safe else 0,
                json.dumps(private_fields or {}),
                now,
                now,
            ),
        )
        self._conn.commit()
        record = self.get_by_id(card_id)
        assert record is not None
        return record

    def list_public_safe(self, limit: int = 100) -> list[PublicCardRecord]:
        rows = self._conn.execute(
            """
            SELECT id, type, title, summary, confidence, concepts_json,
                   source_count, claim_ids_json, public_detail_level,
                   is_public_safe, private_fields_json, created_at, updated_at
            FROM public_cards
            WHERE is_public_safe = 1
            ORDER BY updated_at DESC, id
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [_row_to_public_card(row) for row in rows]


def _row_to_public_card(row: sqlite3.Row) -> PublicCardRecord:
    return PublicCardRecord(
        id=row["id"],
        type=row["type"],
        title=row["title"],
        summary=row["summary"],
        confidence=row["confidence"],
        concepts_json=row["concepts_json"],
        source_count=int(row["source_count"]),
        claim_ids_json=row["claim_ids_json"],
        public_detail_level=row["public_detail_level"],
        is_public_safe=int(row["is_public_safe"]),
        private_fields_json=row["private_fields_json"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def public_card_record_to_export_dict(
    record: PublicCardRecord,
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map a DB record to curated public card JSON."""
    card: dict[str, Any] = {
        "id": record.id,
        "type": record.type,
        "title": record.title,
        "summary": record.summary,
        "confidence": record.confidence,
        "concepts": json.loads(record.concepts_json or "[]"),
        "source_count": record.source_count,
        "public_detail_level": record.public_detail_level,
        "updated_at": record.updated_at,
    }
    if extras:
        for key in ("public_caveats", "public_source_metadata", "related_cards"):
            if key in extras:
                card[key] = extras[key]
    return card
