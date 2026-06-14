"""Domain pack card_templates.yaml loader proof (ticket-117)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rge.modules.domain_pack_loader import (
    DomainPackError,
    load_domain_pack,
    parse_card_templates_yaml,
    template_required_fields,
)
from rge.safety.public_export_policy import validate_public_card

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


def _card_templates_yaml(
    *,
    cluster_required: list[str] | None = None,
    claim_required: list[str] | None = None,
) -> str:
    cluster_fields = cluster_required or [
        "title",
        "summary",
        "confidence",
        "concepts",
        "source_count",
        "strongest_support",
        "strongest_qualification",
        "open_gaps",
    ]
    claim_fields = claim_required or [
        "title",
        "summary",
        "confidence",
        "concepts",
        "source_count",
        "public_caveats",
    ]
    lines = [
        "cards:",
        "  claim_card:",
        "    required_fields:",
    ]
    for field in claim_fields:
        lines.append(f"      - {field}")
    lines.extend(["  cluster_card:", "    required_fields:"])
    for field in cluster_fields:
        lines.append(f"      - {field}")
    lines.extend(
        [
            "  theory_card:",
            "    required_fields:",
            "      - title",
            "      - summary",
            "      - confidence",
            "      - supporting_claim_count",
            "      - weakening_evidence",
            "      - boundary_conditions",
            "      - status",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_demo_pack(
    tmp_path: Path,
    *,
    cluster_required: list[str] | None = None,
    claim_required: list[str] | None = None,
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
    (pack_dir / "card_templates.yaml").write_text(
        _card_templates_yaml(
            cluster_required=cluster_required,
            claim_required=claim_required,
        ),
        encoding="utf-8",
    )
    return pack_dir


def _sample_cluster_card(*, include_caveats: bool = True) -> dict[str, object]:
    card: dict[str, object] = {
        "id": "card_demo_cluster",
        "type": "cluster_card",
        "title": "Demo cluster",
        "summary": "Fixture summary for cluster card validation.",
        "confidence": "medium",
        "concepts": ["AI assistance"],
        "source_count": 2,
        "public_detail_level": "standard",
        "updated_at": "2026-06-12T00:00:00Z",
    }
    if include_caveats:
        card["public_caveats"] = ["Fixture caveat text."]
    return card


def test_creativity_pack_loads_card_templates_overlay() -> None:
    pack = load_domain_pack("creativity")
    overlay = pack.card_templates
    assert overlay.required_fields_by_type["claim_card"] == (
        "title",
        "summary",
        "confidence",
        "concepts",
        "source_count",
        "public_caveats",
    )
    assert overlay.required_fields_by_type["cluster_card"] == (
        "title",
        "summary",
        "confidence",
        "concepts",
        "source_count",
        "strongest_support",
        "strongest_qualification",
        "open_gaps",
    )
    assert overlay.required_fields_by_type["theory_card"] == (
        "title",
        "summary",
        "confidence",
        "supporting_claim_count",
        "weakening_evidence",
        "boundary_conditions",
        "status",
    )


def test_parse_card_templates_yaml_reads_required_fields(tmp_path: Path) -> None:
    path = tmp_path / "card_templates.yaml"
    path.write_text(
        _card_templates_yaml(cluster_required=["title", "summary"]),
        encoding="utf-8",
    )
    overlay = parse_card_templates_yaml(path)
    assert overlay.required_fields_by_type["cluster_card"] == ("title", "summary")


def test_parse_card_templates_yaml_missing_cards_section_fails(tmp_path: Path) -> None:
    path = tmp_path / "card_templates.yaml"
    path.write_text("not_cards:\n  claim_card:\n", encoding="utf-8")
    with pytest.raises(DomainPackError, match="top-level 'cards:'"):
        parse_card_templates_yaml(path)


def test_template_required_fields_returns_pack_fields() -> None:
    pack = load_domain_pack("creativity")
    assert template_required_fields(pack, "cluster_card") == pack.card_templates.required_fields_by_type[
        "cluster_card"
    ]
    assert template_required_fields(pack, "unknown_type") == ()


def test_temp_pack_cluster_template_requires_public_caveats(tmp_path: Path) -> None:
    _write_demo_pack(
        tmp_path,
        cluster_required=[
            "title",
            "summary",
            "confidence",
            "concepts",
            "source_count",
            "public_caveats",
        ],
    )
    pack = load_domain_pack("demo", root=tmp_path)
    template_fields = template_required_fields(pack, "cluster_card")

    missing = validate_public_card(
        _sample_cluster_card(include_caveats=False),
        template_required_fields=template_fields,
    )
    assert any("missing template-required card field: public_caveats" in issue for issue in missing)

    present = validate_public_card(
        _sample_cluster_card(include_caveats=True),
        template_required_fields=template_fields,
    )
    assert not any("missing template-required" in issue for issue in present)


def test_claim_card_template_does_not_apply_to_cluster_cards(tmp_path: Path) -> None:
    _write_demo_pack(
        tmp_path,
        claim_required=["title"],
        cluster_required=["title", "summary"],
    )
    pack = load_domain_pack("demo", root=tmp_path)
    cluster_fields = template_required_fields(pack, "cluster_card")
    assert cluster_fields == ("title", "summary")

    card = _sample_cluster_card(include_caveats=False)
    violations = validate_public_card(card, template_required_fields=cluster_fields)
    assert not any("missing template-required card field: public_caveats" in issue for issue in violations)


def test_pack_only_fields_outside_allowlist_are_not_enforced() -> None:
    pack = load_domain_pack("creativity")
    template_fields = template_required_fields(pack, "cluster_card")
    card = _sample_cluster_card(include_caveats=True)
    violations = validate_public_card(card, template_required_fields=template_fields)
    assert not any("strongest_support" in issue for issue in violations)
    assert not any("open_gaps" in issue for issue in violations)
