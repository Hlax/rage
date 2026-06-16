"""Research Atlas snapshot contract and export inventory (ticket-278)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.contracts.atlas_snapshot_v0 import (
    ATLAS_SNAPSHOT_SCHEMA_VERSION,
    AtlasSnapshotValidationError,
    load_atlas_snapshot_fixture,
    validate_atlas_snapshot,
)
from rge.modules.atlas_contract_inventory import (
    INVENTORY_SCHEMA_VERSION,
    build_contract_inventory,
    collect_research_atlas_gaps,
    render_inventory_markdown,
    write_inventory_report,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = REPO_ROOT / "fixtures" / "atlas" / "atlas_snapshot_v0_minimal.json"


def test_minimal_atlas_snapshot_fixture_validates() -> None:
    snapshot = load_atlas_snapshot_fixture(REPO_ROOT)
    assert snapshot.schema_version == ATLAS_SNAPSHOT_SCHEMA_VERSION
    assert snapshot.snapshot_id == "snap_fixture_minimal_001"
    assert snapshot.root.domain_pack == "creativity"
    assert snapshot.safety.public_safe is True
    assert snapshot.nodes == []
    assert snapshot.cards == []


def test_atlas_snapshot_rejects_wrong_schema_version() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["schema_version"] = "atlas_snapshot_v0.0.0"
    with pytest.raises(AtlasSnapshotValidationError, match="schema_version"):
        validate_atlas_snapshot(payload)


def test_atlas_snapshot_requires_root_fields() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    del payload["root"]["domain_pack"]
    with pytest.raises(AtlasSnapshotValidationError):
        validate_atlas_snapshot(payload)


def test_contract_inventory_lists_db_tables() -> None:
    inventory = build_contract_inventory(REPO_ROOT)
    assert "claims" in inventory["db_tables"]
    assert "public_cards" in inventory["db_tables"]
    assert "improvement_tickets" in inventory["db_tables"]
    assert inventory["inventory_schema_version"] == INVENTORY_SCHEMA_VERSION


def test_contract_inventory_lists_golden_tests() -> None:
    inventory = build_contract_inventory(REPO_ROOT)
    paths = {entry["path"] for entry in inventory["golden_test_coverage"]}
    assert "tests/golden/test_11_public_card_export.py" in paths
    assert "tests/golden/test_22_builder_golden_gate.py" in paths
    assert len(inventory["golden_test_coverage"]) >= 20


def test_contract_inventory_documents_atlas_gaps() -> None:
    gaps = {entry["gap"] for entry in collect_research_atlas_gaps()}
    assert "no_explicit_public_atlas_snapshot_export" in gaps
    assert "no_review_batch_or_synthesis_batch_object" in gaps
    assert "agent_lab_not_separated_from_research_graph" in gaps


def test_contract_inventory_markdown_has_required_sections() -> None:
    inventory = build_contract_inventory(REPO_ROOT)
    markdown = render_inventory_markdown(inventory)
    for heading in (
        "## Current DB tables",
        "## Report JSON shapes",
        "## Export JSON shapes",
        "## Public-site data readers",
        "## Golden test coverage",
        "## Private / public safety classification",
        "## Gaps vs Research Atlas + Agent Lab needs",
    ):
        assert heading in markdown


def test_write_inventory_report_writes_markdown_and_json(tmp_path: Path) -> None:
    output = tmp_path / "inventory.md"
    inventory = write_inventory_report(output, repo_root=REPO_ROOT)
    assert output.is_file()
    assert output.with_suffix(".json").is_file()
    assert inventory["atlas_snapshot_contract_version"] == ATLAS_SNAPSHOT_SCHEMA_VERSION
    assert "claims" in output.read_text(encoding="utf-8")
