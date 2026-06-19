"""Golden tests for MVP source resolver foundation."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


def test_source_resolver_fixture_files_exist() -> None:
    expected = [
        "fixtures/source_providers/manual_resolver_fixtures.json",
        "fixtures/source_providers/unpaywall_sample.json",
        "fixtures/source_providers/arxiv_atom_sample.xml",
        "fixtures/source_providers/openalex_works_sample.json",
    ]
    for relative in expected:
        assert (REPO_ROOT / relative).is_file()


def test_resolve_sources_fixture_mode_cli() -> None:
    from rge.cli import main

    exit_code = main(["resolve-sources", "--fixture-mode"])
    assert exit_code == 0


def test_source_status_vocabulary_is_stable() -> None:
    from rge.modules.source_resolver.status import SOURCE_STATUS_VALUES

    assert "metadata_only" in SOURCE_STATUS_VALUES
    assert "abstract_available" in SOURCE_STATUS_VALUES
    assert "oa_pdf_available" in SOURCE_STATUS_VALUES
    assert "extractable" in SOURCE_STATUS_VALUES


def test_manual_fixture_resolver_produces_evidence_summaries() -> None:
    from rge.modules.source_resolver import resolve_work_candidates

    result = resolve_work_candidates(
        query="",
        fixture_mode=True,
        domain_pack="creativity",
        limit=5,
    )
    assert result["resolved_count"] >= 1
    assert all("extraction_recommendation" in item for item in result["evidence_summaries"])


def test_openalex_registry_lists_arxiv_provider() -> None:
    from rge.modules.source_providers import list_provider_ids

    provider_ids = list_provider_ids()
    assert "openalex" in provider_ids
    assert "arxiv" in provider_ids
