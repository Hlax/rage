"""Unit tests for operator-reviewed live probe scratch DB persistence."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.db.connection import DEFAULT_DB_PATH
from rge.llm.mock_client import MockModelClient
from rge.modules.live_probe import run_probe_mini_run
from rge.modules.live_probe_scratch import (
    LiveProbeScratchValidationError,
    build_scratch_record,
    ensure_scratch_database,
    insert_reviewed_report,
    list_reviewed_reports,
    persist_reviewed_report,
    validate_report_for_scratch_persist,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_REPORT = (
    REPO_ROOT / "tests" / "fixtures" / "probes" / "reviewed_mini_run_report_sample.json"
)


def test_validate_report_rejects_unsupported_type() -> None:
    with pytest.raises(LiveProbeScratchValidationError, match="unsupported report_type"):
        validate_report_for_scratch_persist({"report_type": "live_probe_report"})


def test_build_scratch_record_extracts_stage_counts() -> None:
    report = json.loads(SAMPLE_REPORT.read_text(encoding="utf-8"))
    record = build_scratch_record(
        report,
        report_rel_path="tests/fixtures/probes/reviewed_mini_run_report_sample.json",
        operator_note="reviewed in unit test",
    )
    assert record["stage_claim_accepted"] == 1
    assert record["stage_claim_rejected"] == 1
    assert record["stage_contradiction_accepted"] == 1
    assert record["contradiction_input_mode"] == "hybrid_overlay"
    assert record["run_mode"] == "single"
    assert "scope must appear verbatim" in record["rejection_diagnostics_json"]


def test_insert_and_list_reviewed_report_round_trip(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    report = json.loads(SAMPLE_REPORT.read_text(encoding="utf-8"))
    record = build_scratch_record(
        report,
        report_rel_path="tests/fixtures/probes/reviewed_mini_run_report_sample.json",
        operator_note=None,
        reviewed_at="2026-06-12T22:01:00+00:00",
    )
    conn = ensure_scratch_database(scratch_db)
    try:
        row_id = insert_reviewed_report(conn, record)
        assert row_id == 1
    finally:
        conn.close()
    rows = list_reviewed_reports(scratch_db=scratch_db, limit=5)
    assert len(rows) == 1
    assert rows[0]["report_rel_path"].endswith("reviewed_mini_run_report_sample.json")
    assert rows[0]["floors_met"] == 1


def test_persist_reviewed_report_requires_confirm_review(tmp_path: Path) -> None:
    with pytest.raises(LiveProbeScratchValidationError, match="confirm-review"):
        persist_reviewed_report(
            report_path=SAMPLE_REPORT,
            scratch_db=tmp_path / "scratch.sqlite",
            confirm_review=False,
            root=REPO_ROOT,
        )


def test_persist_reviewed_report_writes_scratch_not_default_db(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    default_db = tmp_path / "creative_research.sqlite"
    default_db.parent.mkdir(parents=True, exist_ok=True)
    default_db.write_bytes(b"")
    default_mtime = default_db.stat().st_mtime

    result = persist_reviewed_report(
        report_path=SAMPLE_REPORT,
        scratch_db=scratch_db,
        operator_note="operator ok",
        confirm_review=True,
        root=REPO_ROOT,
    )
    assert result["status"] == "ok"
    assert result["default_db_written"] is False
    assert scratch_db.is_file()
    assert default_db.stat().st_mtime == default_mtime
    rows = list_reviewed_reports(scratch_db=scratch_db)
    assert len(rows) == 1


def test_persist_rejects_default_db_path_as_scratch(tmp_path: Path) -> None:
    with pytest.raises(LiveProbeScratchValidationError, match="must not equal"):
        persist_reviewed_report(
            report_path=SAMPLE_REPORT,
            scratch_db=DEFAULT_DB_PATH,
            confirm_review=True,
            root=REPO_ROOT,
        )


def test_persist_fails_on_missing_report(tmp_path: Path) -> None:
    with pytest.raises(LiveProbeScratchValidationError, match="report not found"):
        persist_reviewed_report(
            report_path=tmp_path / "missing.json",
            scratch_db=tmp_path / "scratch.sqlite",
            confirm_review=True,
            root=REPO_ROOT,
        )


def test_persist_fails_on_malformed_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(LiveProbeScratchValidationError, match="malformed report JSON"):
        persist_reviewed_report(
            report_path=bad,
            scratch_db=tmp_path / "scratch.sqlite",
            confirm_review=True,
            root=REPO_ROOT,
        )


def test_cli_persist_reviewed_report_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    scratch_db = tmp_path / "scratch.sqlite"
    exit_code = main(
        [
            "probe-persist-reviewed-report",
            "--report",
            str(SAMPLE_REPORT.relative_to(REPO_ROOT)).replace("\\", "/"),
            "--scratch-db",
            str(scratch_db),
            "--confirm-review",
            "--note",
            "cli test",
        ]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert payload["row_id"] == 1


def test_cli_persist_without_confirm_review_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "probe-persist-reviewed-report",
            "--report",
            str(SAMPLE_REPORT.relative_to(REPO_ROOT)).replace("\\", "/"),
        ]
    )
    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out)
    assert "confirm-review" in payload["detail"]


def test_run_probe_mini_run_does_not_create_scratch_db(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")
    scratch_db = tmp_path / "data" / "db" / "live_probe_scratch.sqlite"
    default_db = tmp_path / "data" / "db" / "creative_research.sqlite"
    default_db.parent.mkdir(parents=True)

    with patch("rge.modules.live_probe.default_db_path", return_value=default_db):
        run_probe_mini_run(
            fixture_source=REPO_ROOT
            / "fixtures"
            / "sources"
            / "live_probe_claim_calibration_short.txt",
            root=REPO_ROOT,
            reports_dir=tmp_path / "reports",
            client=MockModelClient(),
            skip_health_check=True,
        )

    assert not scratch_db.exists()
