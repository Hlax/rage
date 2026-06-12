"""Operator-reviewed live probe report persistence in an isolated scratch SQLite DB.

Writes metadata only after explicit CLI review confirmation. Never touches the
default accepted graph database or public export paths.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rge.db.connection import DEFAULT_DB_PATH, connect
from rge.modules.live_probe import mini_run_floors_met

LIVE_PROBE_SCRATCH_DB_PATH = Path("data") / "db" / "live_probe_scratch.sqlite"
SCRATCH_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "db" / "live_probe_scratch_schema.sql"
)
SCRATCH_SCHEMA_VERSION = "0.1.0"
ACCEPTED_MINI_RUN_REPORT_TYPE = "live_probe_mini_run_report"
ACCEPTED_SUITE_REPORT_TYPE = "live_probe_mini_run_suite_report"
MAX_DIAGNOSTICS = 10
MAX_DIAGNOSTIC_LEN = 500


class LiveProbeScratchError(Exception):
    """Scratch persistence failed (validation, I/O)."""


class LiveProbeScratchValidationError(LiveProbeScratchError):
    """Report or operator input failed validation."""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_scratch_db_path(db_path: Path | None = None) -> Path:
    return db_path if db_path is not None else LIVE_PROBE_SCRATCH_DB_PATH


def ensure_scratch_database(db_path: Path | None = None) -> sqlite3.Connection:
    """Open scratch DB and apply isolated schema (not main migrations)."""
    path = get_scratch_db_path(db_path)
    conn = connect(path)
    schema_sql = SCRATCH_SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    conn.commit()
    return conn


def _relative_report_path(report_path: Path, root: Path) -> str:
    resolved = report_path.resolve()
    try:
        return str(resolved.relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        raise LiveProbeScratchValidationError(
            "report path must be inside the repository root"
        ) from None


def _stage_counts(report: dict[str, Any], stage_key: str) -> tuple[int, int]:
    stages = report.get("stages") or {}
    stage = stages.get(stage_key) or {}
    return (
        int(stage.get("accepted_count") or 0),
        int(stage.get("rejected_count") or 0),
    )


def _collect_rejection_diagnostics(report: dict[str, Any]) -> list[str]:
    diagnostics: list[str] = []
    stages = report.get("stages") or {}
    for stage in stages.values():
        if not isinstance(stage, dict):
            continue
        for item in stage.get("rejected") or []:
            if not isinstance(item, dict):
                continue
            text = item.get("validation_diagnostic") or item.get("rejection_reason")
            if text:
                diagnostics.append(str(text)[:MAX_DIAGNOSTIC_LEN])
        for text in stage.get("diagnostics_summary") or []:
            diagnostics.append(str(text)[:MAX_DIAGNOSTIC_LEN])
    if report.get("error"):
        diagnostics.append(str(report["error"])[:MAX_DIAGNOSTIC_LEN])
    for run in report.get("runs") or []:
        if isinstance(run, dict) and run.get("error"):
            diagnostics.append(str(run["error"])[:MAX_DIAGNOSTIC_LEN])
    seen: set[str] = set()
    unique: list[str] = []
    for item in diagnostics:
        if item not in seen:
            seen.add(item)
            unique.append(item)
        if len(unique) >= MAX_DIAGNOSTICS:
            break
    return unique


def validate_report_for_scratch_persist(report: dict[str, Any]) -> None:
    """Fail closed unless report is a safe reviewed live probe artifact."""
    report_type = report.get("report_type")
    if report_type not in (
        ACCEPTED_MINI_RUN_REPORT_TYPE,
        ACCEPTED_SUITE_REPORT_TYPE,
    ):
        raise LiveProbeScratchValidationError(
            f"unsupported report_type {report_type!r}; expected mini-run or suite report"
        )
    if report.get("db_writes") is not False:
        raise LiveProbeScratchValidationError("report must have db_writes: false")
    if report.get("public_export") is not False:
        raise LiveProbeScratchValidationError("report must have public_export: false")
    if report.get("cloud_calls") is not False:
        raise LiveProbeScratchValidationError("report must have cloud_calls: false")
    if not report.get("created_at"):
        raise LiveProbeScratchValidationError("report missing created_at")
    if not report.get("command"):
        raise LiveProbeScratchValidationError("report missing command")


def build_scratch_record(
    report: dict[str, Any],
    *,
    report_rel_path: str,
    operator_note: str | None,
    reviewed_at: str | None = None,
) -> dict[str, Any]:
    """Build a sanitized row dict from a validated probe report."""
    validate_report_for_scratch_persist(report)
    reviewed = reviewed_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    ingested = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    report_type = report["report_type"]
    if report_type == ACCEPTED_MINI_RUN_REPORT_TYPE:
        run_mode = "single"
        floors_met = 1 if mini_run_floors_met(report) else 0
        claim_a, claim_r = _stage_counts(report, "claim_extraction")
        link_a, link_r = _stage_counts(report, "concept_linking")
        rel_a, rel_r = _stage_counts(report, "relationship_drafting")
        con_a, con_r = _stage_counts(report, "contradiction_detection")
        fixture_count = None
        fixtures_passed = None
        fixtures_failed = None
    else:
        run_mode = "suite_summary"
        floors_met = 1 if int(report.get("fixtures_failed") or 0) == 0 else 0
        claim_a = claim_r = link_a = link_r = rel_a = rel_r = con_a = con_r = 0
        fixture_count = int(report.get("fixture_count") or 0)
        fixtures_passed = int(report.get("fixtures_passed") or 0)
        fixtures_failed = int(report.get("fixtures_failed") or 0)

    return {
        "report_rel_path": report_rel_path,
        "report_created_at": str(report["created_at"]),
        "command": str(report["command"]),
        "run_mode": run_mode,
        "fixture_source": report.get("fixture_source"),
        "strict_chain": 1 if report.get("strict_chain") else 0,
        "status": str(report.get("status") or "unknown"),
        "floors_met": floors_met,
        "contradiction_input_mode": report.get("contradiction_input_mode"),
        "effective_llm_mode": report.get("effective_llm_mode"),
        "provider": report.get("provider"),
        "model": report.get("model"),
        "stage_claim_accepted": claim_a,
        "stage_claim_rejected": claim_r,
        "stage_link_accepted": link_a,
        "stage_link_rejected": link_r,
        "stage_relationship_accepted": rel_a,
        "stage_relationship_rejected": rel_r,
        "stage_contradiction_accepted": con_a,
        "stage_contradiction_rejected": con_r,
        "fixture_count": fixture_count,
        "fixtures_passed": fixtures_passed,
        "fixtures_failed": fixtures_failed,
        "rejection_diagnostics_json": json.dumps(
            _collect_rejection_diagnostics(report), ensure_ascii=False
        ),
        "operator_reviewed_at": reviewed,
        "operator_note": operator_note,
        "ingested_at": ingested,
        "schema_version": SCRATCH_SCHEMA_VERSION,
    }


def insert_reviewed_report(conn: sqlite3.Connection, record: dict[str, Any]) -> int:
    """Insert sanitized record; return row id."""
    columns = [
        "report_rel_path",
        "report_created_at",
        "command",
        "run_mode",
        "fixture_source",
        "strict_chain",
        "status",
        "floors_met",
        "contradiction_input_mode",
        "effective_llm_mode",
        "provider",
        "model",
        "stage_claim_accepted",
        "stage_claim_rejected",
        "stage_link_accepted",
        "stage_link_rejected",
        "stage_relationship_accepted",
        "stage_relationship_rejected",
        "stage_contradiction_accepted",
        "stage_contradiction_rejected",
        "fixture_count",
        "fixtures_passed",
        "fixtures_failed",
        "rejection_diagnostics_json",
        "operator_reviewed_at",
        "operator_note",
        "ingested_at",
        "schema_version",
    ]
    placeholders = ", ".join("?" for _ in columns)
    col_list = ", ".join(columns)
    values = [record.get(col) for col in columns]
    cursor = conn.execute(
        f"INSERT INTO reviewed_live_probe_reports ({col_list}) VALUES ({placeholders})",
        values,
    )
    conn.commit()
    return int(cursor.lastrowid)


def load_report_json(report_path: Path) -> dict[str, Any]:
    if not report_path.is_file():
        raise LiveProbeScratchValidationError(f"report not found: {report_path}")
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LiveProbeScratchValidationError(
            f"malformed report JSON: {report_path}"
        ) from exc
    if not isinstance(payload, dict):
        raise LiveProbeScratchValidationError("report JSON must be an object")
    return payload


def persist_reviewed_report(
    *,
    report_path: Path,
    scratch_db: Path | None = None,
    operator_note: str | None = None,
    confirm_review: bool = False,
    root: Path | None = None,
) -> dict[str, Any]:
    """Persist operator-reviewed probe report metadata to scratch DB only."""
    if not confirm_review:
        raise LiveProbeScratchValidationError(
            "operator review required: pass --confirm-review to persist"
        )
    base = root if root is not None else repo_root()
    resolved_report = report_path if report_path.is_absolute() else base / report_path
    report = load_report_json(resolved_report)
    validate_report_for_scratch_persist(report)
    rel_path = _relative_report_path(resolved_report, base)
    record = build_scratch_record(
        report,
        report_rel_path=rel_path,
        operator_note=operator_note,
    )

    scratch_path = get_scratch_db_path(scratch_db)
    if scratch_path.resolve() == DEFAULT_DB_PATH.resolve():
        raise LiveProbeScratchValidationError(
            "scratch DB path must not equal the default accepted graph DB"
        )

    conn = ensure_scratch_database(scratch_path)
    try:
        row_id = insert_reviewed_report(conn, record)
    finally:
        conn.close()

    return {
        "status": "ok",
        "command": "probe-persist-reviewed-report",
        "scratch_db_path": str(scratch_path).replace("\\", "/"),
        "default_db_path": str(DEFAULT_DB_PATH).replace("\\", "/"),
        "default_db_written": False,
        "public_export": False,
        "row_id": row_id,
        "report_rel_path": rel_path,
        "run_mode": record["run_mode"],
        "floors_met": bool(record["floors_met"]),
        "operator_reviewed_at": record["operator_reviewed_at"],
    }


def list_reviewed_reports(
    *,
    scratch_db: Path | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    conn = ensure_scratch_database(scratch_db)
    try:
        rows = conn.execute(
            """
            SELECT id, report_rel_path, report_created_at, command, run_mode,
                   fixture_source, status, floors_met, operator_reviewed_at
            FROM reviewed_live_probe_reports
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
