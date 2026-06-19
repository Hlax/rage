"""Unit tests for unified source resolver (MVP-P1)."""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.modules.source_providers.arxiv import ArxivProvider, parse_arxiv_atom_feed
from rge.modules.source_providers.unpaywall import (
    UnpaywallEnricher,
    enrich_record_with_unpaywall,
    map_unpaywall_payload,
)
from rge.modules.source_resolver import (
    load_manual_fixture_records,
    resolve_work_candidates,
    run_resolve_sources_command,
)
from rge.modules.source_resolver.evidence import explain_source_evidence
from rge.modules.source_resolver.records import resolved_record_from_openalex_candidate
from rge.modules.source_resolver.status import (
    ABSTRACT_AVAILABLE,
    METADATA_ONLY,
    OA_PDF_AVAILABLE,
    OA_TEI_AVAILABLE,
    derive_discovery_source_status,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
UNPAYWALL_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "unpaywall_sample.json"
ARXIV_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "arxiv_atom_sample.xml"


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def mock_network_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.setenv("UNPAYWALL_EMAIL", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)


def _mock_urlopen_factory(payload: bytes):
    def _urlopen(request, timeout=30):  # noqa: ARG001
        return io.BytesIO(payload)

    return _urlopen


def test_derive_discovery_source_status_priority() -> None:
    assert derive_discovery_source_status(abstract_text="") == METADATA_ONLY
    assert (
        derive_discovery_source_status(abstract_text="We studied creativity.")
        == ABSTRACT_AVAILABLE
    )
    assert (
        derive_discovery_source_status(
            abstract_text="We studied creativity.",
            pdf_url="https://example.org/paper.pdf",
        )
        == OA_PDF_AVAILABLE
    )


def test_openalex_candidate_maps_to_resolved_record_with_status() -> None:
    work = json.loads(OPENALEX_FIXTURE.read_text(encoding="utf-8"))["results"][0]
    from rge.modules.source_providers.openalex import map_openalex_work

    candidate = map_openalex_work(work, domain_pack="creativity")
    record = resolved_record_from_openalex_candidate(candidate)

    assert record["source_kind"] == "openalex"
    assert record["source_id"] == "openalex:W2741809807"
    assert record["source_status"] == OA_PDF_AVAILABLE
    assert "Human-AI" in record["abstract_text"]
    assert record["abstract_source"] == "openalex_inverted_index"


def test_openalex_missing_abstract_is_metadata_only() -> None:
    work = json.loads(OPENALEX_FIXTURE.read_text(encoding="utf-8"))["results"][1]
    from rge.modules.source_providers.openalex import map_openalex_work

    candidate = map_openalex_work(work, domain_pack="creativity")
    record = resolved_record_from_openalex_candidate(candidate)

    assert record["source_status"] == METADATA_ONLY
    assert record["abstract_text"] == ""


def test_manual_fixture_mode_returns_explicit_statuses() -> None:
    records = load_manual_fixture_records(domain_pack="creativity")
    statuses = {record["source_status"] for record in records}

    assert len(records) == 4
    assert statuses == {METADATA_ONLY, ABSTRACT_AVAILABLE, OA_PDF_AVAILABLE, OA_TEI_AVAILABLE}


def test_explain_source_evidence_recommends_abstract_first() -> None:
    records = load_manual_fixture_records(domain_pack="creativity")
    abstract_record = next(
        record for record in records if record["source_status"] == ABSTRACT_AVAILABLE
    )
    summary = explain_source_evidence(abstract_record)

    assert summary["can_extract_abstract_claims"] is True
    assert summary["extraction_recommendation"] == "abstract_quote_first"
    assert "abstract-first" in summary["summary"].lower()


def test_explain_source_evidence_skips_llm_for_metadata_only() -> None:
    records = load_manual_fixture_records(domain_pack="creativity")
    metadata_record = next(
        record for record in records if record["source_status"] == METADATA_ONLY
    )
    summary = explain_source_evidence(metadata_record)

    assert summary["can_extract_abstract_claims"] is False
    assert summary["extraction_recommendation"] == "skip_llm_extraction"


def test_unpaywall_enrichment_preserves_metadata_only_when_no_oa() -> None:
    record = resolved_record_from_openalex_candidate(
        {
            "provider_id": "W999",
            "title": "Closed access paper",
            "authors": [],
            "year": 2020,
            "doi": "10.1234/closed",
            "abstract": "",
            "domain_pack": "creativity",
        }
    )
    enriched = enrich_record_with_unpaywall(
        record,
        {"doi": "10.1234/closed", "is_oa": False, "oa_status": "closed"},
    )

    assert enriched["source_status"] == METADATA_ONLY
    assert enriched["is_oa"] is False


def test_unpaywall_enrichment_adds_pdf_without_failing_run() -> None:
    payload = json.loads(UNPAYWALL_FIXTURE.read_text(encoding="utf-8"))
    mapped = map_unpaywall_payload(payload)
    record = resolved_record_from_openalex_candidate(
        {
            "provider_id": "W2741809807",
            "title": "Fixture paper",
            "authors": ["Ada Example"],
            "year": 2023,
            "doi": payload["doi"],
            "abstract": "Human-AI co-creativity supports diverse songwriting outputs.",
            "domain_pack": "creativity",
        }
    )
    enriched = enrich_record_with_unpaywall(record, payload)

    assert enriched["pdf_url"] == mapped["pdf_url"]
    assert enriched["source_status"] == OA_PDF_AVAILABLE
    assert "unpaywall" in enriched["enrichment_backends"]


def test_arxiv_atom_fixture_parses_first_class_records() -> None:
    xml_text = ARXIV_FIXTURE.read_text(encoding="utf-8")
    entries = parse_arxiv_atom_feed(xml_text)

    assert len(entries) == 2
    assert entries[0]["provider_id"] == "2401.01234v1"
    assert "semantic diversity" in entries[0]["abstract"].lower()
    assert entries[0]["pdf_url"].endswith("2401.01234v1.pdf")


def test_resolve_work_candidates_fixture_mode(
    mock_network_env: None,
) -> None:
    result = resolve_work_candidates(
        query="ignored in fixture mode",
        domain_pack="creativity",
        limit=5,
        fixture_mode=True,
    )

    assert result["resolved_count"] == 4
    assert result["fixture_mode"] is True
    assert len(result["evidence_summaries"]) == 4


def test_resolve_work_candidates_openalex_and_arxiv_mocked(
    mock_network_env: None,
) -> None:
    openalex_payload = json.loads(OPENALEX_FIXTURE.read_text(encoding="utf-8"))
    arxiv_payload = ARXIV_FIXTURE.read_text(encoding="utf-8").encode("utf-8")

    def _urlopen(request, timeout=30):  # noqa: ARG001
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        if "api.openalex.org" in url:
            return io.BytesIO(json.dumps(openalex_payload).encode("utf-8"))
        if "export.arxiv.org" in url:
            return io.BytesIO(arxiv_payload)
        raise AssertionError(f"Unexpected URL: {url}")

    openalex_provider = __import__(
        "rge.modules.source_providers.openalex", fromlist=["OpenAlexProvider"]
    ).OpenAlexProvider(urlopen=_urlopen)
    arxiv_provider = __import__(
        "rge.modules.source_providers.arxiv", fromlist=["ArxivProvider"]
    ).ArxivProvider(urlopen=_urlopen)

    def _get_provider(provider_id: str):
        if provider_id == "openalex":
            return openalex_provider
        if provider_id == "arxiv":
            return arxiv_provider
        return None

    with patch("rge.modules.source_providers.get_provider", side_effect=_get_provider):
        result = resolve_work_candidates(
            query="AI creativity diversity",
            domain_pack="creativity",
            limit=2,
            backends=["openalex", "arxiv"],
        )

    assert result["resolved_count"] == 4
    kinds = {record["source_kind"] for record in result["records"]}
    assert kinds == {"openalex", "arxiv"}


def test_resolve_sources_cli_fixture_mode(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "resolve-sources",
            "--fixture-mode",
            "--domain",
            "creativity",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["resolved_count"] == 4
    assert payload["records"][0]["source_status"] in {
        METADATA_ONLY,
        ABSTRACT_AVAILABLE,
        OA_PDF_AVAILABLE,
    }


def test_resolve_sources_blocked_without_network_opt_in(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "0")

    exit_code = main(
        [
            "resolve-sources",
            "--query",
            "AI creativity",
            "--sources",
            "openalex",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "blocked"
    assert payload["reason"] == "source_network_disabled"


def test_resolve_sources_unpaywall_enrichment_mocked(
    mock_network_env: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    openalex_payload = json.loads(OPENALEX_FIXTURE.read_text(encoding="utf-8"))
    unpaywall_payload = json.loads(UNPAYWALL_FIXTURE.read_text(encoding="utf-8"))

    def _openalex_urlopen(request, timeout=30):  # noqa: ARG001
        return io.BytesIO(json.dumps(openalex_payload).encode("utf-8"))

    def _unpaywall_urlopen(request, timeout=30):  # noqa: ARG001
        return io.BytesIO(json.dumps(unpaywall_payload).encode("utf-8"))

    provider = __import__(
        "rge.modules.source_providers.openalex", fromlist=["OpenAlexProvider"]
    ).OpenAlexProvider(urlopen=_openalex_urlopen)
    enricher = UnpaywallEnricher(urlopen=_unpaywall_urlopen)

    with patch("rge.modules.source_providers.get_provider", return_value=provider):
        with patch(
            "rge.modules.source_providers.unpaywall.UnpaywallEnricher",
            return_value=enricher,
        ):
            exit_code = main(
                [
                    "resolve-sources",
                    "--query",
                    "human AI creativity",
                    "--sources",
                    "openalex",
                    "--limit",
                    "1",
                    "--enrich-unpaywall",
                ]
            )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    first = payload["records"][0]
    assert "unpaywall" in first.get("enrichment_backends", [])
    assert first["pdf_url"] == "https://example.org/open-access/paper.pdf"
    assert first.get("license") == "cc-by"
    assert first.get("oa_version") == "publishedVersion"


def test_run_resolve_sources_command_provider_error_is_structured() -> None:
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
            payload, exit_code = run_resolve_sources_command(
                query="creativity",
                domain_pack="creativity",
                limit=5,
                backends=["openalex"],
                enrich_unpaywall=False,
                fixture_mode=False,
            )

    assert exit_code == 1
    assert payload["status"] == "error"
    assert payload["reason"] == "resolver_error"
