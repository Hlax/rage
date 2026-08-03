"""Deterministic source-artifact eligibility and persistence tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.db.connection import ensure_database
from rge.db.repositories import ingest_local_source
from rge.modules.claim_extractor import extract_claims_for_source
from rge.modules.source_quality_gate import (
    ACCESS_CHALLENGE,
    ELIGIBLE,
    EMPTY_CONTENT,
    ERROR_PAGE,
    GATE_VERSION,
    INSUFFICIENT_CONTENT,
    NAVIGATION_SHELL,
    NEEDS_REVIEW,
    QUARANTINED,
    REDIRECT_SHELL,
    SHORT_CONTENT_REVIEW,
    assess_source_eligibility,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCUMENT_DIR = REPO_ROOT / "fixtures" / "research_quality" / "documents"
CONTAMINATED_FIXTURES = {
    "access_challenge.txt": ACCESS_CHALLENGE,
    "navigation_shell.txt": NAVIGATION_SHELL,
    "redirect_shell.txt": REDIRECT_SHELL,
    "error_page.txt": ERROR_PAGE,
    "empty_content.txt": EMPTY_CONTENT,
    "insufficient_content.txt": INSUFFICIENT_CONTENT,
}


@pytest.mark.parametrize(("fixture_name", "reason"), CONTAMINATED_FIXTURES.items())
def test_gate_quarantines_domain_neutral_source_artifacts(
    fixture_name: str,
    reason: str,
) -> None:
    text = (DOCUMENT_DIR / fixture_name).read_text(encoding="utf-8")

    decision = assess_source_eligibility(text)

    assert decision.status == QUARANTINED
    assert decision.reason_codes == (reason,)
    assert decision.extraction_eligible is False
    assert decision.gate_version == GATE_VERSION


def test_gate_distinguishes_short_abstract_from_contaminated_shell() -> None:
    abstract = (
        "A pilot survey found lower fatigue after the schedule change in this "
        "small workplace sample."
    )

    decision = assess_source_eligibility(abstract)

    assert decision.status == NEEDS_REVIEW
    assert decision.reason_codes == (SHORT_CONTENT_REVIEW,)
    assert decision.extraction_eligible is False


def test_validated_short_artifact_is_eligible_after_contamination_checks() -> None:
    text = "Constraint management improves research team workflows."

    decision = assess_source_eligibility(
        text,
        metadata={"artifact_validated": True},
    )

    assert decision.status == ELIGIBLE
    assert decision.extraction_eligible is True


def test_validated_metadata_does_not_override_contamination() -> None:
    text = (DOCUMENT_DIR / "access_challenge.txt").read_text(encoding="utf-8")

    decision = assess_source_eligibility(
        text,
        metadata={"artifact_validated": True},
    )

    assert decision.status == QUARANTINED
    assert decision.reason_codes == (ACCESS_CHALLENGE,)


def test_gate_allows_substantive_domain_neutral_research_text() -> None:
    text = (DOCUMENT_DIR / "clinical_trial.txt").read_text(encoding="utf-8")

    decision = assess_source_eligibility(text)

    assert decision.status == ELIGIBLE
    assert decision.reason_codes == (ELIGIBLE,)
    assert decision.extraction_eligible is True


@pytest.mark.parametrize(("fixture_name", "reason"), CONTAMINATED_FIXTURES.items())
def test_quarantined_ingest_persists_private_diagnostics_and_blocks_mock_extraction(
    tmp_path: Path,
    fixture_name: str,
    reason: str,
) -> None:
    fixture_path = DOCUMENT_DIR / fixture_name
    raw_text = fixture_path.read_text(encoding="utf-8")
    conn = ensure_database(tmp_path / f"{fixture_path.stem}.sqlite")
    try:
        ingested = ingest_local_source(
            conn,
            local_path=fixture_path,
            domain="creativity",
            raw_text=raw_text,
            title=fixture_path.name,
            source_type="fixture",
        )
        source_id = str(ingested["source_id"])
        source_row = conn.execute(
            "SELECT domain_metadata_json FROM sources WHERE id = ?",
            (source_id,),
        ).fetchone()
        metadata = json.loads(source_row["domain_metadata_json"])

        assert ingested["chunk_count"] == 0
        assert metadata["source_eligibility"]["status"] == QUARANTINED
        assert metadata["source_eligibility"]["reason_codes"] == [reason]
        assert metadata["source_eligibility"]["gate_version"] == GATE_VERSION
        assert "raw_text" not in json.dumps(metadata)

        extraction = extract_claims_for_source(
            conn,
            source_id,
            fixture_name="claim_extraction_valid_and_missing_quote.json",
        )
        accepted_count = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ? AND status = 'accepted'",
            (source_id,),
        ).fetchone()[0]

        assert extraction["status"] == "blocked_by_quality_gate"
        assert extraction["quality_gate"]["eligibility_status"] == QUARANTINED
        assert extraction["quality_gate"]["extractable_chunk_count"] == 0
        assert extraction["accepted_count"] == 0
        assert accepted_count == 0
    finally:
        conn.close()


def test_valid_manual_style_ingest_keeps_deterministic_chunks(tmp_path: Path) -> None:
    fixture_path = DOCUMENT_DIR / "river_model.txt"
    raw_text = fixture_path.read_text(encoding="utf-8")
    conn = ensure_database(tmp_path / "valid.sqlite")
    try:
        result = ingest_local_source(
            conn,
            local_path=fixture_path,
            domain="creativity",
            raw_text=raw_text,
            title=fixture_path.name,
            source_type="manual_text",
        )

        assert result["chunk_count"] >= 1
        assert result["source_eligibility"]["status"] == ELIGIBLE
        assert result["source_eligibility"]["extraction_eligible"] is True
    finally:
        conn.close()
