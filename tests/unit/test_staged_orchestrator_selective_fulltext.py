"""Unit tests for staged orchestrator selective full-text wiring."""

from __future__ import annotations

import io
import json
from itertools import cycle
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import (
    STAGED_FIXTURE_QUESTION_ID,
    STAGED_RANK1_CANDIDATE_ID,
    execute_staged_fixture_mode_run,
)
from rge.modules.research_spine import (
    candidate_source_to_fulltext_record,
    wire_staged_orchestrator_selective_fulltext,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
RANK1_HTML = (
    b"<html><body><p>Human-AI co-creativity supports diverse songwriting outputs.</p></body></html>"
)
RANK2_HTML = (
    b"<html><body><p>Constraint management improves AI-assisted creative team workflows.</p></body></html>"
)


@pytest.fixture(autouse=True)
def mock_llm_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)


@pytest.fixture()
def mock_network_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", "0")


@pytest.fixture()
def patched_staged_network() -> None:
    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text())
    html_cycle = cycle([RANK1_HTML, RANK2_HTML])

    def _urlopen(request, timeout=30):  # noqa: ARG001
        url = request.full_url if hasattr(request, "full_url") else str(request)
        if "api.openalex.org" in url:
            return io.BytesIO(json.dumps(fixture_payload).encode("utf-8"))
        html = next(html_cycle)

        class _Response(io.BytesIO):
            headers = {"Content-Type": "text/html; charset=utf-8"}

        return _Response(html)

    with patch(
        "rge.modules.source_providers.openalex.urllib.request.urlopen",
        _urlopen,
    ), patch(
        "rge.modules.fetcher.urllib.request.urlopen",
        _urlopen,
    ):
        yield


def test_candidate_source_to_fulltext_record_fixture_alias() -> None:
    record = candidate_source_to_fulltext_record(
        {"id": STAGED_RANK1_CANDIDATE_ID, "title": "Rank 1 staged candidate"},
        fixture_mode=True,
    )
    assert record["source_id"] == "manual_fixture:manual_oa_tei"
    assert record.get("tei_url")


def test_wire_staged_orchestrator_selective_fulltext_fixture_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rge.db.connection import ensure_database
    from rge.db.repositories import CandidateSourceRepository

    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    db_path = tmp_path / "staged_selective.sqlite"
    conn = ensure_database(db_path)
    try:
        repo = CandidateSourceRepository(conn)
        repo.insert(
            candidate_id=STAGED_RANK1_CANDIDATE_ID,
            research_question_id="q_test",
            contract_id=None,
            title="Human-AI co-creativity in songwriting",
            source_type="peer_reviewed_empirical",
            reason="fixture",
            relevance_score=0.9,
            credibility_prior=0.8,
            gap_fill_score=0.7,
            recency_score=0.6,
            source_diversity_score=0.5,
            novelty_score=0.4,
            drift_risk=0.1,
            priority_score=0.85,
            status="queued",
        )
        wiring = wire_staged_orchestrator_selective_fulltext(
            conn,
            candidate_ids=[STAGED_RANK1_CANDIDATE_ID],
            domain="creativity",
            staging_dir=tmp_path / "selective_fulltext",
            fixture_mode=True,
            persist_claims=True,
        )
    finally:
        conn.close()

    assert wiring["status"] == "completed"
    assert wiring["db_spine"]["accepted_claims_total"] >= 1
    assert wiring["selective_fulltext"]["acquisition_count"] == 1


def test_execute_staged_fixture_mode_run_selective_fulltext_opt_in(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mock_network_env: None,
    patched_staged_network: None,
) -> None:
    monkeypatch.setenv("RGE_ALLOW_STAGED_SELECTIVE_FULLTEXT", "1")

    result = execute_staged_fixture_mode_run(
        topic="AI creativity diversity",
        domain="creativity",
        db_path=tmp_path / "staged.sqlite",
        report_dir=tmp_path / "reports",
        staging_dir=tmp_path / "staged",
        question_id=STAGED_FIXTURE_QUESTION_ID,
    )

    assert result["status"] == "completed"
    assert "selective_fulltext_wiring" in result
    wiring = result["selective_fulltext_wiring"]
    assert wiring is not None
    assert wiring["db_spine"]["accepted_claims_total"] >= 1
    assert "selective_fulltext_wiring" in result["steps_completed"]
