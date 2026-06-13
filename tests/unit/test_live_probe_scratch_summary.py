"""Unit tests for read-only live probe scratch DB summary."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.db.connection import DEFAULT_DB_PATH, connect
from rge.modules.live_probe_scratch import build_scratch_record, ensure_scratch_database, insert_reviewed_report
from rge.modules.live_probe_scratch_summary import (
    LiveProbeScratchSummaryError,
    build_scratch_summary,
    connect_scratch_readonly,
    format_summary_json,
    format_summary_markdown,
    run_scratch_summary,
    validate_summary_output_path,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_REPORT = (
    REPO_ROOT / "tests" / "fixtures" / "probes" / "reviewed_mini_run_report_sample.json"
)


def _sample_record(**overrides: object) -> dict:
    report = json.loads(SAMPLE_REPORT.read_text(encoding="utf-8"))
    record = build_scratch_record(
        report,
        report_rel_path="tests/fixtures/probes/reviewed_mini_run_report_sample.json",
        operator_note="reviewed",
        reviewed_at="2026-06-12T22:01:00+00:00",
    )
    record.update(overrides)
    return record


def _seed_scratch_db(db_path: Path, records: list[dict]) -> None:
    conn = ensure_scratch_database(db_path)
    try:
        for record in records:
            insert_reviewed_report(conn, record)
    finally:
        conn.close()


def test_build_summary_over_seeded_db(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    record = _sample_record()
    record2 = _sample_record(
        report_rel_path="data/reports/live_probes/probe_mini_run_other.json",
        fixture_source="fixtures/sources/live_probe_diversity_calibration_short.txt",
        operator_reviewed_at="2026-06-12T23:00:00+00:00",
        ingested_at="2026-06-12T23:00:01+00:00",
        operator_note=None,
    )
    _seed_scratch_db(scratch_db, [record, record2])

    summary = build_scratch_summary(scratch_db=scratch_db)
    assert summary["total_reviewed_reports"] == 2
    assert summary["floors_passed"] == 2
    assert summary["operator_notes_count"] == 1
    assert "live_probe_claim_calibration_short.txt" in summary["reports_by_fixture"]
    assert summary["stage_totals"]["claim_extraction"]["accepted"] == 2
    assert summary["safety_flags"]["public_export"] is False
    assert summary["safety_flags"]["model_authority"] is False


def test_summary_is_deterministic_across_runs(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    _seed_scratch_db(scratch_db, [_sample_record()])
    first = format_summary_json(build_scratch_summary(scratch_db=scratch_db))
    second = format_summary_json(build_scratch_summary(scratch_db=scratch_db))
    assert first == second


def test_missing_db_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(LiveProbeScratchSummaryError, match="scratch DB not found"):
        build_scratch_summary(scratch_db=tmp_path / "missing.sqlite")


def test_allow_empty_missing_db(tmp_path: Path) -> None:
    summary = build_scratch_summary(
        scratch_db=tmp_path / "missing.sqlite",
        allow_empty=True,
    )
    assert summary["total_reviewed_reports"] == 0
    assert summary["scratch_db_missing"] is True


def test_empty_valid_db_summary(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    ensure_scratch_database(scratch_db).close()
    summary = build_scratch_summary(scratch_db=scratch_db)
    assert summary["total_reviewed_reports"] == 0
    assert summary["scratch_db_missing"] is False


def test_invalid_schema_fails_closed(tmp_path: Path) -> None:
    scratch_db = tmp_path / "bad.sqlite"
    conn = connect(scratch_db)
    conn.execute("CREATE TABLE reviewed_live_probe_reports (id INTEGER)")
    conn.commit()
    conn.close()
    with pytest.raises(LiveProbeScratchSummaryError, match="invalid scratch DB schema"):
        build_scratch_summary(scratch_db=scratch_db)


def test_summary_does_not_create_scratch_db(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    with pytest.raises(LiveProbeScratchSummaryError):
        build_scratch_summary(scratch_db=scratch_db)
    assert not scratch_db.exists()


def test_summary_does_not_mutate_scratch_db(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    _seed_scratch_db(scratch_db, [_sample_record()])
    mtime_before = scratch_db.stat().st_mtime
    size_before = scratch_db.stat().st_size

    build_scratch_summary(scratch_db=scratch_db)
    run_scratch_summary(scratch_db=scratch_db, output_format="markdown")

    assert scratch_db.stat().st_mtime == mtime_before
    assert scratch_db.stat().st_size == size_before


def test_summary_output_has_no_forbidden_patterns(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    _seed_scratch_db(scratch_db, [_sample_record()])
    text = format_summary_json(build_scratch_summary(scratch_db=scratch_db))
    lowered = text.casefold()
    assert "sk-" not in lowered
    assert "api_key" not in lowered
    assert "ai-assisted brainstorming reduced" not in lowered
    assert "reviewed in unit test" not in lowered


def test_markdown_format_includes_sections(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    _seed_scratch_db(scratch_db, [_sample_record()])
    md = format_summary_markdown(build_scratch_summary(scratch_db=scratch_db))
    assert "## Safety flags" in md
    assert "## Reports by fixture" in md


def test_run_summary_writes_private_out_path(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    _seed_scratch_db(scratch_db, [_sample_record()])
    out_path = tmp_path / "data" / "reports" / "live_probes" / "scratch_summary_test.json"
    result = run_scratch_summary(
        scratch_db=scratch_db,
        out_path=out_path,
        root=tmp_path,
    )
    assert out_path.is_file()
    assert result["output_path"].startswith("data/reports/")
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["total_reviewed_reports"] == 1


def test_out_path_rejects_public_export_dir(tmp_path: Path) -> None:
    with pytest.raises(LiveProbeScratchSummaryError, match="public export"):
        validate_summary_output_path(
            tmp_path / "data" / "exports" / "summary.json",
            tmp_path,
        )


def test_connect_scratch_readonly(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    _seed_scratch_db(scratch_db, [_sample_record()])
    conn = connect_scratch_readonly(scratch_db)
    try:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("INSERT INTO reviewed_live_probe_reports DEFAULT VALUES")
    finally:
        conn.close()


def test_default_graph_db_untouched(tmp_path: Path) -> None:
    default_db = tmp_path / "data" / "db" / "creative_research.sqlite"
    default_db.parent.mkdir(parents=True)
    default_db.write_bytes(b"seed")
    mtime_before = default_db.stat().st_mtime

    with patch(
        "rge.modules.live_probe_scratch_summary.DEFAULT_DB_PATH",
        default_db,
    ):
        with pytest.raises(LiveProbeScratchSummaryError, match="must not equal"):
            build_scratch_summary(scratch_db=default_db)

    assert default_db.stat().st_mtime == mtime_before


def test_cli_probe_scratch_summary_success(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    _seed_scratch_db(scratch_db, [_sample_record()])
    exit_code = main(
        [
            "probe-scratch-summary",
            "--scratch-db",
            str(scratch_db),
        ]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "probe-scratch-summary"
    assert payload["total_reviewed_reports"] == 1


def test_cli_missing_db_exits_2(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    exit_code = main(
        [
            "probe-scratch-summary",
            "--scratch-db",
            str(tmp_path / "missing.sqlite"),
        ]
    )
    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out)
    assert "scratch DB not found" in payload["detail"]
