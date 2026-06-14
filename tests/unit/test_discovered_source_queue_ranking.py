"""Unit tests for discovered-source queue ranking (ticket-140)."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.modules.research_queue import (
    compute_discovered_relevance_score,
    infer_source_type_for_discovered_candidate,
    rank_discovered_candidates,
    score_discovered_candidate,
)
from rge.modules.source_discovery import (
    BLOCKED_EXIT_CODE,
    NOT_IMPLEMENTED_EXIT_CODE,
    OK_EXIT_CODE,
    run_discover_sources_command,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
REFERENCE_YEAR = 2026


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def mock_network_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)


def _mock_urlopen_factory(payload: dict):
    body = json.dumps(payload).encode("utf-8")

    def _urlopen(request, timeout=30):  # noqa: ARG001
        return io.BytesIO(body)

    return _urlopen


def _openalex_candidates(domain_pack: str = "creativity") -> list[dict]:
    from rge.modules.source_providers.openalex import OpenAlexProvider

    provider = OpenAlexProvider(
        urlopen=_mock_urlopen_factory(json.loads(OPENALEX_FIXTURE.read_text()))
    )
    return provider.discover("human AI creativity", domain_pack, 10)


def test_infer_source_type_marketing_title() -> None:
    candidate = {"title": "MuseForge AI: The Only Tool You Will Ever Need", "year": 2026}
    assert (
        infer_source_type_for_discovered_candidate(candidate, reference_year=REFERENCE_YEAR)
        == "marketing_page"
    )


def test_infer_source_type_peer_reviewed_with_recent_doi() -> None:
    candidate = {
        "title": "Empirical study",
        "year": 2023,
        "doi": "https://doi.org/10.1234/example",
    }
    assert (
        infer_source_type_for_discovered_candidate(candidate, reference_year=REFERENCE_YEAR)
        == "peer_reviewed_empirical"
    )


def test_infer_source_type_case_study_without_doi() -> None:
    candidate = {
        "title": "Workshop notes",
        "year": 2024,
        "abstract": "A case study of creative teams.",
    }
    assert (
        infer_source_type_for_discovered_candidate(candidate, reference_year=REFERENCE_YEAR)
        == "case_study"
    )


def test_infer_source_type_unknown_fallback() -> None:
    candidate = {"title": "Untitled fragment", "year": 2020}
    assert (
        infer_source_type_for_discovered_candidate(candidate, reference_year=REFERENCE_YEAR)
        == "unknown"
    )


def test_relevance_score_token_overlap() -> None:
    score = compute_discovered_relevance_score(
        query="human AI creativity",
        title="Human-AI co-creativity in songwriting",
        abstract="Supports diverse songwriting outputs.",
    )
    assert score > 0.0
    assert score <= 1.0


def test_rank_discovered_candidates_uses_pack_credibility_prior() -> None:
    candidates = _openalex_candidates()
    ranked = rank_discovered_candidates(
        candidates,
        query="human AI creativity",
        domain_pack="creativity",
        reference_year=REFERENCE_YEAR,
    )
    assert len(ranked) == 2
    empirical = next(item for item in ranked if item["provider_id"] == "W2741809807")
    assert empirical["source_type"] == "peer_reviewed_empirical"
    assert empirical["credibility_prior"] == 0.9
    assert empirical["status"] == "queued"
    assert empirical["formula_version"] == "golden_v0.1.0"
    assert ranked[0]["priority_score"] >= ranked[1]["priority_score"]


def test_marketing_candidate_rejected_in_ranking() -> None:
    candidates = _openalex_candidates()
    candidates.append(
        {
            "provider": "openalex",
            "provider_id": "W999",
            "title": "10 Ways AI Will Supercharge Your Creativity",
            "authors": [],
            "year": 2026,
            "doi": None,
            "open_access_url": None,
            "landing_page_url": "https://example.org/marketing",
            "abstract": "",
            "domain_pack": "creativity",
            "discovered_at": "2026-06-14T12:00:00Z",
        }
    )
    ranked = rank_discovered_candidates(
        candidates,
        query="human AI creativity",
        domain_pack="creativity",
        reference_year=REFERENCE_YEAR,
    )
    marketing = next(item for item in ranked if item["provider_id"] == "W999")
    assert marketing["source_type"] == "marketing_page"
    assert marketing["status"] == "rejected"
    assert marketing["credibility_prior"] == 0.2
    assert ranked[-1]["provider_id"] == "W999"


def test_score_discovered_candidate_unknown_type_default_prior() -> None:
    scored = score_discovered_candidate(
        {"title": "Untitled fragment", "year": 2020},
        query="creativity",
        domain_pack="creativity",
        reference_year=REFERENCE_YEAR,
    )
    assert scored["source_type"] == "unknown"
    assert scored["credibility_prior"] == 0.4


def test_discover_sources_rank_only_mocked(
    mock_network_env: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text())
    with patch(
        "rge.modules.source_providers.openalex.urllib.request.urlopen",
        _mock_urlopen_factory(fixture_payload),
    ):
        exit_code = main(
            [
                "discover-sources",
                "--provider",
                "openalex",
                "--query",
                "human AI creativity",
                "--rank-only",
            ]
        )
    assert exit_code == OK_EXIT_CODE
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert payload["candidate_count"] == 2
    assert len(payload["ranked_candidates"]) == 2
    assert payload["ranked_candidates"][0]["priority_score"] >= payload["ranked_candidates"][1][
        "priority_score"
    ]
    assert all(item["reason"] for item in payload["ranked_candidates"])


def test_discover_sources_without_rank_only_omits_ranked_candidates(
    mock_network_env: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text())
    with patch(
        "rge.modules.source_providers.openalex.urllib.request.urlopen",
        _mock_urlopen_factory(fixture_payload),
    ):
        exit_code = main(
            [
                "discover-sources",
                "--provider",
                "openalex",
                "--query",
                "human AI creativity",
            ]
        )
    assert exit_code == OK_EXIT_CODE
    payload = json.loads(capsys.readouterr().out)
    assert "ranked_candidates" not in payload


def test_discover_sources_stub_unchanged(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["discover-sources"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == NOT_IMPLEMENTED_EXIT_CODE
    assert payload["status"] == "not_implemented"


def test_discover_sources_blocked_without_network_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_ALLOW_SOURCE_NETWORK", raising=False)
    payload, exit_code = run_discover_sources_command(
        provider_id="openalex",
        query="human AI creativity",
        domain_pack="creativity",
        limit=5,
        health=False,
        rank_only=True,
    )
    assert exit_code == BLOCKED_EXIT_CODE
    assert payload["status"] == "blocked"
    assert payload["reason"] == "source_network_disabled"
    assert "ranked_candidates" not in payload
