"""Domain pack source_preferences.yaml loader proof (ticket-116)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rge.modules.domain_pack_loader import (
    DomainPackError,
    load_domain_pack,
    parse_source_preferences_yaml,
    source_type_credibility_prior,
)
from rge.modules.research_queue import (
    compute_priority_score,
    rank_fixture_candidates,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RANKING_FIXTURE = (
    REPO_ROOT / "fixtures" / "candidate_sources" / "source_ranking_fixture.json"
)


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


def _source_preferences_yaml(
    *,
    weights: dict[str, float] | None = None,
) -> str:
    entries = weights or {
        "peer_reviewed_empirical": 0.90,
        "expert_interview": 0.70,
        "marketing_page": 0.20,
    }
    lines = ["source_type_weights:"]
    for key, value in entries.items():
        lines.append(f"  {key}: {value}")
    lines.extend(
        [
            "preferred_sources:",
            "  - manual PDFs",
            "avoid_as_primary:",
            "  - marketing landing pages",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_demo_pack(
    tmp_path: Path,
    *,
    weights: dict[str, float] | None = None,
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
        _source_preferences_yaml(weights=weights),
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


def test_creativity_pack_loads_source_type_weights() -> None:
    pack = load_domain_pack("creativity")
    overlay = pack.source_preferences
    assert overlay.source_type_weights["peer_reviewed_empirical"] == 0.90
    assert overlay.source_type_weights["marketing_page"] == 0.20
    assert "Semantic Scholar" in overlay.preferred_sources
    assert overlay.avoid_as_primary


def test_parse_source_preferences_yaml_reads_weights(tmp_path: Path) -> None:
    path = tmp_path / "source_preferences.yaml"
    path.write_text(
        _source_preferences_yaml(weights={"expert_interview": 0.95}),
        encoding="utf-8",
    )
    overlay = parse_source_preferences_yaml(path)
    assert overlay.source_type_weights["expert_interview"] == 0.95


def test_temp_pack_changes_credibility_prior(tmp_path: Path) -> None:
    _write_demo_pack(
        tmp_path,
        weights={
            "peer_reviewed_empirical": 0.10,
            "expert_interview": 0.95,
        },
    )
    pack = load_domain_pack("demo", root=tmp_path)
    assert source_type_credibility_prior(pack, "expert_interview") == 0.95
    assert source_type_credibility_prior(pack, "peer_reviewed_empirical") == 0.10


def test_pack_credibility_changes_priority_score(tmp_path: Path) -> None:
    _write_demo_pack(
        tmp_path,
        weights={
            "peer_reviewed_empirical": 0.10,
            "expert_interview": 0.95,
        },
    )
    pack = load_domain_pack("demo", root=tmp_path)
    high = compute_priority_score(
        relevance_score=0.5,
        credibility_prior=source_type_credibility_prior(pack, "expert_interview"),
        gap_fill_score=0.5,
    )
    low = compute_priority_score(
        relevance_score=0.5,
        credibility_prior=source_type_credibility_prior(pack, "peer_reviewed_empirical"),
        gap_fill_score=0.5,
    )
    assert high > low


def test_temp_pack_weight_inversion_changes_rank_credibility_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_demo_pack(
        tmp_path,
        weights={
            "peer_reviewed_empirical": 0.10,
            "expert_interview": 0.95,
            "theory_essay": 0.60,
            "blog_post": 0.35,
            "marketing_page": 0.20,
        },
    )

    def _load_pack(pack_id: str, *, root: Path | None = None):
        if pack_id == "demo":
            return load_domain_pack("demo", root=tmp_path)
        return load_domain_pack(pack_id, root=root)

    monkeypatch.setattr(
        "rge.modules.domain_pack_loader.load_domain_pack",
        _load_pack,
    )
    monkeypatch.setattr(
        "rge.modules.research_queue.load_domain_pack",
        _load_pack,
    )

    fixture = __import__("json").loads(RANKING_FIXTURE.read_text(encoding="utf-8"))
    ranked = rank_fixture_candidates(
        fixture.get("candidates", []),
        domain_pack="demo",
    )
    empirical = next(
        row for row in ranked if row["candidate_source_id"] == "cand_empirical_paper"
    )
    expert = next(
        row for row in ranked if row["candidate_source_id"] == "cand_expert_interview"
    )
    assert empirical["credibility_prior"] == 0.10
    assert expert["credibility_prior"] == 0.95


def test_marketing_still_rejected_despite_high_pack_weight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_demo_pack(
        tmp_path,
        weights={
            "peer_reviewed_empirical": 0.90,
            "marketing_page": 0.99,
        },
    )

    def _load_pack(pack_id: str, *, root: Path | None = None):
        if pack_id == "demo":
            return load_domain_pack("demo", root=tmp_path)
        return load_domain_pack(pack_id, root=root)

    monkeypatch.setattr(
        "rge.modules.domain_pack_loader.load_domain_pack",
        _load_pack,
    )
    monkeypatch.setattr(
        "rge.modules.research_queue.load_domain_pack",
        _load_pack,
    )

    fixture = __import__("json").loads(RANKING_FIXTURE.read_text(encoding="utf-8"))
    ranked = rank_fixture_candidates(
        fixture.get("candidates", []),
        domain_pack="demo",
    )
    marketing = next(
        row for row in ranked if row["candidate_source_id"] == "cand_marketing_page"
    )
    assert marketing["credibility_prior"] == 0.99
    assert marketing["status"] == "rejected"


def test_load_domain_pack_requires_source_preferences_file(tmp_path: Path) -> None:
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
    with pytest.raises(DomainPackError, match="Source preferences file not found"):
        load_domain_pack("demo", root=tmp_path)
