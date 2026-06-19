"""Unpaywall DOI open-access enrichment for resolved source records."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from rge.modules.source_providers.openalex import SourceDiscoveryProviderError
from rge.modules.source_resolver.status import (
    derive_discovery_source_status,
    merge_source_status,
    normalize_doi,
)

UNPAYWALL_API = "https://api.unpaywall.org/v2"


def fetch_unpaywall_work(
    doi: str,
    *,
    email: str,
    urlopen: Any = urllib.request.urlopen,
) -> dict[str, Any]:
    normalized = normalize_doi(doi)
    if not normalized:
        raise SourceDiscoveryProviderError("Unpaywall requires a non-empty DOI.")
    if not email:
        raise SourceDiscoveryProviderError(
            "Unpaywall requires UNPAYWALL_EMAIL or OPENALEX_MAILTO."
        )
    encoded_doi = urllib.parse.quote(normalized, safe="")
    url = f"{UNPAYWALL_API}/{encoded_doi}?email={urllib.parse.quote(email)}"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"doi": normalized, "is_oa": False, "oa_status": "closed"}
        raise SourceDiscoveryProviderError(
            f"Unpaywall request failed: HTTP {exc.code}"
        ) from exc
    except urllib.error.URLError as exc:
        raise SourceDiscoveryProviderError(
            f"Unpaywall request failed: {exc.reason or exc}"
        ) from exc
    return json.loads(payload)


def map_unpaywall_payload(payload: dict[str, Any]) -> dict[str, Any]:
    best = payload.get("best_oa_location") or {}
    pdf_url = best.get("url_for_pdf") or best.get("url")
    host_type = str(best.get("host_type") or "")
    tei_url = None
    if host_type == "repository" and str(best.get("url") or "").endswith(".xml"):
        tei_url = best.get("url")

    return {
        "doi": normalize_doi(payload.get("doi")),
        "is_oa": bool(payload.get("is_oa")),
        "oa_status": payload.get("oa_status"),
        "best_oa_location_url": best.get("url"),
        "pdf_url": pdf_url,
        "tei_url": tei_url,
        "landing_page_url": best.get("url"),
        "license": best.get("license"),
        "oa_version": best.get("version"),
        "resolver_backend": "unpaywall",
    }


def enrich_record_with_unpaywall(
    record: dict[str, Any],
    unpaywall_payload: dict[str, Any],
) -> dict[str, Any]:
    """Merge Unpaywall OA fields into an existing resolved record."""
    mapped = map_unpaywall_payload(unpaywall_payload)
    merged = dict(record)
    for key in (
        "is_oa",
        "oa_status",
        "best_oa_location_url",
        "pdf_url",
        "tei_url",
        "landing_page_url",
        "license",
        "oa_version",
    ):
        incoming = mapped.get(key)
        if incoming is not None and (key not in merged or not merged.get(key)):
            merged[key] = incoming

    backends = list(merged.get("enrichment_backends") or [])
    if "unpaywall" not in backends:
        backends.append("unpaywall")
    merged["enrichment_backends"] = backends

    merged["source_status"] = merge_source_status(
        merged.get("source_status"),
        derive_discovery_source_status(
            abstract_text=merged.get("abstract_text"),
            pdf_url=merged.get("pdf_url"),
            tei_url=merged.get("tei_url"),
        ),
    )
    return merged


class UnpaywallEnricher:
    """Enrich DOI-backed resolved records with Unpaywall OA metadata."""

    provider_id = "unpaywall"

    def __init__(self, *, urlopen: Any | None = None) -> None:
        self._urlopen = urlopen

    def _email(self) -> str:
        from rge.config import load_config

        config = load_config()
        return config.unpaywall_email

    def health_check(self) -> dict[str, Any]:
        email = self._email()
        return {
            "provider": self.provider_id,
            "configured": True,
            "email_set": bool(email),
        }

    def enrich_doi(self, doi: str) -> dict[str, Any]:
        from rge.modules.source_resolver.records import build_resolved_record

        email = self._email()
        urlopen = self._urlopen or urllib.request.urlopen
        payload = fetch_unpaywall_work(doi, email=email, urlopen=urlopen)
        mapped = map_unpaywall_payload(payload)
        provider_id = normalize_doi(doi) or "unknown"
        return build_resolved_record(
            source_kind="unpaywall",
            provider_id=provider_id,
            title=str(payload.get("title") or mapped.get("title") or ""),
            doi=provider_id,
            is_oa=mapped.get("is_oa"),
            oa_status=mapped.get("oa_status"),
            best_oa_location_url=mapped.get("best_oa_location_url"),
            pdf_url=mapped.get("pdf_url"),
            tei_url=mapped.get("tei_url"),
            landing_page_url=mapped.get("landing_page_url"),
            license_info=mapped.get("license"),
            oa_version=mapped.get("oa_version"),
            resolver_backend="unpaywall",
            raw_provider="unpaywall",
        )
