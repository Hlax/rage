"""Idempotency proof for manual synthnote pipeline (ticket-093)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNTHNOTE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "manual_synthnote.txt"
SYNTHNOTE_TITLE = (
    "Synthetic Source Note: AI-Assisted Ideation and Semantic Diversity"
)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "manual_source_pipeline_idempotency.sqlite"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


@dataclass(frozen=True)
class _PipelineCounts:
    sources: int
    accepted_claims: int
    rejected_claims: int
    concept_links: int
    relationships: int
    supports_evidence: int
    qualifies_evidence: int


def _ingest_args(db_path: Path) -> list[str]:
    return [
        "ingest",
        str(SYNTHNOTE_SOURCE),
        "--domain",
        "creativity",
        "--source-type",
        "manual_text",
        "--source-title",
        SYNTHNOTE_TITLE,
        "--db",
        str(db_path),
    ]


def _source_id(db_path: Path) -> str:
    from rge.db.connection import connect

    conn = connect(db_path)
    try:
        return conn.execute("SELECT id FROM sources").fetchone()[0]
    finally:
        conn.close()


def _pipeline_counts(db_path: Path, source_id: str) -> _PipelineCounts:
    from rge.db.connection import connect

    conn = connect(db_path)
    try:
        sources = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        accepted = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ? AND status = 'accepted'",
            (source_id,),
        ).fetchone()[0]
        rejected = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ? AND status = 'rejected'",
            (source_id,),
        ).fetchone()[0]
        links = conn.execute(
            "SELECT COUNT(*) FROM claim_concepts WHERE claim_id IN "
            "(SELECT id FROM claims WHERE source_id = ?)",
            (source_id,),
        ).fetchone()[0]
        relationships = conn.execute(
            """
            SELECT COUNT(DISTINCT r.id)
            FROM relationships r
            JOIN relationship_evidence re ON re.relationship_id = r.id
            JOIN claims c ON c.id = re.claim_id
            WHERE c.source_id = ?
            """,
            (source_id,),
        ).fetchone()[0]
        supports = conn.execute(
            """
            SELECT COUNT(*)
            FROM relationship_evidence re
            JOIN claims c ON c.id = re.claim_id
            WHERE c.source_id = ? AND re.stance = 'supports'
            """,
            (source_id,),
        ).fetchone()[0]
        qualifies = conn.execute(
            "SELECT COUNT(*) FROM relationship_evidence WHERE stance = 'qualifies'"
        ).fetchone()[0]
        return _PipelineCounts(
            sources=sources,
            accepted_claims=accepted,
            rejected_claims=rejected,
            concept_links=links,
            relationships=relationships,
            supports_evidence=supports,
            qualifies_evidence=qualifies,
        )
    finally:
        conn.close()


def _run_full_spine(db_path: Path) -> str:
    from rge.cli import main

    assert main(_ingest_args(db_path)) == 0
    source_id = _source_id(db_path)
    assert main(["extract-claims", "--source", source_id, "--db", str(db_path)]) == 0
    assert main(["link-concepts", "--source", source_id, "--db", str(db_path)]) == 0
    assert (
        main(["build-relationships", "--source", source_id, "--db", str(db_path)]) == 0
    )
    assert (
        main(["detect-contradictions", "--source", source_id, "--db", str(db_path)]) == 0
    )
    return source_id


def test_manual_synthnote_pipeline_full_spine_twice_is_idempotent(
    temp_db: Path,
) -> None:
    source_id = _run_full_spine(temp_db)
    first = _pipeline_counts(temp_db, source_id)

    assert first.sources == 1
    assert first.accepted_claims == 2
    assert first.rejected_claims == 1
    assert first.concept_links == 4
    assert first.relationships == 2
    assert first.supports_evidence == 2
    assert first.qualifies_evidence == 1

    _run_full_spine(temp_db)
    second = _pipeline_counts(temp_db, source_id)

    assert second == first


def test_manual_synthnote_pipeline_per_command_reruns_are_idempotent(
    temp_db: Path,
) -> None:
    from rge.cli import main

    source_id = _run_full_spine(temp_db)
    baseline = _pipeline_counts(temp_db, source_id)

    assert main(_ingest_args(temp_db)) == 0
    assert _pipeline_counts(temp_db, source_id) == baseline

    for command in (
        ["extract-claims", "--source", source_id, "--db", str(temp_db)],
        ["link-concepts", "--source", source_id, "--db", str(temp_db)],
        ["build-relationships", "--source", source_id, "--db", str(temp_db)],
        ["detect-contradictions", "--source", source_id, "--db", str(temp_db)],
    ):
        assert main(command) == 0
        assert _pipeline_counts(temp_db, source_id) == baseline
