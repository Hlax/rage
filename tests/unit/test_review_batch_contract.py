"""Agent Lab review_batch contract (ticket-280)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.contracts.review_batch_v0 import (
    AGENT_LAB_CLASSIFICATION,
    REVIEW_BATCH_SCHEMA_VERSION,
    ReviewBatchValidationError,
    load_review_batch_fixture,
    validate_review_batch,
)
from rge.modules.atlas_contract_inventory import (
    build_contract_inventory,
    collect_research_atlas_gaps,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = REPO_ROOT / "fixtures" / "agent_lab" / "review_batch_v0_minimal.json"


def test_minimal_review_batch_fixture_validates() -> None:
    batch = load_review_batch_fixture(REPO_ROOT)
    assert batch.schema_version == REVIEW_BATCH_SCHEMA_VERSION
    assert batch.classification == AGENT_LAB_CLASSIFICATION
    assert batch.safety.public_safe is False
    assert batch.safety.operator_only is True
    assert batch.model_runtime.llm_mode == "mock"
    assert batch.outputs.review_status == "completed"
    assert batch.outputs.candidate_findings


def test_review_batch_rejects_wrong_schema_version() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["schema_version"] = "review_batch_v0.0.0"
    with pytest.raises(ReviewBatchValidationError, match="schema_version"):
        validate_review_batch(payload)


def test_review_batch_rejects_public_safe_true() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["safety"]["public_safe"] = True
    with pytest.raises(ReviewBatchValidationError, match="non-public"):
        validate_review_batch(payload)


def test_review_batch_requires_model_runtime_fields() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    del payload["model_runtime"]["task_name"]
    with pytest.raises(ReviewBatchValidationError):
        validate_review_batch(payload)


def test_contract_inventory_notes_review_batch_agent_lab_private() -> None:
    inventory = build_contract_inventory(REPO_ROOT)
    shapes = inventory["export_json_shapes"]
    review_batch_shapes = [
        entry for entry in shapes if entry["artifact"] == "review_batch.json"
    ]
    assert review_batch_shapes
    assert review_batch_shapes[0]["safety_class"] == AGENT_LAB_CLASSIFICATION

    gaps = {entry["gap"]: entry for entry in collect_research_atlas_gaps()}
    assert "no_review_batch_or_synthesis_batch_object" in gaps
    assert "review_batch_v0.1.0" in gaps["no_review_batch_or_synthesis_batch_object"]["notes"]
