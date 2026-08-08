"""Parse source text into deterministic structural chunks.

Offsets are half-open indexes into the exact ``raw_text`` string passed to
``parse_source_text``. Chunk boundaries may discard only surrounding whitespace;
therefore ``chunk_text == raw_text[char_start:char_end]`` for every new chunk.
Parsed source text remains untrusted data, never instructions.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from rge.db.repositories import make_chunk_id, sha256_hex

_DEFAULT_CHUNK_CHAR_LIMIT = 4000

SECTION_TITLE_METADATA = "title_metadata"
SECTION_ABSTRACT = "abstract"
SECTION_INTRODUCTION = "introduction_background"
SECTION_METHODS = "methods"
SECTION_RESULTS = "results"
SECTION_DISCUSSION = "discussion"
SECTION_LIMITATIONS = "limitations"
SECTION_REFERENCES = "references"
SECTION_ACKNOWLEDGEMENTS = "acknowledgements"
SECTION_NAVIGATION = "navigation"
SECTION_BOILERPLATE = "boilerplate"
SECTION_UNKNOWN = "unknown"

SECTION_TYPES = frozenset(
    {
        SECTION_TITLE_METADATA,
        SECTION_ABSTRACT,
        SECTION_INTRODUCTION,
        SECTION_METHODS,
        SECTION_RESULTS,
        SECTION_DISCUSSION,
        SECTION_LIMITATIONS,
        SECTION_REFERENCES,
        SECTION_ACKNOWLEDGEMENTS,
        SECTION_NAVIGATION,
        SECTION_BOILERPLATE,
        SECTION_UNKNOWN,
    }
)
NON_EXTRACTABLE_SECTION_TYPES = frozenset(
    {
        SECTION_TITLE_METADATA,
        SECTION_REFERENCES,
        SECTION_ACKNOWLEDGEMENTS,
        SECTION_NAVIGATION,
        SECTION_BOILERPLATE,
    }
)

_SECTION_ALIASES = {
    "title": SECTION_TITLE_METADATA,
    "metadata": SECTION_TITLE_METADATA,
    "author information": SECTION_TITLE_METADATA,
    "authors": SECTION_TITLE_METADATA,
    "abstract": SECTION_ABSTRACT,
    "summary": SECTION_ABSTRACT,
    "introduction": SECTION_INTRODUCTION,
    "background": SECTION_INTRODUCTION,
    "introduction and background": SECTION_INTRODUCTION,
    "methods": SECTION_METHODS,
    "method": SECTION_METHODS,
    "methodology": SECTION_METHODS,
    "materials and methods": SECTION_METHODS,
    "study design": SECTION_METHODS,
    "results": SECTION_RESULTS,
    "findings": SECTION_RESULTS,
    "observations": SECTION_RESULTS,
    "discussion": SECTION_DISCUSSION,
    "conclusion": SECTION_DISCUSSION,
    "conclusions": SECTION_DISCUSSION,
    "limitations": SECTION_LIMITATIONS,
    "limitations and future work": SECTION_LIMITATIONS,
    "references": SECTION_REFERENCES,
    "bibliography": SECTION_REFERENCES,
    "works cited": SECTION_REFERENCES,
    "acknowledgements": SECTION_ACKNOWLEDGEMENTS,
    "acknowledgments": SECTION_ACKNOWLEDGEMENTS,
    "funding": SECTION_ACKNOWLEDGEMENTS,
    "navigation": SECTION_NAVIGATION,
    "menu": SECTION_NAVIGATION,
    "boilerplate": SECTION_BOILERPLATE,
    "copyright": SECTION_BOILERPLATE,
    "disclosures": SECTION_BOILERPLATE,
}
_NUMBERED_HEADING_PREFIX = re.compile(r"^\d+(?:\.\d+)*[.)]?\s+")
_MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class SectionSpan:
    section_type: str
    section_title: str | None
    char_start: int
    char_end: int


def _approximate_token_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def _trim_span(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _normalize_heading(value: str) -> str:
    normalized = value.strip().rstrip(":").strip().casefold()
    normalized = _NUMBERED_HEADING_PREFIX.sub("", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _heading_from_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped:
        return None
    markdown = _MARKDOWN_HEADING.match(stripped)
    if markdown:
        title = markdown.group(2).strip().rstrip(":").strip()
        section_type = _SECTION_ALIASES.get(_normalize_heading(title))
        if section_type is None and markdown.group(1) == "#":
            section_type = SECTION_TITLE_METADATA
        return (section_type or SECTION_UNKNOWN, title)

    title = stripped.rstrip(":").strip()
    section_type = _SECTION_ALIASES.get(_normalize_heading(title))
    if section_type is None:
        return None
    return section_type, title


def identify_section_spans(raw_text: str) -> list[SectionSpan]:
    """Return deterministic structural body spans over ``raw_text``."""
    if not raw_text.strip():
        return []

    headings: list[tuple[int, int, str, str]] = []
    cursor = 0
    for line in raw_text.splitlines(keepends=True):
        line_start = cursor
        cursor += len(line)
        heading = _heading_from_line(line.rstrip("\r\n"))
        if heading is not None:
            headings.append((line_start, cursor, heading[0], heading[1]))
    if cursor < len(raw_text):
        line = raw_text[cursor:]
        heading = _heading_from_line(line)
        if heading is not None:
            headings.append((cursor, len(raw_text), heading[0], heading[1]))

    if not headings:
        start, end = _trim_span(raw_text, 0, len(raw_text))
        return [SectionSpan(SECTION_UNKNOWN, None, start, end)] if start < end else []

    spans: list[SectionSpan] = []
    preamble_start, preamble_end = _trim_span(raw_text, 0, headings[0][0])
    if preamble_start < preamble_end:
        spans.append(
            SectionSpan(
                SECTION_TITLE_METADATA,
                None,
                preamble_start,
                preamble_end,
            )
        )

    for index, (_, body_start, section_type, title) in enumerate(headings):
        body_end = headings[index + 1][0] if index + 1 < len(headings) else len(raw_text)
        start, end = _trim_span(raw_text, body_start, body_end)
        if start < end:
            spans.append(SectionSpan(section_type, title, start, end))
    return spans


def _bounded_chunk_spans(
    raw_text: str,
    *,
    start: int,
    end: int,
    chunk_char_limit: int,
) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    cursor = start
    while cursor < end:
        cursor, _ = _trim_span(raw_text, cursor, end)
        if cursor >= end:
            break
        candidate_end = min(cursor + chunk_char_limit, end)
        advance_to = candidate_end
        if candidate_end < end:
            paragraph_break = raw_text.rfind("\n\n", cursor, candidate_end)
            if paragraph_break > cursor:
                candidate_end = paragraph_break
                advance_to = paragraph_break + 2
        chunk_start, chunk_end = _trim_span(raw_text, cursor, candidate_end)
        if chunk_start < chunk_end:
            spans.append((chunk_start, chunk_end))
        cursor = max(advance_to, chunk_end)
    return spans


def _page_for_span(
    char_start: int,
    char_end: int,
    page_spans: Sequence[Mapping[str, Any]],
) -> str | None:
    pages: list[str] = []
    for span in page_spans:
        try:
            page_start = int(span["char_start"])
            page_end = int(span["char_end"])
        except (KeyError, TypeError, ValueError):
            continue
        if char_start < page_end and char_end > page_start:
            label = str(span.get("page") or "").strip()
            if label and label not in pages:
                pages.append(label)
    if not pages:
        return None
    if len(pages) == 1:
        return pages[0]
    if all(page.isdigit() for page in pages):
        return f"{pages[0]}-{pages[-1]}"
    return ",".join(pages)


def parse_source_text(
    raw_text: str,
    *,
    source_id: str,
    chunk_char_limit: int = _DEFAULT_CHUNK_CHAR_LIMIT,
    source_extraction_eligible: bool = True,
    page_spans: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Split source text into ordered structural chunks with exact offsets."""
    if chunk_char_limit <= 0:
        raise ValueError("chunk_char_limit must be positive")

    chunks: list[dict[str, Any]] = []
    pages = page_spans or ()
    for section in identify_section_spans(raw_text):
        section_allowed = section.section_type not in NON_EXTRACTABLE_SECTION_TYPES
        if section.section_type == SECTION_UNKNOWN:
            section_allowed = source_extraction_eligible
        extraction_eligible = bool(source_extraction_eligible and section_allowed)
        for char_start, char_end in _bounded_chunk_spans(
            raw_text,
            start=section.char_start,
            end=section.char_end,
            chunk_char_limit=chunk_char_limit,
        ):
            chunk_text = raw_text[char_start:char_end]
            text_checksum = sha256_hex(chunk_text)
            chunk_index = len(chunks)
            chunks.append(
                {
                    "id": make_chunk_id(source_id, chunk_index, text_checksum),
                    "chunk_index": chunk_index,
                    "chunk_text": chunk_text,
                    "text_checksum": text_checksum,
                    "token_count": _approximate_token_count(chunk_text),
                    "page": _page_for_span(char_start, char_end, pages),
                    "section": section.section_title or section.section_type,
                    "section_type": section.section_type,
                    "section_title": section.section_title,
                    "char_start": char_start,
                    "char_end": char_end,
                    "extraction_eligible": extraction_eligible,
                }
            )
    return chunks


def parse_source(source: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse one fetched source into structural chunks."""
    raw_text = source.get("raw_text")
    source_id = source.get("source_id")
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("parse_source requires non-empty raw_text")
    if not isinstance(source_id, str) or not source_id:
        raise ValueError("parse_source requires source_id")
    return parse_source_text(
        raw_text,
        source_id=source_id,
        source_extraction_eligible=bool(
            source.get("source_extraction_eligible", True)
        ),
        page_spans=(
            source.get("page_spans")
            if isinstance(source.get("page_spans"), Sequence)
            else None
        ),
    )
