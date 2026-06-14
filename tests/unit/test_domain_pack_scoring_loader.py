"""Domain pack scoring.yaml loader proof (ticket-113)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from rge.db.repositories import ClaimRecord
from rge.modules.domain_pack_loader import (
    DomainPackError,
    load_domain_pack,
    parse_scoring_yaml,
)
from rge.modules.score_reconciler import compute_relationship_score

REPO_ROOT = Path(__file__).resolve().parents[2]


def _scoring_yaml(
    *,
    boost: float = 0.12,
    threshold: float = 0.8,
    formula_version: str = "golden_v0.1.0",
    reason: str = "Pack-defined stronger evidence reason.",
) -> str:
    return (
        "overlay_version: 0.1.0\n"
        "score_reconciliation:\n"
        f"  formula_version: {formula_version}\n"
        f"  stronger_evidence_boost: {boost}\n"
        f"  stronger_claim_confidence_threshold: {threshold}\n"
        f"  stronger_source_reason: {reason}\n"
    )


def _write_demo_pack(
    tmp_path: Path,
    *,
    pack_id: str = "demo",
    boost: float = 0.20,
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
        "concepts:\n  - id: concept_ai\n    label: AI assistance\n",
        encoding="utf-8",
    )
    (pack_dir / "aliases.yaml").write_text(
        "aliases:\n  AI assistance:\n    - AI-assisted brainstorming\n",
        encoding="utf-8",
    )
    (pack_dir / "scoring.yaml").write_text(
        _scoring_yaml(boost=boost),
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
    return pack_dir


def _strong_claim(confidence: float = 0.85) -> ClaimRecord:
    return ClaimRecord(
        id="claim-strong",
        source_id="source-1",
        chunk_id="chunk-1",
        claim_text="AI assistance may reduce semantic diversity in brainstorming.",
        statement_type="empirical",
        subject="AI assistance",
        predicate="may_reduce",
        object="semantic diversity",
        scope="brainstorming",
        evidence_type="empirical_study",
        confidence=confidence,
        limitations_json="[]",
        domain="creativity",
        status="accepted",
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )


def test_creativity_pack_loads_score_reconciliation_overlay() -> None:
    pack = load_domain_pack("creativity")
    overlay = pack.score_reconciliation
    assert overlay.formula_version == "golden_v0.1.0"
    assert overlay.stronger_evidence_boost == 0.12
    assert overlay.stronger_claim_confidence_threshold == 0.8
    assert "higher-credibility source" in overlay.stronger_source_reason


def test_parse_scoring_yaml_reads_folded_reason_block(tmp_path: Path) -> None:
    path = tmp_path / "scoring.yaml"
    path.write_text(
        "overlay_version: 0.1.0\n"
        "score_reconciliation:\n"
        "  formula_version: golden_v0.1.0\n"
        "  stronger_evidence_boost: 0.12\n"
        "  stronger_claim_confidence_threshold: 0.8\n"
        "  stronger_source_reason: >-\n"
        "    New supporting empirical claim from higher-credibility source.\n",
        encoding="utf-8",
    )
    overlay = parse_scoring_yaml(path)
    assert overlay.stronger_source_reason == (
        "New supporting empirical claim from higher-credibility source."
    )


def test_temp_pack_boost_changes_compute_relationship_score(tmp_path: Path) -> None:
    _write_demo_pack(tmp_path, boost=0.20)
    pack = load_domain_pack("demo", root=tmp_path)
    claim = _strong_claim()
    new_score = compute_relationship_score(
        0.5,
        claim,
        overlay=pack.score_reconciliation,
    )
    assert new_score == 0.70


def test_temp_pack_threshold_blocks_weaker_claim(tmp_path: Path) -> None:
    _write_demo_pack(tmp_path, boost=0.20)
    pack = load_domain_pack("demo", root=tmp_path)
    blocked = replace(pack.score_reconciliation, stronger_claim_confidence_threshold=0.9)
    claim = _strong_claim(confidence=0.85)
    assert compute_relationship_score(0.5, claim, overlay=blocked) == 0.5


def test_missing_score_reconciliation_section_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "scoring.yaml"
    path.write_text("overlay_version: 0.1.0\n", encoding="utf-8")
    with pytest.raises(DomainPackError, match="score_reconciliation"):
        parse_scoring_yaml(path)


def test_load_domain_pack_requires_scoring_file(tmp_path: Path) -> None:
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
    with pytest.raises(DomainPackError, match="Scoring file not found"):
        load_domain_pack("demo", root=tmp_path)
