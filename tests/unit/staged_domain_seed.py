"""Shared domain opposing-context seed helpers for staged pytest proofs."""

from __future__ import annotations

from pathlib import Path

from rge.cli import main
from rge.db.connection import connect

REPO_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_BASE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"


def seed_domain_opposing_context(temp_db: Path) -> None:
    """Seed GT7-style base graph so staged qualification has an opposing domain edge."""
    assert (
        main(
            [
                "ingest",
                str(DOMAIN_BASE_SOURCE),
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    conn = connect(temp_db)
    try:
        base_source_id = conn.execute("SELECT id FROM sources").fetchone()["id"]
    finally:
        conn.close()
    assert main(["extract-claims", "--source", base_source_id, "--db", str(temp_db)]) == 0
    assert main(["link-concepts", "--source", base_source_id, "--db", str(temp_db)]) == 0
    assert main(["build-relationships", "--source", base_source_id, "--db", str(temp_db)]) == 0
