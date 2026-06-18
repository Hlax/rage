"""Curate operator atlas exports for public-site preview fixtures (ticket-320).

Transforms private export-atlas-snapshot output into committed mock-safe preview JSON.
Does not call export-public or widen public export policy.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from rge.contracts.atlas_snapshot_v0 import validate_atlas_snapshot
from rge.modules.atlas_snapshot_builder import (
    ATLAS_COHERENCE_PREVIEW_SCHEMA_VERSION,
    assert_no_private_fields,
    build_atlas_coherence_preview,
    export_atlas_snapshot_to_path,
)

STAGED_PREVIEW_SNAPSHOT_ID = "snap_staged_fixture_preview_v0_001"
STAGED_PREVIEW_GENERATED_AT = "2026-06-18T00:00:00Z"
STAGED_PREVIEW_SAFETY_AUDIT_ID = "audit_atlas_staged_preview_v0_001"
STAGED_PREVIEW_LABEL = "Mock staged-spine atlas preview (fixture-safe)"
STAGED_PREVIEW_TOPIC = (
    "Does staged fixture-mode discovery improve atlas preview coherence?"
)

FIXTURES_ATLAS_STAGED_SPINE_PREVIEW = (
    "fixtures/atlas/atlas_snapshot_staged_spine_preview.json"
)


def curate_snapshot_for_public_preview(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Apply public-preview curation on a validated atlas snapshot dict."""
    curated = copy.deepcopy(snapshot)
    followups: list[dict[str, Any]] = []
    for item in curated.get("follow_up_questions") or []:
        row = dict(item)
        if str(row.get("status", "")).strip().casefold() == "active":
            row["status"] = "queued"
        followups.append(row)
    curated["follow_up_questions"] = followups

    verdict = str(
        (curated.get("coherence_summary") or {}).get("overall_coherence_verdict")
        or "partial"
    )
    curated["coherence_summary"] = {
        "overall_coherence_verdict": verdict,
        "preview_label": STAGED_PREVIEW_LABEL,
    }
    curated["snapshot_id"] = STAGED_PREVIEW_SNAPSHOT_ID
    curated["generated_at"] = STAGED_PREVIEW_GENERATED_AT
    safety = dict(curated.get("safety") or {})
    safety["public_safe"] = True
    safety["safety_audit_id"] = STAGED_PREVIEW_SAFETY_AUDIT_ID
    curated["safety"] = safety
    return curated


def validate_public_preview_snapshot(snapshot: dict[str, Any]) -> None:
    """Fail closed when preview snapshot violates contract or private-field policy."""
    validate_atlas_snapshot(snapshot)
    violations = assert_no_private_fields(snapshot)
    if violations:
        raise ValueError(
            "Public atlas preview snapshot blocked: " + "; ".join(violations[:5])
        )


def write_public_preview_fixtures(
    snapshot: dict[str, Any],
    *,
    snapshot_path: Path,
    coherence_path: Path,
    fixtures_reference_path: Path | None = None,
) -> dict[str, Any]:
    """Validate, curate, and write public-site atlas preview JSON files."""
    curated = curate_snapshot_for_public_preview(snapshot)
    validate_public_preview_snapshot(curated)
    coherence = build_atlas_coherence_preview(curated)
    coherence["schema_version"] = ATLAS_COHERENCE_PREVIEW_SCHEMA_VERSION

    snapshot_payload = json.dumps(curated, indent=2, ensure_ascii=False) + "\n"
    coherence_payload = json.dumps(coherence, indent=2, ensure_ascii=False) + "\n"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    coherence_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(snapshot_payload, encoding="utf-8")
    coherence_path.write_text(coherence_payload, encoding="utf-8")
    if fixtures_reference_path is not None:
        fixtures_reference_path.parent.mkdir(parents=True, exist_ok=True)
        fixtures_reference_path.write_text(snapshot_payload, encoding="utf-8")
    result = {
        "status": "completed",
        "snapshot_path": str(snapshot_path),
        "coherence_path": str(coherence_path),
        "snapshot_id": curated["snapshot_id"],
        "overall_coherence_verdict": coherence["overall_coherence_verdict"],
        "population": coherence["population"],
    }
    if fixtures_reference_path is not None:
        result["fixtures_reference_path"] = str(fixtures_reference_path)
    return result


def export_staged_spine_preview_from_db(
    conn: Any,
    *,
    topic: str = STAGED_PREVIEW_TOPIC,
    domain_pack: str = "creativity",
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build curated staged-spine preview dict from an existing research DB connection."""
    from rge.modules.atlas_snapshot_builder import build_atlas_snapshot_from_db

    snapshot = build_atlas_snapshot_from_db(
        conn,
        topic=topic,
        primary_question=topic,
        domain_pack=domain_pack,
        snapshot_id=STAGED_PREVIEW_SNAPSHOT_ID,
        generated_at=STAGED_PREVIEW_GENERATED_AT,
        safety_audit_id=STAGED_PREVIEW_SAFETY_AUDIT_ID,
        fixture_mode=False,
        repo_root=repo_root,
    )
    return curate_snapshot_for_public_preview(snapshot)


def export_staged_spine_preview_to_paths(
    conn: Any,
    *,
    snapshot_path: Path,
    coherence_path: Path,
    topic: str = STAGED_PREVIEW_TOPIC,
    domain_pack: str = "creativity",
    repo_root: Path | None = None,
    fixtures_reference_path: Path | None = None,
) -> dict[str, Any]:
    """Export staged-spine atlas from DB, curate, and write public preview fixture paths."""
    scratch = snapshot_path.parent / "_scratch_atlas_snapshot.json"
    export_atlas_snapshot_to_path(
        conn,
        scratch,
        topic=topic,
        primary_question=topic,
        domain_pack=domain_pack,
        snapshot_id=STAGED_PREVIEW_SNAPSHOT_ID,
        generated_at=STAGED_PREVIEW_GENERATED_AT,
        safety_audit_id=STAGED_PREVIEW_SAFETY_AUDIT_ID,
        fixture_mode=False,
        repo_root=repo_root,
    )
    snapshot = json.loads(scratch.read_text(encoding="utf-8"))
    if scratch.exists():
        scratch.unlink()
    return write_public_preview_fixtures(
        snapshot,
        snapshot_path=snapshot_path,
        coherence_path=coherence_path,
        fixtures_reference_path=fixtures_reference_path,
    )
