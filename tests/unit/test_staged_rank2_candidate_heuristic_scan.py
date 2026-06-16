"""Unit tests for rank-2 staged candidate heuristic scan (ticket-251)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.config import ConfigError, load_config, parse_staged_rank2_scan_max
from rge.db.connection import ensure_database
from rge.modules.staged_candidate_selection import (
    Rank2StagedCandidateNotFoundError,
    select_rank1_staged_candidate_id,
    select_rank2_staged_candidate_id,
)

QUESTION_ID = "rq_rank2_heuristic_scan"
RANK1_TITLE = "Human-AI co-creativity and semantic diversity in songwriting workshops"
RANK2_OFFSET1_TITLE = "Unrelated creativity paper without staged markers"
RANK2_MATCH_TITLE = "Constraint management in AI-assisted creative teams"


def _insert_candidate(
    conn,
    *,
    candidate_id: str,
    title: str,
    priority_score: float,
) -> None:
    conn.execute(
        """
        INSERT INTO candidate_sources (
            id, research_question_id, contract_id, title, url, source_type,
            reason, relevance_score, credibility_prior, gap_fill_score,
            recency_score, source_diversity_score, novelty_score, drift_risk,
            priority_score, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            candidate_id,
            QUESTION_ID,
            "contract_golden_v0",
            title,
            f"https://example.org/{candidate_id}.html",
            "peer_reviewed_empirical",
            "test",
            priority_score,
            0.8,
            0.5,
            0.5,
            0.5,
            0.5,
            0.1,
            priority_score,
            "queued",
        ),
    )


@pytest.fixture()
def conn(tmp_path: Path):
    database = ensure_database(tmp_path / "rank2_scan.sqlite")
    _insert_candidate(
        database,
        candidate_id="disc_rank1",
        title=RANK1_TITLE,
        priority_score=0.95,
    )
    _insert_candidate(
        database,
        candidate_id="disc_rank2_miss",
        title=RANK2_OFFSET1_TITLE,
        priority_score=0.85,
    )
    _insert_candidate(
        database,
        candidate_id="disc_rank3_hit",
        title=RANK2_MATCH_TITLE,
        priority_score=0.75,
    )
    database.commit()
    yield database
    database.close()


def test_select_rank1_unchanged_offset_zero(conn) -> None:
    assert select_rank1_staged_candidate_id(conn, QUESTION_ID) == "disc_rank1"


def test_select_rank2_scans_past_offset_one_for_title_match(conn) -> None:
    assert select_rank2_staged_candidate_id(conn, QUESTION_ID) == "disc_rank3_hit"


def test_select_rank2_not_found_payload_includes_scan_metadata(tmp_path: Path) -> None:
    database = ensure_database(tmp_path / "rank2_scan_miss.sqlite")
    _insert_candidate(
        database,
        candidate_id="disc_rank1",
        title=RANK1_TITLE,
        priority_score=0.95,
    )
    _insert_candidate(
        database,
        candidate_id="disc_rank2_miss",
        title=RANK2_OFFSET1_TITLE,
        priority_score=0.85,
    )
    database.commit()

    with pytest.raises(Rank2StagedCandidateNotFoundError) as exc_info:
        select_rank2_staged_candidate_id(database, QUESTION_ID, max_scan=5)

    payload = exc_info.value.to_skip_payload()
    assert payload["reason"] == "unsuitable_live_rank2_artifact"
    assert payload["scanned_candidates"] == 1
    assert payload["candidate_ids"] == ["disc_rank2_miss"]
    assert payload["max_scan"] == 5
    database.close()


def test_select_rank2_requires_minimum_candidate_count(conn) -> None:
    conn.execute("DELETE FROM candidate_sources WHERE id IN ('disc_rank2_miss', 'disc_rank3_hit')")
    conn.commit()
    with pytest.raises(ValueError, match="at least 2 candidates"):
        select_rank2_staged_candidate_id(conn, QUESTION_ID)


def test_select_rank2_honors_env_scan_max_override(
    conn, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RGE_STAGED_RANK2_SCAN_MAX", "1")
    with pytest.raises(Rank2StagedCandidateNotFoundError) as exc_info:
        select_rank2_staged_candidate_id(conn, QUESTION_ID)
    assert exc_info.value.max_scan == 1
    assert exc_info.value.scanned_candidates == 1

    monkeypatch.setenv("RGE_STAGED_RANK2_SCAN_MAX", "2")
    assert select_rank2_staged_candidate_id(conn, QUESTION_ID) == "disc_rank3_hit"


def test_parse_staged_rank2_scan_max_rejects_out_of_range() -> None:
    with pytest.raises(ConfigError, match="out of range"):
        parse_staged_rank2_scan_max("0")
    with pytest.raises(ConfigError, match="out of range"):
        parse_staged_rank2_scan_max("51")


def test_load_config_includes_staged_rank2_scan_max(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_STAGED_RANK2_SCAN_MAX", "15")
    config = load_config()
    assert config.staged_rank2_scan_max == 15


def test_live_staged_wrapper_skips_when_no_title_match(tmp_path: Path) -> None:
    from tests.unit.live_staged_candidates import select_rank2_candidate_id

    database = ensure_database(tmp_path / "rank2_scan_wrapper.sqlite")
    _insert_candidate(
        database,
        candidate_id="disc_rank1",
        title=RANK1_TITLE,
        priority_score=0.95,
    )
    _insert_candidate(
        database,
        candidate_id="disc_rank2_miss",
        title=RANK2_OFFSET1_TITLE,
        priority_score=0.85,
    )
    database.commit()

    with pytest.raises(pytest.skip.Exception) as exc_info:
        select_rank2_candidate_id(database, QUESTION_ID)

    payload = json.loads(str(exc_info.value))
    assert payload["reason"] == "unsuitable_live_rank2_artifact"
    assert payload["scanned_candidates"] == 1
    database.close()
