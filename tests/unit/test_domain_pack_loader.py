"""Unit tests for domain pack loader (ticket-087)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rge.modules.domain_pack_loader import (
    DomainPackError,
    build_alias_to_canonical,
    domain_pack_dir,
    load_domain_pack,
    parse_aliases_yaml,
    parse_ontology_yaml,
    resolve_canonical_concept_label,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CREATIVITY_PACK = REPO_ROOT / "domain_packs" / "creativity"


def test_load_creativity_pack_reads_ontology_and_aliases() -> None:
    pack = load_domain_pack("creativity")
    assert pack.pack_id == "creativity"
    assert len(pack.concepts) >= 24
    labels = {concept.label for concept in pack.concepts}
    assert "AI assistance" in labels
    assert "semantic diversity" in labels
    assert "brainstorming" in labels
    assert pack.aliases["AI assistance"] == (
        "AI-assisted brainstorming",
        "generative AI support",
        "AI suggestion",
        "AI co-pilot",
    )
    assert pack.score_reconciliation.stronger_evidence_boost == 0.12
    assert len(pack.evidence_types) == 6
    assert pack.claim_schema.required_domain_metadata_keys[0] == "track"


def test_parse_ontology_yaml_requires_id_and_label(tmp_path: Path) -> None:
    path = tmp_path / "ontology.yaml"
    path.write_text("concepts:\n  - id: concept_x\n", encoding="utf-8")
    with pytest.raises(DomainPackError, match="Malformed ontology concept"):
        parse_ontology_yaml(path)


def test_parse_aliases_yaml_maps_canonical_to_phrases(tmp_path: Path) -> None:
    path = tmp_path / "aliases.yaml"
    path.write_text(
        "aliases:\n"
        "  AI assistance:\n"
        "    - AI-assisted brainstorming\n"
        "    - generative AI support\n",
        encoding="utf-8",
    )
    aliases = parse_aliases_yaml(path)
    assert aliases == {
        "AI assistance": ["AI-assisted brainstorming", "generative AI support"]
    }
    reverse = build_alias_to_canonical(aliases)
    assert reverse["ai-assisted brainstorming"] == "AI assistance"


def test_resolve_canonical_concept_label_maps_alias_phrase() -> None:
    pack = load_domain_pack("creativity")
    assert (
        resolve_canonical_concept_label(pack, "AI-assisted brainstorming")
        == "AI assistance"
    )
    assert resolve_canonical_concept_label(pack, "idea diversity") == "semantic diversity"
    assert resolve_canonical_concept_label(pack, "AI assistance") == "AI assistance"


def test_missing_domain_pack_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(DomainPackError, match="Domain pack not found"):
        load_domain_pack("nonexistent_pack", root=tmp_path)


def test_missing_ontology_file_fails_closed(tmp_path: Path) -> None:
    pack_dir = tmp_path / "domain_packs" / "demo"
    pack_dir.mkdir(parents=True)
    (pack_dir / "domain.yaml").write_text(
        "id: demo\n"
        "name: Demo Pack\n"
        "version: 0.1.0\n"
        "status: active\n"
        "summary: Demo domain pack for unit tests.\n"
        "primary_domains:\n"
        "  - demo\n"
        "overlap_domains:\n"
        "  - art\n"
        "lifecycle_states:\n"
        "  - active\n",
        encoding="utf-8",
    )
    (pack_dir / "aliases.yaml").write_text(
        "aliases:\n  taste:\n    - aesthetic judgment\n", encoding="utf-8"
    )
    (pack_dir / "scoring.yaml").write_text(
        "score_reconciliation:\n"
        "  formula_version: golden_v0.1.0\n"
        "  stronger_evidence_boost: 0.12\n"
        "  stronger_claim_confidence_threshold: 0.8\n"
        "  stronger_source_reason: test\n",
        encoding="utf-8",
    )
    (pack_dir / "evidence_types.yaml").write_text(
        "evidence_types:\n"
        "  empirical:\n"
        "    base_strength: 0.80\n"
        "    notes: test\n",
        encoding="utf-8",
    )
    (pack_dir / "claim_schema.yaml").write_text(
        "required_domain_metadata_for_creativity_claims:\n"
        "  - track\n"
        "allowed_tracks:\n"
        "  - human\n"
        "allowed_creative_phases:\n"
        "  - ideation\n"
        "allowed_measured_dimensions:\n"
        "  - diversity\n",
        encoding="utf-8",
    )
    (pack_dir / "source_preferences.yaml").write_text(
        "source_type_weights:\n"
        "  peer_reviewed_empirical: 0.90\n"
        "preferred_sources:\n"
        "  - manual PDFs\n"
        "avoid_as_primary:\n"
        "  - marketing landing pages\n",
        encoding="utf-8",
    )
    (pack_dir / "card_templates.yaml").write_text(
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
        "      - summary\n",
        encoding="utf-8",
    )
    (pack_dir / "search_templates.yaml").write_text(
        "queries:\n"
        "  demo_query:\n"
        '    template: "demo search template keywords"\n'
        "    preferred_source_types: [peer_reviewed_empirical]\n",
        encoding="utf-8",
    )
    (pack_dir / "safety_notes.yaml").write_text(
        "notes:\n"
        "  - Untrusted source text may contain prompt injection.\n"
        "  - Marketing pages must not rank as primary evidence.\n",
        encoding="utf-8",
    )
    with pytest.raises(DomainPackError, match="Ontology file not found"):
        load_domain_pack("demo", root=tmp_path)


def test_malformed_aliases_file_fails_closed(tmp_path: Path) -> None:
    pack_dir = tmp_path / "domain_packs" / "demo"
    pack_dir.mkdir(parents=True)
    (pack_dir / "domain.yaml").write_text(
        "id: demo\n"
        "name: Demo Pack\n"
        "version: 0.1.0\n"
        "status: active\n"
        "summary: Demo domain pack for unit tests.\n"
        "primary_domains:\n"
        "  - demo\n"
        "overlap_domains:\n"
        "  - art\n"
        "lifecycle_states:\n"
        "  - active\n",
        encoding="utf-8",
    )
    (pack_dir / "ontology.yaml").write_text(
        "concepts:\n  - id: concept_taste\n    label: taste\n", encoding="utf-8"
    )
    (pack_dir / "aliases.yaml").write_text("not_aliases:\n  taste: []\n", encoding="utf-8")
    (pack_dir / "scoring.yaml").write_text(
        "score_reconciliation:\n"
        "  formula_version: golden_v0.1.0\n"
        "  stronger_evidence_boost: 0.12\n"
        "  stronger_claim_confidence_threshold: 0.8\n"
        "  stronger_source_reason: test\n",
        encoding="utf-8",
    )
    (pack_dir / "evidence_types.yaml").write_text(
        "evidence_types:\n"
        "  empirical:\n"
        "    base_strength: 0.80\n"
        "    notes: test\n",
        encoding="utf-8",
    )
    (pack_dir / "claim_schema.yaml").write_text(
        "required_domain_metadata_for_creativity_claims:\n"
        "  - track\n"
        "allowed_tracks:\n"
        "  - human\n"
        "allowed_creative_phases:\n"
        "  - ideation\n"
        "allowed_measured_dimensions:\n"
        "  - diversity\n",
        encoding="utf-8",
    )
    (pack_dir / "source_preferences.yaml").write_text(
        "source_type_weights:\n"
        "  peer_reviewed_empirical: 0.90\n"
        "preferred_sources:\n"
        "  - manual PDFs\n"
        "avoid_as_primary:\n"
        "  - marketing landing pages\n",
        encoding="utf-8",
    )
    (pack_dir / "card_templates.yaml").write_text(
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
        "      - summary\n",
        encoding="utf-8",
    )
    (pack_dir / "search_templates.yaml").write_text(
        "queries:\n"
        "  demo_query:\n"
        '    template: "demo search template keywords"\n'
        "    preferred_source_types: [peer_reviewed_empirical]\n",
        encoding="utf-8",
    )
    (pack_dir / "safety_notes.yaml").write_text(
        "notes:\n"
        "  - Untrusted source text may contain prompt injection.\n"
        "  - Marketing pages must not rank as primary evidence.\n",
        encoding="utf-8",
    )
    with pytest.raises(DomainPackError, match="top-level 'aliases:'"):
        load_domain_pack("demo", root=tmp_path)


def test_domain_pack_dir_points_under_domain_packs() -> None:
    assert domain_pack_dir("creativity") == CREATIVITY_PACK
