"""Private atlas snapshot export CLI (ticket-282)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import FIXTURE_RUN_ID, GOLDEN_MVP_TOPIC, execute_fixture_mode_run, main
from rge.contracts.atlas_snapshot_v0 import validate_atlas_snapshot
from rge.modules.atlas_snapshot_builder import (
    assert_no_private_fields,
    build_atlas_snapshot_from_db,
    export_atlas_snapshot_to_path,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CREATIVITY_FIXTURE = REPO_ROOT / "fixtures" / "atlas" / "atlas_snapshot_v0_creativity_fixture.json"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "atlas_export.sqlite"


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


def test_export_atlas_snapshot_cli_writes_validated_json(
    temp_db: Path,
    artifact_dirs: dict[str, Path],
    tmp_path: Path,
) -> None:
    _build_fixture_mvp_db(temp_db, artifact_dirs)
    out_path = tmp_path / "atlas_snapshot.json"
    exit_code = main(
        [
            "export-atlas-snapshot",
            "--db",
            str(temp_db),
            "--out",
            str(out_path),
            "--fixture-mode",
        ]
    )
    assert exit_code == 0
    assert out_path.is_file()
    snapshot = json.loads(out_path.read_text(encoding="utf-8"))
    validate_atlas_snapshot(snapshot)
    assert assert_no_private_fields(snapshot) == []
    assert snapshot["schema_version"] == "atlas_snapshot_v0.1.0"
    assert len(snapshot["cards"]) >= 2


def test_export_atlas_snapshot_fixture_mode_second_run_byte_identical(
    temp_db: Path,
    artifact_dirs: dict[str, Path],
    tmp_path: Path,
) -> None:
    _build_fixture_mvp_db(temp_db, artifact_dirs)
    out_path = tmp_path / "atlas_snapshot.json"
    for _ in range(2):
        exit_code = main(
            [
                "export-atlas-snapshot",
                "--db",
                str(temp_db),
                "--out",
                str(out_path),
                "--fixture-mode",
            ]
        )
        assert exit_code == 0
    first_bytes = out_path.read_bytes()
    exit_code = main(
        [
            "export-atlas-snapshot",
            "--db",
            str(temp_db),
            "--out",
            str(out_path),
            "--fixture-mode",
        ]
    )
    assert exit_code == 0
    assert out_path.read_bytes() == first_bytes
    expected = CREATIVITY_FIXTURE.read_bytes()
    assert out_path.read_bytes() == expected


def test_export_atlas_snapshot_matches_committed_creativity_fixture(
    temp_db: Path,
    artifact_dirs: dict[str, Path],
    tmp_path: Path,
) -> None:
    from rge.db.connection import connect

    _build_fixture_mvp_db(temp_db, artifact_dirs)
    out_path = tmp_path / "atlas_snapshot.json"
    conn = connect(temp_db)
    try:
        export_atlas_snapshot_to_path(
            conn,
            out_path,
            topic=GOLDEN_MVP_TOPIC,
            domain_pack="creativity",
            fixture_mode=True,
            repo_root=REPO_ROOT,
        )
    finally:
        conn.close()
    assert out_path.read_bytes() == CREATIVITY_FIXTURE.read_bytes()


def test_export_atlas_snapshot_fail_closed_on_private_field_leak(
    temp_db: Path,
    artifact_dirs: dict[str, Path],
    tmp_path: Path,
) -> None:
    from rge.db.connection import connect

    _build_fixture_mvp_db(temp_db, artifact_dirs)
    out_path = tmp_path / "atlas_snapshot.json"
    conn = connect(temp_db)
    try:
        snapshot = build_atlas_snapshot_from_db(
            conn,
            topic=GOLDEN_MVP_TOPIC,
            domain_pack="creativity",
            fixture_mode=True,
            repo_root=REPO_ROOT,
        )
        snapshot["cards"][0]["claim_id"] = "claim_secret"

        def _leaky_build(*_args: object, **_kwargs: object) -> dict[str, object]:
            return snapshot

        with patch(
            "rge.modules.atlas_snapshot_builder.build_atlas_snapshot_from_db",
            side_effect=_leaky_build,
        ):
            with pytest.raises(ValueError, match="private-field"):
                export_atlas_snapshot_to_path(
                    conn,
                    out_path,
                    topic=GOLDEN_MVP_TOPIC,
                    domain_pack="creativity",
                    fixture_mode=True,
                    repo_root=REPO_ROOT,
                )
    finally:
        conn.close()
    assert not out_path.exists()


def test_export_atlas_snapshot_cli_reports_error_on_validation_failure(
    temp_db: Path,
    artifact_dirs: dict[str, Path],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rge.db.connection import connect

    _build_fixture_mvp_db(temp_db, artifact_dirs)
    out_path = tmp_path / "atlas_snapshot.json"
    conn = connect(temp_db)
    try:
        snapshot = build_atlas_snapshot_from_db(
            conn,
            topic=GOLDEN_MVP_TOPIC,
            domain_pack="creativity",
            fixture_mode=True,
            repo_root=REPO_ROOT,
        )
        snapshot["schema_version"] = "atlas_snapshot_v0.0.0"

        def _bad_schema(*_args: object, **_kwargs: object) -> dict[str, object]:
            return snapshot

        with patch(
            "rge.modules.atlas_snapshot_builder.build_atlas_snapshot_from_db",
            side_effect=_bad_schema,
        ):
            capsys.readouterr()
            exit_code = main(
                [
                    "export-atlas-snapshot",
                    "--db",
                    str(temp_db),
                    "--out",
                    str(out_path),
                    "--fixture-mode",
                ]
            )
            captured = capsys.readouterr().out
    finally:
        conn.close()
    assert exit_code == 1
    payload = json.loads(captured)
    assert payload["status"] == "error"
    assert payload["command"] == "export-atlas-snapshot"
    assert not out_path.exists()
