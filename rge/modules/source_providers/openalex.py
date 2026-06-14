"""OpenAlex metadata provider for source discovery (Phase 3)."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any

OPENALEX_WORKS_API = "https://api.openalex.org/works"


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    if not inverted_index:
        return ""
    positions: list[tuple[int, str]] = []
    for token, idxs in inverted_index.items():
        for idx in idxs:
            positions.append((idx, token))
    if not positions:
        return ""
    positions.sort(key=lambda item: item[0])
    return " ".join(token for _, token in positions)


def map_openalex_work(work: dict[str, Any], *, domain_pack: str) -> dict[str, Any]:
    authors = [
        item.get("author", {}).get("display_name")
        for item in work.get("authorships") or []
        if item.get("author", {}).get("display_name")
    ]
    open_access = work.get("open_access") or {}
    primary_location = work.get("primary_location") or {}
    provider_id = str(work.get("id") or "")
    if provider_id.startswith("https://openalex.org/"):
        provider_id = provider_id.rsplit("/", 1)[-1]

    return {
        "provider": "openalex",
        "provider_id": provider_id,
        "title": work.get("display_name") or "",
        "authors": authors,
        "year": work.get("publication_year"),
        "doi": work.get("doi"),
        "open_access_url": open_access.get("oa_url"),
        "landing_page_url": primary_location.get("landing_page_url"),
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
        "domain_pack": domain_pack,
        "discovered_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z"
        ),
    }


def fetch_openalex_works(
    *,
    query: str,
    limit: int,
    mailto: str,
    api_key: str,
    urlopen: Any = urllib.request.urlopen,
) -> dict[str, Any]:
    params: dict[str, str] = {
        "search": query,
        "per-page": str(max(1, min(limit, 25))),
    }
    if mailto:
        params["mailto"] = mailto
    if api_key:
        params["api_key"] = api_key
    url = f"{OPENALEX_WORKS_API}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


class OpenAlexProvider:
    provider_id = "openalex"

    def __init__(self, *, urlopen: Any | None = None) -> None:
        self._urlopen = urlopen

    def _settings(self) -> tuple[str, str]:
        from rge.config import load_config

        config = load_config()
        return config.openalex_mailto, config.openalex_api_key

    def health_check(self) -> dict[str, Any]:
        mailto, api_key = self._settings()
        return {
            "provider": self.provider_id,
            "configured": True,
            "mailto_set": bool(mailto),
            "api_key_set": bool(api_key),
        }

    def discover(
        self, query: str, domain_pack: str, limit: int
    ) -> list[dict[str, Any]]:
        mailto, api_key = self._settings()
        urlopen = self._urlopen or urllib.request.urlopen
        try:
            payload = fetch_openalex_works(
                query=query,
                limit=limit,
                mailto=mailto,
                api_key=api_key,
                urlopen=urlopen,
            )
        except urllib.error.URLError as exc:
            raise SourceDiscoveryProviderError(
                f"OpenAlex request failed: {exc.reason or exc}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise SourceDiscoveryProviderError("OpenAlex returned invalid JSON.") from exc

        results = payload.get("results") or []
        return [
            map_openalex_work(work, domain_pack=domain_pack)
            for work in results[: max(1, limit)]
        ]


class SourceDiscoveryProviderError(Exception):
    """Provider-level discovery failure with operator-safe messaging."""
