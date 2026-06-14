"""Domain pack search_templates.yaml loader proof (ticket-118)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rge.modules.domain_pack_loader import (
    DomainPackError,
    load_domain_pack,
    parse_search_templates_yaml,
    search_template_topic_signals,
    source_strategy_from_search_templates,
)
from rge.modules.research_planner import _score_followup, validate_followup_question

REPO_ROOT = Path(__file__).resolve().parents[2]

IN_SCOPE_QUESTION = (
    "Does divergent prompting reduce AI-driven semantic convergence?"
)
OFF_TOPIC_QUESTION = "What is the weather in Seattle tomorrow?"


def _scoring_yaml() -> str:
    return (
        "score_reconciliation:\n"
        "  formula_version: golden_v0.1.0\n"
        "  stronger_evidence_boost: 0.12\n"
        "  stronger_claim_confidence_threshold: 0.8\n"
        "  stronger_source_reason: test\n"
    )


def _evidence_types_yaml() -> str:
    return (
        "evidence_types:\n"
        "  empirical:\n"
        "    base_strength: 0.80\n"
        "    notes: test\n"
    )


def _claim_schema_yaml() -> str:
    return (
        "required_domain_metadata_for_creativity_claims:\n"
        "  - track\n"
        "allowed_tracks:\n"
        "  - human\n"
        "allowed_creative_phases:\n"
        "  - ideation\n"
        "allowed_measured_dimensions:\n"
        "  - diversity\n"
    )


def _source_preferences_yaml() -> str:
    return (
        "source_type_weights:\n"
        "  peer_reviewed_empirical: 0.90\n"
        "preferred_sources:\n"
        "  - manual PDFs\n"
        "avoid_as_primary:\n"
        "  - marketing landing pages\n"
    )


def _card_templates_yaml() -> str:
    return (
        "cards:\n"
        "  claim_card:\n"
        "    required_fields:\n"
        "      - title\n"
        "      - summary\n"
        "  cluster_card:\n"
        "    required_fields:\n"
        "      - title\n"
        "      - summary\n"
        "  theory_card:\n"
        "    required_fields:\n"
        "      - title\n"
        "      - summary\n"
    )


def _search_templates_yaml(
    *,
    queries: dict[str, tuple[str, list[str]]] | None = None,
) -> str:
    entries = queries or {
        "demo_query": (
            "demo search template keywords",
            ["peer_reviewed_empirical"],
        ),
    }
    lines = ["queries:"]
    for query_id, (template, preferred) in entries.items():
        lines.append(f"  {query_id}:")
        lines.append(f'    template: "{template}"')
        preferred_joined = ", ".join(preferred)
        lines.append(f"    preferred_source_types: [{preferred_joined}]")
    return "\n".join(lines) + "\n"


def _write_demo_pack(
    tmp_path: Path,
    *,
    queries: dict[str, tuple[str, list[str]]] | None = None,
) -> Path:
    pack_dir = tmp_path / "domain_packs" / "demo"
    pack_dir.mkdir(parents=True)
    (pack_dir / "ontology.yaml").write_text(
        "concepts:\n  - id: concept_ai\n    label: AI assistance\n",
        encoding="utf-8",
    )
    (pack_dir / "aliases.yaml").write_text(
        "aliases:\n  AI assistance:\n    - AI-assisted brainstorming\n",
        encoding="utf-8",
    )
    (pack_dir / "scoring.yaml").write_text(_scoring_yaml(), encoding="utf-8")
    (pack_dir / "evidence_types.yaml").write_text(_evidence_types_yaml(), encoding="utf-8")
    (pack_dir / "claim_schema.yaml").write_text(_claim_schema_yaml(), encoding="utf-8")
    (pack_dir / "source_preferences.yaml").write_text(
        _source_preferences_yaml(),
        encoding="utf-8",
    )
    (pack_dir / "card_templates.yaml").write_text(_card_templates_yaml(), encoding="utf-8")
    (pack_dir / "search_templates.yaml").write_text(
        _search_templates_yaml(queries=queries),
        encoding="utf-8",
    )
    return pack_dir


def test_creativity_pack_loads_search_templates_overlay() -> None:
    pack = load_domain_pack("creativity")
    overlay = pack.search_templates
    assert len(overlay.queries) == 3
    divergent = overlay.queries["divergent_prompting"]
    assert divergent.template == "divergent prompting AI ideation originality diversity"
    assert divergent.preferred_source_types == ("empirical", "benchmark_paper")


def test_parse_search_templates_yaml_reads_queries(tmp_path: Path) -> None:
    path = tmp_path / "search_templates.yaml"
    path.write_text(
        _search_templates_yaml(
            queries={
                "custom_query": (
                    "custom template phrase for testing",
                    ["expert_interview", "case_study"],
                ),
            }
        ),
        encoding="utf-8",
    )
    overlay = parse_search_templates_yaml(path)
    query = overlay.queries["custom_query"]
    assert query.template == "custom template phrase for testing"
    assert query.preferred_source_types == ("expert_interview", "case_study")


def test_parse_search_templates_yaml_missing_queries_section_fails(tmp_path: Path) -> None:
    path = tmp_path / "search_templates.yaml"
    path.write_text("not_queries:\n  demo:\n", encoding="utf-8")
    with pytest.raises(DomainPackError, match="top-level 'queries:'"):
        parse_search_templates_yaml(path)


def test_source_strategy_from_search_templates_maps_pack_queries() -> None:
    pack = load_domain_pack("creativity")
    strategy = source_strategy_from_search_templates(pack)
    assert strategy["mode"] == "pack_search_templates"
    assert "divergent_prompting" in strategy["search_queries"]
    assert strategy["search_queries"]["ai_diversity_empirical"]["template"].startswith(
        "generative AI"
    )


def test_temp_pack_search_templates_change_followup_scoring(tmp_path: Path) -> None:
    creativity = load_domain_pack("creativity")
    _write_demo_pack(
        tmp_path,
        queries={
            "off_topic_only": (
                "weather forecast meteorology rainfall",
                ["peer_reviewed_empirical"],
            ),
        },
    )
    demo = load_domain_pack("demo", root=tmp_path)
    allowed = ["AI assistance", "originality"]

    creativity_scores = _score_followup(IN_SCOPE_QUESTION, allowed, creativity)
    demo_scores = _score_followup(IN_SCOPE_QUESTION, allowed, demo)

    assert creativity_scores["topic_fit"] > demo_scores["topic_fit"]
    assert creativity_scores["priority_score"] > demo_scores["priority_score"]


def test_validate_followup_uses_pack_templates_for_scoring(tmp_path: Path) -> None:
    _write_demo_pack(
        tmp_path,
        queries={
            "divergent_only": (
                "divergent prompting semantic convergence ideation",
                ["peer_reviewed_empirical"],
            ),
        },
    )
    contract = {
        "domain_pack": "demo",
        "allowed_concepts": ["AI assistance", "originality"],
        "out_of_scope_concepts": [],
        "drift_threshold": 0.35,
    }
    # Monkeypatch load_domain_pack root via contract domain_pack demo on tmp_path
    from rge.modules import domain_pack_loader

    original_load = domain_pack_loader.load_domain_pack

    def _load_demo(pack_id: str, *, root: Path | None = None) -> object:
        if pack_id == "demo":
            return original_load("demo", root=tmp_path)
        return original_load(pack_id, root=root)

    domain_pack_loader.load_domain_pack = _load_demo
    try:
        from rge.modules import research_planner

        research_planner.load_domain_pack = _load_demo
        result = validate_followup_question(IN_SCOPE_QUESTION, contract)
        assert result["decision"] == "accepted"
        result_off = validate_followup_question(OFF_TOPIC_QUESTION, contract)
        assert result_off["decision"] == "parked"
    finally:
        domain_pack_loader.load_domain_pack = original_load
