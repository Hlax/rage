"""Golden Test 33: GROBID fixture parse proof (no live GROBID server)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from rge.modules.document_parser import CLEAN_TEXT_READY, parse_pdf_bytes

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_FIXTURES = REPO_ROOT / "fixtures" / "source_documents"


def test_grobid_fixture_tei_response_produces_clean_text_ready_parse() -> None:
    pdf_bytes = (DOC_FIXTURES / "manual_oa_minimal.pdf").read_bytes()
    tei_bytes = (DOC_FIXTURES / "grobid_response_tei.xml").read_bytes()

    class _FakeResponse:
        def read(self) -> bytes:
            return tei_bytes

        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    with patch("urllib.request.urlopen", return_value=_FakeResponse()):
        result = parse_pdf_bytes(pdf_bytes, grobid_url="http://grobid-fixture.local")

    assert result.parser_backend == "grobid_tei"
    assert result.source_status == CLEAN_TEXT_READY
    assert result.quoteable_span_count >= 1
