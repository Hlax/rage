"""Unit tests for OpenAlex source provider and discover-sources CLI (ticket-139)."""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.modules.source_discovery import (
    BLOCKED_EXIT_CODE,
    ERROR_EXIT_CODE,
    NOT_IMPLEMENTED_EXIT_CODE,
    OK_EXIT_CODE,
    run_discover_sources_command,
)
from rge.modules.source_providers.openalex import (
    OpenAlexProvider,
    map_openalex_work,
    reconstruct_abstract,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"


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


def test_reconstruct_abstract_from_inverted_index() -> None:
    abstract = reconstruct_abstract(
        {
            "Human-AI": [0],
            "co-creativity": [1],
            "supports": [2],
            "diverse": [3],
            "songwriting": [4],
            "outputs.": [5],
        }
    )
    assert "Human-AI" in abstract
    assert abstract.index("Human-AI") < abstract.index("outputs.")


def test_map_openalex_work_shapes_candidate_metadata() -> None:
    work = json.loads(OPENALEX_FIXTURE.read_text(encoding="utf-8"))["results"][0]
    candidate = map_openalex_work(work, domain_pack="creativity")

    assert candidate["provider"] == "openalex"
    assert candidate["provider_id"] == "W2741809807"
    assert candidate["title"] == work["display_name"]
    assert candidate["authors"] == ["Ada Example", "Alan Sample"]
    assert candidate["year"] == 2023
    assert candidate["doi"] == "https://doi.org/10.1234/rge-openalex-fixture"
    assert candidate["open_access_url"] == "https://example.org/open-access/paper.pdf"
    assert candidate["landing_page_url"] == "https://example.org/landing/human-ai-cocreativity"
    assert candidate["url"] == "https://example.org/open-access/paper.pdf"
    assert candidate["selected_url_kind"] == "best_oa_location.pdf_url"
    assert candidate["fetch_url_candidates"][0]["kind"] == "best_oa_location.pdf_url"
    assert candidate["domain_pack"] == "creativity"
    assert candidate["discovered_at"].endswith("Z")
    assert "Human-AI" in candidate["abstract"]


def test_openalex_health_check_never_prints_secret(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("OPENALEX_API_KEY", "super-secret-key-value")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")

    exit_code = main(
        ["discover-sources", "--provider", "openalex", "--health"]
    )
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert exit_code == OK_EXIT_CODE
    assert payload["health"]["api_key_set"] is True
    assert payload["health"]["mailto_set"] is True
    assert "super-secret-key-value" not in output


def test_discover_sources_without_provider_remains_stub(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["discover-sources"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == NOT_IMPLEMENTED_EXIT_CODE
    assert payload["status"] == "not_implemented"
    assert payload["command"] == "discover-sources"


def test_discover_sources_blocked_without_network_opt_in(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "0")

    exit_code = main(
        [
            "discover-sources",
            "--provider",
            "openalex",
            "--query",
            "human AI creativity",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == BLOCKED_EXIT_CODE
    assert payload["status"] == "blocked"
    assert payload["reason"] == "source_network_disabled"
    assert payload["provider"] == "openalex"


def test_discover_sources_unknown_provider_returns_structured_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "discover-sources",
            "--provider",
            "unknown-provider",
            "--query",
            "creativity",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == ERROR_EXIT_CODE
    assert payload["status"] == "error"
    assert payload["reason"] == "unknown_provider"


def test_discover_sources_missing_query_returns_structured_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["discover-sources", "--provider", "openalex"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == ERROR_EXIT_CODE
    assert payload["status"] == "error"
    assert payload["reason"] == "missing_query"


def test_discover_sources_openalex_mocked_response(
    mock_network_env: None,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text(encoding="utf-8"))
    provider = OpenAlexProvider(urlopen=_mock_urlopen_factory(fixture_payload))

    with patch(
        "rge.modules.source_providers.get_provider",
        return_value=provider,
    ):
        exit_code = main(
            [
                "discover-sources",
                "--provider",
                "openalex",
                "--query",
                "human AI creativity",
                "--limit",
                "2",
                "--domain",
                "creativity",
            ]
        )

    payload = json.loads(capsys.readouterr().out)

    assert exit_code == OK_EXIT_CODE
    assert payload["status"] == "ok"
    assert payload["provider"] == "openalex"
    assert payload["candidate_count"] == 2
    assert len(payload["candidates"]) == 2
    first = payload["candidates"][0]
    assert first["provider"] == "openalex"
    assert first["provider_id"] == "W2741809807"
    assert first["domain_pack"] == "creativity"


def test_run_discover_sources_command_provider_error_is_structured() -> None:
    class _BrokenProvider:
        provider_id = "openalex"

        def health_check(self) -> dict[str, str]:
            return {"provider": "openalex", "configured": True}

        def discover(self, query: str, domain_pack: str, limit: int) -> list[dict]:
            _ = (query, domain_pack, limit)
            from rge.modules.source_providers.openalex import (
                SourceDiscoveryProviderError,
            )

            raise SourceDiscoveryProviderError("network down")

    with patch.dict(os.environ, {"RGE_ALLOW_SOURCE_NETWORK": "1"}, clear=False):
        with patch(
            "rge.modules.source_providers.get_provider",
            return_value=_BrokenProvider(),
        ):
            payload, exit_code = run_discover_sources_command(
                provider_id="openalex",
                query="creativity",
                domain_pack="creativity",
                limit=5,
                health=False,
            )

    assert exit_code == ERROR_EXIT_CODE
    assert payload["status"] == "error"
    assert payload["reason"] == "provider_error"
