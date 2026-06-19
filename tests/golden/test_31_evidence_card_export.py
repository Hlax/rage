"""Golden Test 31: operator-private evidence card export."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "evidence_card_export.sqlite"


@pytest.fixture()
def export_dir(tmp_path: Path) -> Path:
    return tmp_path / "evidence_card_exports"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def test_export_evidence_cards_cli_emits_canonical_bundle(
    temp_db: Path,
    export_dir: Path,
) -> None:
    from rge.cli import main

    assert (
        main(
            [
                "ingest",
                str(BASE_SOURCE),
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    from rge.db.connection import connect

    conn = connect(temp_db)
    try:
        source_id = conn.execute("SELECT id FROM sources").fetchone()[0]
    finally:
        conn.close()

    assert main(["extract-claims", "--source", source_id, "--db", str(temp_db)]) == 0
    assert (
        main(
            [
                "export-evidence-cards",
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
                "--output-dir",
                str(export_dir),
                "--limit",
                "10",
            ]
        )
        == 0
    )

    bundle = json.loads((export_dir / "evidence_cards.json").read_text(encoding="utf-8"))
    assert bundle["card_count"] >= 1
    assert bundle["evidence_cards"][0]["schema_version"] == "evidence_card_v0.1.0"
    assert bundle["evidence_cards"][0]["quote"]
    assert bundle["atlas_safe_previews"][0]["summary"]
    assert "quote" not in bundle["atlas_safe_previews"][0]
