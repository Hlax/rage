"""Agent Lab review_batch contract v0.1.0 (ticket-280).

Durable private envelope for principal larger-model review passes (Qwen local →
stronger model → improvement loop). Shape-only in v0; persistence wiring deferred.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

REVIEW_BATCH_SCHEMA_VERSION = "review_batch_v0.1.0"
AGENT_LAB_CLASSIFICATION = "agent_lab_private"
FIXTURE_RELATIVE_PATH = Path("fixtures/agent_lab/review_batch_v0_minimal.json")


class ReviewBatchValidationError(ValueError):
    """Raised when a review batch payload fails contract validation."""


class ReviewBatchModelRuntime_v0_1(BaseModel):
    llm_mode: Literal["mock", "ollama"]
    model_provider: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    task_name: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    prompt_template_version: str = Field(min_length=1)
    raw_response_stored: bool = False


class ReviewBatchScope_v0_1(BaseModel):
    run_id: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    domain_pack: str = Field(min_length=1)
    review_kind: str = Field(min_length=1)


class ReviewBatchInputs_v0_1(BaseModel):
    artifact_refs: list[str] = Field(default_factory=list)
    improvement_ticket_ids: list[str] = Field(default_factory=list)
    atlas_snapshot_id: str | None = None


class ReviewBatchOutputs_v0_1(BaseModel):
    review_status: Literal["completed", "failed", "pending"] = "pending"
    candidate_findings: list[dict[str, Any]] = Field(default_factory=list)
    recommended_tickets: list[dict[str, Any]] = Field(default_factory=list)


class ReviewBatchSafety_v0_1(BaseModel):
    public_safe: bool = False
    operator_only: bool = True


class ReviewBatch_v0_1(BaseModel):
    schema_version: Literal["review_batch_v0.1.0"] = REVIEW_BATCH_SCHEMA_VERSION
    batch_id: str = Field(min_length=1)
    generated_at: str = Field(min_length=1)
    classification: Literal["agent_lab_private"] = AGENT_LAB_CLASSIFICATION
    review_scope: ReviewBatchScope_v0_1
    model_runtime: ReviewBatchModelRuntime_v0_1
    inputs: ReviewBatchInputs_v0_1 = Field(default_factory=ReviewBatchInputs_v0_1)
    outputs: ReviewBatchOutputs_v0_1 = Field(default_factory=ReviewBatchOutputs_v0_1)
    safety: ReviewBatchSafety_v0_1 = Field(default_factory=ReviewBatchSafety_v0_1)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def validate_review_batch(payload: dict[str, Any]) -> ReviewBatch_v0_1:
    """Validate a candidate review batch dict. Fail closed on schema mismatch."""
    declared = payload.get("schema_version")
    if declared != REVIEW_BATCH_SCHEMA_VERSION:
        raise ReviewBatchValidationError(
            f"schema_version must be {REVIEW_BATCH_SCHEMA_VERSION!r}, got {declared!r}"
        )
    if payload.get("classification") != AGENT_LAB_CLASSIFICATION:
        raise ReviewBatchValidationError(
            f"classification must be {AGENT_LAB_CLASSIFICATION!r}"
        )
    if payload.get("safety", {}).get("public_safe") is True:
        raise ReviewBatchValidationError("review_batch must remain non-public (public_safe=false)")
    try:
        return ReviewBatch_v0_1.model_validate(payload)
    except ValidationError as exc:
        raise ReviewBatchValidationError(str(exc)) from exc


def load_review_batch_fixture(
    repo_root: Path | None = None,
    *,
    relative_path: Path = FIXTURE_RELATIVE_PATH,
) -> ReviewBatch_v0_1:
    """Load and validate the committed minimal review batch fixture."""
    root = repo_root or _repo_root()
    path = root / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    return validate_review_batch(payload)


def review_batch_to_dict(batch: ReviewBatch_v0_1) -> dict[str, Any]:
    return batch.model_dump(mode="json")
