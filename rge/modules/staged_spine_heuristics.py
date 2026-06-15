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
