"""Golden tests for research spine DB integration."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


def test_research_run_fixture_db_persist_cli(tmp_path: Path) -> None:
    from rge.cli import main

    db_path = tmp_path / "research.sqlite"
    assert (
        main(
            [
                "research-run",
                "--fixture-mode",
                "--mode",
                "full-text-augmented",
                "--full-text-top-n",
                "1",
                "--db",
                str(db_path),
                "--persist-claims",
                "--out",
                str(tmp_path / "reports"),
            ]
        )
        == 0
    )
    assert db_path.is_file()
