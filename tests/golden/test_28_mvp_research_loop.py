"""Golden tests for MVP research loop packets P2/P3/P4."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


def test_abstract_evidence_fixture_mode_cli() -> None:
    from rge.cli import main

    assert main(["generate-abstract-evidence", "--fixture-mode"]) == 0


def test_field_map_fixture_mode_cli() -> None:
    from rge.cli import main

    assert (
        main(
            [
                "generate-field-map",
                "--fixture-mode",
                "--query",
                "AI creativity diversity",
            ]
        )
        == 0
    )


def test_recommend_improvement_packet_fixture_mode_cli() -> None:
    from rge.cli import main

    assert main(["recommend-improvement-packet", "--fixture-mode"]) == 0


def test_end_to_end_fixture_research_loop_chain() -> None:
    from rge.modules.abstract_evidence import generate_abstract_evidence_cards
    from rge.modules.failure_recommender import recommend_from_abstract_evidence_run
    from rge.modules.field_map import generate_field_map_report
    from rge.modules.source_resolver import resolve_work_candidates

    resolved = resolve_work_candidates(query="", fixture_mode=True, domain_pack="creativity")
    evidence = generate_abstract_evidence_cards(resolved["records"], domain_pack="creativity")
    recommendation = recommend_from_abstract_evidence_run(
        evidence,
        source_statuses=[record["source_status"] for record in resolved["records"]],
    )
    field_map = generate_field_map_report(
        query="AI creativity diversity",
        fixture_mode=True,
        top_sources=2,
    )

    assert evidence["accepted_claims_total"] >= 1
    assert recommendation["recommended_packet"].startswith("MVP-P")
    assert field_map["field_map_report"]["abstract_evidence_summary"]["accepted_claims_total"] >= 0
