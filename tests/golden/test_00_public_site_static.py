"""Golden Test 00: public site placeholder is static and safe.

Verifies the static JSON data files exist and parse, public cards carry only
curated public fields, and the placeholder site source contains no write/
ingestion/agent routes and no raw HTML rendering. Does not run npm; the
static build itself is verified by `cd apps/public-site && npm run build`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = REPO_ROOT / "apps" / "public-site"
DATA_DIR = SITE_DIR / "public" / "data"

ALLOWED_CARD_FIELDS = {
    "id",
    "type",
    "title",
    "summary",
    "confidence",
    "concepts",
    "source_count",
    "public_caveats",
    "public_source_metadata",
    "related_cards",
    "public_detail_level",
    "updated_at",
}

FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"[A-Za-z]:\\"),          # Windows local paths
    re.compile(r"/(?:home|Users)/\w+"),   # Unix local paths
    re.compile(r"sk-[A-Za-z0-9]{16,}"),   # API-key-like strings
    re.compile(r"api[_-]?key", re.IGNORECASE),
    re.compile(r"<script", re.IGNORECASE),
)


def _iter_strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)


def test_static_data_files_exist_and_parse() -> None:
    for filename in ("public_cards.json", "public_memos.json", "build_info.json"):
        path = DATA_DIR / filename
        assert path.is_file(), f"missing static data file: {filename}"
        json.loads(path.read_text(encoding="utf-8"))


def test_public_cards_have_only_curated_public_fields() -> None:
    cards = json.loads((DATA_DIR / "public_cards.json").read_text(encoding="utf-8"))
    assert isinstance(cards, list)
    for card in cards:
        extra = set(card) - ALLOWED_CARD_FIELDS
        assert not extra, f"card {card.get('id')} has non-public fields: {extra}"


def test_public_data_contains_no_forbidden_content() -> None:
    for filename in ("public_cards.json", "public_memos.json", "build_info.json"):
        payload = json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))
        for text in _iter_strings(payload):
            for pattern in FORBIDDEN_VALUE_PATTERNS:
                assert not pattern.search(text), (
                    f"{filename} contains forbidden content "
                    f"matching {pattern.pattern!r}: {text!r}"
                )


def test_site_has_no_api_routes() -> None:
    assert not (SITE_DIR / "app" / "api").exists(), "public site must not have API routes"
    assert not (SITE_DIR / "pages" / "api").exists(), "public site must not have API routes"


def test_site_source_has_no_write_or_unsafe_patterns() -> None:
    forbidden_source_patterns = (
        "dangerouslySetInnerHTML",
        "method=\"post\"",
        "method='post'",
        "method: 'POST'",
        'method: "POST"',
        "PUT",
        "DELETE",
        "<form",
    )
    source_files = [
        *SITE_DIR.glob("app/**/*.tsx"),
        *SITE_DIR.glob("app/**/*.ts"),
        SITE_DIR / "next.config.js",
    ]
    assert source_files, "expected public site source files"
    for path in source_files:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden_source_patterns:
            assert pattern not in text, f"{path.name} contains forbidden pattern: {pattern}"


def test_site_is_configured_for_static_export() -> None:
    config_text = (SITE_DIR / "next.config.js").read_text(encoding="utf-8")
    assert "output" in config_text and "export" in config_text
