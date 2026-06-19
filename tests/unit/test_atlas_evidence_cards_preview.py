"""Atlas evidence card preview projection tests (Packet 5 follow-on)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.cli import FIXTURE_RUN_ID, GOLDEN_MVP_TOPIC, execute_fixture_mode_run
from rge.contracts.atlas_snapshot_v0 import validate_atlas_snapshot
from rge.db.connection import connect
from rge.modules.atlas_snapshot_builder import (
    assert_no_private_fields,
    build_atlas_snapshot_from_db,
)
from rge.modules.evidence_card_exporter import (
    audit_atlas_evidence_cards_preview,
    audit_snapshot_evidence_cards_preview,
    build_atlas_evidence_cards_preview,
    derive_atlas_safe_evidence_preview,
)
from rge.modules.safety_auditor import run_safety_audit

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "atlas_evidence_cards.sqlite"


@pytest.fixture()
def artifact_dirs(tmp_path: Path) -> dict[str, Path]:
    export_dir = tmp_path / "export"
    report_dir = tmp_path / "reports"
    ticket_dir = tmp_path / "tickets"
    for directory in (export_dir, report_dir, ticket_dir):
        directory.mkdir(parents=True, exist_ok=True)
    return {
        "export": export_dir,
        "reports": report_dir,
        "tickets": ticket_dir,
    }


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def _build_fixture_mvp_db(temp_db: Path, artifact_dirs: dict[str, Path]) -> None:
    result = execute_fixture_mode_run(
        topic=GOLDEN_MVP_TOPIC,
        domain="creativity",
        db_path=temp_db,
        run_id=FIXTURE_RUN_ID,
        report_dir=artifact_dirs["reports"],
        ticket_dir=artifact_dirs["tickets"],
        export_dirs=[artifact_dirs["export"]],
    )
    assert result["status"] == "completed"


def test_build_atlas_evidence_cards_preview_omits_quote_and_private_keys(
    temp_db: Path,
    artifact_dirs: dict[str, Path],
) -> None:
    _build_fixture_mvp_db(temp_db, artifact_dirs)
    conn = connect(temp_db)
    try:
        previews = build_atlas_evidence_cards_preview(
            conn,
            domain_pack="creativity",
            limit=5,
        )
        assert previews
        assert audit_atlas_evidence_cards_preview(previews) == []
        for preview in previews:
            assert "quote" not in preview
            assert preview["summary"]
            assert preview["evidence_maturity"]
    finally:
        conn.close()


def test_atlas_snapshot_includes_evidence_cards_preview(
    temp_db: Path,
    artifact_dirs: dict[str, Path],
) -> None:
    _build_fixture_mvp_db(temp_db, artifact_dirs)
    conn = connect(temp_db)
    try:
        snapshot = build_atlas_snapshot_from_db(
            conn,
            topic=GOLDEN_MVP_TOPIC,
            domain_pack="creativity",
            fixture_mode=True,
            repo_root=REPO_ROOT,
        )
        validate_atlas_snapshot(snapshot)
        assert isinstance(snapshot["evidence_cards_preview"], list)
        assert len(snapshot["evidence_cards_preview"]) >= 1
        assert audit_snapshot_evidence_cards_preview(snapshot) == []
        assert assert_no_private_fields(snapshot) == []
    finally:
        conn.close()


def test_audit_atlas_evidence_cards_preview_rejects_quote_leakage() -> None:
    preview = derive_atlas_safe_evidence_preview(
        {
            "card_type": "evidence_claim",
            "claim": "Scoped claim text.",
            "quote": "literal quote leak",
            "source": {"title": "Fixture", "source_type": "paper"},
            "stance": "supports",
            "evidence_type": "empirical",
            "scope": "short-form writing tasks",
            "concepts": [],
            "confidence": "medium",
            "limitations": [],
            "asset_tags": [],
            "evidence_maturity": "seed",
        }
    )
    preview["quote"] = "leaked quote"
    violations = audit_atlas_evidence_cards_preview([preview])
    assert any("quote" in item for item in violations)


def test_safety_audit_passes_with_valid_atlas_snapshot_preview() -> None:
    report = run_safety_audit("secrets", root=REPO_ROOT)
    assert report["status"] == "pass", report.get("blocked_reasons")
