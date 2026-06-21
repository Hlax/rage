"""Operator full Atlas refresh checklist: full-cycle validation → sync → build → report.

Chains live abstract evidence quality smoke (optional), fixture operator-packet
refreshes, Atlas-safe artifact validation across the operator-product loop,
trace-summary validation, public-site build, and final status report.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import date
from pathlib import Path
from typing import Any, Callable

from rge.db.connection import ensure_database
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.live_arbitrary_source_health import (
    LIVE_ABSTRACT_EVIDENCE_QUALITY_RUN_ID,
    LIVE_SOURCE_HEALTH_ARTIFACT_NAME,
    LOCAL_SAFE_ARBITRARY_QUESTION,
    assert_live_abstract_evidence_quality_smoke_env,
    run_live_network_abstract_evidence_quality_smoke,
)
from rge.modules.operator_loop import public_site_applicable, resolve_npm_executable
from rge.modules.principal_audit_gate import repo_root

CHECKLIST_ID = "operator-loop-full-atlas-refresh-checklist"
CHECKLIST_TITLE = "Operator Loop Full Atlas Refresh Checklist"
FULL_ATLAS_REFRESH_SCHEMA_VERSION = "atlas_full_atlas_refresh_checklist_v0.1.0"
FULL_ATLAS_REFRESH_ARTIFACT_NAME = "atlas_full_atlas_refresh_checklist_latest.json"

REQUIRED_LIVE_ENV_VARS: tuple[str, ...] = (
    "RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE",
    "RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE",
    "RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE",
    "RGE_ALLOW_SOURCE_NETWORK",
    "OPENALEX_MAILTO",
)

CHECKLIST_STEPS: tuple[str, ...] = (
    "live_abstract_evidence_quality_smoke",
    "atlas_source_health_sync",
    "trace_summary_validation",
    "fixture_operator_packet_refresh",
    "operator_packet_artifact_validation",
    "public_site_build",
    "final_status_report",
)

OPERATOR_PACKET_ARTIFACTS: tuple[dict[str, Any], ...] = (
    {
        "packet_id": "live-source-health",
        "filename": LIVE_SOURCE_HEALTH_ARTIFACT_NAME,
        "schema_version": "atlas_source_health_run_v0.1.0",
        "verdict_field": None,
        "require_trace": True,
        "require_expansion_verdict_when_summary": True,
    },
    {
        "packet_id": "multi-question-live-abstract-runs",
        "filename": "atlas_multi_question_live_abstract_latest.json",
        "schema_version": "atlas_multi_question_live_abstract_v0.1.0",
        "verdict_field": "multi_question_verdict",
        "require_trace": False,
    },
    {
        "packet_id": "local-model-extraction-comparison",
        "filename": "atlas_local_model_extraction_comparison_latest.json",
        "schema_version": "atlas_local_model_extraction_comparison_v0.1.0",
        "verdict_field": "comparison_verdict",
        "require_trace": False,
    },
    {
        "packet_id": "graph-maturity-evidence-atom-upgrade",
        "filename": "atlas_graph_maturity_evidence_atom_upgrade_latest.json",
        "schema_version": "atlas_graph_maturity_evidence_atom_upgrade_v0.1.0",
        "verdict_field": "graph_maturity_verdict",
        "require_trace": False,
    },
    {
        "packet_id": "web-adapter-scrapling-proof",
        "filename": "atlas_web_adapter_scrapling_proof_latest.json",
        "schema_version": "atlas_web_adapter_scrapling_proof_v0.1.0",
        "verdict_field": "web_adapter_verdict",
        "require_trace": False,
    },
    {
        "packet_id": "pdf-tei-milestone",
        "filename": "atlas_pdf_tei_milestone_latest.json",
        "schema_version": "atlas_pdf_tei_milestone_v0.1.0",
        "verdict_field": "pdf_tei_verdict",
        "require_trace": False,
    },
    {
        "packet_id": "demo-loop-polish",
        "filename": "atlas_demo_loop_polish_latest.json",
        "schema_version": "atlas_demo_loop_polish_v0.1.0",
        "verdict_field": "demo_loop_verdict",
        "require_trace": False,
    },
)

FIXTURE_REFRESH_PACKETS: tuple[str, ...] = (
    "web-adapter-scrapling-proof",
    "pdf-tei-milestone",
    "demo-loop-polish",
)

NEXT_RECOMMENDED_PACKET = {
    "id": "multi-question-live-abstract-runs",
    "title": "Multi-Question Live Abstract Runs",
}

PUBLIC_ARTIFACT_REL = (
    "apps/public-site/public/data/" + LIVE_SOURCE_HEALTH_ARTIFACT_NAME
)
PUBLIC_DATA_REL = "apps/public-site/public/data"


def _env_enabled(name: str) -> bool:
    value = os.environ.get(name, "0").strip().casefold()
    return value in {"1", "true", "yes"}


def missing_live_gates() -> dict[str, str]:
    """Return missing or unset live gates; empty dict means all gates satisfied."""
    missing: dict[str, str] = {}
    for name in REQUIRED_LIVE_ENV_VARS:
        if name == "OPENALEX_MAILTO":
            if not os.environ.get(name, "").strip():
                missing[name] = "(set to operator email, e.g. operator@example.com)"
        elif not _env_enabled(name):
            missing[name] = "1"
    return missing


def missing_operator_full_atlas_refresh_gate() -> dict[str, str]:
    if not _env_enabled("RGE_ALLOW_OPERATOR_FULL_ATLAS_REFRESH"):
        return {"RGE_ALLOW_OPERATOR_FULL_ATLAS_REFRESH": "1"}
    return {}


def required_env_setup_commands(*, fixture_only: bool = False) -> list[str]:
    """PowerShell-friendly env setup lines for operator reports."""
    lines = [
        '$env:RGE_ALLOW_OPERATOR_FULL_ATLAS_REFRESH = "1"',
        '$env:RGE_LLM_MODE = "mock"',
    ]
    if not fixture_only:
        lines.extend(
            f'$env:{name} = "{value}"'
            for name, value in (
                ("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE", "1"),
                ("RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE", "1"),
                ("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1"),
                ("RGE_ALLOW_SOURCE_NETWORK", "1"),
                ("OPENALEX_MAILTO", "operator@example.com"),
            )
        )
    lines.append(
        "python scripts/run_full_atlas_refresh_checklist.py"
        + (" --fixture-only" if fixture_only else "")
    )
    return lines


def assert_full_atlas_refresh_env(*, fixture_only: bool = False) -> dict[str, str]:
    """Fail closed unless operator opts into full Atlas refresh checklist."""
    combined = dict(missing_operator_full_atlas_refresh_gate())
    if combined:
        raise RuntimeError(
            "Full Atlas refresh checklist requires RGE_ALLOW_OPERATOR_FULL_ATLAS_REFRESH=1."
        )
    combined["RGE_ALLOW_OPERATOR_FULL_ATLAS_REFRESH"] = "1"
    if fixture_only:
        return combined
    missing = missing_live_gates()
    if missing:
        lines = [f"  {name}={hint}" for name, hint in missing.items()]
        raise RuntimeError(
            "Full Atlas refresh checklist requires explicit live-network opt-in. "
            "Set:\n" + "\n".join(lines)
        )
    combined.update(assert_live_abstract_evidence_quality_smoke_env())
    return combined


def validate_operator_packet_artifact(
    artifact_path: Path,
    spec: dict[str, Any],
) -> dict[str, Any]:
    """Validate one public operator-packet artifact."""
    packet_id = str(spec["packet_id"])
    if not artifact_path.is_file():
        return {
            "packet_id": packet_id,
            "status": "missing",
            "errors": [f"missing file: {spec['filename']}"],
        }
    try:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "packet_id": packet_id,
            "status": "invalid",
            "errors": [f"invalid JSON: {exc}"],
        }
    errors: list[str] = []
    expected_schema = str(spec.get("schema_version") or "")
    if str(artifact.get("schema_version") or "") != expected_schema:
        errors.append(f"schema_version must be {expected_schema!r}")
    if str(artifact.get("status") or "").casefold() == "pending":
        errors.append("status is pending")
    verdict_field = spec.get("verdict_field")
    if verdict_field:
        verdict = str(artifact.get(verdict_field) or "")
        if verdict in {"PENDING", ""}:
            errors.append(f"{verdict_field} is pending or empty")
    if spec.get("require_trace"):
        trace = artifact.get("trace_summary") or {}
        if int(trace.get("trace_count") or 0) < 1:
            errors.append("trace_summary.trace_count must be >= 1")
    if spec.get("require_expansion_verdict_when_summary") and artifact.get(
        "source_expansion_summary"
    ):
        expansion_verdict = str(artifact.get("source_expansion_verdict") or "")
        if expansion_verdict in {"PENDING", ""}:
            errors.append(
                "source_expansion_verdict is pending or empty when "
                "source_expansion_summary is present"
            )
    private_violations = assert_no_private_fields({"artifact": artifact})
    if private_violations:
        errors.extend(private_violations[:3])
    return {
        "packet_id": packet_id,
        "status": "valid" if not errors else "invalid",
        "errors": errors,
        "schema_version": artifact.get("schema_version"),
    }


def validate_all_operator_packet_artifacts(
    *,
    root: Path,
) -> dict[str, Any]:
    """Validate all operator-product loop public artifacts."""
    public_data = root / PUBLIC_DATA_REL
    rows = [
        validate_operator_packet_artifact(public_data / str(spec["filename"]), spec)
        for spec in OPERATOR_PACKET_ARTIFACTS
    ]
    valid_count = sum(1 for row in rows if row["status"] == "valid")
    invalid = [row for row in rows if row["status"] != "valid"]
    if invalid:
        cycle_status = "invalid" if any(r["status"] == "invalid" for r in invalid) else "partial"
    else:
        cycle_status = "valid"
    return {
        "status": cycle_status,
        "valid_count": valid_count,
        "total_count": len(rows),
        "artifacts": rows,
    }


def refresh_fixture_operator_packets(
    *,
    root: Path,
    export_dir: Path,
) -> dict[str, Any]:
    """Refresh mock/fixture operator packets and sync public preview artifacts."""
    os.environ.setdefault("RGE_LLM_MODE", "mock")
    public_data = root / PUBLIC_DATA_REL
    public_data.mkdir(parents=True, exist_ok=True)
    refreshed: dict[str, str] = {}

    os.environ["RGE_ALLOW_WEB_ADAPTER_SCRAPLING_PROOF"] = "1"
    from rge.modules.web_adapter_scrapling_proof import (
        WEB_ADAPTER_ARTIFACT_NAME,
        run_web_adapter_scrapling_with_fresh_db,
        sync_web_adapter_artifact_to_public_site,
    )

    web_result = run_web_adapter_scrapling_with_fresh_db(
        output_dir=export_dir / "web_adapter_scrapling_proof",
    )
    sync_web_adapter_artifact_to_public_site(
        web_result["atlas_safe_artifact"],
        public_path=public_data / WEB_ADAPTER_ARTIFACT_NAME,
    )
    refreshed["web-adapter-scrapling-proof"] = str(web_result["web_adapter_verdict"])

    os.environ["RGE_ALLOW_PDF_TEI_MILESTONE"] = "1"
    from rge.modules.pdf_tei_milestone import (
        PDF_TEI_ARTIFACT_NAME,
        run_pdf_tei_milestone_with_fresh_db,
        sync_pdf_tei_artifact_to_public_site,
    )

    pdf_result = run_pdf_tei_milestone_with_fresh_db(
        output_dir=export_dir / "pdf_tei_milestone",
    )
    sync_pdf_tei_artifact_to_public_site(
        pdf_result["atlas_safe_artifact"],
        public_path=public_data / PDF_TEI_ARTIFACT_NAME,
    )
    refreshed["pdf-tei-milestone"] = str(pdf_result["pdf_tei_verdict"])

    os.environ["RGE_ALLOW_DEMO_LOOP_POLISH"] = "1"
    from rge.modules.demo_loop_polish import (
        DEMO_LOOP_ARTIFACT_NAME,
        run_demo_loop_polish_with_fresh_db,
        sync_demo_loop_artifact_to_public_site,
    )

    demo_result = run_demo_loop_polish_with_fresh_db(
        output_dir=export_dir / "demo_loop_polish",
        persist_claims=True,
    )
    sync_demo_loop_artifact_to_public_site(
        demo_result["atlas_safe_artifact"],
        public_path=public_data / DEMO_LOOP_ARTIFACT_NAME,
    )
    refreshed["demo-loop-polish"] = str(demo_result["demo_loop_verdict"])

    return {
        "status": "completed",
        "refreshed_packets": refreshed,
    }


def _classify_overall_verdict(
    evidence_verdict: str,
    *,
    build_status: str | None,
    packet_validation: dict[str, Any],
) -> str:
    if packet_validation.get("status") == "invalid":
        return "FAIL"
    if evidence_verdict == "NO-GO":
        return "FAIL"
    if evidence_verdict == "PARTIAL":
        return "PARTIAL"
    if packet_validation.get("status") == "partial":
        return "PARTIAL"
    if build_status == "failed":
        return "PARTIAL"
    return "GO"


def build_atlas_safe_checklist_artifact(
    *,
    overall_verdict: str,
    evidence_verdict: str,
    evidence_rationale: str,
    packet_validation: dict[str, Any],
    fixture_refresh: dict[str, Any] | None,
    step_status: dict[str, str],
) -> dict[str, Any]:
    artifact: dict[str, Any] = {
        "schema_version": FULL_ATLAS_REFRESH_SCHEMA_VERSION,
        "status": "completed",
        "packet_id": CHECKLIST_ID,
        "run_id": LIVE_ABSTRACT_EVIDENCE_QUALITY_RUN_ID,
        "full_atlas_refresh_verdict": overall_verdict,
        "full_atlas_refresh_rationale": evidence_rationale,
        "evidence_quality_verdict": evidence_verdict,
        "operator_packet_validation": {
            "status": packet_validation.get("status"),
            "valid_count": packet_validation.get("valid_count"),
            "total_count": packet_validation.get("total_count"),
            "artifacts": [
                {
                    "packet_id": row.get("packet_id"),
                    "status": row.get("status"),
                    "error_count": len(row.get("errors") or []),
                }
                for row in packet_validation.get("artifacts") or []
            ],
        },
        "fixture_refresh_summary": fixture_refresh or {"status": "skipped"},
        "checklist_steps": list(CHECKLIST_STEPS),
        "step_status": step_status,
        "next_recommended_packet": NEXT_RECOMMENDED_PACKET,
    }
    violations = assert_no_private_fields({"artifact": artifact})
    if violations:
        raise ValueError(
            "Full Atlas refresh artifact blocked by private-field policy: "
            + "; ".join(violations[:5])
        )
    return artifact


def _run_public_site_build(
    root: Path,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> dict[str, Any]:
    if not public_site_applicable(root):
        return {"status": "skipped", "reason": "public-site not applicable"}
    npm = resolve_npm_executable()
    if not npm:
        return {"status": "skipped", "reason": "npm not found on PATH"}
    run = runner or subprocess.run
    completed = run(
        [npm, "run", "build"],
        cwd=str(root / "apps" / "public-site"),
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "status": "completed" if completed.returncode == 0 else "failed",
        "exit_code": completed.returncode,
        "shell": "cd apps/public-site && npm run build",
    }


def run_full_atlas_refresh_checklist(
    *,
    root: Path | None = None,
    output_dir: Path | None = None,
    public_artifact_path: Path | None = None,
    build_site: bool = True,
    skip_site: bool = False,
    fixture_only: bool = False,
    refresh_fixture_packets: bool = True,
    question: str = LOCAL_SAFE_ARBITRARY_QUESTION,
    command_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> dict[str, Any]:
    """Execute the full operator Atlas refresh checklist."""
    project_root = root or repo_root()
    gates = assert_full_atlas_refresh_env(fixture_only=fixture_only)
    os.environ.setdefault("RGE_LLM_MODE", "mock")

    export_dir = output_dir or (project_root / "data" / "exports" / "full_atlas_refresh")
    export_dir.mkdir(parents=True, exist_ok=True)
    public_path = public_artifact_path or (project_root / PUBLIC_ARTIFACT_REL)
    public_data = project_root / PUBLIC_DATA_REL

    from scripts.refresh_atlas_source_health_preview import (
        refresh_public_source_health_preview,
        validate_source_health_artifact,
    )

    step_status: dict[str, str] = {}
    smoke_result: dict[str, Any] = {}
    evidence_verdict = "SKIPPED"
    evidence_rationale = "Live smoke skipped (--fixture-only)."

    if fixture_only:
        step_status["live_abstract_evidence_quality_smoke"] = "skipped"
        step_status["atlas_source_health_sync"] = "skipped"
        if public_path.is_file():
            step_status["trace_summary_validation"] = "completed"
        else:
            step_status["trace_summary_validation"] = "skipped"
    else:
        db_path = export_dir / "full_atlas_refresh.sqlite"
        conn = ensure_database(db_path)
        try:
            smoke_result = run_live_network_abstract_evidence_quality_smoke(
                conn,
                question=question,
                output_dir=export_dir,
            )
            step_status["live_abstract_evidence_quality_smoke"] = "completed"
        finally:
            conn.close()

        artifact_path = Path(smoke_result.get("artifact_path") or "")
        if not artifact_path.is_file():
            raise RuntimeError(
                "Live abstract evidence quality smoke did not write "
                f"{LIVE_SOURCE_HEALTH_ARTIFACT_NAME}."
            )

        sync_result = refresh_public_source_health_preview(
            input_path=artifact_path,
            output_path=public_path,
            require_trace_summary=True,
        )
        step_status["atlas_source_health_sync"] = sync_result["status"]

        artifact = json.loads(public_path.read_text(encoding="utf-8"))
        validation_errors = validate_source_health_artifact(
            artifact,
            require_trace_summary=True,
        )
        if validation_errors:
            raise ValueError(
                "Trace-summary validation failed: " + "; ".join(validation_errors)
            )
        step_status["trace_summary_validation"] = "completed"
        evidence_verdict = str(smoke_result.get("evidence_quality_verdict") or "NO-GO")
        evidence_rationale = str(smoke_result.get("evidence_quality_rationale") or "")

    fixture_refresh: dict[str, Any] | None = None
    if refresh_fixture_packets:
        fixture_refresh = refresh_fixture_operator_packets(
            root=project_root,
            export_dir=export_dir,
        )
        step_status["fixture_operator_packet_refresh"] = fixture_refresh["status"]
    else:
        step_status["fixture_operator_packet_refresh"] = "skipped"

    packet_validation = validate_all_operator_packet_artifacts(root=project_root)
    step_status["operator_packet_artifact_validation"] = packet_validation["status"]

    build_result: dict[str, Any] | None = None
    if skip_site:
        step_status["public_site_build"] = "skipped"
        build_result = {"status": "skipped", "reason": "--skip-site"}
    elif build_site:
        build_result = _run_public_site_build(project_root, runner=command_runner)
        step_status["public_site_build"] = build_result["status"]
    else:
        step_status["public_site_build"] = "skipped"
        build_result = {"status": "skipped", "reason": "build_site=False"}

    overall_verdict = _classify_overall_verdict(
        evidence_verdict,
        build_status=build_result.get("status") if build_result else None,
        packet_validation=packet_validation,
    )

    if not evidence_rationale or evidence_rationale == "Live smoke skipped (--fixture-only).":
        if overall_verdict == "GO":
            evidence_rationale = (
                f"Full-cycle validation passed for {packet_validation.get('valid_count')} "
                f"of {packet_validation.get('total_count')} operator packet artifacts."
            )

    checklist_artifact = build_atlas_safe_checklist_artifact(
        overall_verdict=overall_verdict,
        evidence_verdict=evidence_verdict,
        evidence_rationale=evidence_rationale,
        packet_validation=packet_validation,
        fixture_refresh=fixture_refresh,
        step_status=step_status,
    )
    checklist_path = public_data / FULL_ATLAS_REFRESH_ARTIFACT_NAME
    checklist_path.write_text(json.dumps(checklist_artifact, indent=2), encoding="utf-8")

    quality_summary = dict(smoke_result.get("evidence_quality_summary") or {})
    source_artifact = {}
    if public_path.is_file():
        source_artifact = json.loads(public_path.read_text(encoding="utf-8"))

    report = {
        "report_type": "operator_full_atlas_refresh_checklist",
        "checklist_id": CHECKLIST_ID,
        "date": date.today().isoformat(),
        "overall_verdict": overall_verdict,
        "evidence_quality_verdict": evidence_verdict,
        "evidence_quality_rationale": evidence_rationale,
        "test_question": question,
        "fixture_only": fixture_only,
        "llm_mode": os.environ.get("RGE_LLM_MODE", "mock"),
        "live_gates": gates,
        "checklist_steps": list(CHECKLIST_STEPS),
        "step_status": step_status,
        "live_run_summary": quality_summary,
        "operator_packet_validation": packet_validation,
        "fixture_refresh_summary": fixture_refresh,
        "operator_export_path": str(export_dir.relative_to(project_root)).replace("\\", "/"),
        "public_artifact": str(public_path.relative_to(project_root)).replace("\\", "/"),
        "checklist_artifact": str(checklist_path.relative_to(project_root)).replace("\\", "/"),
        "run_id": LIVE_ABSTRACT_EVIDENCE_QUALITY_RUN_ID,
        "atlas_artifact_public_safe": assert_no_private_fields({"artifact": source_artifact})
        == [],
        "public_site_build": build_result,
        "atlas_preview_ready": overall_verdict in {"GO", "PARTIAL"},
        "next_recommended_packet": NEXT_RECOMMENDED_PACKET,
    }
    step_status["final_status_report"] = "completed"
    return report


def write_checklist_reports(
    report: dict[str, Any],
    *,
    root: Path | None = None,
) -> dict[str, str]:
    """Write markdown + JSON operator reports under agent_reports/."""
    project_root = root or repo_root()
    reports_dir = project_root / "agent_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    day = report.get("date") or date.today().isoformat()
    slug = "operator-full-atlas-refresh-checklist"
    md_path = reports_dir / f"{day}_{slug}.md"
    json_path = reports_dir / f"{day}_{slug}-latest.json"

    summary = report.get("live_run_summary") or {}
    trace = summary.get("trace_summary") or {}
    packet_validation = report.get("operator_packet_validation") or {}
    lines = [
        f"# {CHECKLIST_TITLE}",
        "",
        f"**Date:** {day}",
        f"**Overall verdict:** {report.get('overall_verdict')}",
        f"**Evidence quality:** {report.get('evidence_quality_verdict')}",
        f"**Fixture-only mode:** {report.get('fixture_only', False)}",
        "",
        "## Question",
        "",
        str(report.get("test_question") or ""),
        "",
        "## Live run summary",
        "",
        "| Signal | Count |",
        "| --- | ---: |",
        f"| Live source count | {summary.get('live_source_count', 0)} |",
        f"| Abstract availability | {summary.get('abstract_availability_count', 0)} |",
        f"| Claims accepted | {summary.get('claims_accepted', 0)} |",
        f"| Claims rejected | {summary.get('claims_rejected', 0)} |",
        f"| Purpose-fit counts | {json.dumps(summary.get('purpose_fit_status_counts') or {})} |",
        f"| Evidence atoms | {summary.get('evidence_atom_count', 0)} |",
        f"| Relationships | {summary.get('relationship_count', 0)} |",
        f"| Trace summary rows | {trace.get('preview_row_count', 0)} |",
        "",
        "## Operator packet validation",
        "",
        f"- Valid artifacts: **{packet_validation.get('valid_count', 0)}** / "
        f"{packet_validation.get('total_count', 0)}",
        "",
    ]
    for row in packet_validation.get("artifacts") or []:
        lines.append(f"- `{row.get('packet_id')}`: **{row.get('status')}**")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Source health artifact: `{report.get('public_artifact')}`",
            f"- Checklist artifact: `{report.get('checklist_artifact')}`",
            f"- Operator export: `{report.get('operator_export_path')}`",
            "",
            "## Checklist steps",
            "",
        ]
    )
    for step in CHECKLIST_STEPS:
        status = (report.get("step_status") or {}).get(step, "pending")
        lines.append(f"- {step}: **{status}**")
    lines.extend(
        [
            "",
            "## Next recommended packet",
            "",
            f"- **{NEXT_RECOMMENDED_PACKET['title']}** (`{NEXT_RECOMMENDED_PACKET['id']}`)",
            "",
            "## Operator command",
            "",
            "```powershell",
            '$env:RGE_ALLOW_OPERATOR_FULL_ATLAS_REFRESH = "1"',
            "python scripts/run_full_atlas_refresh_checklist.py --fixture-only",
            "```",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {"markdown": str(md_path), "json": str(json_path)}


def inspect_full_atlas_refresh_checklist_status(
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Read-only full Atlas refresh checklist readiness for operator plan mode."""
    project_root = root or repo_root()
    atlas = _import_atlas_refresh_status(project_root)
    live_abstract_work = _live_abstract_evidence_quality_work_detected(root=project_root)
    source_health_stale = (
        "atlas_source_health_run_latest" in (atlas.get("missing_outputs") or [])
        or any(
            "atlas_source_health_run_latest" in reason
            for reason in (atlas.get("refresh_reasons") or [])
        )
    )
    packet_validation = validate_all_operator_packet_artifacts(root=project_root)
    gates_missing = bool(missing_live_gates()) or bool(
        missing_operator_full_atlas_refresh_gate()
    )
    return {
        "status": "available",
        "checklist_id": CHECKLIST_ID,
        "live_abstract_evidence_work_detected": live_abstract_work,
        "source_health_stale": source_health_stale,
        "operator_packet_validation": packet_validation,
        "full_atlas_refresh_recommended": live_abstract_work and source_health_stale,
        "gates_set": not gates_missing,
        "missing_gates": {
            **missing_operator_full_atlas_refresh_gate(),
            **missing_live_gates(),
        },
        "operator_command": "python scripts/run_full_atlas_refresh_checklist.py",
        "env_setup": required_env_setup_commands(),
        "checklist_steps": list(CHECKLIST_STEPS),
    }


def _import_atlas_refresh_status(project_root: Path) -> dict[str, Any]:
    from rge.modules.operator_loop import inspect_atlas_preview_refresh_status

    return inspect_atlas_preview_refresh_status(root=project_root)


def _live_abstract_evidence_quality_work_detected(*, root: Path) -> bool:
    reports_dir = root / "agent_reports"
    if not reports_dir.is_dir():
        return False
    from rge.modules.operator_loop import _REPORT_NAME_RE

    markers = (
        "abstract-evidence-quality",
        "live-abstract-evidence-quality",
        "live-abstract-evidence-atom-trace",
        "abstract-evidence-atom-trace",
        "demo-loop-polish",
        "pdf-tei-milestone",
        "web-adapter-scrapling",
    )
    for path in sorted(reports_dir.glob("*.md")):
        if not _REPORT_NAME_RE.match(path.name):
            continue
        lowered = path.name.casefold().replace("_", "-")
        if any(marker in lowered for marker in markers):
            return True
    return False
