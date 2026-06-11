"""Golden Test 2: claim extraction produces atomic, scoped claims."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"

EXPECTED_ACCEPTED_CLAIMS = [
    {
        "claim_text": (
            "AI-assisted brainstorming increased average idea quality in "
            "short-form writing tasks."
        ),
        "subject": "AI-assisted brainstorming",
        "predicate": "increased",
        "object": "average idea quality",
        "scope": "short-form writing tasks",
        "evidence_type": "empirical",
        "domain": "creativity",
    },
    {
        "claim_text": (
            "AI-assisted brainstorming reduced semantic diversity in "
            "short-form writing tasks."
        ),
        "subject": "AI-assisted brainstorming",
        "predicate": "reduced",
        "object": "semantic diversity",
        "scope": "short-form writing tasks",
        "evidence_type": "empirical",
        "domain": "creativity",
    },
]


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "claim_extraction_test.sqlite"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def _ingest_fixture(db_path: Path) -> str:
    from rge.cli import main

    exit_code = main(
        [
            "ingest",
            str(FIXTURE_SOURCE),
            "--domain",
            "creativity",
            "--db",
            str(db_path),
        ]
    )
    assert exit_code == 0
    from rge.db.connection import connect

    conn = connect(db_path)
    try:
        row = conn.execute("SELECT id FROM sources").fetchone()
        assert row is not None
        return row[0]
    finally:
        conn.close()


def test_extract_claims_produces_scoped_accepted_claims(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ClaimRepository

    source_id = _ingest_fixture(temp_db)
    assert (
        main(["extract-claims", "--source", source_id, "--db", str(temp_db)]) == 0
    )

    conn = connect(temp_db)
    try:
        claim_repo = ClaimRepository(conn)
        accepted = claim_repo.list_for_source(source_id, status="accepted")
        assert len(accepted) >= 2

        for expected in EXPECTED_ACCEPTED_CLAIMS:
            matches = [
                claim
                for claim in accepted
                if claim.claim_text == expected["claim_text"]
            ]
            assert len(matches) == 1, f"missing accepted claim: {expected['claim_text']}"
            claim = matches[0]
            assert claim.source_id == source_id
            assert claim.chunk_id.startswith("chk_")
            assert claim.subject == expected["subject"]
            assert claim.predicate == expected["predicate"]
            assert claim.object == expected["object"]
            assert claim.scope == expected["scope"]
            assert claim.evidence_type == expected["evidence_type"]
            assert claim.domain == expected["domain"]
            assert claim.confidence is not None
            assert json.loads(claim.limitations_json) is not None

            quotes = claim_repo.list_quotes_for_claim(claim.id)
            assert len(quotes) >= 1
            assert any(quote["is_primary"] == 1 for quote in quotes)
            assert quotes[0]["quote_text"]
    finally:
        conn.close()


def test_claims_without_quote_spans_are_rejected(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ClaimRepository

    source_id = _ingest_fixture(temp_db)
    assert (
        main(
            [
                "extract-claims",
                "--source",
                source_id,
                "--db",
                str(temp_db),
                "--fixture",
                "claim_extraction_valid_and_missing_quote.json",
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        claim_repo = ClaimRepository(conn)
        rejected = claim_repo.list_for_source(source_id, status="rejected")
        accepted = claim_repo.list_for_source(source_id, status="accepted")
        assert len(accepted) == 1
        assert len(rejected) == 1
        assert rejected[0].rejection_reason == "missing_quote_span"
        assert "increased average idea quality" in rejected[0].claim_text
    finally:
        conn.close()


def test_overgeneralized_claims_are_rejected(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ClaimRepository

    source_id = _ingest_fixture(temp_db)
    assert (
        main(
            [
                "extract-claims",
                "--source",
                source_id,
                "--db",
                str(temp_db),
                "--fixture",
                "claim_extraction_overgeneralized.json",
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        claim_repo = ClaimRepository(conn)
        accepted = claim_repo.list_for_source(source_id, status="accepted")
        rejected = claim_repo.list_for_source(source_id, status="rejected")
        assert len(accepted) == 0
        assert len(rejected) == 1
        assert rejected[0].rejection_reason == "overgeneralized_scope"
        assert rejected[0].claim_text == "AI reduces creativity."
    finally:
        conn.close()


def test_extract_claims_cli_emits_machine_readable_json(
    temp_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    source_id = _ingest_fixture(temp_db)
    capsys.readouterr()
    exit_code = main(["extract-claims", "--source", source_id, "--db", str(temp_db)])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] in {"completed", "already_extracted"}
    assert payload["command"] == "extract-claims"
    assert payload["accepted_count"] >= 2
    assert len(payload["accepted_claims"]) >= 2
