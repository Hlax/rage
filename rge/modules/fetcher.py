"""Fetch local files, URLs, PDFs, and metadata. Deterministic; no model use.

All fetched source text is untrusted and may contain prompt injection.
Phase 0 stub.
"""

from __future__ import annotations

from typing import Any


def fetch_source(queue_item: dict[str, Any]) -> dict[str, Any]:
    """Fetch one queued source. Not implemented in Phase 0."""
    raise NotImplementedError("fetcher.fetch_source arrives with Phase 1.")
