"""Text quality gate tests for pre-extraction blocking."""

from __future__ import annotations

from dataclasses import dataclass

from rge.modules.text_quality_gate import (
    assess_chunk_extractability,
    discover_quoteable_spans,
    gate_source_for_extraction,
)


@dataclass
class _Chunk:
    id: str
    chunk_text: str


@dataclass
class _Source:
    domain_metadata_json: str


def test_discover_quoteable_spans_finds_sentence_level_spans() -> None:
    text = (
        "AI-assisted brainstorming increased average idea quality in short-form "
        "writing tasks. AI-assisted brainstorming reduced semantic diversity in "
        "short-form writing tasks."
    )
    spans = discover_quoteable_spans(text)

    assert len(spans) >= 2
    assert all(len(span) >= 24 for span in spans)


def test_assess_chunk_extractability_marks_clean_fixture_chunk_extractable() -> None:
    text = (
        "AI-assisted brainstorming increased average idea quality in short-form "
        "writing tasks. AI-assisted brainstorming reduced semantic diversity in "
        "short-form writing tasks."
    )
    assessment = assess_chunk_extractability(text)

    assert assessment["is_clean"] is True
    assert assessment["extractable"] is True
    assert assessment["quoteable_span_count"] >= 1


def test_gate_source_for_extraction_blocks_dirty_acquisition_status() -> None:
    source = _Source(domain_metadata_json='{"acquisition_status": "dirty_text"}')
    chunks = [_Chunk(id="chk_1", chunk_text="short")]

    gate = gate_source_for_extraction(source, chunks)

    assert gate["allowed"] is False
    assert gate["reason"] == "dirty_text"


def test_gate_source_for_extraction_allows_quoteable_chunks() -> None:
    source = _Source(domain_metadata_json="{}")
    chunks = [
        _Chunk(
            id="chk_1",
            chunk_text=(
                "AI-assisted brainstorming increased average idea quality in short-form "
                "writing tasks. AI-assisted brainstorming reduced semantic diversity in "
                "short-form writing tasks."
            ),
        )
    ]

    gate = gate_source_for_extraction(source, chunks)

    assert gate["allowed"] is True
    assert gate["extractable_chunk_count"] == 1
