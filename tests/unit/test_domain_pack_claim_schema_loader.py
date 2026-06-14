"""Domain pack claim_schema.yaml loader proof (ticket-115)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rge.modules.concept_linker import (
    REJECTION_WEAK_CONCEPT_MAPPING,
    link_rejection_diagnostic,
    validate_concept_links,
)
from rge.modules.domain_pack_loader import (
    DomainPackError,
    load_domain_pack,
    measured_dimension_allowed,
    parse_claim_schema_yaml,
    validate_link_domain_metadata,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


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


def _claim_schema_yaml(
    *,
    phases: list[str] | None = None,
    dimensions: list[str] | None = None,
) -> str:
    phase_items = phases or ["ideation"]
    dimension_items = dimensions or ["diversity", "semantic diversity", "quality"]
    lines = [
        "required_domain_metadata_for_creativity_claims:",
        "  - track",
        "  - creative_phase",
        "  - measured_dimension",
        "allowed_tracks:",
        "  - human",
        "  - AI",
        "  - human-AI",
        "allowed_creative_phases:",
    ]
    lines.extend(f"  - {phase}" for phase in phase_items)
    lines.append("allowed_measured_dimensions:")
    lines.extend(f"  - {dimension}" for dimension in dimension_items)
    return "\n".join(lines) + "\n"


def _write_demo_pack(
    tmp_path: Path,
    *,
    pack_id: str = "demo",
    phases: list[str] | None = None,
    dimensions: list[str] | None = None,
) -> Path:
    pack_dir = tmp_path / "domain_packs" / pack_id
    pack_dir.mkdir(parents=True)
    (pack_dir / "domain.yaml").write_text(
        f"id: {pack_id}\n"
        f"name: {pack_id.title()} Pack\n"
        "version: 0.1.0\n"
        "status: active\n"
        "summary: Demo domain pack for unit tests.\n"
        "primary_domains:\n"
        f"  - {pack_id}\n"
        "overlap_domains:\n"
        "  - art\n"
        "lifecycle_states:\n"
        "  - active\n",
        encoding="utf-8",
    )
    (pack_dir / "ontology.yaml").write_text(
        "concepts:\n"
        "  - id: concept_semantic_diversity\n"
        "    label: semantic diversity\n",
        encoding="utf-8",
    )
    (pack_dir / "aliases.yaml").write_text(
        "aliases:\n"
        "  semantic diversity:\n"
        "    - idea diversity\n",
        encoding="utf-8",
    )
    (pack_dir / "scoring.yaml").write_text(_scoring_yaml(), encoding="utf-8")
    (pack_dir / "evidence_types.yaml").write_text(_evidence_types_yaml(), encoding="utf-8")
    (pack_dir / "claim_schema.yaml").write_text(
        _claim_schema_yaml(phases=phases, dimensions=dimensions),
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
    return pack_dir


def _sample_links(*, metadata: dict[str, str]) -> list[dict[str, object]]:
    return [
        {
            "claim_id": "claim-1",
            "concept_label": "semantic diversity",
            "role": "object",
            "confidence": 0.9,
            "domain_metadata": dict(metadata),
        },
        {
            "claim_id": "claim-1",
            "concept_label": "brainstorming",
            "role": "method",
            "confidence": 0.8,
            "domain_metadata": dict(metadata),
        },
    ]


def test_creativity_pack_loads_claim_schema_overlay() -> None:
    pack = load_domain_pack("creativity")
    schema = pack.claim_schema
    assert schema.required_domain_metadata_keys == (
        "track",
        "creative_phase",
        "measured_dimension",
    )
    assert "human-ai" in schema.allowed_tracks
    assert "ideation" in schema.allowed_creative_phases
    assert "semantic diversity" in schema.allowed_measured_dimensions


def test_parse_claim_schema_yaml_reads_lists(tmp_path: Path) -> None:
    path = tmp_path / "claim_schema.yaml"
    path.write_text(
        _claim_schema_yaml(phases=["critique"], dimensions=["quality"]),
        encoding="utf-8",
    )
    overlay = parse_claim_schema_yaml(path)
    assert overlay.allowed_creative_phases == frozenset({"critique"})
    assert overlay.allowed_measured_dimensions == frozenset({"quality"})


def test_creativity_normalizes_idea_diversity_measured_dimension() -> None:
    pack = load_domain_pack("creativity")
    assert measured_dimension_allowed(pack, "idea diversity") is True
    ok, message = validate_link_domain_metadata(
        pack,
        {
            "track": "human-AI",
            "creative_phase": "ideation",
            "measured_dimension": "idea diversity",
        },
    )
    assert ok is True
    assert message is None


def test_temp_pack_restricted_phase_rejects_ideation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_demo_pack(tmp_path, phases=["critique"])

    def _load_pack(pack_id: str, *, root: Path | None = None):
        if pack_id == "demo":
            return load_domain_pack("demo", root=tmp_path)
        return load_domain_pack(pack_id, root=root)

    monkeypatch.setattr(
        "rge.modules.domain_pack_loader.load_domain_pack",
        _load_pack,
    )
    monkeypatch.setattr(
        "rge.modules.concept_linker.load_domain_pack",
        _load_pack,
    )
    links = _sample_links(
        metadata={
            "track": "human-AI",
            "creative_phase": "ideation",
            "measured_dimension": "diversity",
        }
    )
    result = validate_concept_links(links, domain_pack="demo")
    assert result["accepted"] == []
    assert len(result["rejected"]) == 2
    diagnostic = link_rejection_diagnostic(
        result["rejected"][0],
        rejection_reason=REJECTION_WEAK_CONCEPT_MAPPING,
        domain_pack="demo",
    )
    assert "creative_phase 'ideation'" in diagnostic


def test_partial_domain_metadata_link_still_accepted() -> None:
    links = [
        {
            "claim_id": "claim-1",
            "concept_label": "semantic diversity",
            "role": "object",
            "confidence": 0.9,
            "domain_metadata": {
                "track": "human-AI",
                "creative_phase": "ideation",
            },
        },
        {
            "claim_id": "claim-1",
            "concept_label": "brainstorming",
            "role": "method",
            "confidence": 0.8,
            "domain_metadata": {
                "track": "human-AI",
                "creative_phase": "ideation",
                "measured_dimension": "quality",
            },
        },
    ]
    result = validate_concept_links(links, domain_pack="creativity")
    assert len(result["accepted"]) == 2
    assert result["rejected"] == []


def test_load_domain_pack_requires_claim_schema_file(tmp_path: Path) -> None:
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
        "concepts:\n  - id: concept_ai\n    label: AI assistance\n",
        encoding="utf-8",
    )
    (pack_dir / "aliases.yaml").write_text(
        "aliases:\n  AI assistance:\n    - AI-assisted brainstorming\n",
        encoding="utf-8",
    )
    (pack_dir / "scoring.yaml").write_text(_scoring_yaml(), encoding="utf-8")
    (pack_dir / "evidence_types.yaml").write_text(_evidence_types_yaml(), encoding="utf-8")
    with pytest.raises(DomainPackError, match="Claim schema file not found"):
        load_domain_pack("demo", root=tmp_path)
