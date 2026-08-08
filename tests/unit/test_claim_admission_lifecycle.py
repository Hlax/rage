"""Private claim admission lifecycle tests (ticket-417)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from rge.db.connection import apply_migrations, ensure_database
from rge.db.repositories import (
    ChunkRecord,
    ChunkRepository,
    ClaimRepository,
    SourceRecord,
    SourceRepository,
    utc_now_iso,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _seed_source(conn: sqlite3.Connection) -> tuple[str, str]:
    now = utc_now_iso()
    source_id = "src_claim_lifecycle"
    chunk_id = "chk_claim_lifecycle_0"
    SourceRepository(conn).insert(
        SourceRecord(
            id=source_id,
            title="Lifecycle fixture",
            source_type="manual_text",
            domain="creativity",
            local_path="",
            raw_text_checksum="lifecycle-checksum",
            status="ingested",
            created_at=now,
            updated_at=now,
        )
    )
    ChunkRepository(conn).insert_many(
        [
            ChunkRecord(
                id=chunk_id,
                source_id=source_id,
                chunk_index=0,
                chunk_text="A bounded study reported a measurable effect.",
                text_checksum="chunk-checksum",
                created_at=now,
            )
        ]
    )
    return source_id, chunk_id


def _candidate(source_id: str, chunk_id: str, *, suffix: str = "") -> dict:
    text = f"A bounded study reported a measurable effect{suffix}."
    return {
        "source_id": source_id,
        "chunk_id": chunk_id,
        "claim_text": text,
        "quote_span": "A bounded study reported a measurable effect.",
        "subject": "bounded study",
        "predicate": "reported",
        "object": "measurable effect",
        "scope": "bounded study",
        "evidence_type": "empirical",
        "confidence": 0.7,
        "limitations": ["Synthetic fixture."],
        "domain": "creativity",
        "domain_metadata": {},
    }


def test_model_candidate_moves_through_private_append_only_lifecycle(
    tmp_path: Path,
) -> None:
    conn = ensure_database(tmp_path / "lifecycle.sqlite")
    try:
        source_id, chunk_id = _seed_source(conn)
        claim = _candidate(source_id, chunk_id)
        repo = ClaimRepository(conn)

        proposed = repo.insert_proposed(
            claim,
            extractor_provider="mock",
            extractor_model="mock-claim-extractor",
            llm_schema_version="0.1.0",
        )
        assert proposed.status == "proposed"
        assert len(repo.list_quotes_for_claim(proposed.id)) == 1

        review = repo.transition_status(
            proposed.id,
            "needs_review",
            actor_type="python_validator",
            reason_code="semantic_uncertainty",
        )
        assert review.status == "needs_review"

        accepted = repo.transition_status(
            proposed.id,
            "accepted",
            actor_type="python_reviewer",
            reason_code="bounded_entailment_confirmed",
            claim=claim,
        )
        assert accepted.status == "accepted"
        assert len(repo.list_quotes_for_claim(accepted.id)) == 1

        decisions = repo.list_decisions(accepted.id)
        assert [item.new_status for item in decisions] == [
            "proposed",
            "needs_review",
            "accepted",
        ]
        assert [item.prior_status for item in decisions] == [
            None,
            "proposed",
            "needs_review",
        ]
        assert all(item.actor_type for item in decisions)
        assert all(item.reason_code for item in decisions)
        assert all(item.validator_version or item.policy_version for item in decisions)

        repeated = repo.transition_status(
            proposed.id,
            "accepted",
            actor_type="python_reviewer",
            reason_code="bounded_entailment_confirmed",
            claim=claim,
        )
        assert repeated.status == "accepted"
        assert len(repo.list_decisions(accepted.id)) == 3

        with pytest.raises(ValueError, match="not allowed"):
            repo.transition_status(
                proposed.id,
                "rejected",
                actor_type="python_validator",
                reason_code="late_rejection",
                rejection_reason="late_rejection",
            )
    finally:
        conn.close()


def test_python_compatibility_writer_records_genesis_decision(tmp_path: Path) -> None:
    conn = ensure_database(tmp_path / "compatibility.sqlite")
    try:
        source_id, chunk_id = _seed_source(conn)
        claim = _candidate(source_id, chunk_id, suffix=" in a fixture")
        repo = ClaimRepository(conn)

        accepted = repo.insert_accepted(
            claim,
            extractor_provider="fixture",
            extractor_model="deterministic-fixture",
            llm_schema_version="0.1.0",
            actor_type="python_fixture",
            reason_code="fixture_admission",
        )
        decisions = repo.list_decisions(accepted.id)
        assert len(decisions) == 1
        assert decisions[0].prior_status is None
        assert decisions[0].new_status == "accepted"
        assert decisions[0].actor_type == "python_fixture"

        repo.insert_accepted(
            claim,
            extractor_provider="fixture",
            extractor_model="deterministic-fixture",
            llm_schema_version="0.1.0",
            actor_type="python_fixture",
            reason_code="fixture_admission",
        )
        assert len(repo.list_decisions(accepted.id)) == 1
    finally:
        conn.close()


def test_mock_model_extraction_records_proposed_before_python_terminal_decision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from rge.cli import main

    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    db_path = tmp_path / "extractor-lifecycle.sqlite"
    source_path = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
    assert main(["ingest", str(source_path), "--domain", "creativity", "--db", str(db_path)]) == 0

    conn = ensure_database(db_path)
    try:
        source_id = str(conn.execute("SELECT id FROM sources").fetchone()[0])
    finally:
        conn.close()
    assert main(
        [
            "extract-claims",
            "--source",
            source_id,
            "--db",
            str(db_path),
            "--fixture",
            "claim_extraction_valid_and_missing_quote.json",
        ]
    ) == 0

    conn = ensure_database(db_path)
    try:
        repo = ClaimRepository(conn)
        claims = repo.list_for_source(source_id)
        assert {claim.status for claim in claims} == {"accepted", "rejected"}
        for claim in claims:
            decisions = repo.list_decisions(claim.id)
            assert [item.new_status for item in decisions] == ["proposed", claim.status]
            assert decisions[0].actor_type == "model_candidate"
            assert decisions[1].actor_type == "python_validator"
    finally:
        conn.close()


def test_migration_preserves_historical_terminal_rows_without_invented_history(
    tmp_path: Path,
) -> None:
    conn = ensure_database(tmp_path / "migration.sqlite")
    try:
        now = utc_now_iso()
        conn.execute("DROP TABLE claim_decisions")
        conn.execute(
            "DELETE FROM schema_migrations WHERE version = '0012_claim_admission_lifecycle'"
        )
        for claim_id, status in (("clm_old_accept", "accepted"), ("clm_old_reject", "rejected")):
            conn.execute(
                """
                INSERT INTO claims (id, claim_text, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (claim_id, claim_id, status, now, now),
            )
        conn.commit()

        assert apply_migrations(conn) == ["0012_claim_admission_lifecycle"]
        rows = conn.execute(
            "SELECT id, status FROM claims ORDER BY id"
        ).fetchall()
        assert [(row["id"], row["status"]) for row in rows] == [
            ("clm_old_accept", "accepted"),
            ("clm_old_reject", "rejected"),
        ]
        assert conn.execute("SELECT COUNT(*) FROM claim_decisions").fetchone()[0] == 0
    finally:
        conn.close()
