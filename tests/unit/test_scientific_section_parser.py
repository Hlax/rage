"""Section-aware parsing, provenance, migration, and extraction-gate tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from rge.db.connection import apply_migrations, ensure_database
from rge.db.repositories import ChunkRepository, ingest_local_source
from rge.modules.claim_extractor import extract_claims_for_source
from rge.modules.document_parser import parse_document_bytes
from rge.modules.parser import (
    SECTION_ABSTRACT,
    SECTION_ACKNOWLEDGEMENTS,
    SECTION_BOILERPLATE,
    SECTION_DISCUSSION,
    SECTION_INTRODUCTION,
    SECTION_LIMITATIONS,
    SECTION_METHODS,
    SECTION_NAVIGATION,
    SECTION_REFERENCES,
    SECTION_RESULTS,
    SECTION_TITLE_METADATA,
    SECTION_UNKNOWN,
    parse_source_text,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCIENTIFIC_FIXTURE = (
    REPO_ROOT / "fixtures" / "source_documents" / "scientific_sections.txt"
)
BENCHMARK_DOCUMENTS = REPO_ROOT / "fixtures" / "research_quality" / "documents"
MIGRATIONS_DIR = REPO_ROOT / "rge" / "db" / "migrations"


def test_parser_distinguishes_required_scientific_sections_with_exact_offsets() -> None:
    raw_text = SCIENTIFIC_FIXTURE.read_text(encoding="utf-8")

    chunks = parse_source_text(raw_text, source_id="src_structural_fixture")

    section_types = {chunk["section_type"] for chunk in chunks}
    assert section_types >= {
        SECTION_TITLE_METADATA,
        SECTION_ABSTRACT,
        SECTION_INTRODUCTION,
        SECTION_METHODS,
        SECTION_RESULTS,
        SECTION_DISCUSSION,
        SECTION_LIMITATIONS,
        SECTION_ACKNOWLEDGEMENTS,
        SECTION_REFERENCES,
    }
    for chunk in chunks:
        assert chunk["chunk_text"] == raw_text[
            chunk["char_start"] : chunk["char_end"]
        ]
        assert chunk["char_start"] < chunk["char_end"]
        assert chunk["section"]

    by_type = {chunk["section_type"]: chunk for chunk in chunks}
    assert by_type[SECTION_RESULTS]["section_title"] == "Results"
    assert by_type[SECTION_LIMITATIONS]["section_title"] == "Limitations"
    assert by_type[SECTION_REFERENCES]["extraction_eligible"] is False
    assert by_type[SECTION_ACKNOWLEDGEMENTS]["extraction_eligible"] is False
    assert by_type[SECTION_TITLE_METADATA]["extraction_eligible"] is False
    assert by_type[SECTION_RESULTS]["extraction_eligible"] is True


def test_navigation_and_boilerplate_sections_default_non_extractable() -> None:
    raw_text = (
        "Navigation\nHome | Search | Previous | Next\n\n"
        "Boilerplate\nCopyright 2026. Terms and conditions apply."
    )

    chunks = parse_source_text(raw_text, source_id="src_shell_sections")

    assert [chunk["section_type"] for chunk in chunks] == [
        SECTION_NAVIGATION,
        SECTION_BOILERPLATE,
    ]
    assert all(chunk["extraction_eligible"] is False for chunk in chunks)


def test_unknown_section_inherits_explicit_source_policy() -> None:
    raw_text = (
        "A bounded study reported a measurable outcome in one sample. "
        "A second sentence records the limitation."
    )

    allowed = parse_source_text(
        raw_text,
        source_id="src_unknown_allowed",
        source_extraction_eligible=True,
    )
    blocked = parse_source_text(
        raw_text,
        source_id="src_unknown_blocked",
        source_extraction_eligible=False,
    )

    assert allowed[0]["section_type"] == SECTION_UNKNOWN
    assert allowed[0]["extraction_eligible"] is True
    assert blocked[0]["section_type"] == SECTION_UNKNOWN
    assert blocked[0]["extraction_eligible"] is False


def test_page_spans_are_persisted_when_parser_supplies_them(tmp_path: Path) -> None:
    raw_text = (
        "Results\nThe first page reports a bounded result.\n\n"
        "Discussion\nThe second page discusses the bounded result."
    )
    second_page_start = raw_text.index("Discussion")
    page_spans = [
        {"page": "1", "char_start": 0, "char_end": second_page_start},
        {
            "page": "2",
            "char_start": second_page_start,
            "char_end": len(raw_text),
        },
    ]

    chunks = parse_source_text(
        raw_text,
        source_id="src_pages",
        page_spans=page_spans,
    )

    assert [chunk["page"] for chunk in chunks] == ["1", "2"]

    source_path = tmp_path / "page-spans.txt"
    source_path.write_text(raw_text, encoding="utf-8")
    conn = ensure_database(tmp_path / "page-spans.sqlite")
    try:
        result = ingest_local_source(
            conn,
            local_path=source_path,
            domain="creativity",
            raw_text=raw_text,
            title=source_path.name,
            source_type="fixture",
            page_spans=page_spans,
        )
        persisted = ChunkRepository(conn).list_for_source(str(result["source_id"]))

        assert [chunk.page for chunk in persisted] == ["1", "2"]
        assert all(
            chunk.chunk_text == raw_text[chunk.char_start : chunk.char_end]
            for chunk in persisted
        )
    finally:
        conn.close()


def test_html_markdown_and_plain_text_fallbacks_are_deterministic() -> None:
    markdown = (
        "# Synthetic Study\n\n## Results\nA bounded result was observed.\n\n"
        "## References\nExample citation."
    )
    markdown_chunks = parse_source_text(markdown, source_id="src_markdown")
    assert [chunk["section_type"] for chunk in markdown_chunks] == [
        SECTION_RESULTS,
        SECTION_REFERENCES,
    ]

    html = (
        b"<html><body><h2>Results</h2><p>A bounded result was observed in this "
        b"synthetic sample.</p></body></html>"
    )
    parsed_html = parse_document_bytes(html, content_type="text/html", suffix=".html")
    html_chunks = parse_source_text(
        parsed_html.clean_text,
        source_id="src_html",
    )
    assert html_chunks == parse_source_text(
        parsed_html.clean_text,
        source_id="src_html",
    )
    assert all(
        chunk["chunk_text"]
        == parsed_html.clean_text[chunk["char_start"] : chunk["char_end"]]
        for chunk in html_chunks
    )

    plain = "A plain-text finding is preserved exactly. A limitation follows."
    plain_chunks = parse_source_text(plain, source_id="src_plain")
    assert plain_chunks[0]["section_type"] == SECTION_UNKNOWN
    assert plain_chunks[0]["chunk_text"] == plain


def test_repository_persists_structural_fields(tmp_path: Path) -> None:
    raw_text = SCIENTIFIC_FIXTURE.read_text(encoding="utf-8")
    conn = ensure_database(tmp_path / "structural.sqlite")
    try:
        result = ingest_local_source(
            conn,
            local_path=SCIENTIFIC_FIXTURE,
            domain="creativity",
            raw_text=raw_text,
            title=SCIENTIFIC_FIXTURE.name,
            source_type="fixture",
        )
        chunks = ChunkRepository(conn).list_for_source(str(result["source_id"]))

        assert chunks
        assert {chunk.section_type for chunk in chunks} >= {
            SECTION_ABSTRACT,
            SECTION_RESULTS,
            SECTION_REFERENCES,
        }
        for chunk in chunks:
            assert chunk.chunk_text == raw_text[chunk.char_start : chunk.char_end]
        references = [
            chunk for chunk in chunks if chunk.section_type == SECTION_REFERENCES
        ]
        assert references and all(not chunk.extraction_eligible for chunk in references)
    finally:
        conn.close()


def test_reference_only_source_produces_zero_accepted_claims(tmp_path: Path) -> None:
    fixture_path = BENCHMARK_DOCUMENTS / "bibliography_page.txt"
    raw_text = fixture_path.read_text(encoding="utf-8")
    conn = ensure_database(tmp_path / "references.sqlite")
    try:
        result = ingest_local_source(
            conn,
            local_path=fixture_path,
            domain="creativity",
            raw_text=raw_text,
            title=fixture_path.name,
            source_type="fixture",
        )
        source_id = str(result["source_id"])

        extraction = extract_claims_for_source(
            conn,
            source_id,
            fixture_name="claim_extraction_valid_and_missing_quote.json",
        )
        accepted = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ? AND status = 'accepted'",
            (source_id,),
        ).fetchone()[0]

        assert extraction["status"] == "blocked_by_section_gate"
        assert extraction["section_gate"]["eligible_chunk_count"] == 0
        assert accepted == 0
    finally:
        conn.close()


def test_additive_migration_preserves_pre_ticket_chunk(tmp_path: Path) -> None:
    db_path = tmp_path / "pre_ticket_415.sqlite"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(
            (MIGRATIONS_DIR / "0001_initial.sql").read_text(encoding="utf-8")
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO schema_migrations VALUES ('0001_initial', datetime('now'))"
        )
        conn.execute(
            """
            INSERT INTO sources (id, title, status, created_at, updated_at)
            VALUES ('src_legacy', 'Legacy source', 'ingested', datetime('now'), datetime('now'))
            """
        )
        conn.execute(
            """
            INSERT INTO chunks (
                id, source_id, chunk_index, chunk_text, text_checksum, created_at
            ) VALUES (
                'chk_legacy', 'src_legacy', 0, 'Legacy chunk.', 'checksum', datetime('now')
            )
            """
        )
        conn.commit()

        applied = apply_migrations(conn)
        row = conn.execute(
            "SELECT * FROM chunks WHERE id = 'chk_legacy'"
        ).fetchone()

        assert applied[-2:] == [
            "0010_structural_chunk_provenance",
            "0011_structured_research_claim",
        ]
        assert row["chunk_text"] == "Legacy chunk."
        assert row["section_type"] == SECTION_UNKNOWN
        assert row["section_title"] is None
        assert row["char_start"] is None
        assert row["char_end"] is None
        assert row["extraction_eligible"] == 1
    finally:
        conn.close()
