"""Parse text/PDF/HTML sources into chunks. Deterministic; no model use.

Produces ``chunks`` records with checksums for deduplication. Parsed text
remains untrusted data, never instructions.
"""

from __future__ import annotations

import re
from typing import Any

from rge.db.repositories import make_chunk_id, sha256_hex

_DEFAULT_CHUNK_CHAR_LIMIT = 4000


def _approximate_token_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def parse_source_text(
    raw_text: str,
    *,
    source_id: str,
    chunk_char_limit: int = _DEFAULT_CHUNK_CHAR_LIMIT,
) -> list[dict[str, Any]]:
    """Split source text into ordered chunks with stable IDs and checksums."""
    normalized = raw_text.strip()
    if not normalized:
        return []

    chunks: list[dict[str, Any]] = []
    start = 0
    chunk_index = 0

    while start < len(normalized):
        end = min(start + chunk_char_limit, len(normalized))
        if end < len(normalized):
            break_at = normalized.rfind("\n\n", start, end)
            if break_at > start:
                end = break_at
        chunk_text = normalized[start:end].strip()
        if not chunk_text:
            break
        text_checksum = sha256_hex(chunk_text)
        chunks.append(
            {
                "id": make_chunk_id(source_id, chunk_index, text_checksum),
                "chunk_index": chunk_index,
                "chunk_text": chunk_text,
                "text_checksum": text_checksum,
                "token_count": _approximate_token_count(chunk_text),
            }
        )
        chunk_index += 1
        start = end

    return chunks


def parse_source(source: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse one fetched source into chunks."""
    raw_text = source.get("raw_text")
    source_id = source.get("source_id")
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("parse_source requires non-empty raw_text")
    if not isinstance(source_id, str) or not source_id:
        raise ValueError("parse_source requires source_id")
    return parse_source_text(raw_text, source_id=source_id)
