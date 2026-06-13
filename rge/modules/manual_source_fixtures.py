"""Resolve mock LLM fixtures for manual_text sources by content checksum."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MANUAL_SOURCE_FIXTURE_MAP_PATH = _REPO_ROOT / "fixtures" / "manual_source_fixture_map.json"


def resolve_manual_source_fixture(checksum: str, task: str) -> str | None:
    """Return fixture filename for a manual source checksum and pipeline task."""
    if not _MANUAL_SOURCE_FIXTURE_MAP_PATH.is_file():
        return None
    mapping: dict[str, Any] = json.loads(
        _MANUAL_SOURCE_FIXTURE_MAP_PATH.read_text(encoding="utf-8")
    )
    entry = mapping.get(checksum)
    if isinstance(entry, str):
        return entry if task == "extract_claims" else None
    if isinstance(entry, dict):
        value = entry.get(task)
        return str(value) if value else None
    return None


def link_fixture_for_manual_source(source: Any | None) -> str | None:
    if source is None or getattr(source, "source_type", None) != "manual_text":
        return None
    checksum = getattr(source, "raw_text_checksum", None)
    if not checksum:
        return None
    return resolve_manual_source_fixture(str(checksum), "link_concepts")


def extract_fixture_for_manual_source(source: Any | None) -> str | None:
    if source is None or getattr(source, "source_type", None) != "manual_text":
        return None
    checksum = getattr(source, "raw_text_checksum", None)
    if not checksum:
        return None
    return resolve_manual_source_fixture(str(checksum), "extract_claims")
