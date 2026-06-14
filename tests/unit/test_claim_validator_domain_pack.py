"""Claim validator domain pack allowlist proof (ticket-121)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rge.modules.claim_validator import (
    REJECTION_UNSUPPORTED,
    rejection_diagnostic,
    validate_candidate_claim,
)
from rge.modules.domain_pack_loader import allowed_domains_for_pack, load_domain_pack

REPO_ROOT = Path(__file__).resolve().parents[2]


def _valid_candidate(*, domain: str) -> dict[str, str | float | list[str]]:
    return {
        "claim_text": "AI-assisted brainstorming increased average idea quality in short-form writing tasks.",
        "source_id": "src_1",
        "chunk_id": "chk_1",
        "quote_span": "AI-assisted brainstorming increased average idea quality across submitted ideas",
        "subject": "AI-assisted brainstorming",
        "predicate": "increased",
        "object": "average idea quality",
        "scope": "short-form writing tasks",
        "evidence_type": "empirical",
        "confidence": 0.7,
        "limitations": ["Only tested short-form writing tasks."],
        "domain": domain,
    }


_CHUNK_TEXT = (
    "In a controlled study of short-form writing tasks, we found that "
    "AI-assisted brainstorming increased average idea quality across submitted ideas."
)


def test_creativity_pack_allows_primary_and_overlap_domains() -> None:
    pack = load_domain_pack("creativity")
    allowed = allowed_domains_for_pack(pack)
    assert "creativity" in allowed
    assert "design" in allowed
    assert "art" in allowed

    for overlap in ("creativity", "art", "design", "film", "music", "digital_media"):
        candidate = _valid_candidate(domain=overlap)
        status, _, reason = validate_candidate_claim(
            candidate,
            chunk_text=_CHUNK_TEXT,
            domain_pack="creativity",
        )
        assert status == "accepted"
        assert reason is None


def test_creativity_pack_rejects_out_of_scope_domain_label() -> None:
    candidate = _valid_candidate(domain="meteorology")
    status, _, reason = validate_candidate_claim(
        candidate,
        chunk_text=_CHUNK_TEXT,
        domain_pack="creativity",
    )
    assert status == "rejected"
    assert reason == REJECTION_UNSUPPORTED
    diagnostic = rejection_diagnostic(
        candidate,
        chunk_text=_CHUNK_TEXT,
        rejection_reason=reason,
        domain_pack="creativity",
    )
    assert "domain 'meteorology'" in diagnostic
    assert "domain pack 'creativity'" in diagnostic


def test_temp_pack_primary_domains_change_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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

    def _load_pack(pack_id: str, *, root: Path | None = None):
        if pack_id == "demo":
            return load_domain_pack("demo", root=tmp_path)
        return load_domain_pack(pack_id, root=root)

    monkeypatch.setattr(
        "rge.modules.domain_pack_loader.load_domain_pack",
        _load_pack,
    )

    art_candidate = _valid_candidate(domain="art")
    status, _, reason = validate_candidate_claim(
        art_candidate,
        chunk_text=_CHUNK_TEXT,
        domain_pack="demo",
    )
    assert status == "accepted"
    assert reason is None

    (pack_dir / "domain.yaml").write_text(
        "id: demo\n"
        "name: Demo Pack\n"
        "version: 0.1.0\n"
        "status: active\n"
        "summary: Demo domain pack for unit tests.\n"
        "primary_domains:\n"
        "  - demo\n"
        "overlap_domains:\n"
        "  - music\n"
        "lifecycle_states:\n"
        "  - active\n",
        encoding="utf-8",
    )

    status, _, reason = validate_candidate_claim(
        art_candidate,
        chunk_text=_CHUNK_TEXT,
        domain_pack="demo",
    )
    assert status == "rejected"
    assert reason == REJECTION_UNSUPPORTED
    diagnostic = rejection_diagnostic(
        art_candidate,
        chunk_text=_CHUNK_TEXT,
        rejection_reason=reason,
        domain_pack="demo",
    )
    assert "domain 'art'" in diagnostic
