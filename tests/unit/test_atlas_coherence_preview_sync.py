"""Atlas coherence preview JSON sync from snapshot export (ticket-307)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.cli import FIXTURE_RUN_ID, GOLDEN_MVP_TOPIC, execute_fixture_mode_run, main
from rge.modules.atlas_snapshot_builder import (
    ATLAS_COHERENCE_PREVIEW_SCHEMA_VERSION,
    build_atlas_coherence_preview,
    build_atlas_snapshot_from_db,
    export_atlas_coherence_preview_to_path,
    export_atlas_snapshot_to_path,
)

from tests.unit.test_evidence_db_atlas_projection import REPO_ROOT

CREATIVITY_FIXTURE = REPO_ROOT / "fixtures" / "atlas" / "atlas_snapshot_v0_creativity_fixture.json"
COMMITTED_COHERENCE_PREVIEW = (
    REPO_ROOT / "apps" / "public-site" / "public" / "data" / "atlas_coherence_preview.json"
)
EXPECTED_PREVIEW_LABEL = "Fixture-mode creativity atlas (mock-safe)"


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


def test_build_atlas_coherence_preview_whitelists_public_fields() -> None:
    snapshot = json.loads(CREATIVITY_FIXTURE.read_text(encoding="utf-8"))
    preview = build_atlas_coherence_preview(snapshot)
    assert set(preview.keys()) == {
        "overall_coherence_verdict",
        "population",
        "preview_label",
        "schema_version",
    }
    assert preview["schema_version"] == ATLAS_COHERENCE_PREVIEW_SCHEMA_VERSION
    assert preview["overall_coherence_verdict"] == "pass"
    assert preview["preview_label"] == EXPECTED_PREVIEW_LABEL
    assert preview["population"]["runs"] == 1
    assert preview["population"]["nodes"] == 24


def test_committed_coherence_preview_matches_fixture_export() -> None:
    snapshot = json.loads(CREATIVITY_FIXTURE.read_text(encoding="utf-8"))
    expected = build_atlas_coherence_preview(snapshot)
    committed = json.loads(COMMITTED_COHERENCE_PREVIEW.read_text(encoding="utf-8"))
    assert committed == expected


def test_fixture_mode_export_writes_matching_coherence_preview(
    tmp_path: Path,
    artifact_dirs: dict[str, Path],
) -> None:
    temp_db = tmp_path / "atlas_coherence_preview.sqlite"
    execute_fixture_mode_run(
        topic=GOLDEN_MVP_TOPIC,
        domain="creativity",
        db_path=temp_db,
        run_id=FIXTURE_RUN_ID,
        report_dir=artifact_dirs["reports"],
        ticket_dir=artifact_dirs["tickets"],
        export_dirs=[artifact_dirs["export"]],
    )
    snapshot_path = tmp_path / "atlas_snapshot.json"
    coherence_path = tmp_path / "atlas_coherence_preview.json"
    conn = __import__("rge.db.connection", fromlist=["connect"]).connect(temp_db)
    try:
        export_atlas_snapshot_to_path(
            conn,
            snapshot_path,
            topic=GOLDEN_MVP_TOPIC,
            domain_pack="creativity",
            fixture_mode=True,
            repo_root=REPO_ROOT,
            coherence_preview_path=coherence_path,
        )
    finally:
        conn.close()
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    preview = json.loads(coherence_path.read_text(encoding="utf-8"))
    assert preview == build_atlas_coherence_preview(snapshot)
    assert preview == json.loads(COMMITTED_COHERENCE_PREVIEW.read_text(encoding="utf-8"))


def test_export_coherence_preview_bytes_stable(
    tmp_path: Path,
) -> None:
    snapshot = json.loads(CREATIVITY_FIXTURE.read_text(encoding="utf-8"))
    out_path = tmp_path / "atlas_coherence_preview.json"
    export_atlas_coherence_preview_to_path(snapshot, out_path)
    assert out_path.read_bytes() == COMMITTED_COHERENCE_PREVIEW.read_bytes()


def test_build_atlas_coherence_preview_requires_inline_summary() -> None:
    snapshot = json.loads(CREATIVITY_FIXTURE.read_text(encoding="utf-8"))
    snapshot.pop("coherence_summary")
    with pytest.raises(ValueError, match="coherence_summary"):
        build_atlas_coherence_preview(snapshot)


def test_fixture_mode_snapshot_export_population_matches_preview(
    tmp_path: Path,
    artifact_dirs: dict[str, Path],
) -> None:
    temp_db = tmp_path / "atlas_population.sqlite"
    execute_fixture_mode_run(
        topic=GOLDEN_MVP_TOPIC,
        domain="creativity",
        db_path=temp_db,
        run_id=FIXTURE_RUN_ID,
        report_dir=artifact_dirs["reports"],
        ticket_dir=artifact_dirs["tickets"],
        export_dirs=[artifact_dirs["export"]],
    )
    conn = __import__("rge.db.connection", fromlist=["connect"]).connect(temp_db)
    try:
        snapshot = build_atlas_snapshot_from_db(
            conn,
            topic=GOLDEN_MVP_TOPIC,
            domain_pack="creativity",
            fixture_mode=True,
            repo_root=REPO_ROOT,
        )
    finally:
        conn.close()
    preview = build_atlas_coherence_preview(snapshot)
    assert preview["population"]["cards"] == len(snapshot["cards"])
    assert preview["population"]["clusters"] == len(snapshot["clusters"])


def test_export_atlas_snapshot_cli_writes_coherence_preview_sidecar(
    tmp_path: Path,
    artifact_dirs: dict[str, Path],
) -> None:
    temp_db = tmp_path / "atlas_cli_coherence.sqlite"
    execute_fixture_mode_run(
        topic=GOLDEN_MVP_TOPIC,
        domain="creativity",
        db_path=temp_db,
        run_id=FIXTURE_RUN_ID,
        report_dir=artifact_dirs["reports"],
        ticket_dir=artifact_dirs["tickets"],
        export_dirs=[artifact_dirs["export"]],
    )
    snapshot_path = tmp_path / "atlas_snapshot.json"
    coherence_path = tmp_path / "atlas_coherence_preview.json"
    exit_code = main(
        [
            "export-atlas-snapshot",
            "--db",
            str(temp_db),
            "--out",
            str(snapshot_path),
            "--coherence-preview-out",
            str(coherence_path),
            "--topic",
            GOLDEN_MVP_TOPIC,
            "--domain",
            "creativity",
            "--fixture-mode",
        ]
    )
    assert exit_code == 0
    assert snapshot_path.is_file()
    assert coherence_path.is_file()
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    preview = json.loads(coherence_path.read_text(encoding="utf-8"))
    assert preview == build_atlas_coherence_preview(snapshot)
    assert preview == json.loads(COMMITTED_COHERENCE_PREVIEW.read_text(encoding="utf-8"))
