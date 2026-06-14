"""NM-4 evidence DB score reconciliation proof (ticket-131)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.llm.schemas import (
    CandidateClaimBatch_v0_1,
    CandidateConceptLinkBatch_v0_1,
    CandidateRelationshipBatch_v0_1,
    SCHEMA_VERSION_0_1_0,
)
from rge.modules.score_reconciler import (
    FORMULA_VERSION,
    STRONGER_SOURCE_BOOST,
    STRONGER_SOURCE_REASON,
    claim_supports_relationship,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_SOURCE_TEXT = (
    "Ticket-131 NM-4 evidence primary source.\n\n"
    "Researchers noted that human-AI songwriting pairs completed draft verses "
    "faster in this songwriting workshop."
)
FOLLOWUP_SOURCE = REPO_ROOT / "fixtures" / "sources" / "ticket131_nm4_evidence_followup.txt"
FOLLOWUP_CHECKSUM = (
    "044a97ae8419e35a20a8abd645c458e5128660c43eb891cd8c1b52384ad5139e"
)
EVIDENCE_SCOPE = "this songwriting workshop"
INITIAL_CONFIDENCE = 0.5
EXPECTED_NEW_CONFIDENCE = round(INITIAL_CONFIDENCE + STRONGER_SOURCE_BOOST, 2)


class _EvidencePrimaryStub:
    provider = "ollama"
    model = "stub-qwen"

    def extract_claims(self, **kwargs: object) -> CandidateClaimBatch_v0_1:
        return CandidateClaimBatch_v0_1.model_validate(
            {
                "task_name": "claim_extraction",
                "schema_version": SCHEMA_VERSION_0_1_0,
                "items": [
                    {
                        "claim_text": (
                            "Human-AI songwriting pairs completed draft verses "
                            "faster in this songwriting workshop."
                        ),
                        "quote_span": "completed draft verses faster in this songwriting workshop",
                        "scope": EVIDENCE_SCOPE,
                        "subject": "Human-AI songwriting pairs",
                        "predicate": "completed",
                        "object": "draft verses faster",
                        "evidence_type": "empirical",
                        "confidence": 0.7,
                        "limitations": [],
                        "domain": "creativity",
                        "domain_metadata": {},
                    }
                ],
            }
        )

    def link_concepts(self, **kwargs: object) -> CandidateConceptLinkBatch_v0_1:
        claims = kwargs["claims"]
        claim_id = claims[0]["id"]
        return CandidateConceptLinkBatch_v0_1.model_validate(
            {
                "task_name": "concept_linking",
                "schema_version": SCHEMA_VERSION_0_1_0,
                "items": [
                    {
                        "claim_id": claim_id,
                        "concept_label": "AI assistance",
                        "role": "method",
                        "confidence": 0.8,
                        "domain_metadata": {},
                    },
                    {
                        "claim_id": claim_id,
                        "concept_label": "constraint",
                        "role": "object",
                        "confidence": 0.78,
                        "domain_metadata": {},
                    },
                ],
            }
        )

    def draft_relationships(self, **kwargs: object) -> CandidateRelationshipBatch_v0_1:
        claims = kwargs["claims"]
        claim_id = claims[0]["id"]
        return CandidateRelationshipBatch_v0_1.model_validate(
            {
                "task_name": "relationship_drafting",
                "schema_version": SCHEMA_VERSION_0_1_0,
                "items": [
                    {
                        "subject_concept": "AI assistance",
                        "predicate": "supports",
                        "object_concept": "constraint",
                        "stance": "supports",
                        "scope": EVIDENCE_SCOPE,
                        "confidence": "medium",
                        "supporting_claim_ids": [claim_id],
                    }
                ],
            }
        )


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "nm4_evidence_score_reconciliation.sqlite"


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


def _ingest_primary_source(db_path: Path) -> str:
    source_path = db_path.parent / "nm4_primary_manual.txt"
    source_path.write_text(PRIMARY_SOURCE_TEXT, encoding="utf-8")
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
                "Ticket-131 NM-4 evidence primary",
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    from rge.db.connection import connect

    conn = connect(db_path)
    try:
        source_id = conn.execute("SELECT id FROM sources").fetchone()["id"]
    finally:
        conn.close()
    return str(source_id)


def _run_live_spine(db_path: Path, source_id: str) -> None:
    from rge.cli import main

    stub = _EvidencePrimaryStub()
    with patch.dict(
        os.environ,
        {"RGE_LLM_MODE": "ollama", "RGE_ALLOW_LIVE_LLM": "1"},
        clear=False,
    ):
        with patch(
            "rge.modules.live_extraction_write.assert_ollama_health",
            return_value={"model_available": True},
        ), patch(
            "rge.modules.live_probe.assert_ollama_health",
            return_value={"model_available": True},
        ), patch(
            "rge.modules.live_extraction_write.get_model_client",
            return_value=stub,
        ), patch(
            "rge.modules.concept_linker.get_model_client",
            return_value=stub,
        ), patch(
            "rge.modules.relationship_builder.get_model_client",
            return_value=stub,
        ):
            assert (
                main(
                    [
                        "extract-claims",
                        "--source",
                        source_id,
                        "--db",
                        str(db_path),
                        "--live-manual-fallthrough",
                    ]
                )
                == 0
            )
            assert (
                main(
                    [
                        "link-concepts",
                        "--source",
                        source_id,
                        "--db",
                        str(db_path),
                        "--live-manual-link-fallthrough",
                    ]
                )
                == 0
            )
            assert (
                main(
                    [
                        "build-relationships",
                        "--source",
                        source_id,
                        "--db",
                        str(db_path),
                        "--live-manual-relationship-fallthrough",
                    ]
                )
                == 0
            )


def _ingest_followup_source(db_path: Path) -> str:
    from rge.cli import main
    from rge.db.connection import connect

    assert (
        main(
            [
                "ingest",
                str(FOLLOWUP_SOURCE),
                "--domain",
                "creativity",
                "--source-type",
                "manual_text",
                "--source-title",
                "Ticket-131 NM-4 evidence follow-up",
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    conn = connect(db_path)
    try:
        row = conn.execute(
            "SELECT id, raw_text_checksum FROM sources WHERE title = ?",
            ("Ticket-131 NM-4 evidence follow-up",),
        ).fetchone()
        assert row is not None
        assert row["raw_text_checksum"] == FOLLOWUP_CHECKSUM
        return str(row["id"])
    finally:
        conn.close()


def test_followup_fixture_map_resolves_checksum() -> None:
    from rge.modules.manual_source_fixtures import extract_fixture_for_manual_source

    class _Source:
        source_type = "manual_text"
        raw_text_checksum = FOLLOWUP_CHECKSUM

    assert (
        extract_fixture_for_manual_source(_Source())
        == "claim_extraction_ticket131_nm4_evidence_followup.json"
    )


def test_claim_supports_active_relationship_edge_for_evidence_shape() -> None:
    from rge.db.repositories import ClaimRecord

    claim = ClaimRecord(
        id="clm_test",
        source_id="src_test",
        chunk_id="chk_test",
        claim_text=(
            "In this songwriting workshop follow-up, AI assistance improved teams' "
            "management of time constraints during draft verse completion."
        ),
        statement_type="empirical",
        scope=EVIDENCE_SCOPE,
        subject="AI assistance",
        predicate="improved",
        object="time constraint management",
        evidence_type="empirical",
        confidence=0.85,
        limitations_json="[]",
        domain="creativity",
        status="accepted",
        created_at="2026-06-14T00:00:00Z",
        updated_at="2026-06-14T00:00:00Z",
    )
    relationship = {
        "subject_concept": "AI assistance",
        "object_concept": "constraint",
        "predicate": "supports",
        "scope": EVIDENCE_SCOPE,
    }
    assert claim_supports_relationship(claim, relationship) is True


def test_nm4_evidence_followup_reconciles_active_edge(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    source_id = _ingest_primary_source(temp_db)
    _run_live_spine(temp_db, source_id)
    followup_id = _ingest_followup_source(temp_db)
    assert main(["extract-claims", "--source", followup_id, "--db", str(temp_db)]) == 0
    assert (
        main(
            [
                "reconcile-scores",
                "--source",
                followup_id,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        relationship = conn.execute(
            """
            SELECT r.id, r.confidence
            FROM relationships r
            JOIN concepts sub ON sub.id = r.subject_concept_id
            JOIN concepts obj ON obj.id = r.object_concept_id
            WHERE sub.label = 'AI assistance'
              AND obj.label = 'constraint'
              AND r.predicate = 'supports'
            """
        ).fetchone()
        assert relationship is not None
        assert float(relationship["confidence"]) == EXPECTED_NEW_CONFIDENCE

        event = conn.execute(
            """
            SELECT old_score, new_score, reason, formula_version
            FROM score_events
            WHERE entity_type = 'relationship' AND entity_id = ?
            """,
            (relationship["id"],),
        ).fetchone()
        assert event is not None
        assert float(event["old_score"]) == INITIAL_CONFIDENCE
        assert float(event["new_score"]) == EXPECTED_NEW_CONFIDENCE
        assert event["reason"] == STRONGER_SOURCE_REASON
        assert event["formula_version"] == FORMULA_VERSION
    finally:
        conn.close()


def test_nm4_evidence_reconcile_is_idempotent(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    source_id = _ingest_primary_source(temp_db)
    _run_live_spine(temp_db, source_id)
    followup_id = _ingest_followup_source(temp_db)
    assert main(["extract-claims", "--source", followup_id, "--db", str(temp_db)]) == 0
    args = ["reconcile-scores", "--source", followup_id, "--db", str(temp_db)]
    assert main(args) == 0
    assert main(args) == 0

    conn = connect(temp_db)
    try:
        count = conn.execute("SELECT COUNT(*) AS n FROM score_events").fetchone()["n"]
        assert count == 1
    finally:
        conn.close()


def test_nm4_evidence_reconcile_skips_low_confidence_claim(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    source_id = _ingest_primary_source(temp_db)
    _run_live_spine(temp_db, source_id)
    followup_id = _ingest_followup_source(temp_db)
    assert main(["extract-claims", "--source", followup_id, "--db", str(temp_db)]) == 0

    conn = connect(temp_db)
    try:
        conn.execute(
            "UPDATE claims SET confidence = 0.5 WHERE source_id = ?",
            (followup_id,),
        )
        conn.commit()
    finally:
        conn.close()

    assert (
        main(["reconcile-scores", "--source", followup_id, "--db", str(temp_db)]) == 0
    )
    conn = connect(temp_db)
    try:
        count = conn.execute("SELECT COUNT(*) AS n FROM score_events").fetchone()["n"]
        assert count == 0
    finally:
        conn.close()


def test_evidence_db_reconcile_flag_blocked_on_default_graph_db(temp_db: Path) -> None:
    from rge.cli import main

    source_id = _ingest_primary_source(temp_db)
    exit_code = main(
        [
            "reconcile-scores",
            "--source",
            source_id,
            "--db",
            "data/db/creative_research.sqlite",
            "--evidence-db-reconcile",
        ]
    )
    assert exit_code == 1
