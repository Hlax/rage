"""Unit tests for live extraction write gates (mock-only; no Ollama)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.modules.live_extraction_write import (
    LiveExtractionWriteError,
    assert_checksum_not_in_fixture_map,
    is_default_graph_db,
)


def test_assert_checksum_rejects_manual_fixture_map_entry() -> None:
    mapping_path = (
        Path(__file__).resolve().parents[2]
        / "fixtures"
        / "manual_source_fixture_map.json"
    )
    checksums = json.loads(mapping_path.read_text(encoding="utf-8"))
    pinned = next(iter(checksums))
    with pytest.raises(LiveExtractionWriteError, match="fixture_map"):
        assert_checksum_not_in_fixture_map(pinned)


def test_assert_checksum_allows_unknown_source() -> None:
    assert_checksum_not_in_fixture_map("0" * 64)


def test_is_default_graph_db_detects_creative_research_path() -> None:
    assert is_default_graph_db(Path("data/db/creative_research.sqlite"))


def test_extract_claims_live_cli_rejects_default_db(tmp_path: Path) -> None:
    from rge.cli import main

    with patch.dict(
        "os.environ",
        {"RGE_LLM_MODE": "ollama", "RGE_ALLOW_LIVE_LLM": "1"},
        clear=False,
    ):
        exit_code = main(
            [
                "extract-claims-live",
                "--source",
                "src_test",
                "--db",
                "data/db/creative_research.sqlite",
            ]
        )
    assert exit_code == 1


def test_extract_claims_live_cli_requires_live_opt_in() -> None:
    from rge.cli import main

    with patch.dict(
        "os.environ",
        {"RGE_LLM_MODE": "mock", "RGE_ALLOW_LIVE_LLM": "0"},
        clear=False,
    ):
        exit_code = main(
            [
                "extract-claims-live",
                "--source",
                "src_test",
                "--db",
                "data/db/live_research_evidence.sqlite",
            ]
        )
    assert exit_code == 1
