"""Tiny Atlas connection preview fixture and static route checks."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from rge.modules.atlas_snapshot_builder import assert_no_private_fields

REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = REPO_ROOT / "apps" / "public-site"
DATA_PATH = SITE_DIR / "public" / "data" / "tiny_atlas_connection_preview.json"
ATLAS_PREVIEW_PAGE = SITE_DIR / "app" / "atlas-preview" / "page.tsx"
ATLAS_PREVIEW_LIB = SITE_DIR / "lib" / "atlasPreview.ts"

FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"/(?:home|Users)/\w+"),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"api[_-]?key", re.IGNORECASE),
    re.compile(r"<script", re.IGNORECASE),
    re.compile(r"IGNORE ALL PREVIOUS INSTRUCTIONS", re.IGNORECASE),
    re.compile(r"prompt template", re.IGNORECASE),
    re.compile(r"evaluator notes", re.IGNORECASE),
)


def _load_preview() -> dict[str, Any]:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def test_tiny_atlas_connection_preview_fixture_contains_required_sections() -> None:
    preview = _load_preview()

    assert preview["schema_version"] == "tiny_atlas_connection_preview_v0.1.0"
    assert preview["public_safe"] is True
    assert preview["question"]["primary_question"]
    assert preview["question"]["research_purpose"]
    assert preview["question"]["asset_affordance_tags"]
    assert "PARTIAL" in preview["question"]["readiness_verdict"]
    assert preview["source_health"]["source_counts_by_status"]
    assert preview["source_health"]["blocked_dirty_failed_reasons"]
    assert preview["cluster"]["cluster_name"]
    assert preview["cluster"]["relationship_density"] >= 0.5
    assert preview["cluster"]["source_diversity"] >= 1
    assert preview["evidence_atoms"]
    assert preview["relationships"]
    assert preview["trace_details"]
    assert preview["gaps_next_move"]["next_recommended_packet"]


def test_tiny_atlas_atom_cards_expose_maturity_and_purpose_fields() -> None:
    preview = _load_preview()

    for atom in preview["evidence_atoms"]:
        assert atom["canonical_atom_text"]
        assert atom["maturity"]
        assert atom["purpose_match_status"]
        assert "support_count" in atom
        assert "contradiction_count" in atom
        assert "qualification_count" in atom
        assert "source_count" in atom
        assert atom["asset_tags"]
        assert atom["why_clustered"] or atom["why_weak"]


def test_tiny_atlas_relationship_metrics_and_weak_warnings_appear() -> None:
    preview = _load_preview()
    relationship_types = {item["type"] for item in preview["relationships"]}
    expected_types = {
        "supports",
        "contradicts",
        "qualifies",
        "defines",
        "scope-difference",
    }

    assert expected_types <= relationship_types
    assert preview["cluster"]["relationship_density_threshold"] == 0.5
    assert preview["gaps_next_move"]["graph_health_warnings"]
    assert any(
        readiness["status"] in {"PARTIAL", "NO-GO"}
        for readiness in preview["readiness"].values()
    )


def test_tiny_atlas_trace_preview_excludes_private_fields() -> None:
    preview = _load_preview()
    payload_text = DATA_PATH.read_text(encoding="utf-8")

    assert assert_no_private_fields({"tiny_atlas_connection_preview": preview}) == []
    forbidden_keys = (
        "claim_id",
        "source_id",
        "quote_id",
        "chunk_id",
        "local_path",
        "raw_quote",
        "quote_text",
        '"prompt"',
        "raw_prompt",
        "prompt_template",
        "private_note",
        "hidden_evaluator_notes",
    )
    for key in forbidden_keys:
        assert key not in payload_text
    for pattern in FORBIDDEN_VALUE_PATTERNS:
        assert not pattern.search(payload_text), (
            f"preview leaked forbidden content matching {pattern.pattern!r}"
        )


def test_atlas_preview_route_renders_tiny_connection_sections_from_static_fixture() -> None:
    page = ATLAS_PREVIEW_PAGE.read_text(encoding="utf-8")
    lib = ATLAS_PREVIEW_LIB.read_text(encoding="utf-8")

    assert "tinyAtlasConnectionPreview" in page
    assert "Tiny Atlas connection preview" in page
    assert "Source health panel" in page
    assert "Evidence cluster panel" in page
    assert "Evidence atom cards" in page
    assert "Relationship view" in page
    assert "Evidence trace detail panel" in page
    assert "Gaps / next move panel" in page
    assert "Relationship-density warning" in page
    assert "Next recommended packet" in page
    assert "tiny_atlas_connection_preview.json" in lib
    assert "fetch(" not in page
    assert "dangerouslySetInnerHTML" not in page
