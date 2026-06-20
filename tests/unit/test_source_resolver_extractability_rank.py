"""Purpose-gated source expansion ranking tests."""

from __future__ import annotations

from rge.modules.research_queue import score_discovered_candidate
from rge.modules.source_resolver.status import (
    ABSTRACT_AVAILABLE,
    METADATA_ONLY,
    rank_records_by_extractability,
)


def test_rank_records_by_extractability_prefers_abstracts() -> None:
    records = [
        {"source_id": "a", "source_status": METADATA_ONLY, "abstract_text": ""},
        {"source_id": "b", "source_status": ABSTRACT_AVAILABLE, "abstract_text": "AI creativity"},
        {"source_id": "c", "source_status": METADATA_ONLY, "abstract_text": ""},
    ]
    ranked = rank_records_by_extractability(records)
    assert ranked[0]["source_id"] == "b"


def test_score_discovered_candidate_abstract_bonus() -> None:
    with_abstract = score_discovered_candidate(
        {
            "title": "Human AI creativity",
            "abstract": "Generative models affect songwriting diversity.",
            "year": 2024,
            "doi": "10.1000/example",
        },
        query="human AI creativity",
    )
    without_abstract = score_discovered_candidate(
        {
            "title": "Human AI creativity",
            "abstract": "",
            "year": 2024,
            "doi": "10.1000/example",
        },
        query="human AI creativity",
    )
    assert with_abstract["priority_score"] > without_abstract["priority_score"]
