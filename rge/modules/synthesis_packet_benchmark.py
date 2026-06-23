"""Repeated mock-first synthesis packet runs for throughput and review-cadence dry runs."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from rge.llm.cloud_synthesis_providers import normalize_provider_id
from rge.modules.autonomous_synthesis_governor import (
    _private_value_violations,
    _safe_rel,
    utc_now_iso,
)
from rge.modules.principal_audit_gate import repo_root
from rge.modules.synthesis_packet_runner import (
    GROUNDED_PACKET_FIXTURE_REL,
    run_synthesis_packet,
)
from rge.modules.synthesis_review_threshold_policy import evaluate_synthesis_review_threshold

BENCHMARK_SCHEMA_VERSION = "synthesis_packet_benchmark_v0.1.0"
DEFAULT_RUNS = 25
DEFAULT_BENCHMARK_ARTIFACT_REL = Path("data/reports/synthesis_packet_benchmark_latest.json")
SYNTHESIS_PACKET_CLI_BRANCH_MARKERS = (
    "cloud-synthesis-packet",
    "synthesis-packet-cli",
)
BENCHMARK_OPERATOR_COMMAND = (
    "python scripts/run_synthesis_packet_benchmark.py "
    f"--packet {GROUNDED_PACKET_FIXTURE_REL.as_posix()} --runs {DEFAULT_RUNS}"
)


def _round3(value: float) -> float:
    return round(value, 3)


def estimate_reports_per_hour(*, runs_completed: int, total_elapsed_seconds: float) -> float:
    """Deterministic throughput estimate: completed reports per wall-clock hour."""
    if runs_completed <= 0 or total_elapsed_seconds <= 0:
        return 0.0
    return _round3((runs_completed / total_elapsed_seconds) * 3600.0)


def aggregate_throughput_counters(runs: list[dict[str, Any]]) -> dict[str, int]:
    totals = {
        "claim_count": 0,
        "concept_link_count": 0,
        "relationship_count": 0,
        "qualification_count": 0,
    }
    for run in runs:
        throughput = run.get("throughput") or {}
        for key in totals:
            totals[key] += int(throughput.get(key) or 0)
    return totals


def build_cumulative_throughput(
    *,
    runs_completed: int,
    counters: dict[str, int],
) -> dict[str, Any]:
    return {
        "reports_completed": runs_completed,
        "claim_count": int(counters.get("claim_count") or 0),
        "concept_link_count": int(counters.get("concept_link_count") or 0),
        "relationship_count": int(counters.get("relationship_count") or 0),
        "qualification_count": int(counters.get("qualification_count") or 0),
    }


def is_synthesis_packet_cli_branch(branch: str | None) -> bool:
    if not branch:
        return False
    return any(marker in branch for marker in SYNTHESIS_PACKET_CLI_BRANCH_MARKERS)


def synthesis_packet_cli_wired(*, root: Path | None = None) -> bool:
    project_root = root or repo_root()
    runner_path = project_root / "rge" / "modules" / "synthesis_packet_runner.py"
    cli_path = project_root / "rge" / "cli.py"
    if not runner_path.is_file() or not cli_path.is_file():
        return False
    try:
        cli_text = cli_path.read_text(encoding="utf-8")
    except OSError:
        return False
    return '"synthesize"' in cli_text or "'synthesize'" in cli_text


def default_benchmark_artifact_path(*, root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_BENCHMARK_ARTIFACT_REL


def load_benchmark_artifact(
    *,
    root: Path | None = None,
    artifact_path: Path | str | None = None,
) -> dict[str, Any] | None:
    project_root = root or repo_root()
    resolved = Path(artifact_path) if artifact_path else default_benchmark_artifact_path(root=project_root)
    if not resolved.is_file():
        return None
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def write_benchmark_artifact(
    summary: dict[str, Any],
    *,
    root: Path | None = None,
    artifact_path: Path | str | None = None,
) -> Path:
    project_root = root or repo_root()
    resolved = Path(artifact_path) if artifact_path else default_benchmark_artifact_path(root=project_root)
    if not resolved.is_absolute():
        resolved = project_root / resolved
    payload = dict(summary)
    payload["artifact_written_at"] = utc_now_iso()
    violations = _private_value_violations(payload, label="synthesis_packet_benchmark_artifact")
    if violations:
        raise RuntimeError(
            "Benchmark artifact blocked by private-field policy: " + "; ".join(violations[:5])
        )
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return resolved


def inspect_synthesis_packet_benchmark_plan_status(
    *,
    root: Path | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    """Read benchmark artifact for operator plan when synthesis packet CLI branch is active."""
    project_root = root or repo_root()
    active_branch_match = is_synthesis_packet_cli_branch(branch)
    cli_wired = synthesis_packet_cli_wired(root=project_root)
    artifact_path = default_benchmark_artifact_path(root=project_root)
    rel_artifact = _safe_rel(artifact_path, project_root)

    if not active_branch_match or not cli_wired:
        return {
            "status": "not_applicable",
            "active_branch_match": active_branch_match,
            "cli_wired": cli_wired,
            "artifact_path": rel_artifact,
            "reports_per_hour_estimate": None,
            "benchmark_recommended": False,
        }

    payload = load_benchmark_artifact(root=project_root, artifact_path=artifact_path)
    if payload is None:
        return {
            "status": "missing",
            "active_branch_match": True,
            "cli_wired": True,
            "artifact_path": rel_artifact,
            "reports_per_hour_estimate": None,
            "benchmark_recommended": True,
            "operator_commands": {
                "benchmark": BENCHMARK_OPERATOR_COMMAND,
            },
            "env_setup": ['$env:RGE_LLM_MODE = "mock"'],
        }

    return {
        "status": "available",
        "active_branch_match": True,
        "cli_wired": True,
        "artifact_path": rel_artifact,
        "reports_per_hour_estimate": payload.get("reports_per_hour_estimate"),
        "runs_completed": payload.get("runs_completed"),
        "average_elapsed_seconds": payload.get("average_elapsed_seconds"),
        "local_review_recommended": payload.get("local_review_recommended"),
        "openai_big_review_recommended": payload.get("openai_big_review_recommended"),
        "cloud_call_made_any": payload.get("cloud_call_made_any"),
        "benchmark_recommended": False,
        "artifact_written_at": payload.get("artifact_written_at"),
        "operator_commands": {
            "benchmark": BENCHMARK_OPERATOR_COMMAND,
        },
        "env_setup": ['$env:RGE_LLM_MODE = "mock"'],
    }


def build_benchmark_summary(
    *,
    runs_completed: int,
    total_elapsed_seconds: float,
    counters: dict[str, int],
    provider: str,
    mode: str,
    cloud_call_made_any: bool,
    estimated_cost_usd_total: float,
    local_review: dict[str, Any],
    openai_big_review: dict[str, Any],
) -> dict[str, Any]:
    average_elapsed_seconds = (
        _round3(total_elapsed_seconds / runs_completed) if runs_completed > 0 else 0.0
    )
    return {
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "runs_completed": runs_completed,
        "total_elapsed_seconds": _round3(total_elapsed_seconds),
        "average_elapsed_seconds": average_elapsed_seconds,
        "reports_per_hour_estimate": estimate_reports_per_hour(
            runs_completed=runs_completed,
            total_elapsed_seconds=total_elapsed_seconds,
        ),
        "total_claim_count": int(counters.get("claim_count") or 0),
        "total_concept_link_count": int(counters.get("concept_link_count") or 0),
        "total_relationship_count": int(counters.get("relationship_count") or 0),
        "total_qualification_count": int(counters.get("qualification_count") or 0),
        "provider": provider,
        "mode": mode,
        "cloud_call_made_any": cloud_call_made_any,
        "estimated_cost_usd_total": _round3(estimated_cost_usd_total),
        "local_review_recommended": bool(local_review.get("review_recommended")),
        "openai_big_review_recommended": bool(openai_big_review.get("review_recommended")),
        "openai_live_call_blocked": bool(openai_big_review.get("openai_live_call_blocked")),
        "review_threshold": {
            "local": local_review,
            "openai_big": openai_big_review,
        },
    }


def run_synthesis_packet_benchmark(
    *,
    packet_path: Path | str,
    runs: int = DEFAULT_RUNS,
    provider: str | None = None,
    output_dir: Path | str | None = None,
    root: Path | None = None,
    run_once: Callable[..., dict[str, Any]] | None = None,
    write_artifact: bool = True,
    artifact_path: Path | str | None = None,
) -> dict[str, Any]:
    """Run synthesis packet CLI repeatedly in mock-first mode; aggregate throughput."""
    if runs <= 0:
        raise ValueError("runs must be positive")

    project_root = root or repo_root()
    resolved_packet = Path(packet_path)
    if not resolved_packet.is_absolute():
        resolved_packet = project_root / resolved_packet

    provider_id = normalize_provider_id(provider or "mock_cloud")
    if provider_id == "openai":
        raise ValueError(
            "Benchmark refuses live OpenAI provider; use mock_cloud (default)."
        )

    export_dir = Path(output_dir) if output_dir else project_root / "data" / "tmp_benchmark_out"
    if not export_dir.is_absolute():
        export_dir = project_root / export_dir
    export_dir.mkdir(parents=True, exist_ok=True)

    runner = run_once or run_synthesis_packet
    completed_runs: list[dict[str, Any]] = []
    estimated_cost_usd_total = 0.0
    cloud_call_made_any = False
    mode = "mock"

    benchmark_started = time.monotonic()
    for _ in range(runs):
        result = runner(
            packet_path=resolved_packet,
            provider=provider_id,
            output_dir=export_dir,
            root=project_root,
            evaluate_governor=False,
        )
        if result.get("status") != "completed":
            raise RuntimeError(
                f"Benchmark run failed: {result.get('detail') or result.get('status')}"
            )
        completed_runs.append(result)
        throughput = result.get("throughput") or {}
        mode = str(throughput.get("mode") or mode)
        if throughput.get("cloud_call_made"):
            cloud_call_made_any = True
        cost = throughput.get("estimated_cost_usd")
        if cost is not None:
            try:
                estimated_cost_usd_total += float(cost)
            except (TypeError, ValueError):
                pass

    total_elapsed_seconds = time.monotonic() - benchmark_started

    counters = aggregate_throughput_counters(completed_runs)
    cumulative = build_cumulative_throughput(
        runs_completed=len(completed_runs),
        counters=counters,
    )
    quality_signals = {
        "grounding_failed": any(
            bool((run.get("grounding") or {}).get("needs_human_review"))
            for run in completed_runs
        ),
        "contradiction_threshold_exceeded": False,
        "drift_warning_active": False,
        "quality_threshold_failed": False,
    }
    local_review = evaluate_synthesis_review_threshold(
        provider=provider_id,
        throughput=cumulative,
        quality_signals=quality_signals,
        root=project_root,
    )
    openai_big_review = evaluate_synthesis_review_threshold(
        provider="openai",
        throughput=cumulative,
        quality_signals=quality_signals,
        root=project_root,
    )

    summary = build_benchmark_summary(
        runs_completed=len(completed_runs),
        total_elapsed_seconds=total_elapsed_seconds,
        counters=counters,
        provider=provider_id,
        mode=mode,
        cloud_call_made_any=cloud_call_made_any,
        estimated_cost_usd_total=estimated_cost_usd_total,
        local_review=local_review,
        openai_big_review=openai_big_review,
    )
    violations = _private_value_violations(summary, label="synthesis_packet_benchmark")
    if violations:
        raise RuntimeError(
            "Benchmark summary blocked by private-field policy: " + "; ".join(violations[:5])
        )
    if write_artifact:
        written_path = write_benchmark_artifact(
            summary,
            root=project_root,
            artifact_path=artifact_path,
        )
        summary = dict(summary)
        summary["artifact_path"] = _safe_rel(written_path, project_root)
    return summary


def run_synthesis_packet_benchmark_execute_safe_hook(
    *,
    root: Path | None = None,
    branch: str | None = None,
) -> dict[str, Any] | None:
    """Run mock benchmark when plan recommends it; writes gitignored operator artifact."""
    project_root = root or repo_root()
    status = inspect_synthesis_packet_benchmark_plan_status(
        root=project_root,
        branch=branch,
    )
    if not status.get("benchmark_recommended"):
        return None
    fixture = project_root / GROUNDED_PACKET_FIXTURE_REL
    if not fixture.is_file():
        return {
            "status": "skipped",
            "detail": f"fixture missing: {GROUNDED_PACKET_FIXTURE_REL.as_posix()}",
        }
    try:
        summary = run_synthesis_packet_benchmark(
            packet_path=fixture,
            runs=DEFAULT_RUNS,
            root=project_root,
            write_artifact=True,
        )
    except (RuntimeError, ValueError) as exc:
        return {"status": "error", "detail": str(exc)}
    return {
        "status": "completed",
        "runs_completed": summary.get("runs_completed"),
        "reports_per_hour_estimate": summary.get("reports_per_hour_estimate"),
        "artifact_path": summary.get("artifact_path"),
        "cloud_call_made_any": summary.get("cloud_call_made_any"),
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Repeated mock-first synthesis packet benchmark "
            "(throughput + review-threshold dry run; no live OpenAI)."
        ),
    )
    parser.add_argument(
        "--packet",
        required=True,
        help="Path to grounded synthesis evidence packet JSON.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=DEFAULT_RUNS,
        help=f"Number of synthesis runs (default: {DEFAULT_RUNS}).",
    )
    parser.add_argument(
        "--provider",
        default="mock_cloud",
        help="Cloud synthesis provider (default: mock_cloud).",
    )
    parser.add_argument(
        "--output-dir",
        default="data/tmp_benchmark_out",
        help="Directory for per-run synthesis output JSON.",
    )
    parser.add_argument(
        "--artifact-out",
        default=str(DEFAULT_BENCHMARK_ARTIFACT_REL),
        help="Gitignored operator benchmark summary path (default: data/reports/...).",
    )
    parser.add_argument(
        "--no-write-artifact",
        action="store_true",
        help="Skip writing synthesis_packet_benchmark_latest.json.",
    )
    args = parser.parse_args(argv)

    summary = run_synthesis_packet_benchmark(
        packet_path=args.packet,
        runs=args.runs,
        provider=args.provider,
        output_dir=args.output_dir,
        write_artifact=not args.no_write_artifact,
        artifact_path=args.artifact_out,
    )
    print(json.dumps(summary, indent=2))
    return 0
