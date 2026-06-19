"""Conservative derived asset export candidates from evidence atoms.

Transforms quote-backed atoms into eval/style/reasoning candidate records
without exporting long raw quotes or marking training_ready by default.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Literal

from rge.modules.evidence_atoms import list_top_evidence_atoms

ExportCategory = Literal[
    "reasoning_eval_candidate",
    "qa_eval_candidate",
    "rubric_candidate",
    "style_descriptor_candidate",
    "visual_taxonomy_candidate",
    "prompt_pattern_candidate",
    "concept_ontology_candidate",
    "do_not_export",
]

EXPORT_SCHEMA_VERSION = "asset_export_candidates_v0.1.0"
MAX_DERIVED_SUMMARY_CHARS = 200
QA_EVAL_MATURITY = "clustered"
REVIEW_STATUS_PENDING = "pending"
REVIEW_STATUS_NOT_APPLICABLE = "not_applicable"


def _category_for_atom(atom: dict[str, Any]) -> ExportCategory:
    tags = {str(tag) for tag in (atom.get("asset_tags") or [])}
    maturity = str(atom.get("evidence_maturity") or "seed")
    training = str(atom.get("training_suitability") or "not_ready")
    if training == "do_not_train":
        return "do_not_export"
    if "visual_descriptor_candidate" in tags:
        return "visual_taxonomy_candidate"
    if "style_vocabulary_candidate" in tags:
        return "style_descriptor_candidate"
    if "prompt_pattern_candidate" in tags:
        return "prompt_pattern_candidate"
    if "concept_ontology_candidate" in tags:
        return "concept_ontology_candidate"
    if "rubric_candidate" in tags and maturity == QA_EVAL_MATURITY:
        return "rubric_candidate"
    if maturity in ("eval_ready", "synthesis_ready"):
        return "reasoning_eval_candidate"
    if maturity == QA_EVAL_MATURITY:
        return "qa_eval_candidate"
    return "do_not_export"


def _human_review_required(category: ExportCategory, atom: dict[str, Any]) -> bool:
    if category == "do_not_export":
        return False
    if category == "qa_eval_candidate":
        return str(atom.get("evidence_maturity") or "") == QA_EVAL_MATURITY
    return True


def _review_status(category: ExportCategory, atom: dict[str, Any]) -> str:
    if _human_review_required(category, atom):
        return REVIEW_STATUS_PENDING
    return REVIEW_STATUS_NOT_APPLICABLE


def derive_asset_candidate(atom: dict[str, Any]) -> dict[str, Any]:
    """Derive a conservative export candidate from one evidence atom summary."""
    canonical = str(atom.get("canonical_text") or "")
    if len(canonical) > MAX_DERIVED_SUMMARY_CHARS:
        summary = canonical[: MAX_DERIVED_SUMMARY_CHARS - 3].rstrip() + "..."
    else:
        summary = canonical
    category = _category_for_atom(atom)
    human_review_required = _human_review_required(category, atom)
    return {
        "atom_id": atom["atom_id"],
        "export_category": category,
        "summary": summary,
        "scope": atom.get("scope"),
        "evidence_type": atom.get("evidence_type"),
        "evidence_maturity": atom.get("evidence_maturity"),
        "training_suitability": atom.get("training_suitability"),
        "concepts": list(atom.get("concepts") or [])[:8],
        "human_review_required": human_review_required,
        "review_status": _review_status(category, atom),
    }


def _group_candidates_by_category(
    candidates: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        category = str(candidate["export_category"])
        grouped.setdefault(category, []).append(candidate)
    return grouped


def export_asset_candidates(
    conn: sqlite3.Connection,
    *,
    domain: str,
    limit: int = 50,
) -> dict[str, Any]:
    """Build a conservative asset-export candidate bundle from persisted atoms."""
    atoms = list_top_evidence_atoms(conn, limit=limit)
    candidates = [derive_asset_candidate(atom) for atom in atoms]
    exportable = [c for c in candidates if c["export_category"] != "do_not_export"]
    qa_eval_candidates = [
        c
        for c in exportable
        if c["export_category"] == "qa_eval_candidate" and c["human_review_required"]
    ]
    by_category = _group_candidates_by_category(exportable)
    return {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "command": "export-asset-candidates",
        "domain": domain,
        "atom_count": len(atoms),
        "candidate_count": len(exportable),
        "human_review_required_count": sum(
            1 for candidate in exportable if candidate["human_review_required"]
        ),
        "qa_eval_candidate_count": len(qa_eval_candidates),
        "candidates": candidates,
        "exportable_candidates": exportable,
        "qa_eval_candidates": qa_eval_candidates,
        "candidates_by_category": by_category,
    }


def write_asset_candidates_bundle(
    conn: sqlite3.Connection,
    *,
    domain: str,
    output_path: str | Any,
    limit: int = 50,
) -> dict[str, Any]:
    """Write asset candidate JSON to an operator-private path."""
    from pathlib import Path

    bundle = export_asset_candidates(conn, domain=domain, limit=limit)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    return {
        "status": "success",
        "command": "export-asset-candidates",
        "domain": domain,
        "candidate_count": bundle["candidate_count"],
        "written_file": str(path),
    }
