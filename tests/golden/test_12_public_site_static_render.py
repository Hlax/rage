"""Golden Test 12: public site renders exported cards in static mode."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = REPO_ROOT / "apps" / "public-site"
DATA_DIR = SITE_DIR / "public" / "data"
OUT_DIR = SITE_DIR / "out"

CARD_DETAIL_PAGE = SITE_DIR / "app" / "cards" / "[id]" / "page.tsx"
CONCEPT_DETAIL_PAGE = SITE_DIR / "app" / "concepts" / "[id]" / "page.tsx"
LIST_PAGE = SITE_DIR / "app" / "page.tsx"

FORBIDDEN_SOURCE_PATTERNS = (
    "dangerouslySetInnerHTML",
    "method=\"post\"",
    "method='post'",
    "method: 'POST'",
    'method: "POST"',
    "<form",
)


def _concept_slug(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", label.strip().lower()).strip("-")


def _static_html_path(base: Path, *segments: str) -> Path:
    """Next static export writes flat ``segment.html`` files."""
    if not segments:
        return base / "index.html"
    return base.joinpath(*segments[:-1], f"{segments[-1]}.html")


def _cards() -> list[dict]:
    return json.loads((DATA_DIR / "public_cards.json").read_text(encoding="utf-8"))


def test_static_detail_route_files_exist() -> None:
    assert CARD_DETAIL_PAGE.is_file(), "missing card detail route"
    assert CONCEPT_DETAIL_PAGE.is_file(), "missing concept detail route"


def test_detail_routes_declare_generate_static_params() -> None:
    for path in (CARD_DETAIL_PAGE, CONCEPT_DETAIL_PAGE):
        text = path.read_text(encoding="utf-8")
        assert "generateStaticParams" in text, f"{path} must pre-render static paths"


def test_list_page_links_to_card_and_concept_routes() -> None:
    text = LIST_PAGE.read_text(encoding="utf-8")
    assert "next/link" in text
    assert "/cards/" in text
    assert "/concepts/" in text
    assert "Last updated:" in text
    assert "buildInfo.generated_at" in text


def test_public_site_source_has_no_write_or_unsafe_patterns() -> None:
    source_files = [
        *SITE_DIR.glob("app/**/*.tsx"),
        *SITE_DIR.glob("app/**/*.ts"),
        *SITE_DIR.glob("lib/**/*.ts"),
        SITE_DIR / "next.config.js",
    ]
    for path in source_files:
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_SOURCE_PATTERNS:
            assert pattern not in text, f"{path} contains forbidden pattern: {pattern}"


def test_static_export_json_includes_golden_card_ids() -> None:
    cards = _cards()
    ids = {card["id"] for card in cards}
    assert "card_golden_diversity_001" in ids
    assert "card_golden_originality_002" in ids


def test_static_export_html_pages_exist() -> None:
    """Requires a prior ``npm run build`` (see ticket-015 test_plan)."""
    if not (OUT_DIR / "index.html").is_file():
        pytest.skip("Run `cd apps/public-site && npm run build` before this test")

    cards = _cards()
    assert cards, "public_cards.json must not be empty for GT12"

    index_html = (OUT_DIR / "index.html").read_text(encoding="utf-8")
    assert "Last updated:" in index_html
    assert cards[0]["title"] in index_html

    for card in cards:
        card_page = _static_html_path(OUT_DIR, "cards", card["id"])
        assert card_page.is_file(), f"missing static export for card {card['id']}"
        card_html = card_page.read_text(encoding="utf-8")
        assert card["title"] in card_html
        assert card["summary"] in card_html

    concept_slugs = sorted(
        {_concept_slug(concept) for card in cards for concept in card["concepts"]}
    )
    for slug in concept_slugs:
        concept_page = _static_html_path(OUT_DIR, "concepts", slug)
        assert concept_page.is_file(), f"missing static export for concept {slug}"
