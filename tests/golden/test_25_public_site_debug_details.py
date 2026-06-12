"""Golden Test 25: public site debug details without private data exposure."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

from rge.modules.card_exporter import GOLDEN_PRIVATE_FIELDS

REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = REPO_ROOT / "apps" / "public-site"
DATA_DIR = SITE_DIR / "public" / "data"
CARD_DETAIL_PAGE = SITE_DIR / "app" / "cards" / "[id]" / "page.tsx"
FIXTURE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"

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
    "evidence_type",
    "public_run_timestamp",
    "updated_at",
}

FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"/(?:home|Users)/\w+"),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"api[_-]?key", re.IGNORECASE),
    re.compile(r"<script", re.IGNORECASE),
    re.compile(r"IGNORE ALL PREVIOUS INSTRUCTIONS", re.IGNORECASE),
    re.compile(r"prompt template", re.IGNORECASE),
    re.compile(r"evaluator notes", re.IGNORECASE),
)

FORBIDDEN_PRIVATE_KEYS = tuple(GOLDEN_PRIVATE_FIELDS.keys())


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "public_site_debug_test.sqlite"


@pytest.fixture()
def export_dir(tmp_path: Path) -> Path:
    return tmp_path / "export"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def _run_base_graph(db_path: Path) -> None:
    from rge.cli import main

    assert (
        main(
            [
                "ingest",
                str(FIXTURE_SOURCE),
                "--domain",
                "creativity",
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    from rge.db.connection import connect

    conn = connect(db_path)
    try:
        source_id = conn.execute("SELECT id FROM sources").fetchone()[0]
    finally:
        conn.close()
    assert main(["extract-claims", "--source", source_id, "--db", str(db_path)]) == 0
    assert main(["link-concepts", "--source", source_id, "--db", str(db_path)]) == 0
    assert (
        main(["build-relationships", "--source", source_id, "--db", str(db_path)]) == 0
    )


def _export(db_path: Path, export_dir: Path) -> list[dict]:
    from rge.cli import main

    assert (
        main(
            [
                "export-public",
                "--limit",
                "100",
                "--db",
                str(db_path),
                "--output-dir",
                str(export_dir),
            ]
        )
        == 0
    )
    return json.loads((export_dir / "public_cards.json").read_text(encoding="utf-8"))


def test_export_includes_public_debug_fields(temp_db: Path, export_dir: Path) -> None:
    _run_base_graph(temp_db)
    cards = _export(temp_db, export_dir)
    payload_text = (export_dir / "public_cards.json").read_text(encoding="utf-8")

    assert cards, "export must include at least one public card"
    for card in cards:
        extra = set(card) - ALLOWED_CARD_FIELDS
        assert not extra, f"card {card.get('id')} has non-public fields: {extra}"
        assert card.get("evidence_type"), f"card {card.get('id')} missing evidence_type"
        assert card.get("public_run_timestamp"), (
            f"card {card.get('id')} missing public_run_timestamp"
        )

    for pattern in FORBIDDEN_VALUE_PATTERNS:
        assert not pattern.search(payload_text), (
            f"export leaked forbidden content matching {pattern.pattern!r}"
        )


def test_export_excludes_private_db_fields(temp_db: Path, export_dir: Path) -> None:
    _run_base_graph(temp_db)
    cards = _export(temp_db, export_dir)
    payload_text = (export_dir / "public_cards.json").read_text(encoding="utf-8").casefold()

    for key in FORBIDDEN_PRIVATE_KEYS:
        assert key.casefold() not in payload_text, f"export leaked private key {key}"
    for value in GOLDEN_PRIVATE_FIELDS.values():
        assert str(value).casefold() not in payload_text, (
            f"export leaked private value: {value!r}"
        )

    assert "private_fields" not in payload_text
    assert "claim_ids" not in payload_text


def test_card_detail_page_renders_debug_section_without_private_fields() -> None:
    text = CARD_DETAIL_PAGE.read_text(encoding="utf-8")

    assert "Research debug details" in text
    assert "Evidence type" in text
    assert "Public run timestamp" in text
    assert "evidence_type" in text
    assert "public_run_timestamp" in text
    assert "dangerouslySetInnerHTML" not in text

    for key in FORBIDDEN_PRIVATE_KEYS:
        assert key not in text, f"card detail page references private field {key}"


def test_static_public_cards_json_includes_debug_fields() -> None:
    cards = json.loads((DATA_DIR / "public_cards.json").read_text(encoding="utf-8"))
    assert cards, "committed public_cards.json must not be empty"

    for card in cards:
        assert card.get("evidence_type"), f"static card {card.get('id')} missing evidence_type"
        assert card.get("public_run_timestamp"), (
            f"static card {card.get('id')} missing public_run_timestamp"
        )
