"""Unit tests for three-layer live staged proof helpers (ticket-234)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.unit.live_staged_candidates import MOCK_STAGED_ARTIFACT_MARKERS
from tests.unit.live_staged_proof_layers import (
    UNSUITABLE_LIVE_ARTIFACT,
    evaluate_mock_spine_compatibility,
    format_unsuitable_live_artifact_skip,
    require_mock_spine_compatible_fetch_or_skip,
)


def test_evaluate_mock_spine_compatibility_accepts_matching_artifact(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "sample.html"
    artifact.write_text(
        "<html><body>Human-AI co-creativity supports diverse songwriting outputs.</body></html>",
        encoding="utf-8",
    )
    payload = {"artifact_path": str(artifact), "selected_url_kind": "best_oa_location.pdf_url"}

    result = evaluate_mock_spine_compatibility(payload, MOCK_STAGED_ARTIFACT_MARKERS)

    assert result["compatible"] is True
    assert result["missing_markers"] == []


def test_evaluate_mock_spine_compatibility_rejects_missing_markers(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "other.html"
    artifact.write_text(
        "<html><body>Generic creativity research abstract.</body></html>",
        encoding="utf-8",
    )
    payload = {"artifact_path": str(artifact)}

    result = evaluate_mock_spine_compatibility(payload, MOCK_STAGED_ARTIFACT_MARKERS)

    assert result["compatible"] is False
    assert result["reason"] == UNSUITABLE_LIVE_ARTIFACT
    assert "songwriting" in result["missing_markers"]


def test_format_unsuitable_live_artifact_skip_is_machine_readable() -> None:
    body = format_unsuitable_live_artifact_skip(
        research_question_id="rq_test",
        required_markers=MOCK_STAGED_ARTIFACT_MARKERS,
        unsuitable_candidates=[
            {
                "candidate_id": "disc_openalex_W1",
                "missing_markers": ["songwriting"],
            }
        ],
        fetch_failures=[],
    )
    parsed = json.loads(body)
    assert parsed["reason"] == UNSUITABLE_LIVE_ARTIFACT
    assert parsed["proof_layer"] == "combined_live_mock_spine"
    assert "Not a fetch/reconcile/report regression" in parsed["assessment"]


def test_require_mock_spine_compatible_fetch_or_skip_skips_when_unsuitable(
    tmp_path: Path,
) -> None:
    from rge.db.connection import ensure_database

    db_path = tmp_path / "proof_layers.sqlite"
    staging_dir = tmp_path / "staged"
    staging_dir.mkdir()
    conn = ensure_database(db_path)
    question_id = "rq_proof_layers_skip"
    candidate_id = "disc_openalex_W999"
    artifact = staging_dir / f"{candidate_id}.html"
    artifact.write_text(
        "<html><body><p>Live paper without fixture phrases but with enough extractable "
        "plain text for staged ingest quality validation and operator live fetch proofs "
        "on gitignored evidence databases without publisher landing stubs.</p></body></html>",
        encoding="utf-8",
    )

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
            candidate_id,
            question_id,
            "contract_golden_v0",
            "Live candidate",
            "https://example.org/live.html",
            "peer_reviewed_empirical",
            "test",
            0.8,
            0.8,
            0.5,
            0.5,
            0.5,
            0.5,
            0.1,
            0.8,
            "queued",
        ),
    )
    conn.commit()

    def _urlopen(request, timeout=30):  # noqa: ARG001
        return type(
            "Resp",
            (),
            {
                "read": lambda self, size=-1: artifact.read_bytes(),  # noqa: ARG005
                "headers": {"Content-Type": "text/html"},
                "__enter__": lambda self: self,
                "__exit__": lambda *args: None,
            },
        )()

    with patch.dict("os.environ", {"RGE_ALLOW_SOURCE_NETWORK": "1"}, clear=False):
        with pytest.raises(pytest.skip.Exception) as exc_info:
            require_mock_spine_compatible_fetch_or_skip(
                conn,
                research_question_id=question_id,
                staging_dir=staging_dir,
                artifact_text_markers=MOCK_STAGED_ARTIFACT_MARKERS,
                urlopen=_urlopen,
            )

    skip_payload = json.loads(str(exc_info.value))
    assert skip_payload["reason"] == UNSUITABLE_LIVE_ARTIFACT
    conn.close()


def test_require_mock_spine_compatible_fetch_or_skip_returns_compatible_candidate(
    tmp_path: Path,
) -> None:
    from rge.db.connection import ensure_database

    db_path = tmp_path / "proof_layers_ok.sqlite"
    staging_dir = tmp_path / "staged"
    staging_dir.mkdir()
    conn = ensure_database(db_path)
    question_id = "rq_proof_layers_ok"
    candidate_id = "disc_openalex_W888"
    artifact = staging_dir / f"{candidate_id}.html"
    artifact.write_text(
        "<html><body>Human-AI co-creativity supports diverse songwriting outputs.</body></html>",
        encoding="utf-8",
    )

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
            candidate_id,
            question_id,
            "contract_golden_v0",
            "Fixture-compatible candidate",
            "https://example.org/compatible.html",
            "peer_reviewed_empirical",
            "test",
            0.8,
            0.8,
            0.5,
            0.5,
            0.5,
            0.5,
            0.1,
            0.8,
            "queued",
        ),
    )
    conn.commit()

    def _urlopen(request, timeout=30):  # noqa: ARG001
        return type(
            "Resp",
            (),
            {
                "read": lambda self, size=-1: artifact.read_bytes(),  # noqa: ARG005
                "headers": {"Content-Type": "text/html"},
                "__enter__": lambda self: self,
                "__exit__": lambda *args: None,
            },
        )()

    with patch.dict("os.environ", {"RGE_ALLOW_SOURCE_NETWORK": "1"}, clear=False):
        resolved_id, payload = require_mock_spine_compatible_fetch_or_skip(
            conn,
            research_question_id=question_id,
            staging_dir=staging_dir,
            artifact_text_markers=MOCK_STAGED_ARTIFACT_MARKERS,
            urlopen=_urlopen,
        )

    assert resolved_id == candidate_id
    assert payload["status"] in {"completed", "already_fetched"}
    conn.close()
