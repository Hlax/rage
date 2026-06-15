"""Unit tests for OpenAlex fetch URL candidate ordering (ticket-233)."""

from __future__ import annotations

import io
import json
from pathlib import Path
import pytest

from rge.modules.fetcher import FetchError
import urllib.error

from rge.modules.fetcher import (
    ERROR_EXIT_CODE,
    OK_EXIT_CODE,
    classify_fetch_failure,
    fetch_staged_candidate_artifact,
    fetch_url_bytes_with_retry,
    parse_url_candidates,
    run_fetch_candidate_command,
)
from rge.modules.research_queue import enqueue_discovered_candidates, rank_discovered_candidates
from rge.modules.source_providers.openalex import map_openalex_work
from rge.modules.source_providers.openalex_urls import build_openalex_fetch_url_candidates
from rge.db.connection import ensure_database

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
TEST_QUESTION_ID = "rq_openalex_url_candidates_test"


def _work(**overrides: object) -> dict:
    base = {
        "id": "https://openalex.org/W9999999999",
        "display_name": "Fixture work",
        "open_access": {"is_oa": True, "oa_url": "https://example.org/oa.pdf"},
        "best_oa_location": {
            "pdf_url": "https://example.org/best-oa.pdf",
            "landing_page_url": "https://example.org/best-oa-landing",
        },
        "primary_location": {
            "landing_page_url": "https://example.org/publisher/landing",
            "pdf_url": "https://example.org/publisher/paper.pdf",
        },
        "locations": [
            {
                "id": "loc:1",
                "is_oa": True,
                "pdf_url": "https://example.org/locations/1.pdf",
                "landing_page_url": "https://example.org/locations/1-landing",
            }
        ],
    }
    base.update(overrides)
    return base


def test_oa_pdf_preferred_over_landing_page() -> None:
    candidates = build_openalex_fetch_url_candidates(_work())
    kinds = [item["kind"] for item in candidates]
    assert kinds[0] == "best_oa_location.pdf_url"
    assert "best_oa_location.landing_page_url" in kinds
    assert kinds.index("best_oa_location.pdf_url") < kinds.index(
        "best_oa_location.landing_page_url"
    )


def test_open_access_oa_url_used_when_best_oa_location_absent() -> None:
    work = _work(best_oa_location={})
    candidates = build_openalex_fetch_url_candidates(work)
    assert candidates[0]["url"] == "https://example.org/oa.pdf"
    assert candidates[0]["kind"] == "open_access.oa_url"


def test_publisher_landing_page_used_only_as_fallback() -> None:
    work = _work(
        open_access={"is_oa": False, "oa_url": None},
        best_oa_location={},
        locations=[],
        primary_location={"landing_page_url": "https://example.org/publisher/landing"},
    )
    candidates = build_openalex_fetch_url_candidates(work)
    assert len(candidates) == 1
    assert candidates[0]["kind"] == "primary_location.landing_page_url_non_oa"


def _mock_urlopen_sequence(responses: list[tuple[int | None, bytes | Exception]]):
    call_index = {"value": 0}

    def _urlopen(request, timeout=30):  # noqa: ARG001
        index = call_index["value"]
        call_index["value"] += 1
        status, payload = responses[index]

        if isinstance(payload, Exception):
            raise payload

        if status is not None and status >= 400:

            class _ErrorResponse(io.BytesIO):
                def __init__(self, code: int) -> None:
                    super().__init__(b"")
                    self.code = code

                def read(self, size=-1):  # noqa: ARG002
                    raise urllib.error.HTTPError(
                        request.full_url,
                        status,
                        "error",
                        hdrs=None,
                        fp=None,
                    )

            return _ErrorResponse(status)

        class _Response(io.BytesIO):
            headers = {"Content-Type": "text/html; charset=utf-8"}

        return _Response(payload)

    return _urlopen


def test_403_on_first_url_attempts_next_url(tmp_path: Path) -> None:
    routes = [
        {"url": "https://example.org/blocked", "kind": "primary_location.landing_page_url"},
        {"url": "https://example.org/open.pdf", "kind": "open_access.oa_url"},
    ]
    html = b"<html><body>open access</body></html>"
    urlopen = _mock_urlopen_sequence(
        [
            (403, b""),
            (None, html),
        ]
    )

    body, content_type, selected, attempted = fetch_url_bytes_with_retry(
        routes,
        urlopen=urlopen,
    )
    assert body == html
    assert selected["kind"] == "open_access.oa_url"
    assert len(attempted) == 1
    assert attempted[0]["http_status"] == 403


def test_all_urls_blocked_produces_clear_failure_reason() -> None:
    routes = [
        {"url": "https://example.org/blocked", "kind": "primary_location.landing_page_url_non_oa"},
    ]
    urlopen = _mock_urlopen_sequence([(403, b"")])

    with pytest.raises(FetchError) as exc_info:
        fetch_url_bytes_with_retry(routes, urlopen=urlopen)

    error = exc_info.value
    assert getattr(error, "reason", "") == "paywall_blocked"
    reason, _ = classify_fetch_failure(error.attempted_urls)
    assert reason == "paywall_blocked"


def test_map_openalex_work_exposes_fetch_url_candidates() -> None:
    work = json.loads(OPENALEX_FIXTURE.read_text())["results"][0]
    candidate = map_openalex_work(work, domain_pack="creativity")
    assert candidate["url"] == "https://example.org/open-access/paper.pdf"
    assert candidate["selected_url_kind"] == "best_oa_location.pdf_url"
    assert candidate["fetch_url_candidates"][0]["kind"] == "best_oa_location.pdf_url"


def test_enqueue_persists_url_candidates_json(tmp_path: Path) -> None:
    work = json.loads(OPENALEX_FIXTURE.read_text())["results"][0]
    candidate = map_openalex_work(work, domain_pack="creativity")
    ranked = rank_discovered_candidates(
        [candidate],
        query="human AI creativity",
        reference_year=2026,
    )
    db_path = tmp_path / "url_candidates.sqlite"
    conn = ensure_database(db_path)
    try:
        enqueue_discovered_candidates(
            conn,
            ranked,
            provider_id="openalex",
            research_question_id=TEST_QUESTION_ID,
        )
        row = conn.execute(
            "SELECT url, url_candidates_json FROM candidate_sources LIMIT 1",
        ).fetchone()
        assert row["url"] == "https://example.org/open-access/paper.pdf"
        routes = parse_url_candidates(dict(row))
        assert routes[0]["kind"] == "best_oa_location.pdf_url"
    finally:
        conn.close()


def test_fetch_staged_candidate_reports_selected_url_kind(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    candidate = {
        "id": "disc_openalex_W999",
        "url": "https://example.org/blocked",
        "url_candidates_json": json.dumps(
            [
                {
                    "url": "https://example.org/blocked",
                    "kind": "primary_location.landing_page_url",
                },
                {
                    "url": "https://example.org/open.pdf",
                    "kind": "open_access.oa_url",
                },
            ]
        ),
    }
    html = b"<html><body>fallback success</body></html>"
    urlopen = _mock_urlopen_sequence([(403, b""), (None, html)])
    result = fetch_staged_candidate_artifact(
        candidate,
        output_dir=tmp_path,
        urlopen=urlopen,
    )
    assert result["status"] == "completed"
    assert result["selected_url_kind"] == "open_access.oa_url"
    assert len(result["attempted_urls"]) == 1


def test_run_fetch_candidate_command_no_fetchable_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    db_path = tmp_path / "no_url.sqlite"
    conn = ensure_database(db_path)
    try:
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
                "disc_openalex_empty",
                TEST_QUESTION_ID,
                "contract_golden_v0",
                "No URL candidate",
                None,
                "unknown",
                "test",
                0.5,
                0.5,
                0.5,
                0.5,
                0.5,
                0.5,
                0.1,
                0.5,
                "queued",
            ),
        )
        conn.commit()
        payload, exit_code = run_fetch_candidate_command(
            conn,
            candidate_id="disc_openalex_empty",
        )
    finally:
        conn.close()
    assert exit_code == ERROR_EXIT_CODE
    assert payload["reason"] == "no_fetchable_url"
