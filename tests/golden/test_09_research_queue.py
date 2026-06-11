"""Golden Test 9: research queue ranks sources by relevance, credibility, and gap value."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RANKING_FIXTURE = (
    REPO_ROOT / "fixtures" / "candidate_sources" / "source_ranking_fixture.json"
)
EMPIRICAL_ID = "cand_empirical_paper"
MARKETING_ID = "cand_marketing_page"
EXPERT_ID = "cand_expert_interview"
REQUIRED_QUEUE_FIELDS = (
    "candidate_source_id",
    "priority_score",
    "reason",
    "status",
    "research_question_id",
    "source_type",
    "relevance_score",
    "credibility_prior",
    "gap_fill_score",
)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "research_queue_test.sqlite"


def test_queue_sources_ranks_empirical_above_marketing(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    assert main(["queue-sources", "--db", str(temp_db)]) == 0

    conn = connect(temp_db)
    try:
        candidates = conn.execute(
            "SELECT * FROM candidate_sources ORDER BY priority_score DESC"
        ).fetchall()
        assert len(candidates) == 5

        empirical = next(row for row in candidates if row["id"] == EMPIRICAL_ID)
        marketing = next(row for row in candidates if row["id"] == MARKETING_ID)
        expert = next(row for row in candidates if row["id"] == EXPERT_ID)

        assert empirical["priority_score"] > marketing["priority_score"]
        assert empirical["priority_score"] > expert["priority_score"]
        assert marketing["status"] == "rejected"

        queued = conn.execute(
            """
            SELECT q.*, c.source_type, c.relevance_score, c.credibility_prior,
                   c.gap_fill_score
            FROM research_queue q
            JOIN candidate_sources c ON c.id = q.candidate_source_id
            ORDER BY q.priority_score DESC
            """
        ).fetchall()
        assert len(queued) == 4
        assert queued[0]["candidate_source_id"] == EMPIRICAL_ID
        assert all(row["reason"] for row in queued)
        assert MARKETING_ID not in {row["candidate_source_id"] for row in queued}

        for row in queued:
            for field in REQUIRED_QUEUE_FIELDS:
                assert field in row.keys() or field in {
                    "candidate_source_id",
                    "priority_score",
                    "reason",
                    "status",
                    "research_question_id",
                    "source_type",
                    "relevance_score",
                    "credibility_prior",
                    "gap_fill_score",
                }
    finally:
        conn.close()


def test_queue_sources_is_idempotent(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    args = ["queue-sources", "--db", str(temp_db)]
    assert main(args) == 0
    assert main(args) == 0

    conn = connect(temp_db)
    try:
        count = conn.execute("SELECT COUNT(*) FROM research_queue").fetchone()[0]
        assert count == 4
    finally:
        conn.close()


def test_queue_sources_cli_emits_machine_readable_json(
    temp_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    assert main(["queue-sources", "--db", str(temp_db)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "queue-sources"
    assert payload["status"] == "completed"
    assert payload["queue_count"] == 4
    assert len(payload["queue_items"]) == 4
    assert payload["queue_items"][0]["candidate_source_id"] == EMPIRICAL_ID
    marketing_candidates = [
        item
        for item in payload["candidate_sources"]
        if item["id"] == MARKETING_ID
    ]
    assert len(marketing_candidates) == 1
    assert marketing_candidates[0]["status"] == "rejected"
    assert RANKING_FIXTURE.is_file()
