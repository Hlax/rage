"""Domain-neutral structured research claim contract tests (ticket-416)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from pydantic import ValidationError

from rge.db.connection import apply_migrations, ensure_database
from rge.db.repositories import (
    ChunkRecord,
    ChunkRepository,
    ClaimRepository,
    SourceRecord,
    SourceRepository,
    claim_record_to_public_dict,
    utc_now_iso,
)
from rge.llm.schemas import CandidateClaimBatch_v0_1, CandidateClaim_v0_1
from rge.modules.claim_extractor import extract_claims_for_source
from rge.modules.claim_validator import (
    REJECTION_INVALID_STRUCTURED_CLAIM,
    rejection_diagnostic,
    validate_candidate_claim,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "rge" / "db" / "migrations"
CHUNK_TEXT = (
    "In a 12-participant experiment, AI assistance increased accuracy in the "
    "12-participant experiment while the comparison group was unchanged. "
    "The bounded observation was recorded in the synthetic results section."
)
QUOTE = "AI assistance increased accuracy in the 12-participant experiment"
CHUNK_PROVENANCE = {
    "id": "chk_structured_1",
    "section_type": "results",
    "section_title": "Results",
    "page": "2",
    "char_start": 120,
    "char_end": 120 + len(CHUNK_TEXT),
}


def _structured_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "contract_version": "0.1.0",
        "claim_kind": "empirical_result",
        "study_design": "experiment",
        "population_or_sample": "12 participants",
        "intervention_or_exposure": "AI assistance",
        "comparator": "comparison group",
        "outcome": "accuracy",
        "effect_direction": "increase",
        "statistical_context": "descriptive comparison; no inferential statistic reported",
        "limitations": ["Small synthetic sample."],
        "section_provenance": {
            "chunk_id": CHUNK_PROVENANCE["id"],
            "section_type": CHUNK_PROVENANCE["section_type"],
            "section_title": CHUNK_PROVENANCE["section_title"],
            "page": CHUNK_PROVENANCE["page"],
            "char_start": CHUNK_PROVENANCE["char_start"],
            "char_end": CHUNK_PROVENANCE["char_end"],
        },
    }
    payload.update(overrides)
    return payload


def _candidate(**structured_overrides: object) -> dict[str, object]:
    return {
        "claim_text": (
            "AI assistance increased accuracy in the 12-participant experiment."
        ),
        "source_id": "src_structured_1",
        "chunk_id": CHUNK_PROVENANCE["id"],
        "quote_span": QUOTE,
        "subject": "AI assistance",
        "predicate": "increased",
        "object": "accuracy",
        "scope": "12-participant experiment",
        "evidence_type": "empirical",
        "confidence": 0.72,
        "limitations": ["Small synthetic sample."],
        "domain": "creativity",
        "domain_metadata": {},
        "structured_claim": _structured_payload(**structured_overrides),
    }


def _validated_candidate(**structured_overrides: object) -> dict[str, object]:
    return CandidateClaim_v0_1.model_validate(
        _candidate(**structured_overrides)
    ).model_dump(mode="json")


def test_structured_empirical_result_accepts_with_matching_chunk_provenance() -> None:
    candidate = _validated_candidate()

    status, accepted, reason = validate_candidate_claim(
        candidate,
        chunk_text=CHUNK_TEXT,
        chunk_provenance=CHUNK_PROVENANCE,
        domain_pack="creativity",
    )

    assert status == "accepted"
    assert reason is None
    assert accepted is not None
    assert accepted["structured_claim"]["claim_kind"] == "empirical_result"
    assert accepted["structured_claim"]["outcome"] == "accuracy"


def test_structured_contract_requires_explicit_nullable_keys() -> None:
    structured = _structured_payload()
    structured.pop("comparator")
    candidate = _candidate()
    candidate["structured_claim"] = structured

    with pytest.raises(ValidationError, match="comparator"):
        CandidateClaim_v0_1.model_validate(candidate)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("claim_kind", "creativity_result"),
        ("study_design", "brainstorming_workshop"),
        ("effect_direction", "better"),
    ],
)
def test_structured_contract_rejects_invalid_enum_values(
    field: str, value: str
) -> None:
    with pytest.raises(ValidationError):
        CandidateClaim_v0_1.model_validate(_candidate(**{field: value}))


def test_empirical_result_requires_outcome_and_section_provenance() -> None:
    for overrides, expected in (
        ({"outcome": None, "effect_direction": None}, "requires a non-empty outcome"),
        ({"section_provenance": None}, "requires section_provenance"),
    ):
        candidate = _validated_candidate(**overrides)
        status, _, reason = validate_candidate_claim(
            candidate,
            chunk_text=CHUNK_TEXT,
            chunk_provenance=CHUNK_PROVENANCE,
            domain_pack="creativity",
        )
        assert status == "rejected"
        assert reason == REJECTION_INVALID_STRUCTURED_CLAIM
        assert expected in rejection_diagnostic(
            candidate,
            chunk_text=CHUNK_TEXT,
            rejection_reason=reason,
            chunk_provenance=CHUNK_PROVENANCE,
        )


def test_non_empirical_claim_keeps_empirical_fields_explicitly_null() -> None:
    chunk_text = "Prior work described a bounded background proposition."
    candidate = {
        "claim_text": "Prior work described a bounded background proposition.",
        "source_id": "src_background",
        "chunk_id": "chk_background",
        "quote_span": "Prior work described a bounded background proposition",
        "subject": "prior work",
        "predicate": "described",
        "object": "bounded background proposition",
        "scope": "prior work",
        "evidence_type": "theory",
        "confidence": 0.5,
        "limitations": [],
        "domain": "creativity",
        "structured_claim": {
            "contract_version": "0.1.0",
            "claim_kind": "background",
            "study_design": None,
            "population_or_sample": None,
            "intervention_or_exposure": None,
            "comparator": None,
            "outcome": None,
            "effect_direction": None,
            "statistical_context": None,
            "limitations": [],
            "section_provenance": None,
        },
    }
    candidate = CandidateClaim_v0_1.model_validate(candidate).model_dump(mode="json")

    status, accepted, reason = validate_candidate_claim(
        candidate,
        chunk_text=chunk_text,
        domain_pack="creativity",
    )

    assert status == "accepted"
    assert reason is None
    assert accepted["structured_claim"]["outcome"] is None


@pytest.mark.parametrize(
    "overrides",
    [
        {"outcome": None},
        {"intervention_or_exposure": None},
        {"claim_kind": "background"},
    ],
)
def test_structured_contract_rejects_contradictory_combinations(
    overrides: dict[str, object]
) -> None:
    candidate = _validated_candidate(**overrides)
    status, _, reason = validate_candidate_claim(
        candidate,
        chunk_text=CHUNK_TEXT,
        chunk_provenance=CHUNK_PROVENANCE,
        domain_pack="creativity",
    )

    assert status == "rejected"
    assert reason == REJECTION_INVALID_STRUCTURED_CLAIM


def test_structured_contract_rejects_chunk_provenance_mismatch() -> None:
    mismatched = dict(CHUNK_PROVENANCE)
    mismatched["section_type"] = "discussion"
    candidate = _validated_candidate()

    status, _, reason = validate_candidate_claim(
        candidate,
        chunk_text=CHUNK_TEXT,
        chunk_provenance=mismatched,
        domain_pack="creativity",
    )

    assert status == "rejected"
    assert reason == REJECTION_INVALID_STRUCTURED_CLAIM
    assert "section_type" in rejection_diagnostic(
        candidate,
        chunk_text=CHUNK_TEXT,
        rejection_reason=reason,
        chunk_provenance=mismatched,
    )


def test_repository_persists_private_structured_fields_without_public_widening(
    tmp_path: Path,
) -> None:
    conn = ensure_database(tmp_path / "structured.sqlite")
    try:
        now = utc_now_iso()
        SourceRepository(conn).insert(
            SourceRecord(
                id="src_structured_1",
                title="Structured fixture",
                source_type="fixture",
                domain="creativity",
                local_path=None,
                raw_text_checksum="checksum",
                status="ingested",
                created_at=now,
                updated_at=now,
            )
        )
        ChunkRepository(conn).insert_many(
            [
                ChunkRecord(
                    id=str(CHUNK_PROVENANCE["id"]),
                    source_id="src_structured_1",
                    chunk_index=0,
                    chunk_text=CHUNK_TEXT,
                    text_checksum="chunk-checksum",
                    created_at=now,
                    token_count=20,
                    page="2",
                    section="Results",
                    section_type="results",
                    section_title="Results",
                    char_start=120,
                    char_end=int(CHUNK_PROVENANCE["char_end"]),
                )
            ]
        )
        candidate = _validated_candidate()
        status, accepted, _ = validate_candidate_claim(
            candidate,
            chunk_text=CHUNK_TEXT,
            chunk_provenance=CHUNK_PROVENANCE,
            domain_pack="creativity",
        )
        assert status == "accepted" and accepted is not None
        record = ClaimRepository(conn).insert_accepted(
            accepted,
            extractor_provider="mock",
            extractor_model="structured_fixture",
            llm_schema_version="0.1.0",
        )

        assert record.claim_contract_version == "0.1.0"
        assert record.claim_kind == "empirical_result"
        assert record.study_design == "experiment"
        assert record.outcome == "accuracy"
        assert record.effect_direction == "increase"
        assert json.loads(record.section_provenance_json or "{}") == candidate[
            "structured_claim"
        ]["section_provenance"]

        public_view = claim_record_to_public_dict(record)
        private_keys = {
            "claim_contract_version",
            "claim_kind",
            "study_design",
            "population_or_sample",
            "intervention_or_exposure",
            "comparator",
            "outcome",
            "effect_direction",
            "statistical_context",
            "section_provenance",
        }
        assert private_keys.isdisjoint(public_view)
    finally:
        conn.close()


def test_extractor_validates_then_persists_structured_candidate(tmp_path: Path) -> None:
    class StructuredCandidateClient:
        provider = "mock"
        model = "structured-candidate-test"

        def extract_claims(self, **kwargs: object) -> CandidateClaimBatch_v0_1:
            chunk = kwargs["chunk"]
            assert isinstance(chunk, dict)
            candidate = _candidate()
            candidate["source_id"] = chunk["source_id"]
            candidate["chunk_id"] = chunk["id"]
            structured = dict(candidate["structured_claim"])
            structured["section_provenance"] = {
                "chunk_id": chunk["id"],
                "section_type": chunk["section_type"],
                "section_title": chunk["section_title"],
                "page": chunk["page"],
                "char_start": chunk["char_start"],
                "char_end": chunk["char_end"],
            }
            candidate["structured_claim"] = structured
            return CandidateClaimBatch_v0_1.model_validate(
                {
                    "task_name": "claim_extraction",
                    "schema_version": "0.1.0",
                    "items": [candidate],
                }
            )

    conn = ensure_database(tmp_path / "extractor-structured.sqlite")
    try:
        now = utc_now_iso()
        SourceRepository(conn).insert(
            SourceRecord(
                id="src_structured_1",
                title="Structured extractor fixture",
                source_type="fixture",
                domain="creativity",
                local_path=None,
                raw_text_checksum="extractor-checksum",
                status="ingested",
                created_at=now,
                updated_at=now,
            )
        )
        ChunkRepository(conn).insert_many(
            [
                ChunkRecord(
                    id=str(CHUNK_PROVENANCE["id"]),
                    source_id="src_structured_1",
                    chunk_index=0,
                    chunk_text=CHUNK_TEXT,
                    text_checksum="extractor-chunk-checksum",
                    created_at=now,
                    token_count=20,
                    page="2",
                    section="Results",
                    section_type="results",
                    section_title="Results",
                    char_start=120,
                    char_end=int(CHUNK_PROVENANCE["char_end"]),
                )
            ]
        )

        result = extract_claims_for_source(
            conn,
            "src_structured_1",
            client=StructuredCandidateClient(),
        )

        assert result["status"] == "completed"
        assert result["accepted_count"] == 1, [
            (record.rejection_reason, record.claim_text)
            for record in ClaimRepository(conn).list_for_source(
                "src_structured_1", status="rejected"
            )
        ]
        record = ClaimRepository(conn).get_by_id(result["accepted_claim_ids"][0])
        assert record is not None
        assert record.claim_contract_version == "0.1.0"
        assert record.claim_kind == "empirical_result"
        assert record.outcome == "accuracy"
    finally:
        conn.close()


def test_additive_migration_preserves_legacy_claim_as_explicit_nulls(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "pre_ticket_416.sqlite"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        migration_paths = sorted(MIGRATIONS_DIR.glob("*.sql"))
        pre_ticket_paths = [path for path in migration_paths if path.name < "0011_"]
        for path in pre_ticket_paths:
            conn.executescript(path.read_text(encoding="utf-8"))
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
        conn.executemany(
            "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
            [(path.stem, "2026-08-08T00:00:00Z") for path in pre_ticket_paths],
        )
        conn.execute(
            """
            INSERT INTO claims (
                id, source_id, chunk_id, claim_text, statement_type, subject,
                predicate, object, scope, evidence_type, confidence,
                limitations_json, domain, domain_metadata_json, status,
                created_at, updated_at
            ) VALUES (
                'clm_legacy', NULL, NULL, 'Legacy claim', 'source_claim', 'a',
                'relates', 'b', 'legacy scope', 'theory', 0.5,
                '[]', 'creativity', '{}', 'accepted',
                '2026-08-08T00:00:00Z', '2026-08-08T00:00:00Z'
            )
            """
        )
        conn.commit()

        assert apply_migrations(conn) == ["0011_structured_research_claim"]
        row = conn.execute(
            """
            SELECT claim_contract_version, claim_kind, outcome,
                   section_provenance_json
            FROM claims WHERE id = 'clm_legacy'
            """
        ).fetchone()
        assert tuple(row) == (None, None, None, None)
    finally:
        conn.close()
