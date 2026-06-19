"""Golden tests for MVP P5/P6/P7 research demo loop."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


def test_research_run_fixture_mode_cli() -> None:
    from rge.cli import main

    assert (
        main(
            [
                "research-run",
                "--fixture-mode",
                "--topic",
                "AI creativity diversity",
                "--top-sources",
                "3",
                "--full-text-top-n",
                "2",
            ]
        )
        == 0
    )


def test_document_parser_tei_fixture_is_clean() -> None:
    from pathlib import Path

    from rge.modules.document_parser import CLEAN_TEXT_READY, parse_document_file

    path = (
        Path(__file__).resolve().parents[2]
        / "fixtures"
        / "source_documents"
        / "manual_oa_tei.xml"
    )
    result = parse_document_file(path)
    assert result.source_status == CLEAN_TEXT_READY


def test_selective_fulltext_does_not_fail_whole_run() -> None:
    from rge.modules.research_run import run_research_demo

    payload = run_research_demo(
        topic="AI creativity",
        fixture_mode=True,
        full_text_top_n=3,
    )
    assert payload["selective_fulltext"]["acquisition_count"] >= 1
