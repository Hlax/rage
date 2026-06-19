"""arXiv metadata provider for source discovery."""

from __future__ import annotations

import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any

from rge.modules.source_providers.openalex import SourceDiscoveryProviderError

ARXIV_API = "http://export.arxiv.org/api/query"
_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
_ARXIV_ID_PATTERN = re.compile(r"arxiv\.org/abs/([^/\s]+)", re.IGNORECASE)


def extract_arxiv_id_from_url(url: str | None) -> str | None:
    if not url:
        return None
    match = _ARXIV_ID_PATTERN.search(url)
    return match.group(1) if match else None


def normalize_arxiv_id(raw: str | None) -> str | None:
    if not raw:
        return None
    value = str(raw).strip()
    if value.startswith("arxiv:"):
        value = value.removeprefix("arxiv:")
    if "arxiv.org/abs/" in value:
        return extract_arxiv_id_from_url(value)
    return value or None


def parse_arxiv_atom_feed(xml_text: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    entries: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", _ATOM_NS):
        entry_id = entry.findtext("atom:id", default="", namespaces=_ATOM_NS)
        arxiv_id = extract_arxiv_id_from_url(entry_id) or entry_id.rsplit("/", 1)[-1]
        title = (entry.findtext("atom:title", default="", namespaces=_ATOM_NS) or "").strip()
        summary = (
            entry.findtext("atom:summary", default="", namespaces=_ATOM_NS) or ""
        ).strip()
        authors = [
            author.findtext("atom:name", default="", namespaces=_ATOM_NS)
            for author in entry.findall("atom:author", _ATOM_NS)
        ]
        authors = [name for name in authors if name]
        published = entry.findtext("atom:published", default="", namespaces=_ATOM_NS)
        year = int(published[:4]) if len(published) >= 4 and published[:4].isdigit() else None
        doi = None
        for link in entry.findall("atom:link", _ATOM_NS):
            if link.attrib.get("title") == "doi":
                doi = link.attrib.get("href")
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        entries.append(
            {
                "provider": "arxiv",
                "provider_id": arxiv_id,
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": authors,
                "year": year,
                "doi": doi,
                "abstract": summary,
                "pdf_url": pdf_url,
                "landing_page_url": f"https://arxiv.org/abs/{arxiv_id}",
                "discovered_at": datetime.now(UTC)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
            }
        )
    return entries


def fetch_arxiv_entries(
    *,
    query: str,
    limit: int,
    urlopen: Any = urllib.request.urlopen,
) -> list[dict[str, Any]]:
    params = {
        "search_query": f"all:{query}",
        "start": "0",
        "max_results": str(max(1, min(limit, 25))),
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"Accept": "application/atom+xml"})
    try:
        with urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise SourceDiscoveryProviderError(
            f"arXiv request failed: {exc.reason or exc}"
        ) from exc
    return parse_arxiv_atom_feed(payload)


def map_arxiv_entry(entry: dict[str, Any], *, domain_pack: str) -> dict[str, Any]:
    mapped = dict(entry)
    mapped["domain_pack"] = domain_pack
    return mapped


class ArxivProvider:
    provider_id = "arxiv"

    def __init__(self, *, urlopen: Any | None = None) -> None:
        self._urlopen = urlopen

    def health_check(self) -> dict[str, Any]:
        return {
            "provider": self.provider_id,
            "configured": True,
        }

    def discover(
        self, query: str, domain_pack: str, limit: int
    ) -> list[dict[str, Any]]:
        urlopen = self._urlopen or urllib.request.urlopen
        try:
            entries = fetch_arxiv_entries(query=query, limit=limit, urlopen=urlopen)
        except ET.ParseError as exc:
            raise SourceDiscoveryProviderError("arXiv returned invalid Atom XML.") from exc
        return [
            map_arxiv_entry(entry, domain_pack=domain_pack)
            for entry in entries[: max(1, limit)]
        ]
