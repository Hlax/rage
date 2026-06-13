"""Deterministic operator evidence review composed from scratch DB summary data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rge.modules.live_probe_scratch_summary import (
    LiveProbeScratchSummaryError,
    build_scratch_summary,
    validate_summary_output_path,
)


class LiveProbeEvidenceReviewError(LiveProbeScratchSummaryError):
    """Evidence review failed (validation, I/O)."""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_evidence_review_payload(summary: dict[str, Any]) -> dict[str, Any]:
    """Wrap a scratch summary in an operator/principal evidence review envelope."""
    generated_at = (
        summary.get("last_reviewed_at")
        or summary.get("first_reviewed_at")
        or "1970-01-01T00:00:00+00:00"
    )
    return {
        "report_type": "live_probe_scratch_evidence_review",
        "command": "probe-scratch-evidence-review",
        "status": summary.get("status", "ok"),
        "generated_at": generated_at,
        "generated_from": "probe-scratch-summary",
        "scratch_db_path": summary.get("scratch_db_path"),
        "scratch_db_missing": summary.get("scratch_db_missing", False),
        "allow_empty": summary.get("allow_empty", False),
        "schema_version": summary.get("schema_version"),
        "total_reviewed_reports": summary.get("total_reviewed_reports", 0),
        "first_reviewed_at": summary.get("first_reviewed_at"),
        "last_reviewed_at": summary.get("last_reviewed_at"),
        "floors_passed": summary.get("floors_passed", 0),
        "floors_failed": summary.get("floors_failed", 0),
        "fixture_pass_rate": summary.get("fixture_pass_rate"),
        "reports_by_fixture": summary.get("reports_by_fixture") or {},
        "stage_totals": summary.get("stage_totals") or {},
        "contradiction_input_mode_counts": summary.get(
            "contradiction_input_mode_counts"
        )
        or {},
        "rejection_reason_counts": summary.get("rejection_reason_counts") or {},
        "latest_report_path_by_fixture": summary.get(
            "latest_report_path_by_fixture"
        )
        or {},
        "operator_notes_count": summary.get("operator_notes_count", 0),
        "safety_attestation": summary.get("safety_flags") or {},
        "human_review_required": True,
        "automated_ticket_recommendations": False,
    }


def format_evidence_review_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Live probe scratch evidence review",
        "",
        "Deterministic operator/principal review artifact. "
        "No LLM synthesis. No automated ticket recommendations.",
        "",
        "## Snapshot",
        f"- Generated at: {payload.get('generated_at')}",
        f"- Scratch DB: `{payload.get('scratch_db_path')}`",
        f"- Total reviewed reports: {payload.get('total_reviewed_reports')}",
        f"- Review window: {payload.get('first_reviewed_at')} → "
        f"{payload.get('last_reviewed_at')}",
        f"- Floors passed: {payload.get('floors_passed')}",
        f"- Floors failed: {payload.get('floors_failed')}",
        f"- Fixture pass rate: {payload.get('fixture_pass_rate')}",
        f"- Operator notes count: {payload.get('operator_notes_count')}",
        "",
        "## Safety attestation",
    ]
    for key, value in sorted((payload.get("safety_attestation") or {}).items()):
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Reports by fixture",
        ]
    )
    fixtures = payload.get("reports_by_fixture") or {}
    if fixtures:
        for fixture, count in sorted(fixtures.items()):
            lines.append(f"- {fixture}: {count}")
    else:
        lines.append("- (none)")
    lines.extend(["", "## Stage totals"])
    stages = payload.get("stage_totals") or {}
    if stages:
        for stage, totals in sorted(stages.items()):
            lines.append(
                f"- {stage}: accepted={totals.get('accepted')}, "
                f"rejected={totals.get('rejected')}"
            )
    else:
        lines.append("- (none)")
    lines.extend(["", "## Contradiction input modes"])
    modes = payload.get("contradiction_input_mode_counts") or {}
    if modes:
        for mode, count in sorted(modes.items()):
            lines.append(f"- {mode}: {count}")
    else:
        lines.append("- (none)")
    lines.extend(["", "## Rejection diagnostics (counts)"])
    rejections = payload.get("rejection_reason_counts") or {}
    if rejections:
        for reason, count in sorted(rejections.items()):
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- (none)")
    lines.extend(["", "## Latest report path by fixture"])
    latest = payload.get("latest_report_path_by_fixture") or {}
    if latest:
        for fixture, path in sorted(latest.items()):
            lines.append(f"- {fixture}: `{path}`")
    else:
        lines.append("- (none)")
    lines.extend(
        [
            "",
            "## Human review note",
            "- automated_ticket_recommendations: false",
            "- human_review_required: true",
            "- Operator/principal decides whether to seed improvement tickets.",
            "",
        ]
    )
    return "\n".join(lines)


def format_evidence_review_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def run_evidence_review(
    *,
    scratch_db: Path | None = None,
    limit: int | None = None,
    fixture_filter: str | None = None,
    allow_empty: bool = False,
    output_format: str = "markdown",
    out_path: Path | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Build evidence review from scratch summary; optional private file write."""
    if output_format not in {"json", "markdown"}:
        raise LiveProbeEvidenceReviewError(
            f"unsupported format {output_format!r}; use json or markdown"
        )

    try:
        summary = build_scratch_summary(
            scratch_db=scratch_db,
            limit=limit,
            fixture_filter=fixture_filter,
            allow_empty=allow_empty,
        )
    except LiveProbeScratchSummaryError as exc:
        raise LiveProbeEvidenceReviewError(str(exc)) from exc
    payload = build_evidence_review_payload(summary)
    text = (
        format_evidence_review_json(payload)
        if output_format == "json"
        else format_evidence_review_markdown(payload)
    )

    base = root if root is not None else repo_root()
    if out_path is not None:
        try:
            target = validate_summary_output_path(out_path, base)
        except LiveProbeScratchSummaryError as exc:
            raise LiveProbeEvidenceReviewError(str(exc)) from exc
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        payload["output_path"] = str(
            target.relative_to(base.resolve()).as_posix()
            if target.is_relative_to(base.resolve())
            else target
        ).replace("\\", "/")
    return payload
