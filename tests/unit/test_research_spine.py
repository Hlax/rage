"""Unit tests for research spine DB wiring."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.cli import main
from rge.db.connection import connect
from rge.modules.research_run import run_research_demo
from rge.modules.research_spine import wire_research_demo_to_db


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "research_spine.sqlite"


def test_wire_research_demo_to_db_ingests_and_extracts_claims(temp_db: Path) -> None:
    from rge.db.connection import ensure_database

    conn = ensure_database(temp_db)
    try:
        demo = run_research_demo(
            topic="AI creativity diversity",
            fixture_mode=True,
            top_sources=3,
            full_text_top_n=2,
            mode="full-text-augmented",
        )
        spine = wire_research_demo_to_db(
            conn,
            demo,
            domain="creativity",
            persist_claims=True,
            staging_dir=temp_db.parent / "staging",
        )
    finally:
        conn.close()

    assert spine["status"] == "completed"
    assert spine["accepted_claims_total"] >= 1
    assert any(
        row.get("status") in {"completed", "already_ingested", "ingested"}
        for row in spine["ingest_rows"]
    )

    conn = connect(temp_db)
    try:
        accepted = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE status = 'accepted'"
        ).fetchone()[0]
        assert accepted >= 1
    finally:
        conn.close()


def test_research_run_cli_db_persist_fixture_mode(
    temp_db: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "research-run",
            "--fixture-mode",
            "--topic",
            "AI creativity diversity",
            "--mode",
            "full-text-augmented",
            "--full-text-top-n",
            "2",
            "--db",
            str(temp_db),
            "--persist-claims",
            "--staging-dir",
            str(temp_db.parent / "staging"),
            "--out",
            str(temp_db.parent / "reports"),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["db_spine"]["accepted_claims_total"] >= 1
