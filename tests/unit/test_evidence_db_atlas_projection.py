"""Evidence DB atlas projection: run lineage + claim-backed cards (ticket-294)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.contracts.atlas_snapshot_v0 import validate_atlas_snapshot
from rge.db.connection import connect
from rge.llm.schemas import (
    CandidateClaimBatch_v0_1,
    CandidateConceptLinkBatch_v0_1,
    SCHEMA_VERSION_0_1_0,
)
from rge.modules.atlas_coherence_report import build_atlas_coherence_report
from rge.modules.atlas_snapshot_builder import build_atlas_snapshot_from_db
from rge.modules.evidence_db_atlas import (
    db_has_non_fixture_manual_claims,
    ensure_claim_backed_public_cards,
    ensure_evidence_research_run_lineage,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TICKET127_SOURCE = REPO_ROOT / "fixtures" / "sources" / "ticket127_arbitrary_manual_live.txt"
TOPIC = "Does AI-assisted songwriting reduce creative diversity in workshop drafts?"


class _StubOllamaClient:
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
                            "Participants in this songwriting workshop reused similar "
                            "rhyme schemes in approximately 40 percent of AI-assisted drafts."
                        ),
                        "quote_span": (
                            "Participants in this songwriting workshop also reused similar "
                            "rhyme schemes in approximately 40 percent of AI-assisted drafts"
                        ),
                        "scope": "this songwriting workshop",
                        "subject": "Participants in this songwriting workshop",
                        "predicate": "reused",
                        "object": "similar rhyme schemes",
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
                        "confidence": 0.85,
                        "domain_metadata": {},
                    },
                    {
                        "claim_id": claim_id,
                        "concept_label": "ideation",
                        "role": "context",
                        "confidence": 0.78,
                        "domain_metadata": {},
                    },
                ],
            }
        )


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "evidence_atlas.sqlite"


@pytest.fixture(autouse=True)
def mock_llm_env() -> None:
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


def _ingest_ticket127(temp_db: Path) -> str:
    exit_code = main(
        [
            "ingest",
            str(TICKET127_SOURCE),
            "--domain",
            "creativity",
            "--source-type",
            "manual_text",
            "--source-title",
            "Ticket-294 evidence atlas projection",
            "--db",
            str(temp_db),
        ]
    )
    assert exit_code == 0
    conn = connect(temp_db)
    try:
        row = conn.execute(
            "SELECT id FROM sources ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        assert row is not None
        return str(row["id"])
    finally:
        conn.close()


def _run_mock_live_spine(temp_db: Path, source_id: str) -> None:
    stub = _StubOllamaClient()
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
        ):
            with patch(
                "rge.modules.live_extraction_write.get_model_client",
                return_value=stub,
            ), patch(
                "rge.modules.concept_linker.get_model_client",
                return_value=stub,
            ):
                assert (
                    main(
                        [
                            "extract-claims",
                            "--source",
                            source_id,
                            "--db",
                            str(temp_db),
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
                            str(temp_db),
                            "--live-manual-link-fallthrough",
                        ]
                    )
                    == 0
                )


def test_db_has_non_fixture_manual_claims_after_ticket127_spine(temp_db: Path) -> None:
    source_id = _ingest_ticket127(temp_db)
    _run_mock_live_spine(temp_db, source_id)
    conn = connect(temp_db)
    try:
        assert db_has_non_fixture_manual_claims(conn) is True
    finally:
        conn.close()


def test_evidence_run_lineage_and_claim_backed_cards(temp_db: Path) -> None:
    source_id = _ingest_ticket127(temp_db)
    _run_mock_live_spine(temp_db, source_id)

    conn = connect(temp_db)
    try:
        lineage = ensure_evidence_research_run_lineage(
            conn, topic=TOPIC, domain_pack="creativity"
        )
        assert lineage["status"] in {"created", "already_present"}
        seeded = ensure_claim_backed_public_cards(conn)
        assert len(seeded) >= 1
        assert all(card_id.startswith("card_claim_") for card_id in seeded)

        snapshot = build_atlas_snapshot_from_db(
            conn,
            topic=TOPIC,
            domain_pack="creativity",
            fixture_mode=False,
            repo_root=REPO_ROOT,
        )
        validate_atlas_snapshot(snapshot)
        assert len(snapshot["runs"]) >= 1
        assert snapshot["runs"][0].get("research_question_id", "").startswith("rq_evidence_")
        assert len(snapshot["cards"]) >= 1
        assert snapshot["cards"][0]["id"].startswith("card_claim_")
        assert "card_golden_diversity_001" not in {c["id"] for c in snapshot["cards"]}

        report = build_atlas_coherence_report(snapshot)
        assert report["population"]["runs"] >= 1
        assert report["population"]["cards"] >= 1
        assert report["verdict"]["meaningful_atlas_data_from_research_loop"]["verdict"] == "pass"
    finally:
        conn.close()


def test_export_atlas_snapshot_cli_uses_claim_backed_cards(
    temp_db: Path,
    tmp_path: Path,
) -> None:
    source_id = _ingest_ticket127(temp_db)
    _run_mock_live_spine(temp_db, source_id)
    out_path = tmp_path / "atlas_snapshot.json"
    exit_code = main(
        [
            "export-atlas-snapshot",
            "--db",
            str(temp_db),
            "--out",
            str(out_path),
            "--topic",
            TOPIC,
            "--domain",
            "creativity",
        ]
    )
    assert exit_code == 0
    snapshot = json.loads(out_path.read_text(encoding="utf-8"))
    assert snapshot["runs"]
    assert snapshot["cards"][0]["id"].startswith("card_claim_")
