"""Live staged orchestrator real-data spine (ticket-368)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from rge.db.connection import ensure_database
from rge.llm.schemas import (
    SCHEMA_VERSION_0_1_0,
    CandidateClaimBatch_v0_1,
    CandidateConceptLinkBatch_v0_1,
    CandidateContradictionBatch_v0_1,
    CandidateRelationshipBatch_v0_1,
)
from rge.modules.fetcher import OK_EXIT_CODE
from rge.modules.live_staged_orchestrator_spine import (
    live_staged_orchestrator_live_llm_enabled,
    run_staged_ingest_live_spine_for_source,
)
from rge.modules.staged_candidate_selection import fetch_rank1_with_access_fallback

QUESTION_ID = "rq_real_spine_test"
CANDIDATE_ID = "disc_real_spine_rank1"
ARBITRARY_CHUNK_QUOTE = (
    "Generative AI tools accelerated ideation in a controlled creativity study."
)
STAGED_ARTIFACT_TEXT = (
    "Generative AI tools accelerated ideation in a controlled creativity study. "
    "Participants produced more draft concepts per hour while semantic diversity "
    "across outputs remained comparable to the human-only baseline condition. "
    "The authors note that workshop facilitation and prompt scaffolding may moderate "
    "these effects in applied songwriting and co-creative design settings."
)


class _StubRealSpineOllamaClient:
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
                            "Generative AI tools accelerated ideation in a controlled "
                            "creativity study."
                        ),
                        "quote_span": ARBITRARY_CHUNK_QUOTE,
                        "scope": "controlled creativity study",
                        "subject": "Generative AI tools",
                        "predicate": "accelerated",
                        "object": "ideation",
                        "evidence_type": "empirical",
                        "confidence": 0.75,
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
                        "concept_label": "co-creation",
                        "role": "subject",
                        "confidence": 0.82,
                        "domain_metadata": {
                            "track": "human-AI",
                            "creative_phase": "execution",
                            "measured_dimension": "semantic diversity",
                        },
                    },
                    {
                        "claim_id": claim_id,
                        "concept_label": "semantic diversity",
                        "role": "object",
                        "confidence": 0.88,
                        "domain_metadata": {
                            "track": "human-AI",
                            "creative_phase": "execution",
                            "measured_dimension": "semantic diversity",
                        },
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
                        "subject_concept": "co-creation",
                        "predicate": "may_reduce",
                        "object_concept": "semantic diversity",
                        "stance": "supports",
                        "scope": "controlled creativity study",
                        "confidence": "medium",
                        "supporting_claim_ids": [claim_id],
                    }
                ],
            }
        )

    def detect_contradictions(self, **kwargs: object) -> CandidateContradictionBatch_v0_1:
        return CandidateContradictionBatch_v0_1.model_validate(
            {
                "task_name": "contradiction_detection",
                "schema_version": SCHEMA_VERSION_0_1_0,
                "items": [],
            }
        )


def _insert_candidate(conn) -> None:
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
            CANDIDATE_ID,
            QUESTION_ID,
            "contract_golden_v0",
            "Real spine generic creativity paper",
            "https://example.org/real-spine.html",
            "peer_reviewed_empirical",
            "test",
            0.9,
            0.8,
            0.5,
            0.5,
            0.5,
            0.5,
            0.1,
            0.9,
            "queued",
        ),
    )


def test_fetch_accepts_arbitrary_artifact_when_markers_not_required(
    tmp_path: Path,
) -> None:
    conn = ensure_database(tmp_path / "real_spine_fetch.sqlite")
    _insert_candidate(conn)
    conn.commit()
    artifact = tmp_path / f"{CANDIDATE_ID}.html"
    artifact.write_text(STAGED_ARTIFACT_TEXT, encoding="utf-8")

    def _fetch_command(
        conn,
        *,
        candidate_id: str,
        output_dir: Path | None = None,
        urlopen=None,
    ) -> tuple[dict, int]:
        return (
            {
                "status": "completed",
                "candidate_id": candidate_id,
                "artifact_path": str(artifact),
            },
            OK_EXIT_CODE,
        )

    candidate_id, blocked_ids, incompatible = fetch_rank1_with_access_fallback(
        conn,
        research_question_id=QUESTION_ID,
        output_dir=tmp_path,
        fetch_command=_fetch_command,
        live_orchestrator_fallback=True,
        require_mock_spine_markers=False,
    )
    conn.close()

    assert candidate_id == CANDIDATE_ID
    assert blocked_ids == []
    assert incompatible == []


def test_live_staged_orchestrator_live_llm_enabled_requires_all_gates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR_LIVE_LLM", "0")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")
    assert live_staged_orchestrator_live_llm_enabled() is False

    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR_LIVE_LLM", "1")
    assert live_staged_orchestrator_live_llm_enabled() is True


def test_run_staged_ingest_live_spine_with_stub_ollama(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR_LIVE_LLM", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")

    conn = ensure_database(tmp_path / "real_spine.sqlite")
    _insert_candidate(conn)
    conn.commit()

    staging_dir = tmp_path / "staged"
    staging_dir.mkdir()
    artifact = staging_dir / f"{CANDIDATE_ID}.html"
    artifact.write_text(STAGED_ARTIFACT_TEXT, encoding="utf-8")

    from rge.modules.fetcher import ingest_staged_artifact

    ingest_payload = ingest_staged_artifact(
        conn,
        domain="creativity",
        candidate_id=CANDIDATE_ID,
        staging_dir=staging_dir,
    )
    source_id = ingest_payload["source_id"]

    stub = _StubRealSpineOllamaClient()
    with patch("rge.llm.registry.get_model_client", return_value=stub):
        payload = run_staged_ingest_live_spine_for_source(
            conn,
            source_id,
            domain="creativity",
            skip_health_check=True,
            client=stub,
        )

    conn.close()

    assert payload["status"] == "completed"
    assert payload["spine_mode"] == "live_staged_ingest"
    assert payload["extract"]["accepted_count"] >= 1
    assert payload["link"]["link_count"] >= 1
    assert payload["build"]["relationship_count"] >= 1
