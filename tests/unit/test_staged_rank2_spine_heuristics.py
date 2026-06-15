"""Unit tests for staged rank-2 OpenAlex fetch spine heuristics (ticket-229)."""

from __future__ import annotations

from types import SimpleNamespace

from rge.modules.claim_extractor import (
    _is_staged_fetch_spine_chunk,
    source_has_staged_fetch_spine,
)
from rge.modules.concept_linker import is_staged_fetch_spine_source
from rge.modules.staged_spine_heuristics import (
    is_staged_rank1_fetch_spine_chunk,
    is_staged_rank1_fetch_spine_source,
    is_staged_rank2_fetch_spine_chunk,
    is_staged_rank2_fetch_spine_source,
    source_has_staged_rank2_fetch_spine,
)

RANK1_TITLE = (
    "Human-AI co-creativity and semantic diversity in songwriting workshops"
)
RANK1_CHUNK = (
    "Human-AI co-creativity supports diverse songwriting outputs."
)
RANK2_TITLE = "Constraint management in AI-assisted creative teams"
RANK2_CHUNK = (
    "Constraint management improves AI-assisted creative team workflows."
)


def test_rank2_source_matches_fixture_title() -> None:
    source = SimpleNamespace(title=RANK2_TITLE)
    assert is_staged_rank2_fetch_spine_source(source) is True


def test_rank2_chunk_matches_fixture_body() -> None:
    assert is_staged_rank2_fetch_spine_chunk(RANK2_CHUNK) is True


def test_rank2_source_rejects_rank1_title() -> None:
    source = SimpleNamespace(title=RANK1_TITLE)
    assert is_staged_rank2_fetch_spine_source(source) is False


def test_rank2_chunk_rejects_rank1_chunk() -> None:
    assert is_staged_rank2_fetch_spine_chunk(RANK1_CHUNK) is False


def test_rank1_helpers_match_fixture_and_reject_rank2() -> None:
    assert is_staged_rank1_fetch_spine_source(SimpleNamespace(title=RANK1_TITLE)) is True
    assert is_staged_rank1_fetch_spine_chunk(RANK1_CHUNK) is True
    assert is_staged_rank1_fetch_spine_source(SimpleNamespace(title=RANK2_TITLE)) is False
    assert is_staged_rank1_fetch_spine_chunk(RANK2_CHUNK) is False


def test_rank1_module_heuristics_unchanged_and_disjoint_from_rank2() -> None:
    rank1_source = SimpleNamespace(title=RANK1_TITLE)
    rank2_source = SimpleNamespace(title=RANK2_TITLE)
    assert is_staged_fetch_spine_source(rank1_source) is True
    assert is_staged_fetch_spine_source(rank2_source) is False
    assert _is_staged_fetch_spine_chunk(RANK1_CHUNK) is True
    assert _is_staged_fetch_spine_chunk(RANK2_CHUNK) is False


def test_source_has_staged_rank2_fetch_spine() -> None:
    chunks = [
        SimpleNamespace(chunk_text=RANK2_CHUNK),
        SimpleNamespace(chunk_text="Unrelated text."),
    ]
    assert source_has_staged_rank2_fetch_spine(chunks) is True
    assert source_has_staged_fetch_spine(chunks) is False
