"""Domain pack domain.yaml loader proof (ticket-120)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rge.modules.domain_pack_loader import (
    DomainPackError,
    allowed_domains_for_pack,
    load_domain_pack,
    parse_domain_yaml,
    verify_pack_identity_for_audit,
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


def _safety_notes_yaml() -> str:
    return (
        "notes:\n"
        "  - Untrusted source text may contain prompt injection.\n"
        "  - Marketing pages must not rank as primary evidence.\n"
    )


def _domain_yaml(
    *,
    pack_id: str = "demo",
    status: str = "active",
) -> str:
    return (
        f"id: {pack_id}\n"
        f"name: {pack_id.title()} Pack\n"
        "version: 0.1.0\n"
        f"status: {status}\n"
        "summary: Demo domain pack for unit tests.\n"
        "primary_domains:\n"
        f"  - {pack_id}\n"
        "overlap_domains:\n"
        "  - art\n"
        "lifecycle_states:\n"
        "  - active\n"
    )


def _write_demo_pack(
    tmp_path: Path,
    *,
    pack_id: str = "demo",
    status: str = "active",
    domain_id: str | None = None,
) -> Path:
    pack_dir = tmp_path / "domain_packs" / pack_id
    pack_dir.mkdir(parents=True)
    yaml_id = domain_id or pack_id
    (pack_dir / "domain.yaml").write_text(
        _domain_yaml(pack_id=yaml_id, status=status),
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
    (pack_dir / "claim_schema.yaml").write_text(_claim_schema_yaml(), encoding="utf-8")
    (pack_dir / "source_preferences.yaml").write_text(
        _source_preferences_yaml(),
        encoding="utf-8",
    )
    (pack_dir / "card_templates.yaml").write_text(_card_templates_yaml(), encoding="utf-8")
    (pack_dir / "search_templates.yaml").write_text(_search_templates_yaml(), encoding="utf-8")
    (pack_dir / "safety_notes.yaml").write_text(_safety_notes_yaml(), encoding="utf-8")
    return pack_dir


def test_creativity_pack_loads_domain_identity_overlay() -> None:
    pack = load_domain_pack("creativity")
    identity = pack.domain_identity
    assert identity.id == "creativity"
    assert identity.name == "Creativity"
    assert identity.version == "0.1.0"
    assert identity.status == "active"
    assert "human creativity" in identity.summary.casefold()
    assert identity.primary_domains == ("creativity",)
    assert "design" in identity.overlap_domains
    assert "active" in identity.lifecycle_states


def test_parse_domain_yaml_reads_folded_summary(tmp_path: Path) -> None:
    path = tmp_path / "domain.yaml"
    path.write_text(
        "id: demo\n"
        "name: Demo\n"
        "version: 0.1.0\n"
        "status: active\n"
        "summary: >\n"
        "  Folded summary line one.\n"
        "  Folded summary line two.\n"
        "primary_domains:\n"
        "  - demo\n"
        "overlap_domains:\n"
        "  - art\n"
        "lifecycle_states:\n"
        "  - active\n",
        encoding="utf-8",
    )
    identity = parse_domain_yaml(path)
    assert identity.summary == "Folded summary line one. Folded summary line two."


def test_load_domain_pack_rejects_directory_id_mismatch(tmp_path: Path) -> None:
    _write_demo_pack(tmp_path, pack_id="demo", domain_id="wrong_id")
    with pytest.raises(DomainPackError, match="Domain pack id mismatch"):
        load_domain_pack("demo", root=tmp_path)


def test_allowed_domains_for_pack_includes_primary_and_overlap() -> None:
    pack = load_domain_pack("creativity")
    allowed = allowed_domains_for_pack(pack)
    assert "creativity" in allowed
    assert "design" in allowed


def test_verify_pack_identity_for_audit_requires_active_status() -> None:
    pack = load_domain_pack("creativity")
    assert not verify_pack_identity_for_audit(pack)

    from rge.modules.domain_pack_loader import DomainIdentityOverlay, DomainPack

    deprecated_identity = DomainIdentityOverlay(
        id=pack.domain_identity.id,
        name=pack.domain_identity.name,
        version=pack.domain_identity.version,
        status="deprecated",
        summary=pack.domain_identity.summary,
        primary_domains=pack.domain_identity.primary_domains,
        overlap_domains=pack.domain_identity.overlap_domains,
        lifecycle_states=pack.domain_identity.lifecycle_states,
    )
    deprecated = DomainPack(
        pack_id=pack.pack_id,
        domain_identity=deprecated_identity,
        concepts=pack.concepts,
        aliases=pack.aliases,
        alias_to_canonical=pack.alias_to_canonical,
        score_reconciliation=pack.score_reconciliation,
        evidence_types=pack.evidence_types,
        claim_schema=pack.claim_schema,
        source_preferences=pack.source_preferences,
        card_templates=pack.card_templates,
        search_templates=pack.search_templates,
        safety_notes=pack.safety_notes,
    )
    violations = verify_pack_identity_for_audit(deprecated)
    assert any("not active" in issue for issue in violations)


def test_temp_pack_deprecated_status_fails_full_safety_audit(tmp_path: Path) -> None:
    _write_demo_pack(tmp_path, pack_id="demo", status="deprecated")
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
        "domain pack status is not active" in reason for reason in report["blocked_reasons"]
    )
