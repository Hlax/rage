"""Staged OpenAlex fetch spine source/chunk heuristics (rank-1 and rank-2).

Rank-1 markers align with OpenAlex work W2741809807 (co-creativity / songwriting).
Rank-2 markers align with OpenAlex work W1234567890 (constraint management).

These helpers are consumed by future rank-2 live LLM fallthrough tickets (230+).
Rank-1 auto-mock routing in claim_extractor / concept_linker / relationship_builder
remains unchanged; do not broaden rank-1 routing to rank-2 without explicit gates.
"""

from __future__ import annotations

from typing import Any


def is_staged_rank1_fetch_spine_source(source: Any | None) -> bool:
    """Return True when source title matches rank-1 staged OpenAlex fetch spine markers."""
    if source is None:
        return False
    title = str(getattr(source, "title", "") or "").casefold()
    return "human-ai co-creativity" in title and "songwriting" in title


def is_staged_rank1_fetch_spine_chunk(chunk_text: str) -> bool:
    """Return True when chunk text matches rank-1 staged OpenAlex fetch spine markers."""
    lowered = chunk_text.casefold()
    return "human-ai co-creativity" in lowered and "songwriting" in lowered


def is_staged_rank2_fetch_spine_source(source: Any | None) -> bool:
    """Return True when source title matches rank-2 staged OpenAlex fetch spine markers."""
    if source is None:
        return False
    title = str(getattr(source, "title", "") or "").casefold()
    return "constraint management" in title


def is_staged_rank2_fetch_spine_chunk(chunk_text: str) -> bool:
    """Return True when chunk text matches rank-2 staged OpenAlex fetch spine markers."""
    return "constraint management" in chunk_text.casefold()


def source_has_staged_rank2_fetch_spine(chunks: list[Any]) -> bool:
    """Return True when any chunk matches rank-2 staged OpenAlex fetch spine markers."""
    return any(
        is_staged_rank2_fetch_spine_chunk(str(getattr(c, "chunk_text", "") or ""))
        for c in chunks
    )


MIN_STAGED_INGEST_TEXT_CHARS = 200


def staged_ingest_chunk_text(chunks: list[Any]) -> str:
    """Concatenate chunk text for staged ingest validation."""
    return "".join(str(getattr(chunk, "chunk_text", "") or "") for chunk in chunks)


def staged_ingest_has_sufficient_text(chunks: list[Any]) -> bool:
    """Return True when staged ingest chunks contain enough text for live extraction."""
    return len(staged_ingest_chunk_text(chunks).strip()) >= MIN_STAGED_INGEST_TEXT_CHARS


def is_staged_ingest_source(source: Any | None, *, conn: Any | None = None) -> bool:
    """Return True when a source row came from ingest-staged (not checksum-pinned mock)."""
    if source is None:
        return False
    source_type = str(getattr(source, "source_type", "") or "").strip().casefold()
    if source_type == "staged_fetch":
        return True
    local_path = str(getattr(source, "local_path", "") or "").casefold()
    if "staged" in local_path:
        return True
    if conn is not None:
        title = str(getattr(source, "title", "") or "").strip()
        if title:
            row = conn.execute(
                "SELECT 1 FROM candidate_sources WHERE title = ? LIMIT 1",
                (title,),
            ).fetchone()
            if row is not None:
                return True
    return False
