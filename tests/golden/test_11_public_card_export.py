"""Golden Test 11: public card export contains only curated public fields."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
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

REQUIRED_CARD_FIELDS = (
    "id",
    "type",
    "title",
    "summary",
    "confidence",
    "concepts",
    "source_count",
    "public_detail_level",
    "updated_at",
)

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


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "public_card_export_test.sqlite"


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


def _run_base_graph(db_path: Path) -> str:
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
    return source_id


def _export(db_path: Path, export_dir: Path) -> dict:
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
    return json.loads((export_dir / "build_info.json").read_text(encoding="utf-8"))


def test_export_public_writes_curated_json_files(
    temp_db: Path, export_dir: Path
) -> None:
    _run_base_graph(temp_db)
    build_info = _export(temp_db, export_dir)

    for filename in ("public_cards.json", "public_memos.json", "build_info.json"):
        assert (export_dir / filename).is_file()

    cards = json.loads((export_dir / "public_cards.json").read_text(encoding="utf-8"))
    memos = json.loads((export_dir / "public_memos.json").read_text(encoding="utf-8"))

    assert isinstance(cards, list)
    assert len(cards) >= 2
    assert memos == []
    assert build_info["card_count"] == len(cards)
    assert build_info["memo_count"] == 0


def test_export_public_cards_include_required_fields_and_exclude_private_data(
    temp_db: Path, export_dir: Path
) -> None:
    _run_base_graph(temp_db)
    _export(temp_db, export_dir)

    cards = json.loads((export_dir / "public_cards.json").read_text(encoding="utf-8"))
    payload_text = (export_dir / "public_cards.json").read_text(encoding="utf-8")

    for card in cards:
        extra = set(card) - ALLOWED_CARD_FIELDS
        assert not extra, f"card {card.get('id')} has non-public fields: {extra}"
        for field in REQUIRED_CARD_FIELDS:
            assert field in card

    for pattern in FORBIDDEN_VALUE_PATTERNS:
        assert not pattern.search(payload_text), (
            f"export leaked forbidden content matching {pattern.pattern!r}"
        )

    assert "claim_ids" not in payload_text.casefold()
    assert "private_fields" not in payload_text.casefold()
    assert "raw_source_excerpt" not in payload_text


def test_export_public_fail_closed_on_unsafe_card(
    temp_db: Path, export_dir: Path
) -> None:
    from rge.cli import main
    from rge.db.connection import ensure_database
    from rge.db.repositories import PublicCardRepository

    _run_base_graph(temp_db)
    conn = ensure_database(temp_db)
    try:
        PublicCardRepository(conn).insert(
            card_id="card_unsafe_script",
            card_type="cluster_card",
            title="Unsafe card",
            summary="This card contains <script>alert('x')</script> content.",
            confidence="low",
            concepts=["AI assistance"],
            source_count=1,
            claim_ids=[],
            public_detail_level="summary",
            is_public_safe=True,
        )
    finally:
        conn.close()

    exit_code = main(
        [
            "export-public",
            "--db",
            str(temp_db),
            "--output-dir",
            str(export_dir),
        ]
    )
    assert exit_code == 1
    assert not (export_dir / "public_cards.json").exists()


def test_export_public_respects_limit(temp_db: Path, export_dir: Path) -> None:
    _run_base_graph(temp_db)
    from rge.cli import main

    assert (
        main(
            [
                "export-public",
                "--limit",
                "1",
                "--db",
                str(temp_db),
                "--output-dir",
                str(export_dir),
            ]
        )
        == 0
    )
    cards = json.loads((export_dir / "public_cards.json").read_text(encoding="utf-8"))
    assert len(cards) == 1
