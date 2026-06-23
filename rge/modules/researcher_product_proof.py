"""End-to-end mock-first researcher product proof (ticket-381)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from rge.db.connection import connect, get_db_path
from rge.modules.autonomous_synthesis_governor import (
    _private_value_violations,
    _safe_rel,
    utc_now_iso,
)
from rge.modules.operator_proof_bundle import execute_arbitrary_source_proof_bundle
from rge.modules.principal_audit_gate import repo_root
from rge.modules.safety_auditor import run_safety_audit
from rge.modules.synthesis_packet_benchmark import (
    DEFAULT_RUNS as DEFAULT_BENCHMARK_RUNS,
    run_synthesis_packet_benchmark,
)
from rge.modules.synthesis_packet_runner import (
    GROUNDED_PACKET_FIXTURE_REL,
    run_synthesis_packet,
)

PRODUCT_PROOF_SCHEMA_VERSION = "researcher_product_proof_v0.1.0"
COMMAND = "prove-researcher-product"
DEFAULT_ARTIFACT_REL = Path("data/reports/researcher_product_proof_latest.json")
DEFAULT_WORK_DIR_REL = Path("data/tmp/researcher_product_proof_work")
DEFAULT_TOPIC = "Does AI improve creative output while reducing diversity?"
DEFAULT_DOMAIN = "creativity"
PUBLIC_ATLAS_PREVIEW_REL = Path("apps/public-site/public/data/atlas_snapshot_preview.json")
PUBLIC_ATLAS_COHERENCE_REL = Path("apps/public-site/public/data/atlas_coherence_preview.json")

ProofBundleRunner = Callable[..., dict[str, Any]]
SynthesisRunner = Callable[..., dict[str, Any]]
BenchmarkRunner = Callable[..., dict[str, Any]]
SafetyAuditRunner = Callable[..., dict[str, Any]]


def _operator_safe_path(path: Path, root: Path) -> str:
    """Return repo-relative path or a scratch-safe token without local absolute paths."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        if len(path.parts) >= 2:
            return f"scratch/{path.parts[-2]}/{path.name}"
        return f"scratch/{path.name}"


def default_artifact_path(*, root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_ARTIFACT_REL


PRODUCT_PROOF_OPERATOR_COMMAND = (
    "python -m rge.cli prove-researcher-product "
    f"--work-dir {DEFAULT_WORK_DIR_REL.as_posix()} "
    f"--artifact-out {DEFAULT_ARTIFACT_REL.as_posix()} "
    f"--benchmark-runs {DEFAULT_BENCHMARK_RUNS}"
)


def load_product_proof_artifact(
    *,
    root: Path | None = None,
    artifact_path: Path | str | None = None,
) -> dict[str, Any] | None:
    project_root = root or repo_root()
    resolved = Path(artifact_path) if artifact_path else default_artifact_path(root=project_root)
    if not resolved.is_file():
        return None
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _product_drift_warning_active(audit: dict[str, Any]) -> bool:
    warnings = audit.get("drift_warning") or []
    return any(
        token in warning.lower()
        for warning in warnings
        for token in ("product", "live-research", "arbitrary-source")
    )


def inspect_researcher_product_proof_plan_status(
    *,
    root: Path | None = None,
    audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Read-only researcher product proof readiness for operator plan mode."""
    project_root = root or repo_root()
    artifact_path = default_artifact_path(root=project_root)
    rel_artifact = _safe_rel(artifact_path, project_root)
    payload = load_product_proof_artifact(root=project_root, artifact_path=artifact_path)
    product_verdict = payload.get("product_verdict") if payload else None
    audit_payload = audit or {}
    recommended = _product_drift_warning_active(audit_payload) and payload is None
    if payload is None:
        status = "missing"
    else:
        status = "available"
    benchmark = (payload or {}).get("benchmark") or {}
    return {
        "status": status,
        "command": COMMAND,
        "mock_llm_only": True,
        "requires_temp_work_dir": True,
        "product_proof_recommended": recommended,
        "artifact_path": rel_artifact,
        "product_verdict": product_verdict,
        "source_count": payload.get("source_count") if payload else None,
        "claim_count": payload.get("claim_count") if payload else None,
        "evidence_count": payload.get("evidence_count") if payload else None,
        "reports_per_hour_estimate": benchmark.get("reports_per_hour_estimate"),
        "synthesis_output_path": ((payload or {}).get("synthesis") or {}).get(
            "synthesis_output_path"
        ),
        "operator_commands": {
            "product_proof": PRODUCT_PROOF_OPERATOR_COMMAND,
        },
        "env_setup": ['$env:RGE_LLM_MODE = "mock"'],
    }


def collect_db_graph_counts(conn: Any, *, source_id: str | None = None) -> dict[str, int]:
    """Collect source, claim, and relationship-evidence counts for product proof."""
    source_count = int(conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0])
    if source_id:
        claim_count = int(
            conn.execute(
                "SELECT COUNT(*) FROM claims WHERE source_id = ?",
                (source_id,),
            ).fetchone()[0]
        )
        evidence_count = int(
            conn.execute(
                """
                SELECT COUNT(*) FROM relationship_evidence re
                JOIN claims c ON c.id = re.claim_id
                WHERE c.source_id = ?
                """,
                (source_id,),
            ).fetchone()[0]
        )
    else:
        claim_count = int(conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0])
        evidence_count = int(
            conn.execute("SELECT COUNT(*) FROM relationship_evidence").fetchone()[0]
        )
    return {
        "source_count": source_count,
        "claim_count": claim_count,
        "evidence_count": evidence_count,
    }


def inspect_atlas_preview_visibility(*, root: Path | None = None) -> dict[str, Any]:
    """Read-only check that committed public atlas preview fixtures are present."""
    project_root = root or repo_root()
    snapshot_path = project_root / PUBLIC_ATLAS_PREVIEW_REL
    coherence_path = project_root / PUBLIC_ATLAS_COHERENCE_REL
    snapshot_visible = snapshot_path.is_file()
    coherence_visible = coherence_path.is_file()
    snapshot_id: str | None = None
    cluster_count: int | None = None
    if snapshot_visible:
        try:
            payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                snapshot_id = payload.get("snapshot_id")
                clusters = payload.get("clusters")
                if isinstance(clusters, list):
                    cluster_count = len(clusters)
        except (OSError, json.JSONDecodeError):
            snapshot_visible = False
    return {
        "public_preview_visible": snapshot_visible and coherence_visible,
        "atlas_snapshot_preview_path": _safe_rel(snapshot_path, project_root),
        "atlas_coherence_preview_path": _safe_rel(coherence_path, project_root),
        "snapshot_id": snapshot_id,
        "cluster_count": cluster_count,
    }


def compute_product_verdict(
    *,
    proof_bundle: dict[str, Any],
    synthesis: dict[str, Any],
    benchmark: dict[str, Any],
    safety: dict[str, Any],
    atlas_preview: dict[str, Any],
) -> str:
    """Return GO, PARTIAL, or NO-GO for the chained product proof."""
    critical_failures = 0
    partial_signals = 0

    if proof_bundle.get("status") != "completed" or not proof_bundle.get("usable_output"):
        critical_failures += 1
    if synthesis.get("status") != "completed":
        critical_failures += 1
    if not synthesis.get("no_accepted_graph_writes", True):
        critical_failures += 1
    if safety.get("status") != "pass":
        critical_failures += 1

    if critical_failures:
        return "NO-GO"

    if not benchmark.get("reports_per_hour_estimate"):
        partial_signals += 1
    if not atlas_preview.get("public_preview_visible"):
        partial_signals += 1
    if benchmark.get("cloud_call_made_any"):
        partial_signals += 1

    return "PARTIAL" if partial_signals else "GO"


def build_product_proof_artifact(
    *,
    proof_bundle: dict[str, Any],
    graph_counts: dict[str, int],
    synthesis: dict[str, Any],
    benchmark: dict[str, Any],
    safety: dict[str, Any],
    atlas_preview: dict[str, Any],
    work_dir: Path,
    database_path: Path,
    benchmark_artifact_path: Path | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = root or repo_root()
    product_verdict = compute_product_verdict(
        proof_bundle=proof_bundle,
        synthesis=synthesis,
        benchmark=benchmark,
        safety=safety,
        atlas_preview=atlas_preview,
    )
    bundle_path = proof_bundle.get("bundle_path")
    safe_bundle_path = (
        _operator_safe_path(Path(str(bundle_path)), project_root)
        if bundle_path
        else None
    )
    return {
        "schema_version": PRODUCT_PROOF_SCHEMA_VERSION,
        "status": "completed" if product_verdict != "NO-GO" else "error",
        "command": COMMAND,
        "product_verdict": product_verdict,
        "mock_llm_only": True,
        "live_openai_used": False,
        "source_count": graph_counts["source_count"],
        "claim_count": graph_counts["claim_count"],
        "evidence_count": graph_counts["evidence_count"],
        "proof_bundle": {
            "status": proof_bundle.get("status"),
            "usable_output": proof_bundle.get("usable_output"),
            "source_id": proof_bundle.get("source_id"),
            "pipeline_mode": proof_bundle.get("pipeline_mode"),
            "bundle_path": safe_bundle_path,
        },
        "synthesis": {
            "status": synthesis.get("status"),
            "provider": synthesis.get("provider"),
            "packet_id": synthesis.get("packet_id"),
            "synthesis_output_path": synthesis.get("output_path"),
            "no_accepted_graph_writes": synthesis.get("no_accepted_graph_writes", True),
        },
        "benchmark": {
            "runs_completed": benchmark.get("runs_completed"),
            "reports_per_hour_estimate": benchmark.get("reports_per_hour_estimate"),
            "artifact_path": (
                _operator_safe_path(benchmark_artifact_path, project_root)
                if benchmark_artifact_path
                else None
            ),
            "cloud_call_made_any": benchmark.get("cloud_call_made_any"),
        },
        "safety_audit": {
            "status": safety.get("status"),
            "audit_type": safety.get("audit_type"),
            "scan_scope": {
                "checked_routes": len(safety.get("checked_routes") or []),
                "checked_exports": len(safety.get("checked_exports") or []),
                "checked_secrets": len(safety.get("checked_secrets") or []),
                "checked_files": len(safety.get("checked_files") or []),
            },
            "blocked_reason_count": len(safety.get("blocked_reasons") or []),
        },
        "atlas_preview": atlas_preview,
        "work_dir": _operator_safe_path(work_dir, project_root),
        "database_path": _operator_safe_path(database_path, project_root),
        "completed_at": utc_now_iso(),
    }


def write_product_proof_artifact(
    artifact: dict[str, Any],
    *,
    root: Path | None = None,
    artifact_path: Path | str | None = None,
) -> Path:
    project_root = root or repo_root()
    resolved = Path(artifact_path) if artifact_path else default_artifact_path(root=project_root)
    if not resolved.is_absolute():
        resolved = project_root / resolved
    payload = dict(artifact)
    payload["artifact_written_at"] = utc_now_iso()
    violations = _private_value_violations(payload, label="researcher_product_proof_artifact")
    if violations:
        raise RuntimeError(
            "Product proof artifact blocked by private-field policy: "
            + "; ".join(violations[:5])
        )
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return resolved


def run_researcher_product_proof(
    *,
    topic: str = DEFAULT_TOPIC,
    domain: str = DEFAULT_DOMAIN,
    work_dir: Path,
    root: Path | None = None,
    benchmark_runs: int = DEFAULT_BENCHMARK_RUNS,
    write_artifact: bool = True,
    artifact_path: Path | str | None = None,
    run_proof_bundle: ProofBundleRunner | None = None,
    run_synthesis: SynthesisRunner | None = None,
    run_benchmark: BenchmarkRunner | None = None,
    run_safety: SafetyAuditRunner | None = None,
) -> dict[str, Any]:
    """Chain mock arbitrary-source proof, synthesis packet, benchmark, and safety audit."""
    project_root = root or repo_root()
    resolved_work = work_dir if work_dir.is_absolute() else project_root / work_dir
    resolved_work.mkdir(parents=True, exist_ok=True)

    db_path = resolved_work / "researcher_product_proof.sqlite"
    report_dir = resolved_work / "reports"
    staging_dir = resolved_work / "staged"
    export_dir = resolved_work / "export"
    synthesis_out = resolved_work / "synthesis_packets"
    benchmark_out = resolved_work / "benchmark_out"
    bundle_out = resolved_work / "proof_bundle.json"
    benchmark_artifact = resolved_work / "synthesis_packet_benchmark.json"

    proof_runner = run_proof_bundle or execute_arbitrary_source_proof_bundle
    synthesis_runner = run_synthesis or run_synthesis_packet
    benchmark_runner = run_benchmark or run_synthesis_packet_benchmark
    safety_runner = run_safety or run_safety_audit

    proof_bundle = proof_runner(
        topic=topic,
        domain=domain,
        db_path=db_path,
        report_dir=report_dir,
        staging_dir=staging_dir,
        export_dir=export_dir,
        bundle_out=bundle_out,
        repo_root=project_root,
    )
    resolved_db = get_db_path(db_path)
    if proof_bundle.get("status") != "completed":
        artifact = {
            "schema_version": PRODUCT_PROOF_SCHEMA_VERSION,
            "status": "error",
            "command": COMMAND,
            "product_verdict": "NO-GO",
            "failed_step": "proof_bundle",
            "detail": proof_bundle.get("detail") or proof_bundle.get("failed_step"),
            "proof_bundle": {
                "status": proof_bundle.get("status"),
                "usable_output": proof_bundle.get("usable_output"),
            },
            "work_dir": _operator_safe_path(resolved_work, project_root),
            "database_path": _operator_safe_path(resolved_db, project_root),
            "completed_at": utc_now_iso(),
        }
        if write_artifact:
            out = write_product_proof_artifact(
                artifact,
                root=project_root,
                artifact_path=artifact_path,
            )
            artifact["artifact_path"] = _safe_rel(out, project_root)
        return artifact

    conn = connect(resolved_db)
    try:
        graph_counts = collect_db_graph_counts(
            conn,
            source_id=str(proof_bundle.get("source_id") or ""),
        )
    finally:
        conn.close()

    packet_path = project_root / GROUNDED_PACKET_FIXTURE_REL
    synthesis = synthesis_runner(
        packet_path=packet_path,
        provider="mock_cloud",
        output_dir=synthesis_out,
        root=project_root,
        evaluate_governor=False,
    )
    if synthesis.get("status") != "completed" or not synthesis.get(
        "no_accepted_graph_writes", True
    ):
        artifact = build_product_proof_artifact(
            proof_bundle=proof_bundle,
            graph_counts=graph_counts,
            synthesis=synthesis,
            benchmark={"reports_per_hour_estimate": 0},
            safety={"status": "skipped", "audit_type": "full"},
            atlas_preview=inspect_atlas_preview_visibility(root=project_root),
            work_dir=resolved_work,
            database_path=resolved_db,
            root=project_root,
        )
        artifact["status"] = "error"
        artifact["product_verdict"] = "NO-GO"
        artifact["failed_step"] = "synthesis_packet"
        artifact["detail"] = synthesis.get("detail") or synthesis.get("status")
        if write_artifact:
            out = write_product_proof_artifact(
                artifact,
                root=project_root,
                artifact_path=artifact_path,
            )
            artifact["artifact_path"] = _safe_rel(out, project_root)
        return artifact

    benchmark = benchmark_runner(
        packet_path=packet_path,
        runs=benchmark_runs,
        provider="mock_cloud",
        output_dir=benchmark_out,
        root=project_root,
        write_artifact=True,
        artifact_path=benchmark_artifact,
    )
    safety = safety_runner("full", root=project_root)
    atlas_preview = inspect_atlas_preview_visibility(root=project_root)

    artifact = build_product_proof_artifact(
        proof_bundle=proof_bundle,
        graph_counts=graph_counts,
        synthesis=synthesis,
        benchmark=benchmark,
        safety=safety,
        atlas_preview=atlas_preview,
        work_dir=resolved_work,
        database_path=resolved_db,
        benchmark_artifact_path=benchmark_artifact,
        root=project_root,
    )
    if write_artifact:
        out = write_product_proof_artifact(
            artifact,
            root=project_root,
            artifact_path=artifact_path,
        )
        artifact["artifact_path"] = _safe_rel(out, project_root)
    return artifact


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="scripts/run_researcher_product_proof.py",
        description="Run mock-first researcher product proof and write operator artifact.",
    )
    parser.add_argument(
        "--work-dir",
        default=str(DEFAULT_ARTIFACT_REL.parent / "researcher_product_proof_work"),
        help="Scratch work directory (temp paths only).",
    )
    parser.add_argument(
        "--artifact-out",
        default=str(DEFAULT_ARTIFACT_REL),
        help="Gitignored product proof artifact path.",
    )
    parser.add_argument(
        "--topic",
        default=DEFAULT_TOPIC,
        help="Research topic for proof bundle staged spine.",
    )
    parser.add_argument(
        "--domain",
        default=DEFAULT_DOMAIN,
        help="Domain pack id.",
    )
    parser.add_argument(
        "--benchmark-runs",
        type=int,
        default=DEFAULT_BENCHMARK_RUNS,
        help="Synthesis packet benchmark repeat count.",
    )
    parser.add_argument(
        "--no-write-artifact",
        action="store_true",
        help="Skip writing gitignored product proof artifact.",
    )
    args = parser.parse_args(argv)
    result = run_researcher_product_proof(
        topic=args.topic,
        domain=args.domain,
        work_dir=Path(args.work_dir),
        benchmark_runs=args.benchmark_runs,
        write_artifact=not args.no_write_artifact,
        artifact_path=Path(args.artifact_out),
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("product_verdict") in {"GO", "PARTIAL"} else 1
