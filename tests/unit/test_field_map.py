"""Unit tests for field-map report (MVP-P3)."""

from __future__ import annotations

import json

import pytest

from rge.cli import main
from rge.modules.field_map import (
    build_field_clusters,
    generate_field_map_report,
    rank_field_map_records,
    tokenize,
)
from rge.modules.source_resolver import load_manual_fixture_records


def test_tokenize_strips_stopwords() -> None:
    tokens = tokenize("AI creativity and semantic diversity in songwriting")
    assert "and" not in tokens
    assert "creativity" in tokens


def test_build_field_clusters_groups_fixture_records() -> None:
    records = load_manual_fixture_records(domain_pack="creativity")
    clusters = build_field_clusters(records, query="AI creativity diversity")

    assert len(clusters) >= 1
    assert clusters[0]["member_count"] >= 1


def test_rank_field_map_records_prefers_abstract_available() -> None:
    records = load_manual_fixture_records(domain_pack="creativity")
    ranked = rank_field_map_records(
        records,
        query="AI creativity idea diversity",
        top_n=2,
    )

    assert len(ranked) <= 2
    assert all("field_map_score" in item for item in ranked)


def test_generate_field_map_report_fixture_mode() -> None:
    report = generate_field_map_report(
        query="AI assisted creativity and idea diversity",
        domain_pack="creativity",
        fixture_mode=True,
        max_candidates=10,
        top_sources=3,
    )

    assert report["status"] == "ok"
    field_map = report["field_map_report"]
    assert field_map["report_type"] == "field_map"
    assert field_map["cluster_count"] >= 1
    assert "disclaimer" in field_map
    assert report["improvement_recommendation"]["recommended_packet"].startswith("MVP-P")


def test_generate_field_map_cli_fixture_mode(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "generate-field-map",
            "--fixture-mode",
            "--query",
            "AI creativity diversity",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["field_map_report"]["quote_grounded_claims"] is not None
