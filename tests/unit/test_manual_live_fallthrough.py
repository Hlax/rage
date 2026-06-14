"""Unit tests for manual_text live extraction fall-through (ticket-112)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.llm.schemas import CandidateClaimBatch_v0_1, SCHEMA_VERSION_0_1_0
from rge.modules.live_extraction_write import (
    LiveExtractionWriteError,
    assert_checksum_not_in_fixture_map,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNTHNOTE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "manual_synthnote.txt"
ARBITRARY_SOURCE_TEXT = (
    "Ticket-112 arbitrary manual source.\n\n"
    "Researchers noted that human-AI songwriting pairs completed draft verses "
    "faster in this workshop setting. However, teams also reused similar rhyme "
    "schemes more often in this workshop setting."
)
ARBITRARY_CHUNK_QUOTE = (
    "Researchers noted that human-AI songwriting pairs completed draft verses "
    "faster in this workshop setting."
)


class _StubOllamaClient:
    provider = "ollama"
    model = "stub-qwen"

    def extract_claims(self, **kwargs: object) -> CandidateClaimBatch_v0_1:
        chunk = kwargs["chunk"]
        chunk_text = chunk["chunk_text"]
        return CandidateClaimBatch_v0_1.model_validate(
            {
                "task_name": "claim_extraction",
                "schema_version": SCHEMA_VERSION_0_1_0,
                "items": [
                    {
                        "claim_text": (
                            "Human-AI songwriting pairs completed draft verses "
                            "faster in this workshop setting."
                        ),
                        "quote_span": ARBITRARY_CHUNK_QUOTE,
                        "scope": "this workshop setting",
                        "subject": "Human-AI songwriting pairs",
                        "predicate": "completed",
                        "object": "draft verses faster",
                        "evidence_type": "empirical",
                        "confidence": 0.7,
                        "limitations": [],
                        "domain": "creativity",
                        "domain_metadata": {},
                    },
                    {
                        "claim_text": "Teams reused similar rhyme schemes more often.",
                        "quote_span": "teams also reused similar rhyme schemes more often",
                        "scope": "this workshop setting",
                        "subject": "Teams",
                        "predicate": "reused",
                        "object": "similar rhyme schemes",
                        "evidence_type": "empirical",
                        "confidence": 0.6,
                        "limitations": [],
                        "domain": "creativity",
                        "domain_metadata": {},
                    },
                ],
            }
        )


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "manual_live_fallthrough.sqlite"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior_mode = os.environ.get("RGE_LLM_MODE")
    prior_live = os.environ.get("RGE_ALLOW_LIVE_LLM")
    os.environ["RGE_LLM_MODE"] = "mock"
    os.environ["RGE_ALLOW_LIVE_LLM"] = "0"
    yield
    if prior_mode is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior_mode
    if prior_live is None:
        os.environ.pop("RGE_ALLOW_LIVE_LLM", None)
    else:
        os.environ["RGE_ALLOW_LIVE_LLM"] = prior_live


def _ingest_arbitrary_manual_source(db_path: Path) -> str:
    source_path = db_path.parent / "arbitrary_manual.txt"
    source_path.write_text(ARBITRARY_SOURCE_TEXT, encoding="utf-8")
    from rge.cli import main

    assert (
        main(
            [
                "ingest",
                str(source_path),
                "--domain",
                "creativity",
                "--source-type",
                "manual_text",
                "--source-title",
                "Ticket-112 arbitrary manual source",
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    from rge.db.connection import connect

    conn = connect(db_path)
    try:
        row = conn.execute("SELECT id FROM sources").fetchone()
        assert row is not None
        return str(row["id"])
    finally:
        conn.close()


def test_checksum_pinned_manual_source_still_uses_mock_fixture(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    assert (
        main(
            [
                "ingest",
                str(SYNTHNOTE_SOURCE),
                "--domain",
                "creativity",
                "--source-type",
                "manual_text",
                "--source-title",
                "Synthetic Source Note",
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    conn = connect(temp_db)
    try:
        source_id = conn.execute("SELECT id FROM sources").fetchone()["id"]
    finally:
        conn.close()

    assert main(["extract-claims", "--source", source_id, "--db", str(temp_db)]) == 0

    conn = connect(temp_db)
    try:
        accepted = conn.execute(
            "SELECT COUNT(*) AS n FROM claims WHERE status = 'accepted'"
        ).fetchone()["n"]
        rejected = conn.execute(
            "SELECT COUNT(*) AS n FROM claims WHERE status = 'rejected'"
        ).fetchone()["n"]
        assert accepted == 2
        assert rejected == 1
    finally:
        conn.close()


def test_unknown_manual_text_in_mock_mode_raises_clear_error(temp_db: Path) -> None:
    from rge.cli import main

    source_id = _ingest_arbitrary_manual_source(temp_db)
    exit_code = main(["extract-claims", "--source", source_id, "--db", str(temp_db)])
    assert exit_code == 1


def test_live_manual_fallthrough_blocked_without_live_opt_in(temp_db: Path) -> None:
    from rge.cli import main

    source_id = _ingest_arbitrary_manual_source(temp_db)
    exit_code = main(
        [
            "extract-claims",
            "--source",
            source_id,
            "--db",
            str(temp_db),
            "--live-manual-fallthrough",
        ]
    )
    assert exit_code == 1


def test_live_manual_fallthrough_blocked_on_default_graph_db(temp_db: Path) -> None:
    from rge.cli import main

    source_id = _ingest_arbitrary_manual_source(temp_db)
    with patch.dict(
        os.environ,
        {"RGE_LLM_MODE": "ollama", "RGE_ALLOW_LIVE_LLM": "1"},
        clear=False,
    ):
        exit_code = main(
            [
                "extract-claims",
                "--source",
                source_id,
                "--db",
                "data/db/creative_research.sqlite",
                "--live-manual-fallthrough",
            ]
        )
    assert exit_code == 1


def test_mocked_live_fallthrough_persists_validated_claims(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    source_id = _ingest_arbitrary_manual_source(temp_db)
    with patch.dict(
        os.environ,
        {"RGE_LLM_MODE": "ollama", "RGE_ALLOW_LIVE_LLM": "1"},
        clear=False,
    ):
        with patch(
            "rge.modules.live_extraction_write.assert_ollama_health",
            return_value={"model_available": True},
        ):
            with patch(
                "rge.modules.live_extraction_write.get_model_client",
                return_value=_StubOllamaClient(),
            ):
                exit_code = main(
                    [
                        "extract-claims",
                        "--source",
                        source_id,
                        "--db",
                        str(temp_db),
                        "--live-manual-fallthrough",
                    ]
                )
    assert exit_code == 0

    conn = connect(temp_db)
    try:
        accepted = conn.execute(
            "SELECT claim_text, scope FROM claims WHERE status = 'accepted'"
        ).fetchall()
        rejected = conn.execute(
            "SELECT rejection_reason FROM claims WHERE status = 'rejected'"
        ).fetchall()
        assert len(accepted) >= 1
        assert any("workshop setting" in row["scope"] for row in accepted)
        assert len(rejected) >= 1
        quotes = conn.execute("SELECT quote_text FROM claim_quotes").fetchall()
        assert len(quotes) >= 1
    finally:
        conn.close()


def test_assert_checksum_rejects_synthnote_fixture_map_entry() -> None:
    mapping_path = REPO_ROOT / "fixtures" / "manual_source_fixture_map.json"
    checksums = json.loads(mapping_path.read_text(encoding="utf-8"))
    pinned = next(iter(checksums))
    with pytest.raises(LiveExtractionWriteError, match="fixture_map"):
        assert_checksum_not_in_fixture_map(pinned)
