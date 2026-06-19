"""Document parsing and text quality gates (MVP-P6).

Preferred order: TEI/XML, GROBID TEI (optional), PyMuPDF, pypdf fallback.
Never raw UTF-8 decode of PDF bytes.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any

from rge.modules.fetcher import html_to_text

_READABLE_CHAR_PATTERN = re.compile(r"[A-Za-z0-9\s.,;:'\"()\-]")
_SENTENCE_PATTERN = re.compile(r"[.!?]+")
_MIN_READABLE_RATIO = 0.55
_MIN_CLEAN_TEXT_CHARS = 120
_MIN_QUOTEABLE_SPANS = 1
_MIN_SENTENCES = 2

DIRTY_TEXT = "dirty_text"
PARSE_FAILED = "parse_failed"
CLEAN_TEXT_READY = "clean_text_ready"


@dataclass(frozen=True)
class DocumentParseResult:
    clean_text: str
    source_status: str
    parser_backend: str
    readable_char_ratio: float
    sentence_count: int
    quoteable_span_count: int
    extracted_char_count: int
    detail: str
    page_count: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "clean_text": self.clean_text,
            "source_status": self.source_status,
            "parser_backend": self.parser_backend,
            "readable_char_ratio": round(self.readable_char_ratio, 4),
            "sentence_count": self.sentence_count,
            "quoteable_span_count": self.quoteable_span_count,
            "extracted_char_count": self.extracted_char_count,
            "detail": self.detail,
            "page_count": self.page_count,
        }


def is_pdf_bytes(body: bytes) -> bool:
    return body.startswith(b"%PDF")


def score_text_quality(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        return {
            "readable_char_ratio": 0.0,
            "sentence_count": 0,
            "quoteable_span_count": 0,
            "extracted_char_count": 0,
            "is_clean": False,
        }
    readable = len(_READABLE_CHAR_PATTERN.findall(stripped))
    ratio = readable / max(len(stripped), 1)
    sentences = [part for part in _SENTENCE_PATTERN.split(stripped) if part.strip()]
    sentence_count = max(len(sentences), 1 if stripped else 0)
    quoteable = sum(1 for sentence in re.split(r"[.!?]", stripped) if len(sentence.strip()) >= 24)
    is_clean = (
        len(stripped) >= _MIN_CLEAN_TEXT_CHARS
        and ratio >= _MIN_READABLE_RATIO
        and sentence_count >= _MIN_SENTENCES
        and quoteable >= _MIN_QUOTEABLE_SPANS
    )
    return {
        "readable_char_ratio": ratio,
        "sentence_count": sentence_count,
        "quoteable_span_count": quoteable,
        "extracted_char_count": len(stripped),
        "is_clean": is_clean,
    }


def classify_text_quality(text: str, *, parser_backend: str) -> DocumentParseResult:
    scores = score_text_quality(text)
    status = CLEAN_TEXT_READY if scores["is_clean"] else DIRTY_TEXT
    detail = (
        "Clean text ready for quote-first extraction."
        if status == CLEAN_TEXT_READY
        else "Text failed readability/quoteability quality gates."
    )
    return DocumentParseResult(
        clean_text=text.strip(),
        source_status=status,
        parser_backend=parser_backend,
        readable_char_ratio=float(scores["readable_char_ratio"]),
        sentence_count=int(scores["sentence_count"]),
        quoteable_span_count=int(scores["quoteable_span_count"]),
        extracted_char_count=int(scores["extracted_char_count"]),
        detail=detail,
    )


def parse_tei_xml(text: str) -> DocumentParseResult:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return DocumentParseResult(
            clean_text="",
            source_status=PARSE_FAILED,
            parser_backend="tei_xml",
            readable_char_ratio=0.0,
            sentence_count=0,
            quoteable_span_count=0,
            extracted_char_count=0,
            detail=f"TEI parse failed: {exc}",
        )
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    paragraphs: list[str] = []
    for node in root.findall(".//tei:p", ns):
        if node.text or len(node):
            paragraphs.append("".join(node.itertext()).strip())
    if not paragraphs:
        for node in root.iter():
            if node.tag.endswith("p"):
                chunk = "".join(node.itertext()).strip()
                if chunk:
                    paragraphs.append(chunk)
    clean = " ".join(part for part in paragraphs if part)
    if not clean:
        return DocumentParseResult(
            clean_text="",
            source_status=PARSE_FAILED,
            parser_backend="tei_xml",
            readable_char_ratio=0.0,
            sentence_count=0,
            quoteable_span_count=0,
            extracted_char_count=0,
            detail="TEI XML contained no paragraph text.",
        )
    return classify_text_quality(clean, parser_backend="tei_xml")


def _pick_best_parse(candidates: list[DocumentParseResult]) -> DocumentParseResult:
    if not candidates:
        return DocumentParseResult(
            clean_text="",
            source_status=PARSE_FAILED,
            parser_backend="pdf_none",
            readable_char_ratio=0.0,
            sentence_count=0,
            quoteable_span_count=0,
            extracted_char_count=0,
            detail="No PDF parser produced text.",
        )
    clean = [item for item in candidates if item.source_status == CLEAN_TEXT_READY]
    pool = clean or candidates
    return max(
        pool,
        key=lambda item: (
            item.source_status == CLEAN_TEXT_READY,
            item.readable_char_ratio,
            item.extracted_char_count,
        ),
    )


def _extract_pdf_text_pymupdf(body: bytes) -> tuple[str, int] | None:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None
    try:
        document = fitz.open(stream=body, filetype="pdf")
        pages = [page.get_text() for page in document]
        page_count = document.page_count
        document.close()
    except Exception:  # noqa: BLE001
        return None
    clean = " ".join(part.strip() for part in pages if part.strip())
    if not clean:
        return None
    return clean, page_count


def _extract_pdf_text_pypdf(body: bytes) -> tuple[str, int] | None:
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    import io

    try:
        reader = PdfReader(io.BytesIO(body))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception:  # noqa: BLE001
        return None
    clean = " ".join(part.strip() for part in pages if part.strip())
    if not clean:
        return None
    return clean, len(pages)


def _parse_pdf_grobid(body: bytes, grobid_url: str) -> DocumentParseResult | None:
    if not grobid_url:
        return None
    import urllib.error
    import urllib.parse
    import urllib.request

    endpoint = grobid_url.rstrip("/") + "/api/processFulltextDocument"
    data = urllib.parse.urlencode({"input": "pdf"}).encode("utf-8")
    try:
        request = urllib.request.Request(
            endpoint,
            data=body,
            headers={
                "Accept": "application/xml",
                "Content-Type": "application/pdf",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            tei_payload = response.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError):
        return None
    parsed = parse_tei_xml(tei_payload)
    if parsed.parser_backend == "tei_xml":
        return DocumentParseResult(
            clean_text=parsed.clean_text,
            source_status=parsed.source_status,
            parser_backend="grobid_tei",
            readable_char_ratio=parsed.readable_char_ratio,
            sentence_count=parsed.sentence_count,
            quoteable_span_count=parsed.quoteable_span_count,
            extracted_char_count=parsed.extracted_char_count,
            detail=parsed.detail,
            page_count=parsed.page_count,
        )
    return None


def parse_pdf_bytes(body: bytes, *, grobid_url: str = "") -> DocumentParseResult:
    if not is_pdf_bytes(body):
        return DocumentParseResult(
            clean_text="",
            source_status=PARSE_FAILED,
            parser_backend="pdf_reject_non_pdf",
            readable_char_ratio=0.0,
            sentence_count=0,
            quoteable_span_count=0,
            extracted_char_count=0,
            detail="Body is not a PDF document.",
        )

    candidates: list[DocumentParseResult] = []
    grobid_result = _parse_pdf_grobid(body, grobid_url)
    if grobid_result is not None:
        candidates.append(grobid_result)

    pymupdf_payload = _extract_pdf_text_pymupdf(body)
    if pymupdf_payload is not None:
        text, page_count = pymupdf_payload
        parsed = classify_text_quality(text, parser_backend="pymupdf")
        candidates.append(
            DocumentParseResult(
                clean_text=parsed.clean_text,
                source_status=parsed.source_status,
                parser_backend=parsed.parser_backend,
                readable_char_ratio=parsed.readable_char_ratio,
                sentence_count=parsed.sentence_count,
                quoteable_span_count=parsed.quoteable_span_count,
                extracted_char_count=parsed.extracted_char_count,
                detail=parsed.detail,
                page_count=page_count,
            )
        )

    pypdf_payload = _extract_pdf_text_pypdf(body)
    if pypdf_payload is not None:
        text, page_count = pypdf_payload
        parsed = classify_text_quality(text, parser_backend="pypdf")
        candidates.append(
            DocumentParseResult(
                clean_text=parsed.clean_text,
                source_status=parsed.source_status,
                parser_backend=parsed.parser_backend,
                readable_char_ratio=parsed.readable_char_ratio,
                sentence_count=parsed.sentence_count,
                quoteable_span_count=parsed.quoteable_span_count,
                extracted_char_count=parsed.extracted_char_count,
                detail=parsed.detail,
                page_count=page_count,
            )
        )

    if not candidates:
        return DocumentParseResult(
            clean_text="",
            source_status=PARSE_FAILED,
            parser_backend="pdf_unavailable",
            readable_char_ratio=0.0,
            sentence_count=0,
            quoteable_span_count=0,
            extracted_char_count=0,
            detail="No PDF parser backend available (install pypdf or pymupdf).",
        )
    return _pick_best_parse(candidates)


def parse_document_bytes(
    body: bytes,
    *,
    content_type: str | None = None,
    suffix: str = "",
    grobid_url: str = "",
) -> DocumentParseResult:
    """Parse fetched document bytes into quality-scored clean text."""
    lowered_type = (content_type or "").split(";")[0].strip().casefold()
    lowered_suffix = suffix.casefold()

    if is_pdf_bytes(body) or lowered_type == "application/pdf" or lowered_suffix == ".pdf":
        return parse_pdf_bytes(body, grobid_url=grobid_url)

    text = body.decode("utf-8", errors="replace")
    if (
        lowered_type in {"application/xml", "text/xml"}
        or lowered_suffix in {".xml", ".tei"}
        or "<TEI" in text[:500]
    ):
        return parse_tei_xml(text)

    if lowered_type == "text/html" or lowered_suffix == ".html" or text.lstrip().startswith("<"):
        return classify_text_quality(html_to_text(text), parser_backend="html_strip")

    return classify_text_quality(text.strip(), parser_backend="plain_text")


def parse_document_file(path: Any) -> DocumentParseResult:
    from pathlib import Path

    resolved = Path(path)
    body = resolved.read_bytes()
    return parse_document_bytes(body, suffix=resolved.suffix)
