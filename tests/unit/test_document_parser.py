"""Unit tests for document parser (MVP-P6)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rge.modules.document_parser import (
    CLEAN_TEXT_READY,
    DIRTY_TEXT,
    PARSE_FAILED,
    is_pdf_bytes,
    parse_document_bytes,
    parse_document_file,
    parse_pdf_bytes,
    parse_tei_xml,
)
from rge.modules.fetcher import FetchError, artifact_bytes_to_text

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_FIXTURES = REPO_ROOT / "fixtures" / "source_documents"


def test_is_pdf_bytes_detects_pdf_magic() -> None:
    assert is_pdf_bytes(b"%PDF-1.4\n")
    assert not is_pdf_bytes(b"plain text")


def test_parse_tei_xml_extracts_paragraphs() -> None:
    xml_text = (DOC_FIXTURES / "manual_oa_tei.xml").read_text(encoding="utf-8")
    result = parse_tei_xml(xml_text)

    assert result.source_status == CLEAN_TEXT_READY
    assert "Human-AI co-creativity" in result.clean_text
    assert result.parser_backend == "tei_xml"


def test_parse_document_file_clean_fulltext_fixture() -> None:
    result = parse_document_file(DOC_FIXTURES / "manual_oa_clean_fulltext.txt")

    assert result.source_status == CLEAN_TEXT_READY
    assert result.quoteable_span_count >= 1


def test_pdf_bytes_are_not_utf8_decoded_as_text() -> None:
    pdf_bytes = (DOC_FIXTURES / "manual_oa_minimal.pdf").read_bytes()
    result = parse_pdf_bytes(pdf_bytes)

    assert result.source_status in {CLEAN_TEXT_READY, DIRTY_TEXT, PARSE_FAILED}
    if result.source_status == CLEAN_TEXT_READY:
        assert "Human-AI" in result.clean_text
    assert "\x00" not in result.clean_text


def test_artifact_bytes_to_text_rejects_unparseable_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "dirty.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n" + bytes(range(256)) * 20)

    with pytest.raises(FetchError) as excinfo:
        artifact_bytes_to_text(pdf_path.read_bytes(), pdf_path)

    assert excinfo.value.reason in {PARSE_FAILED, DIRTY_TEXT}


def test_artifact_bytes_to_text_parses_tei_fixture() -> None:
    path = DOC_FIXTURES / "manual_oa_tei.xml"
    text = artifact_bytes_to_text(path.read_bytes(), path)

    assert "Human-AI co-creativity" in text
