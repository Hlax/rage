"""Fixture-mode export + atlas coherence CLI pipeline e2e (ticket-292).

Network-free default pytest: builds fixture-mode MVP DB, chains
``export-atlas-snapshot`` CLI → ``atlas-coherence-report`` CLI, and asserts
coherence verdict + population thresholds on written report artifacts.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.cli import FIXTURE_RUN_ID, GOLDEN_MVP_TOPIC, execute_fixture_mode_run, main
from rge.contracts.atlas_snapshot_v0 import (
    ATLAS_SNAPSHOT_SCHEMA_VERSION,
    validate_atlas_snapshot,
)
from rge.modules.atlas_snapshot_builder import assert_no_private_fields

REPO_ROOT = Path(__file__).resolve().parents[2]
CREATIVITY_FIXTURE = REPO_ROOT / "fixtures" / "atlas" / "atlas_snapshot_v0_creativity_fixture.json"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "atlas_coherence_pipeline.sqlite"


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


def test_fixture_mode_export_and_coherence_cli_pipeline(
    temp_db: Path,
    artifact_dirs: dict[str, Path],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Fixture-mode MVP DB → export-atlas-snapshot CLI → atlas-coherence-report CLI."""
    _build_fixture_mvp_db(temp_db, artifact_dirs)
    capsys.readouterr()

    atlas_path = tmp_path / "atlas_snapshot.json"
    export_exit = main(
        [
            "export-atlas-snapshot",
            "--db",
            str(temp_db),
            "--out",
            str(atlas_path),
            "--fixture-mode",
        ]
    )
    assert export_exit == 0
    export_payload = json.loads(capsys.readouterr().out)
    assert export_payload["status"] == "completed"
    assert export_payload["command"] == "export-atlas-snapshot"
    assert export_payload["schema_version"] == ATLAS_SNAPSHOT_SCHEMA_VERSION
    assert export_payload["output_path"] == str(atlas_path)
    assert atlas_path.is_file()

    snapshot = json.loads(atlas_path.read_text(encoding="utf-8"))
    validate_atlas_snapshot(snapshot)
    assert assert_no_private_fields(snapshot) == []
    assert atlas_path.read_bytes() == CREATIVITY_FIXTURE.read_bytes()
    capsys.readouterr()

    coherence_json = tmp_path / "atlas_coherence_report.json"
    coherence_md = tmp_path / "atlas_coherence_report.md"
    coherence_exit = main(
        [
            "atlas-coherence-report",
            "--snapshot",
            str(atlas_path),
            "--out-json",
            str(coherence_json),
            "--out-md",
            str(coherence_md),
        ]
    )
    assert coherence_exit == 0
    coherence_payload = json.loads(capsys.readouterr().out)
    assert coherence_payload["status"] == "completed"
    assert coherence_payload["command"] == "atlas-coherence-report"
    assert coherence_payload["json_path"] == str(coherence_json)
    assert coherence_payload["markdown_path"] == str(coherence_md)
    assert coherence_payload["overall_coherence_verdict"] in {"pass", "partial"}
    assert coherence_json.is_file()
    assert coherence_md.is_file()

    report = json.loads(coherence_json.read_text(encoding="utf-8"))
    assert report["population"]["cards"] >= 2
    assert report["population"]["nodes"] >= 1
    assert report["population"]["runs"] >= 1
    assert report["population"]["reports"] >= 1
    assert report["safety"]["contract_valid"] is True
    assert report["safety"]["private_field_violations"] == []
    assert report["overall_coherence_verdict"] in {"pass", "partial"}
    assert coherence_md.read_text(encoding="utf-8").startswith("# Research Atlas")
