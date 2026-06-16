"""Research Atlas public snapshot contract v0.1.0 (ticket-278).

Stable frontend-facing envelope for graph/atlas UI without coupling to raw DB
rows or operator-private artifacts. Population/export wiring is deferred; this
module defines and validates the contract shape only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

ATLAS_SNAPSHOT_SCHEMA_VERSION = "atlas_snapshot_v0.1.0"
FIXTURE_RELATIVE_PATH = Path("fixtures/atlas/atlas_snapshot_v0_minimal.json")
ATLAS_RUN_LINEAGE_OPTIONAL_FIELDS = (
    "research_question_id",
    "parent_question_id",
    "spawned_from_claim_ids",
    "spawned_from_report_id",
    "spawn_reason",
)


class AtlasSnapshotValidationError(ValueError):
    """Raised when an atlas snapshot payload fails contract validation."""


class AtlasSnapshotRoot_v0_1(BaseModel):
    topic: str = Field(min_length=1)
    primary_question: str = Field(min_length=1)
    domain_pack: str = Field(min_length=1)


class AtlasSnapshotSafety_v0_1(BaseModel):
    public_safe: bool
    safety_audit_id: str = Field(min_length=1)


class AtlasSnapshot_v0_1(BaseModel):
    schema_version: Literal["atlas_snapshot_v0.1.0"] = ATLAS_SNAPSHOT_SCHEMA_VERSION
    generated_at: str = Field(min_length=1)
    snapshot_id: str = Field(min_length=1)
    root: AtlasSnapshotRoot_v0_1
    domains: list[dict[str, Any]] = Field(default_factory=list)
    runs: list[dict[str, Any]] = Field(default_factory=list)
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    clusters: list[dict[str, Any]] = Field(default_factory=list)
    reports: list[dict[str, Any]] = Field(default_factory=list)
    cards: list[dict[str, Any]] = Field(default_factory=list)
    safety: AtlasSnapshotSafety_v0_1


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def validate_atlas_snapshot(payload: dict[str, Any]) -> AtlasSnapshot_v0_1:
    """Validate a candidate atlas snapshot dict. Fail closed on schema mismatch."""
    declared = payload.get("schema_version")
    if declared != ATLAS_SNAPSHOT_SCHEMA_VERSION:
        raise AtlasSnapshotValidationError(
            f"schema_version must be {ATLAS_SNAPSHOT_SCHEMA_VERSION!r}, got {declared!r}"
        )
    try:
        return AtlasSnapshot_v0_1.model_validate(payload)
    except ValidationError as exc:
        raise AtlasSnapshotValidationError(str(exc)) from exc


def load_atlas_snapshot_fixture(
    repo_root: Path | None = None,
    *,
    relative_path: Path = FIXTURE_RELATIVE_PATH,
) -> AtlasSnapshot_v0_1:
    """Load and validate the committed minimal atlas snapshot fixture."""
    root = repo_root or _repo_root()
    path = root / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    return validate_atlas_snapshot(payload)


def atlas_snapshot_to_dict(snapshot: AtlasSnapshot_v0_1) -> dict[str, Any]:
    return snapshot.model_dump(mode="json")
