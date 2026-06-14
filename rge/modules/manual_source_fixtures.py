"""Resolve mock LLM fixtures for manual_text sources by content checksum."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MANUAL_SOURCE_FIXTURE_MAP_PATH = _REPO_ROOT / "fixtures" / "manual_source_fixture_map.json"


def _manual_source_map_entry(checksum: str) -> dict[str, Any] | str | None:
    if not _MANUAL_SOURCE_FIXTURE_MAP_PATH.is_file():
        return None
    mapping: dict[str, Any] = json.loads(
        _MANUAL_SOURCE_FIXTURE_MAP_PATH.read_text(encoding="utf-8")
    )
    return mapping.get(checksum)


def resolve_manual_source_fixture(checksum: str, task: str) -> str | None:
    """Return fixture filename for a manual source checksum and pipeline task."""
    entry = _manual_source_map_entry(checksum)
    if isinstance(entry, str):
        return entry if task == "extract_claims" else None
    if isinstance(entry, dict):
        value = entry.get(task)
        return str(value) if value else None
    return None


def contradiction_claim_hints_for_manual_source(source: Any | None) -> dict[str, str] | None:
    if source is None or getattr(source, "source_type", None) != "manual_text":
        return None
    checksum = getattr(source, "raw_text_checksum", None)
    if not checksum:
        return None
    entry = _manual_source_map_entry(str(checksum))
    if not isinstance(entry, dict):
        return None
    hints = entry.get("contradiction_claim_hints")
    if not isinstance(hints, dict):
        return None
    return {str(key): str(value) for key, value in hints.items() if value}


def contradiction_fixture_for_manual_source(source: Any | None) -> str | None:
    if source is None or getattr(source, "source_type", None) != "manual_text":
        return None
    checksum = getattr(source, "raw_text_checksum", None)
    if not checksum:
        return None
    return resolve_manual_source_fixture(str(checksum), "detect_contradictions")


def link_fixture_for_manual_source(source: Any | None) -> str | None:
    if source is None or getattr(source, "source_type", None) != "manual_text":
        return None
    checksum = getattr(source, "raw_text_checksum", None)
    if not checksum:
        return None
    return resolve_manual_source_fixture(str(checksum), "link_concepts")


def relationship_fixture_for_manual_source(source: Any | None) -> str | None:
    if source is None or getattr(source, "source_type", None) != "manual_text":
        return None
    checksum = getattr(source, "raw_text_checksum", None)
    if not checksum:
        return None
    return resolve_manual_source_fixture(str(checksum), "build_relationships")


def extract_fixture_for_manual_source(source: Any | None) -> str | None:
    if source is None or getattr(source, "source_type", None) != "manual_text":
        return None
    checksum = getattr(source, "raw_text_checksum", None)
    if not checksum:
        return None
    return resolve_manual_source_fixture(str(checksum), "extract_claims")


def manual_text_lacks_extract_fixture(source: Any | None) -> bool:
    """Return True when a manual_text source has no checksum-pinned extract fixture."""
    if source is None or getattr(source, "source_type", None) != "manual_text":
        return False
    return extract_fixture_for_manual_source(source) is None


def manual_text_lacks_link_fixture(source: Any | None) -> bool:
    """Return True when a manual_text source has no checksum-pinned link fixture."""
    if source is None or getattr(source, "source_type", None) != "manual_text":
        return False
    return link_fixture_for_manual_source(source) is None


def manual_text_lacks_relationship_fixture(source: Any | None) -> bool:
    """Return True when a manual_text source has no checksum-pinned relationship fixture."""
    if source is None or getattr(source, "source_type", None) != "manual_text":
        return False
    return relationship_fixture_for_manual_source(source) is None
