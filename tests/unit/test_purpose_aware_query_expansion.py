"""Purpose-aware resolver query expansion tests."""

from __future__ import annotations

from typing import Any

import pytest

from rge.modules.source_resolver import resolve_work_candidates
from rge.modules.source_resolver.query_expansion import (
    metadata_only_dominates,
    purpose_aware_alternate_queries,
)
from rge.modules.source_resolver.status import ABSTRACT_AVAILABLE, METADATA_ONLY


def test_purpose_aware_alternate_queries_strips_question_mark() -> None:
    queries = purpose_aware_alternate_queries("How does AI affect human creativity?")
    assert queries
    assert all("?" not in query for query in queries)
    assert "human AI creativity" in queries


def test_metadata_only_dominates_detects_skewed_set() -> None:
    records = [
        {"source_status": METADATA_ONLY},
        {"source_status": METADATA_ONLY},
        {"source_status": ABSTRACT_AVAILABLE, "abstract_text": "AI creativity"},
    ]
    assert metadata_only_dominates(records) is True


def test_resolve_work_candidates_expands_when_metadata_only_dominates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queries_seen: list[str] = []

    def fake_discover(
        backend: str,
        *,
        query: str,
        domain_pack: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        del backend, domain_pack, limit
        queries_seen.append(query)
        if query == "How does AI affect human creativity?":
            return [
                {
                    "source_id": "openalex:meta1",
                    "source_status": METADATA_ONLY,
                    "abstract_text": "",
                    "source_kind": "openalex",
                },
                {
                    "source_id": "openalex:meta2",
                    "source_status": METADATA_ONLY,
                    "abstract_text": "",
                    "source_kind": "openalex",
                },
                {
                    "source_id": "openalex:meta3",
                    "source_status": METADATA_ONLY,
                    "abstract_text": "",
                    "source_kind": "openalex",
                },
            ]
        return [
            {
                "source_id": "openalex:abs1",
                "source_status": ABSTRACT_AVAILABLE,
                "abstract_text": "Generative AI and human creativity outcomes.",
                "source_kind": "openalex",
            }
        ]

    monkeypatch.setattr(
        "rge.modules.source_resolver._discover_backend_candidates",
        fake_discover,
    )
    result = resolve_work_candidates(
        query="How does AI affect human creativity?",
        limit=3,
        backends=["openalex"],
        fixture_mode=False,
    )
    assert result["query_expansion"]["expanded"] is True
    assert len(queries_seen) >= 2
    statuses = {str(record.get("source_status") or "") for record in result["records"]}
    assert ABSTRACT_AVAILABLE in statuses
