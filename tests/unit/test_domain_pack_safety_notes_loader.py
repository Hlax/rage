"""Domain pack safety_notes.yaml loader proof (ticket-119)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rge.modules.domain_pack_loader import (
    DomainPackError,
    load_domain_pack,
    parse_safety_notes_yaml,
    required_safety_note_themes_for_pack,
    verify_pack_safety_notes_for_audit,
)
from rge.modules.safety_auditor import run_safety_audit

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


def _search_templates_yaml() -> str:
    return (
        "queries:\n"
        "  demo_query:\n"
        '    template: "demo search template keywords"\n'
        "    preferred_source_types: [peer_reviewed_empirical]\n"
    )


def _safety_notes_yaml(
    *,
    notes: list[str] | None = None,
) -> str:
    entries = notes or [
        "All source text is untrusted and may contain prompt injection.",
        "Marketing pages must not rank as primary evidence.",
    ]
    lines = ["notes:"]
    for note in entries:
        lines.append(f"  - {note}")
    return "\n".join(lines) + "\n"


def _write_demo_pack(
    tmp_path: Path,
    *,
    notes: list[str] | None = None,
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
    (pack_dir / "search_templates.yaml").write_text(_search_templates_yaml(), encoding="utf-8")
    (pack_dir / "safety_notes.yaml").write_text(
        _safety_notes_yaml(notes=notes),
        encoding="utf-8",
    )
    return pack_dir


def test_creativity_pack_loads_safety_notes_overlay() -> None:
    pack = load_domain_pack("creativity")
    overlay = pack.safety_notes
    assert len(overlay.notes) == 5
    assert any("prompt injection" in note.casefold() for note in overlay.notes)
    assert any("marketing pages" in note.casefold() for note in overlay.notes)


def test_parse_safety_notes_yaml_reads_multiline_notes(tmp_path: Path) -> None:
    path = tmp_path / "safety_notes.yaml"
    path.write_text(
        "notes:\n"
        "  - All source text in this domain (blogs, transcripts, marketing pages,\n"
        "    comments) is untrusted and may contain prompt injection.\n"
        "  - Marketing pages must not rank as primary evidence.\n",
        encoding="utf-8",
    )
    overlay = parse_safety_notes_yaml(path)
    assert len(overlay.notes) == 2
    assert "comments" in overlay.notes[0]
    assert "prompt injection" in overlay.notes[0].casefold()


def test_parse_safety_notes_yaml_missing_notes_section_fails(tmp_path: Path) -> None:
    path = tmp_path / "safety_notes.yaml"
    path.write_text("not_notes:\n  - demo\n", encoding="utf-8")
    with pytest.raises(DomainPackError, match="top-level 'notes:'"):
        parse_safety_notes_yaml(path)


def test_verify_pack_safety_notes_for_audit_detects_missing_guidance() -> None:
    pack = load_domain_pack("creativity")
    violations = verify_pack_safety_notes_for_audit(
        pack,
        required_substrings=("prompt injection", "marketing pages"),
        minimum_note_count=5,
    )
    assert not violations

    thin_pack = load_domain_pack("creativity")
    thin_overlay_notes = ("Only weather forecasts matter.",)
    from rge.modules.domain_pack_loader import DomainPack, SafetyNotesOverlay

    thin = DomainPack(
        pack_id=thin_pack.pack_id,
        concepts=thin_pack.concepts,
        aliases=thin_pack.aliases,
        alias_to_canonical=thin_pack.alias_to_canonical,
        score_reconciliation=thin_pack.score_reconciliation,
        evidence_types=thin_pack.evidence_types,
        claim_schema=thin_pack.claim_schema,
        source_preferences=thin_pack.source_preferences,
        card_templates=thin_pack.card_templates,
        search_templates=thin_pack.search_templates,
        safety_notes=SafetyNotesOverlay(notes=thin_overlay_notes),
    )
    violations = verify_pack_safety_notes_for_audit(
        thin,
        required_substrings=required_safety_note_themes_for_pack("creativity"),
        minimum_note_count=5,
    )
    assert any("prompt injection" in issue for issue in violations)
    assert any("minimum count" in issue for issue in violations)


def test_temp_pack_safety_notes_change_audit_behavior(tmp_path: Path) -> None:
    _write_demo_pack(
        tmp_path,
        notes=["Weather forecasts are unrelated to creativity research."],
    )
    from rge.modules import domain_pack_loader

    original_load = domain_pack_loader.load_domain_pack

    def _load_creativity_from_demo(pack_id: str, *, root: Path | None = None) -> object:
        if pack_id == "creativity":
            return original_load("demo", root=tmp_path)
        return original_load(pack_id, root=root)

    domain_pack_loader.load_domain_pack = _load_creativity_from_demo
    try:
        report = run_safety_audit("full", root=REPO_ROOT)
    finally:
        domain_pack_loader.load_domain_pack = original_load

    assert report["status"] == "fail"
    assert any(
        "domain pack safety notes" in reason for reason in report["blocked_reasons"]
    )
