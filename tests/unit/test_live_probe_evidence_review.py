"""Unit tests for deterministic scratch evidence review reports."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.db.connection import DEFAULT_DB_PATH
from rge.modules.live_probe_evidence_review import (
    LiveProbeEvidenceReviewError,
    build_evidence_review_payload,
    format_evidence_review_json,
    format_evidence_review_markdown,
    run_evidence_review,
)
from rge.modules.live_probe_scratch import build_scratch_record, ensure_scratch_database, insert_reviewed_report
from rge.modules.live_probe_scratch_summary import build_scratch_summary

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_REPORT = (
    REPO_ROOT / "tests" / "fixtures" / "probes" / "reviewed_mini_run_report_sample.json"
)


def _sample_record(**overrides: object) -> dict:
    report = json.loads(SAMPLE_REPORT.read_text(encoding="utf-8"))
    record = build_scratch_record(
        report,
        report_rel_path="tests/fixtures/probes/reviewed_mini_run_report_sample.json",
        operator_note="reviewed by operator",
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


def test_evidence_review_from_seeded_db(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    _seed_scratch_db(scratch_db, [_sample_record()])
    payload = run_evidence_review(scratch_db=scratch_db, output_format="json")
    assert payload["total_reviewed_reports"] == 1
    assert payload["automated_ticket_recommendations"] is False
    assert payload["human_review_required"] is True
    assert payload["safety_attestation"]["public_export"] is False
    assert payload["generated_at"] == "2026-06-12T22:01:00+00:00"


def test_evidence_review_is_deterministic(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    _seed_scratch_db(scratch_db, [_sample_record()])
    first = format_evidence_review_json(
        run_evidence_review(scratch_db=scratch_db, output_format="json")
    )
    second = format_evidence_review_json(
        run_evidence_review(scratch_db=scratch_db, output_format="json")
    )
    assert first == second


def test_evidence_review_markdown_has_no_ticket_recommendations(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    _seed_scratch_db(scratch_db, [_sample_record()])
    md = format_evidence_review_markdown(
        run_evidence_review(scratch_db=scratch_db, output_format="markdown")
    )
    assert "automated_ticket_recommendations: false" in md
    assert "reviewed by operator" not in md
    assert "ai-assisted brainstorming reduced" not in md.lower()


def test_missing_db_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(LiveProbeEvidenceReviewError, match="scratch DB not found"):
        run_evidence_review(scratch_db=tmp_path / "missing.sqlite")


def test_allow_empty_missing_db(tmp_path: Path) -> None:
    payload = run_evidence_review(
        scratch_db=tmp_path / "missing.sqlite",
        allow_empty=True,
    )
    assert payload["total_reviewed_reports"] == 0
    assert payload["scratch_db_missing"] is True


def test_empty_valid_db_review(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    ensure_scratch_database(scratch_db).close()
    payload = run_evidence_review(scratch_db=scratch_db)
    assert payload["total_reviewed_reports"] == 0


def test_evidence_review_does_not_create_scratch_db(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    with pytest.raises(LiveProbeEvidenceReviewError):
        run_evidence_review(scratch_db=scratch_db)
    assert not scratch_db.exists()


def test_evidence_review_does_not_mutate_scratch_db(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    _seed_scratch_db(scratch_db, [_sample_record()])
    mtime_before = scratch_db.stat().st_mtime
    run_evidence_review(scratch_db=scratch_db)
    assert scratch_db.stat().st_mtime == mtime_before


def test_out_path_rejects_public_export_dir(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    _seed_scratch_db(scratch_db, [_sample_record()])
    with pytest.raises(LiveProbeEvidenceReviewError, match="public export"):
        run_evidence_review(
            scratch_db=scratch_db,
            out_path=tmp_path / "data" / "exports" / "review.md",
            root=tmp_path,
        )


def test_run_evidence_review_writes_private_out_path(tmp_path: Path) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    _seed_scratch_db(scratch_db, [_sample_record()])
    out_path = tmp_path / "agent_reports" / "scratch_evidence_review_test.md"
    result = run_evidence_review(
        scratch_db=scratch_db,
        out_path=out_path,
        root=tmp_path,
    )
    assert out_path.is_file()
    assert result["output_path"].startswith("agent_reports/")


def test_default_graph_db_untouched(tmp_path: Path) -> None:
    default_db = tmp_path / "data" / "db" / "creative_research.sqlite"
    default_db.parent.mkdir(parents=True)
    default_db.write_bytes(b"seed")
    mtime_before = default_db.stat().st_mtime

    with patch(
        "rge.modules.live_probe_scratch_summary.DEFAULT_DB_PATH",
        default_db,
    ):
        with pytest.raises(LiveProbeEvidenceReviewError, match="must not equal"):
            run_evidence_review(scratch_db=default_db)

    assert default_db.stat().st_mtime == mtime_before


def test_build_evidence_review_reuses_summary_fields() -> None:
    payload = build_evidence_review_payload(
        {
            "status": "ok",
            "scratch_db_path": "data/db/live_probe_scratch.sqlite",
            "last_reviewed_at": "2026-06-12T22:01:00+00:00",
            "total_reviewed_reports": 1,
            "safety_flags": {"public_export": False},
        }
    )
    assert payload["generated_from"] == "probe-scratch-summary"
    assert payload["safety_attestation"]["public_export"] is False


def test_cli_probe_scratch_evidence_review_success(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    scratch_db = tmp_path / "live_probe_scratch.sqlite"
    _seed_scratch_db(scratch_db, [_sample_record()])
    exit_code = main(
        [
            "probe-scratch-evidence-review",
            "--scratch-db",
            str(scratch_db),
            "--format",
            "json",
        ]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "probe-scratch-evidence-review"


def test_cli_missing_db_exits_2(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    exit_code = main(
        [
            "probe-scratch-evidence-review",
            "--scratch-db",
            str(tmp_path / "missing.sqlite"),
        ]
    )
    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out)
    assert "scratch DB not found" in payload["detail"]
