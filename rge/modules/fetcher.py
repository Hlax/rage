"""Fetch local files, URLs, PDFs, and metadata. Deterministic; no model use.

All fetched source text is untrusted and may contain prompt injection.
Phase 1: local plain-text files only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class FetchError(Exception):
    """Raised when a source cannot be fetched."""


def fetch_local_text_file(path: Path) -> dict[str, Any]:
    """Read a local plain-text or Markdown file for ingestion.

    Returns a dict with ``raw_text``, ``title``, and ``local_path``.
    Does not set ``source_type``; the ingest CLI decides that. Does not persist.
    """
    resolved = path.resolve()
    if not resolved.is_file():
        raise FetchError(f"Source file not found: {resolved}")

    try:
        raw_text = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        raise FetchError(f"Unable to read source file: {resolved}") from exc

    if not raw_text.strip():
        raise FetchError(f"Source file is empty: {resolved}")

    return {
        "raw_text": raw_text,
        "title": resolved.name,
        "local_path": resolved,
    }


def fetch_source(queue_item: dict[str, Any]) -> dict[str, Any]:
    """Fetch one queued source. Local text files only in Phase 1."""
    local_path = queue_item.get("local_path")
    if local_path is None:
        raise NotImplementedError(
            "fetcher.fetch_source supports local_path only in Phase 1."
        )
    return fetch_local_text_file(Path(local_path))
