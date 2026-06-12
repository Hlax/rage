"""Unit tests for quote span char offset computation."""

from __future__ import annotations

from rge.modules.claim_validator import _collapse_whitespace, locate_quote_offsets

CHUNK = (
    "We found that AI-assisted brainstorming increased average idea quality across "
    "submitted ideas. However, AI-assisted brainstorming reduced semantic diversity "
    "across submitted ideas."
)


def test_locate_quote_offsets_exact_substring() -> None:
    quote = (
        "AI-assisted brainstorming increased average idea quality across "
        "submitted ideas"
    )
    start, end = locate_quote_offsets(quote, CHUNK)
    assert start is not None
    assert end is not None
    assert CHUNK[start:end] == quote


def test_locate_quote_offsets_missing_substring_returns_none() -> None:
    assert locate_quote_offsets("not in chunk", CHUNK) == (None, None)


def test_locate_quote_offsets_newline_in_chunk() -> None:
    chunk = (
        "We found that AI-assisted brainstorming increased average idea quality across\n"
        "submitted ideas."
    )
    quote = (
        "AI-assisted brainstorming increased average idea quality across "
        "submitted ideas"
    )
    start, end = locate_quote_offsets(quote, chunk)
    assert start is not None
    assert end is not None
    assert chunk[start:end].replace("\n", " ").strip() in _collapse_whitespace(chunk)
