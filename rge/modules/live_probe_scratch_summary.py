"""Deterministic read-only summary over operator-reviewed live probe scratch DB rows."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

from rge.db.connection import DEFAULT_DB_PATH
from rge.modules.live_probe_scratch import (
    LIVE_PROBE_SCRATCH_DB_PATH,
    SCRATCH_SCHEMA_VERSION,
    get_scratch_db_path,
)

REVIEWED_TABLE = "reviewed_live_probe_reports"
REQUIRED_COLUMNS = frozenset(
    {
        "id",
        "report_rel_path",
        "report_created_at",
        "command",
        "run_mode",
        "fixture_source",
        "strict_chain",
        "status",
        "floors_met",
        "contradiction_input_mode",
        "stage_claim_accepted",
        "stage_claim_rejected",
        "stage_link_accepted",
        "stage_link_rejected",
        "stage_relationship_accepted",
        "stage_relationship_rejected",
        "stage_contradiction_accepted",
        "stage_contradiction_rejected",
        "rejection_diagnostics_json",
        "operator_reviewed_at",
        "operator_note",
        "ingested_at",
        "schema_version",
    }
)
PRIVATE_OUTPUT_PREFIXES = (
    "data/reports/",
    "agent_reports/",
)
FORBIDDEN_PUBLIC_PREFIXES = (
    "apps/public-site/public/",
    "data/exports/",
)
STAGE_KEYS = (
    ("claim_extraction", "stage_claim_accepted", "stage_claim_rejected"),
    ("concept_linking", "stage_link_accepted", "stage_link_rejected"),
    ("relationship_drafting", "stage_relationship_accepted", "stage_relationship_rejected"),
    ("contradiction_detection", "stage_contradiction_accepted", "stage_contradiction_rejected"),
)


class LiveProbeScratchSummaryError(Exception):
    """Scratch summary failed (validation, I/O, schema)."""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _fixture_name(fixture_source: str | None) -> str:
    if not fixture_source:
        return "(unknown)"
    return Path(str(fixture_source)).name


def connect_scratch_readonly(db_path: Path) -> sqlite3.Connection:
    """Open scratch SQLite read-only; never creates parent dirs or schema."""
    resolved = db_path.resolve()
    uri = f"file:{resolved.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def validate_scratch_schema(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (REVIEWED_TABLE,),
    ).fetchone()
    if row is None:
        raise LiveProbeScratchSummaryError(
            f"invalid scratch DB schema: missing {REVIEWED_TABLE} table"
        )
    columns = {
        str(item[1])
        for item in conn.execute(f"PRAGMA table_info({REVIEWED_TABLE})").fetchall()
    }
    missing = REQUIRED_COLUMNS - columns
    if missing:
        raise LiveProbeScratchSummaryError(
            "invalid scratch DB schema: missing columns "
            f"{sorted(missing)}"
        )


def validate_summary_output_path(output_path: Path, root: Path) -> Path:
    resolved = output_path if output_path.is_absolute() else root / output_path
    resolved = resolved.resolve()
    try:
        rel = resolved.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise LiveProbeScratchSummaryError(
            "summary output path must be inside the repository root"
        ) from exc
    if any(rel.startswith(prefix) for prefix in FORBIDDEN_PUBLIC_PREFIXES):
        raise LiveProbeScratchSummaryError(
            f"summary output path must not be under public export dirs: {rel}"
        )
    if not any(rel.startswith(prefix) for prefix in PRIVATE_OUTPUT_PREFIXES):
        raise LiveProbeScratchSummaryError(
            "summary output path must be under data/reports/ or agent_reports/"
        )
    return resolved


def empty_summary(
    *,
    scratch_db_path: Path,
    allow_empty: bool = False,
    missing_db: bool = False,
) -> dict[str, Any]:
    return {
        "report_type": "live_probe_scratch_summary",
        "command": "probe-scratch-summary",
        "status": "ok",
        "scratch_db_path": str(scratch_db_path).replace("\\", "/"),
        "scratch_db_missing": missing_db,
        "allow_empty": allow_empty,
        "schema_version": SCRATCH_SCHEMA_VERSION,
        "total_reviewed_reports": 0,
        "first_reviewed_at": None,
        "last_reviewed_at": None,
        "floors_passed": 0,
        "floors_failed": 0,
        "fixture_pass_rate": None,
        "reports_by_fixture": {},
        "stage_totals": {
            stage: {"accepted": 0, "rejected": 0} for stage, _, _ in STAGE_KEYS
        },
        "contradiction_input_mode_counts": {},
        "rejection_reason_counts": {},
        "latest_report_path_by_fixture": {},
        "operator_notes_count": 0,
        "safety_flags": _safety_flags(),
    }


def _safety_flags() -> dict[str, bool]:
    return {
        "accepted_graph_writes": False,
        "public_export": False,
        "model_authority": False,
        "raw_response_included": False,
    }


def _fetch_rows(
    conn: sqlite3.Connection,
    *,
    limit: int | None,
    fixture_filter: str | None,
) -> list[sqlite3.Row]:
    query = f"SELECT * FROM {REVIEWED_TABLE}"
    params: list[Any] = []
    clauses: list[str] = []
    if fixture_filter:
        clauses.append("fixture_source LIKE ?")
        params.append(f"%{fixture_filter}%")
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY operator_reviewed_at ASC, id ASC"
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    return list(conn.execute(query, params).fetchall())


def build_scratch_summary(
    *,
    scratch_db: Path | None = None,
    limit: int | None = None,
    fixture_filter: str | None = None,
    allow_empty: bool = False,
) -> dict[str, Any]:
    """Aggregate reviewed scratch rows into a deterministic operator summary."""
    scratch_path = get_scratch_db_path(scratch_db)
    if scratch_path.resolve() == DEFAULT_DB_PATH.resolve():
        raise LiveProbeScratchSummaryError(
            "scratch DB path must not equal the default accepted graph DB"
        )

    if not scratch_path.is_file():
        if allow_empty:
            return empty_summary(
                scratch_db_path=scratch_path,
                allow_empty=True,
                missing_db=True,
            )
        raise LiveProbeScratchSummaryError(f"scratch DB not found: {scratch_path}")

    conn = connect_scratch_readonly(scratch_path)
    try:
        validate_scratch_schema(conn)
        rows = _fetch_rows(conn, limit=limit, fixture_filter=fixture_filter)
    finally:
        conn.close()

    if not rows:
        summary = empty_summary(scratch_db_path=scratch_path)
        summary["allow_empty"] = allow_empty
        return summary

    reports_by_fixture: Counter[str] = Counter()
    contradiction_modes: Counter[str] = Counter()
    rejection_counts: Counter[str] = Counter()
    stage_totals = {
        stage: {"accepted": 0, "rejected": 0} for stage, _, _ in STAGE_KEYS
    }
    latest_by_fixture: dict[str, dict[str, str]] = {}
    operator_notes_count = 0
    floors_passed = 0
    schema_versions: set[str] = set()

    for row in rows:
        fixture = _fixture_name(row["fixture_source"])
        reports_by_fixture[fixture] += 1
        mode = row["contradiction_input_mode"] or "(none)"
        contradiction_modes[str(mode)] += 1
        if int(row["floors_met"] or 0):
            floors_passed += 1
        if row["operator_note"]:
            operator_notes_count += 1
        schema_versions.add(str(row["schema_version"] or SCRATCH_SCHEMA_VERSION))

        for stage, accepted_col, rejected_col in STAGE_KEYS:
            stage_totals[stage]["accepted"] += int(row[accepted_col] or 0)
            stage_totals[stage]["rejected"] += int(row[rejected_col] or 0)

        try:
            diagnostics = json.loads(row["rejection_diagnostics_json"] or "[]")
        except json.JSONDecodeError as exc:
            raise LiveProbeScratchSummaryError(
                "invalid rejection_diagnostics_json in scratch row "
                f"id={row['id']}"
            ) from exc
        if isinstance(diagnostics, list):
            for item in diagnostics:
                rejection_counts[str(item)] += 1

        reviewed_at = str(row["operator_reviewed_at"])
        report_path = str(row["report_rel_path"])
        current = latest_by_fixture.get(fixture)
        if current is None or reviewed_at >= current["operator_reviewed_at"]:
            latest_by_fixture[fixture] = {
                "operator_reviewed_at": reviewed_at,
                "report_rel_path": report_path,
            }

    total = len(rows)
    floors_failed = total - floors_passed
    fixture_pass_rate = round(floors_passed / total, 4) if total else None

    return {
        "report_type": "live_probe_scratch_summary",
        "command": "probe-scratch-summary",
        "status": "ok",
        "scratch_db_path": str(scratch_path).replace("\\", "/"),
        "scratch_db_missing": False,
        "allow_empty": allow_empty,
        "schema_version": sorted(schema_versions)[0] if len(schema_versions) == 1 else sorted(schema_versions),
        "total_reviewed_reports": total,
        "first_reviewed_at": str(rows[0]["operator_reviewed_at"]),
        "last_reviewed_at": str(rows[-1]["operator_reviewed_at"]),
        "floors_passed": floors_passed,
        "floors_failed": floors_failed,
        "fixture_pass_rate": fixture_pass_rate,
        "reports_by_fixture": dict(sorted(reports_by_fixture.items())),
        "stage_totals": stage_totals,
        "contradiction_input_mode_counts": dict(sorted(contradiction_modes.items())),
        "rejection_reason_counts": dict(sorted(rejection_counts.items())),
        "latest_report_path_by_fixture": {
            fixture: payload["report_rel_path"]
            for fixture, payload in sorted(latest_by_fixture.items())
        },
        "operator_notes_count": operator_notes_count,
        "safety_flags": _safety_flags(),
    }


def format_summary_json(summary: dict[str, Any]) -> str:
    return json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def format_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Live probe scratch DB summary",
        "",
        f"- Scratch DB: `{summary.get('scratch_db_path')}`",
        f"- Total reviewed reports: {summary.get('total_reviewed_reports')}",
        f"- First reviewed: {summary.get('first_reviewed_at')}",
        f"- Last reviewed: {summary.get('last_reviewed_at')}",
        f"- Floors passed: {summary.get('floors_passed')}",
        f"- Floors failed: {summary.get('floors_failed')}",
        f"- Fixture pass rate: {summary.get('fixture_pass_rate')}",
        f"- Operator notes count: {summary.get('operator_notes_count')}",
        "",
        "## Safety flags",
    ]
    for key, value in sorted((summary.get("safety_flags") or {}).items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Reports by fixture"])
    for fixture, count in sorted((summary.get("reports_by_fixture") or {}).items()):
        lines.append(f"- {fixture}: {count}")
    lines.extend(["", "## Stage totals"])
    for stage, totals in sorted((summary.get("stage_totals") or {}).items()):
        lines.append(
            f"- {stage}: accepted={totals.get('accepted')}, "
            f"rejected={totals.get('rejected')}"
        )
    lines.extend(["", "## Contradiction input modes"])
    for mode, count in sorted(
        (summary.get("contradiction_input_mode_counts") or {}).items()
    ):
        lines.append(f"- {mode}: {count}")
    lines.extend(["", "## Rejection diagnostics (counts)"])
    for reason, count in sorted(
        (summary.get("rejection_reason_counts") or {}).items()
    ):
        lines.append(f"- {reason}: {count}")
    lines.extend(["", "## Latest report path by fixture"])
    for fixture, path in sorted(
        (summary.get("latest_report_path_by_fixture") or {}).items()
    ):
        lines.append(f"- {fixture}: `{path}`")
    lines.append("")
    return "\n".join(lines)


def run_scratch_summary(
    *,
    scratch_db: Path | None = None,
    limit: int | None = None,
    fixture_filter: str | None = None,
    allow_empty: bool = False,
    output_format: str = "json",
    out_path: Path | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Build summary and optionally write to a private operator path."""
    if output_format not in {"json", "markdown"}:
        raise LiveProbeScratchSummaryError(
            f"unsupported format {output_format!r}; use json or markdown"
        )

    summary = build_scratch_summary(
        scratch_db=scratch_db,
        limit=limit,
        fixture_filter=fixture_filter,
        allow_empty=allow_empty,
    )
    text = (
        format_summary_markdown(summary)
        if output_format == "markdown"
        else format_summary_json(summary)
    )

    base = root if root is not None else repo_root()
    if out_path is not None:
        target = validate_summary_output_path(out_path, base)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        summary["output_path"] = str(
            target.relative_to(base.resolve()).as_posix()
            if target.is_relative_to(base.resolve())
            else target
        ).replace("\\", "/")
    return summary
