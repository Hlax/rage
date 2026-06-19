"""Live staged orchestrator rank-1 fetch fallback on publisher 403 (ticket-366)."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import STAGED_FIXTURE_QUESTION_ID
from rge.db.connection import ensure_database
from rge.modules.fetcher import ERROR_EXIT_CODE, OK_EXIT_CODE
from rge.modules.staged_candidate_selection import (
    Rank1StagedFetchAccessBlockedError,
    UnsuitableLiveArtifactError,
    fetch_rank1_with_access_fallback,
    list_rank1_fetch_candidate_ids,
    resolve_live_staged_spine_fetch_pair,
    select_rank2_staged_candidate_id,
)

QUESTION_ID = "rq_fetch_fallback_test"
RANK1_BLOCKED = "disc_rank1_blocked"
RANK1_FALLBACK = "disc_rank1_fallback"
RANK2_MATCH = "disc_rank2_match"


def _insert_candidate(
    conn,
    *,
    candidate_id: str,
    title: str,
    priority_score: float,
    url_candidates_json: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO candidate_sources (
            id, research_question_id, contract_id, title, url, source_type,
            reason, relevance_score, credibility_prior, gap_fill_score,
            recency_score, source_diversity_score, novelty_score, drift_risk,
            priority_score, status, created_at, url_candidates_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
        """,
        (
            candidate_id,
            QUESTION_ID,
            "contract_golden_v0",
            title,
            f"https://example.org/{candidate_id}.html",
            "peer_reviewed_empirical",
            "test",
            priority_score,
            0.8,
            0.5,
            0.5,
            0.5,
            0.5,
            0.1,
            priority_score,
            "queued",
            url_candidates_json,
        ),
    )


@pytest.fixture()
def conn(tmp_path: Path):
    database = ensure_database(tmp_path / "fetch_fallback.sqlite")
    _insert_candidate(
        database,
        candidate_id=RANK1_BLOCKED,
        title="Top-ranked paper with blocked publisher URLs",
        priority_score=0.95,
        url_candidates_json=json.dumps(
            [{"url": "https://publisher.example/paper.pdf", "kind": "best_oa_location.pdf_url"}]
        ),
    )
    _insert_candidate(
        database,
        candidate_id=RANK1_FALLBACK,
        title="Second-ranked fetchable creativity paper",
        priority_score=0.85,
        url_candidates_json=json.dumps(
            [{"url": "https://example.org/open/paper.html", "kind": "best_oa_location.landing_page_url"}]
        ),
    )
    _insert_candidate(
        database,
        candidate_id=RANK2_MATCH,
        title="Constraint management in AI-assisted creative teams",
        priority_score=0.75,
    )
    database.commit()
    yield database
    database.close()


def _mock_fetch_responses(
    responses: dict[str, tuple[dict, int]],
):
    def _fetch_command(
        conn,
        *,
        candidate_id: str,
        output_dir: Path | None = None,
        urlopen=None,
    ) -> tuple[dict, int]:
        if candidate_id in responses:
            return responses[candidate_id]
        raise AssertionError(f"unexpected fetch candidate_id={candidate_id!r}")

    return _fetch_command


def test_list_rank1_fetch_candidate_ids_prefers_pdf_routes_when_live(conn) -> None:
    ordered = list_rank1_fetch_candidate_ids(
        conn,
        QUESTION_ID,
        live_orchestrator_fallback=True,
        max_scan=10,
    )
    assert ordered[0] == RANK1_BLOCKED
    assert ordered[1:] == [RANK1_FALLBACK, RANK2_MATCH]


def test_fetch_rank1_with_access_fallback_skips_forbidden(tmp_path: Path, conn) -> None:
    artifact = tmp_path / f"{RANK1_FALLBACK}.html"
    artifact.write_text(
        "Human-AI co-creativity supports diverse songwriting workshops.",
        encoding="utf-8",
    )
    fetch_command = _mock_fetch_responses(
        {
            RANK1_BLOCKED: (
                {
                    "status": "error",
                    "reason": "forbidden",
                    "detail": "All URL routes returned 401/403.",
                },
                ERROR_EXIT_CODE,
            ),
            RANK1_FALLBACK: (
                {
                    "status": "completed",
                    "candidate_id": RANK1_FALLBACK,
                    "artifact_path": str(artifact),
                },
                OK_EXIT_CODE,
            ),
        }
    )

    candidate_id, blocked_ids, incompatible = fetch_rank1_with_access_fallback(
        conn,
        research_question_id=QUESTION_ID,
        output_dir=tmp_path,
        fetch_command=fetch_command,
        live_orchestrator_fallback=True,
        max_scan=10,
    )

    assert candidate_id == RANK1_FALLBACK
    assert blocked_ids == [RANK1_BLOCKED]
    assert incompatible == []


def test_fetch_rank1_with_access_fallback_raises_unsuitable_without_mock_markers(
    tmp_path: Path,
    conn,
) -> None:
    artifact = tmp_path / f"{RANK1_FALLBACK}.html"
    artifact.write_text(
        "Generic creativity research abstract without mock-spine marker phrases.",
        encoding="utf-8",
    )
    rank2_artifact = tmp_path / f"{RANK2_MATCH}.html"
    rank2_artifact.write_text(
        "Another generic creativity paper abstract without spine markers.",
        encoding="utf-8",
    )
    fetch_command = _mock_fetch_responses(
        {
            RANK1_BLOCKED: (
                {"status": "error", "reason": "forbidden", "detail": "blocked"},
                ERROR_EXIT_CODE,
            ),
            RANK1_FALLBACK: (
                {
                    "status": "completed",
                    "candidate_id": RANK1_FALLBACK,
                    "artifact_path": str(artifact),
                },
                OK_EXIT_CODE,
            ),
            RANK2_MATCH: (
                {
                    "status": "completed",
                    "candidate_id": RANK2_MATCH,
                    "artifact_path": str(rank2_artifact),
                },
                OK_EXIT_CODE,
            ),
        }
    )

    with pytest.raises(UnsuitableLiveArtifactError) as exc_info:
        fetch_rank1_with_access_fallback(
            conn,
            research_question_id=QUESTION_ID,
            output_dir=tmp_path,
            fetch_command=fetch_command,
            live_orchestrator_fallback=True,
            max_scan=10,
        )

    assert exc_info.value.incompatible_candidates
    assert exc_info.value.incompatible_candidates[0]["candidate_id"] == RANK1_FALLBACK


def test_fetch_rank1_with_access_fallback_raises_when_all_blocked(
    tmp_path: Path,
    conn,
) -> None:
    fetch_command = _mock_fetch_responses(
        {
            RANK1_BLOCKED: (
                {"status": "error", "reason": "forbidden", "detail": "blocked"},
                ERROR_EXIT_CODE,
            ),
            RANK1_FALLBACK: (
                {"status": "error", "reason": "paywall_blocked", "detail": "blocked"},
                ERROR_EXIT_CODE,
            ),
            RANK2_MATCH: (
                {"status": "error", "reason": "forbidden", "detail": "blocked"},
                ERROR_EXIT_CODE,
            ),
        }
    )

    with pytest.raises(Rank1StagedFetchAccessBlockedError) as exc_info:
        fetch_rank1_with_access_fallback(
            conn,
            research_question_id=QUESTION_ID,
            output_dir=tmp_path,
            fetch_command=fetch_command,
            live_orchestrator_fallback=True,
            max_scan=10,
        )

    assert exc_info.value.blocked_candidate_ids == [
        RANK1_BLOCKED,
        RANK1_FALLBACK,
        RANK2_MATCH,
    ]


def test_select_rank2_skips_excluded_candidates(conn) -> None:
    rank2_id = select_rank2_staged_candidate_id(
        conn,
        QUESTION_ID,
        live_orchestrator_fallback=True,
        exclude_ids=frozenset({RANK1_BLOCKED, RANK1_FALLBACK}),
        max_scan=10,
    )
    assert rank2_id == RANK2_MATCH


def test_resolve_live_staged_spine_fetch_pair(tmp_path: Path, conn) -> None:
    artifact = tmp_path / f"{RANK1_FALLBACK}.html"
    artifact.write_text(
        "Human-AI co-creativity supports diverse songwriting workshops.",
        encoding="utf-8",
    )
    fetch_command = _mock_fetch_responses(
        {
            RANK1_BLOCKED: (
                {"status": "error", "reason": "forbidden", "detail": "blocked"},
                ERROR_EXIT_CODE,
            ),
            RANK1_FALLBACK: (
                {
                    "status": "completed",
                    "candidate_id": RANK1_FALLBACK,
                    "artifact_path": str(artifact),
                },
                OK_EXIT_CODE,
            ),
        }
    )

    rank1_id, rank2_id, blocked_ids = resolve_live_staged_spine_fetch_pair(
        conn,
        research_question_id=QUESTION_ID,
        output_dir=tmp_path,
        fetch_command=fetch_command,
        max_scan=10,
    )

    assert rank1_id == RANK1_FALLBACK
    assert blocked_ids == [RANK1_BLOCKED]
    assert rank2_id == RANK2_MATCH


REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
RANK2_HTML = (
    b"<html><body><p>Constraint management improves AI-assisted creative team workflows.</p></body></html>"
)
THIRD_HTML = (
    b"<html><body><p>Human-AI co-creativity supports diverse songwriting workshops.</p></body></html>"
)


def _three_work_openalex_payload() -> dict:
    payload = json.loads(OPENALEX_FIXTURE.read_text())
    payload["results"].insert(
        1,
        {
            "id": "https://openalex.org/W9990000001",
            "display_name": "Fallback fetchable creativity evidence",
            "publication_year": 2024,
            "doi": "https://doi.org/10.1234/rge-fetch-fallback",
            "authorships": [{"author": {"display_name": "Fallback Author"}}],
            "open_access": {
                "is_oa": True,
                "oa_url": "https://example.org/fallback/paper.html",
            },
            "best_oa_location": {
                "landing_page_url": "https://example.org/fallback/paper.html",
            },
            "primary_location": {
                "landing_page_url": "https://example.org/fallback/paper.html",
            },
            "abstract_inverted_index": {
                "Fallback": [0],
                "fetchable": [1],
                "creativity": [2],
                "evidence.": [3],
            },
        },
    )
    return payload


def _fallback_network_urlopen(openalex_payload: dict):
    def _should_block(url: str) -> bool:
        if "api.openalex.org" in url:
            return False
        if "/fallback/" in url:
            return False
        if "constraint-management" in url:
            return False
        return "example.org" in url

    def _urlopen(request, timeout=30):  # noqa: ARG001
        url = request.full_url if hasattr(request, "full_url") else str(request)
        if "api.openalex.org" in url:
            return io.BytesIO(json.dumps(openalex_payload).encode("utf-8"))

        if _should_block(url):
            raise __import__("urllib").error.HTTPError(
                url,
                403,
                "Forbidden",
                hdrs=None,
                fp=None,
            )

        html = THIRD_HTML if "/fallback/" in url else RANK2_HTML

        class _Response(io.BytesIO):
            headers = {"Content-Type": "text/html; charset=utf-8"}

        return _Response(html)

    return _urlopen


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def live_orchestrator_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)


def test_live_orchestrator_resolve_fetch_pair_after_discover(
    live_orchestrator_env: None,
    tmp_path: Path,
) -> None:
    from rge.cli import main
    from rge.db.connection import ensure_database
    from rge.modules.fetcher import run_fetch_candidate_command

    temp_db = tmp_path / "live_fetch_fallback.sqlite"
    staging_dir = tmp_path / "staged"
    staging_dir.mkdir()

    openalex_payload = _three_work_openalex_payload()
    urlopen = _fallback_network_urlopen(openalex_payload)
    with patch(
        "rge.modules.source_providers.openalex.urllib.request.urlopen",
        urlopen,
    ), patch(
        "rge.modules.fetcher.urllib.request.urlopen",
        urlopen,
    ):
        exit_code = main(
            [
                "discover-sources",
                "--provider",
                "openalex",
                "--query",
                "human AI creativity",
                "--rank-only",
                "--enqueue",
                "--question",
                STAGED_FIXTURE_QUESTION_ID,
                "--db",
                str(temp_db),
            ]
        )
        assert exit_code == 0

        conn = ensure_database(temp_db)
        try:
            rank1_id, rank2_id, blocked_ids = resolve_live_staged_spine_fetch_pair(
                conn,
                research_question_id=STAGED_FIXTURE_QUESTION_ID,
                output_dir=staging_dir,
                fetch_command=run_fetch_candidate_command,
            )
        finally:
            conn.close()

    assert blocked_ids == ["disc_openalex_W2741809807"]
    assert rank1_id == "disc_openalex_W9990000001"
    assert rank2_id == "disc_openalex_W1234567890"