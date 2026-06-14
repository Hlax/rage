"""Domain pack evidence_types.yaml loader proof (ticket-114)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rge.modules.claim_validator import (
    REJECTION_UNSUPPORTED,
    rejection_diagnostic,
    validate_candidate_claim,
)
from rge.modules.domain_pack_loader import (
    DomainPackError,
    evidence_type_ids,
    load_domain_pack,
    parse_evidence_types_yaml,
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


def _evidence_types_yaml(
    *,
    types: list[tuple[str, float, str]] | None = None,
) -> str:
    entries = types or [("empirical", 0.80, "Controlled study.")]
    lines = ["evidence_types:"]
    for type_id, strength, notes in entries:
        lines.extend(
            [
                f"  {type_id}:",
                f"    base_strength: {strength}",
                f"    notes: {notes}",
            ]
        )
    return "\n".join(lines) + "\n"


def _claim_schema_yaml() -> str:
    return (
        "required_domain_metadata_for_creativity_claims:\n"
        "  - track\n"
        "  - creative_phase\n"
        "  - measured_dimension\n"
        "allowed_tracks:\n"
        "  - human\n"
        "  - AI\n"
        "  - human-AI\n"
        "allowed_creative_phases:\n"
        "  - ideation\n"
        "allowed_measured_dimensions:\n"
        "  - diversity\n"
        "  - semantic diversity\n"
        "  - quality\n"
    )


def _write_demo_pack(
    tmp_path: Path,
    *,
    pack_id: str = "demo",
    evidence_types: list[tuple[str, float, str]] | None = None,
) -> Path:
    pack_dir = tmp_path / "domain_packs" / pack_id
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
    (pack_dir / "evidence_types.yaml").write_text(
        _evidence_types_yaml(types=evidence_types),
        encoding="utf-8",
    )
    (pack_dir / "claim_schema.yaml").write_text(_claim_schema_yaml(), encoding="utf-8")
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
    return pack_dir


def _valid_candidate(*, domain: str, evidence_type: str) -> dict[str, str | float | list[str]]:
    return {
        "claim_text": "AI-assisted brainstorming increased average idea quality in short-form writing tasks.",
        "source_id": "src_1",
        "chunk_id": "chk_1",
        "quote_span": "AI-assisted brainstorming increased average idea quality across submitted ideas",
        "subject": "AI-assisted brainstorming",
        "predicate": "increased",
        "object": "average idea quality",
        "scope": "short-form writing tasks",
        "evidence_type": evidence_type,
        "confidence": 0.7,
        "limitations": ["Only tested short-form writing tasks."],
        "domain": domain,
    }


_CHUNK_TEXT = (
    "In a controlled study of short-form writing tasks, we found that "
    "AI-assisted brainstorming increased average idea quality across submitted ideas."
)


def test_creativity_pack_loads_evidence_types() -> None:
    pack = load_domain_pack("creativity")
    ids = evidence_type_ids(pack)
    assert ids == frozenset(
        {
            "empirical",
            "meta_analysis",
            "case_study",
            "theory",
            "interview",
            "benchmark",
        }
    )
    empirical = next(item for item in pack.evidence_types if item.id == "empirical")
    assert empirical.base_strength == 0.80
    assert "Controlled" in empirical.notes


def test_parse_evidence_types_yaml_reads_definitions(tmp_path: Path) -> None:
    path = tmp_path / "evidence_types.yaml"
    path.write_text(
        "evidence_types:\n"
        "  benchmark:\n"
        "    base_strength: 0.65\n"
        "    notes: Strong for model behavior if metrics match question.\n",
        encoding="utf-8",
    )
    definitions = parse_evidence_types_yaml(path)
    assert len(definitions) == 1
    assert definitions[0].id == "benchmark"
    assert definitions[0].base_strength == 0.65


def test_temp_pack_restricted_allowlist_rejects_empirical(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_demo_pack(
        tmp_path,
        evidence_types=[("benchmark", 0.65, "Benchmark only.")],
    )

    def _load_pack(pack_id: str, *, root: Path | None = None):
        if pack_id == "demo":
            return load_domain_pack("demo", root=tmp_path)
        return load_domain_pack(pack_id, root=root)

    monkeypatch.setattr(
        "rge.modules.domain_pack_loader.load_domain_pack",
        _load_pack,
    )
    candidate = _valid_candidate(domain="demo", evidence_type="empirical")
    status, _, reason = validate_candidate_claim(candidate, chunk_text=_CHUNK_TEXT)
    assert status == "rejected"
    assert reason == REJECTION_UNSUPPORTED
    diagnostic = rejection_diagnostic(
        candidate,
        chunk_text=_CHUNK_TEXT,
        rejection_reason=reason,
    )
    assert "evidence_type 'empirical'" in diagnostic
    assert "domain pack 'demo'" in diagnostic


def test_temp_pack_accepts_benchmark_evidence_type(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_demo_pack(
        tmp_path,
        evidence_types=[("benchmark", 0.65, "Benchmark only.")],
    )

    def _load_pack(pack_id: str, *, root: Path | None = None):
        if pack_id == "demo":
            return load_domain_pack("demo", root=tmp_path)
        return load_domain_pack(pack_id, root=root)

    monkeypatch.setattr(
        "rge.modules.domain_pack_loader.load_domain_pack",
        _load_pack,
    )
    candidate = _valid_candidate(domain="demo", evidence_type="benchmark")
    status, _, reason = validate_candidate_claim(candidate, chunk_text=_CHUNK_TEXT)
    assert status == "accepted"
    assert reason is None


def test_missing_evidence_types_section_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "evidence_types.yaml"
    path.write_text("overlay_version: 0.1.0\n", encoding="utf-8")
    with pytest.raises(DomainPackError, match="evidence_types"):
        parse_evidence_types_yaml(path)


def test_load_domain_pack_requires_evidence_types_file(tmp_path: Path) -> None:
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
    with pytest.raises(DomainPackError, match="Evidence types file not found"):
        load_domain_pack("demo", root=tmp_path)
