"""Optional Scrapling HTML parser boundary (parser-only; no fetchers required).

Falls back to ``html_to_text`` when Scrapling is not installed. Used by the web
source adapter for operator comparison proofs only — not a hard CI dependency.
"""

from __future__ import annotations

from typing import Any

from rge.modules.fetcher import html_to_text

PARSER_HTML_TO_TEXT = "html_to_text"
PARSER_SCRAPLING = "scrapling"


def scrapling_parser_available() -> bool:
    try:
        from scrapling.parser import Selector  # noqa: F401

        return True
    except ImportError:
        return False


def extract_clean_text_scrapling(html: str) -> str:
    """Extract visible text from HTML using Scrapling Selector."""
    from scrapling.parser import Selector

    page = Selector(html)
    text = page.get_all_text(ignore_tags=("script", "style", "nav", "footer", "header"))
    if hasattr(text, "clean"):
        text = text.clean()
    return " ".join(str(text).split())


def extract_webpage_clean_text(
    html: str,
    *,
    parser_backend: str = PARSER_HTML_TO_TEXT,
) -> dict[str, Any]:
    """Extract clean text using the requested parser backend."""
    backend = str(parser_backend or PARSER_HTML_TO_TEXT).strip().casefold()
    requested = backend
    scrapling_used = False
    fallback_reason: str | None = None

    if backend in {PARSER_SCRAPLING, "auto"}:
        if scrapling_parser_available():
            clean_text = extract_clean_text_scrapling(html)
            backend = PARSER_SCRAPLING
            scrapling_used = True
        else:
            clean_text = html_to_text(html)
            backend = PARSER_HTML_TO_TEXT
            fallback_reason = "scrapling_not_installed"
    else:
        clean_text = html_to_text(html)

    return {
        "clean_text": clean_text,
        "parser_backend": backend,
        "requested_backend": requested,
        "scrapling_available": scrapling_parser_available(),
        "scrapling_used": scrapling_used,
        "fallback_reason": fallback_reason,
    }
