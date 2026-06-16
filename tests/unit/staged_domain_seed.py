"""Shared domain opposing-context seed helpers for staged pytest proofs."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from rge.cli import main
from rge.db.connection import connect

REPO_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_BASE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"


@contextmanager
def _mock_llm_seed_env() -> Iterator[None]:
    """Force mock LLM for GT7 seed spine steps regardless of operator live env."""
    prior_mode = os.environ.get("RGE_LLM_MODE")
    prior_allow = os.environ.get("RGE_ALLOW_LIVE_LLM")
    os.environ["RGE_LLM_MODE"] = "mock"
    os.environ["RGE_ALLOW_LIVE_LLM"] = "0"
    try:
        yield
    finally:
        if prior_mode is None:
            os.environ.pop("RGE_LLM_MODE", None)
        else:
            os.environ["RGE_LLM_MODE"] = prior_mode
        if prior_allow is None:
            os.environ.pop("RGE_ALLOW_LIVE_LLM", None)
        else:
            os.environ["RGE_ALLOW_LIVE_LLM"] = prior_allow


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
    with _mock_llm_seed_env():
        assert main(["extract-claims", "--source", base_source_id, "--db", str(temp_db)]) == 0
        assert main(["link-concepts", "--source", base_source_id, "--db", str(temp_db)]) == 0
        assert main(["build-relationships", "--source", base_source_id, "--db", str(temp_db)]) == 0
