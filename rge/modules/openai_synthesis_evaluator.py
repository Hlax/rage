"""Deterministic read-only evaluator for live OpenAI synthesis artifacts (ticket-394)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rge.llm.openai_synthesis_client import (
    build_public_safe_live_status,
    missing_live_openai_http_gates,
)
from rge.modules.autonomous_synthesis_governor import (
    GovernorOperatorSurfaceError,
    _private_value_violations,
    _safe_rel,
    evaluate_synthesis_governor,
    resolve_synthesis_packet_run_artifact,
    utc_now_iso,
)
from rge.modules.openai_synthesis_adapter_spec import PUBLIC_CREDENTIAL_ENV_HINT
from rge.modules.principal_audit_gate import repo_root
from rge.modules.synthesis_grounding import evaluate_synthesis_grounding
from rge.modules.synthesis_review_threshold_policy import evaluate_synthesis_review_threshold

COMMAND = "evaluate_openai_synthesis"
EVALUATOR_SCHEMA_VERSION = "openai_synthesis_evaluator_v0.1.0"
DEFAULT_ARTIFACT_REL = Path("data/reports/openai_synthesis_evaluator_latest.json")
EVALUATOR_OPERATOR_COMMAND = (
    "python scripts/run_openai_synthesis_evaluator.py "
    "--artifact data/tmp/openai_synthesis_canary/"
    "synthesis_output_syn_packet_grounded_dry_run_fixture.json"
)


class OpenAISynthesisEvaluatorError(RuntimeError):
    """Raised when synthesis artifact evaluation cannot proceed safely."""


def _public_safe_missing_gates(missing: dict[str, str]) -> dict[str, str]:
    credential_keys = frozenset({"OPENAI_API_KEY", "RGE_OPENAI_API_KEY"})
    safe: dict[str, str] = {}
    for key, hint in missing.items():
        out_key = PUBLIC_CREDENTIAL_ENV_HINT if key in credential_keys else key
        safe[out_key] = hint
    return safe


def default_evaluator_artifact_path(*, root: Path | None = None) -> Path:
    return (root or repo_root()) / DEFAULT_ARTIFACT_REL


def _operator_safe_artifact_ref(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def load_synthesis_artifact(path: Path, *, root: Path | None = None) -> dict[str, Any]:
    project_root = root or repo_root()
    resolved = path if path.is_absolute() else project_root / path
    if not resolved.is_file():
        raise OpenAISynthesisEvaluatorError(
            f"Synthesis artifact not found: {_safe_rel(resolved, project_root)}"
        )
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OpenAISynthesisEvaluatorError(
            f"Unable to read synthesis artifact: {_safe_rel(resolved, project_root)}"
        ) from exc
    if not isinstance(payload, dict):
        raise OpenAISynthesisEvaluatorError("Synthesis artifact must be a JSON object.")
    return payload


def _cost_estimate_available(output: dict[str, Any]) -> bool:
    usage = output.get("usage") if isinstance(output.get("usage"), dict) else {}
    if output.get("cost_estimate_usd") is not None:
        return True
    for key in ("usd", "cost_usd"):
        if usage.get(key) is not None:
            return True
    return False


def compute_evaluator_verdict(
    *,
    run_status: str,
    grounding_passed: bool,
    governor_verdict: str,
    no_accepted_graph_writes: bool,
) -> str:
    if run_status != "completed":
        return "NO-GO"
    if not no_accepted_graph_writes:
        return "NO-GO"
    if grounding_passed and governor_verdict == "GO":
        return "GO"
    if run_status == "completed":
        return "PARTIAL"
    return "NO-GO"


def build_remediation_suggestions(
    *,
    evaluator_verdict: str,
    grounding_passed: bool,
    governor_verdict: str,
    governor_reasons: list[str],
    review_reasons: list[str],
    provider: str,
    missing_gates: dict[str, str],
) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    if missing_gates:
        suggestions.append(
            {
                "problem": "Live OpenAI synthesis gates are not satisfied for operator review.",
                "affected_modules": [
                    "rge/llm/openai_synthesis_client.py",
                    "rge/config.py",
                ],
                "expected_files": [
                    "docs/agents/12_RUNTIME_CONFIG.md",
                    "README.md",
                ],
                "recommended_ticket_scope": (
                    "Operator-only env gate setup in .env.local; no engine gate removal."
                ),
                "forbidden_actions": [
                    "auto_merge",
                    "auto_push",
                    "auto_promote_ticket",
                    "edit_TICKET_QUEUE",
                ],
            }
        )
    if not grounding_passed:
        suggestions.append(
            {
                "problem": (
                    "Synthesis candidate output failed deterministic grounding overlap checks."
                ),
                "affected_modules": [
                    "rge/llm/openai_synthesis_client.py",
                    "rge/modules/synthesis_grounding.py",
                    "rge/modules/synthesis_packet_runner.py",
                ],
                "expected_files": [
                    "rge/llm/openai_synthesis_client.py",
                    "tests/unit/test_openai_synthesis_adapter_contract.py",
                    "tests/unit/test_synthesis_packet_runner.py",
                ],
                "recommended_ticket_scope": (
                    "Hydrate grounded claim/atom text in OpenAI requests and normalize citations "
                    "(ticket-393 pattern)."
                ),
                "forbidden_actions": [
                    "auto_merge",
                    "auto_push",
                    "auto_promote_ticket",
                    "edit_TICKET_QUEUE",
                    "loosen_grounding_thresholds",
                ],
            }
        )
    if governor_verdict in {"NO-GO", "PARTIAL"} and governor_reasons:
        suggestions.append(
            {
                "problem": "Autonomous synthesis governor flagged the candidate output.",
                "affected_modules": [
                    "rge/modules/autonomous_synthesis_governor.py",
                    "rge/modules/synthesis_packet_runner.py",
                ],
                "expected_files": [
                    "rge/modules/autonomous_synthesis_governor.py",
                    "tests/unit/test_autonomous_synthesis_governor.py",
                ],
                "recommended_ticket_scope": (
                    "Inspect governor failure_reasons and rerun synthesize --packet after remediation."
                ),
                "forbidden_actions": [
                    "auto_merge",
                    "auto_push",
                    "auto_promote_ticket",
                    "edit_TICKET_QUEUE",
                ],
            }
        )
    if review_reasons:
        suggestions.append(
            {
                "problem": "Synthesis review-threshold policy recommends operator review.",
                "affected_modules": [
                    "rge/modules/synthesis_review_threshold_policy.py",
                    "rge/modules/synthesis_packet_runner.py",
                ],
                "expected_files": [
                    "rge/modules/synthesis_review_threshold_policy.py",
                    "tests/unit/test_synthesis_packet_runner.py",
                ],
                "recommended_ticket_scope": (
                    "Review throughput cadence and quality signals before additional live calls."
                ),
                "forbidden_actions": [
                    "auto_merge",
                    "auto_push",
                    "auto_promote_ticket",
                ],
            }
        )
    if evaluator_verdict == "GO":
        suggestions.append(
            {
                "problem": (
                    "Live OpenAI synthesis canary passed grounding and governor checks; "
                    "improvement handoff may proceed."
                ),
                "affected_modules": [
                    "rge/modules/openai_synthesis_evaluator.py",
                    "rge/modules/instruction_packet_ticket_draft.py",
                    "rge/modules/autonomous_synthesis_governor.py",
                ],
                "expected_files": [
                    "rge/modules/openai_synthesis_evaluator.py",
                    "tests/unit/test_instruction_packet_ticket_draft_handoff.py",
                ],
                "recommended_ticket_scope": (
                    "Bridge evaluator artifact into instruction-packet draft tickets (ticket-395)."
                ),
                "forbidden_actions": [
                    "auto_merge",
                    "auto_push",
                    "auto_promote_ticket",
                    "edit_TICKET_QUEUE",
                ],
            }
        )
    if provider != "openai" and evaluator_verdict != "GO":
        suggestions.append(
            {
                "problem": "Artifact provider is not openai; live OpenAI evaluator is advisory only.",
                "affected_modules": ["rge/modules/synthesis_packet_runner.py"],
                "expected_files": ["README.md"],
                "recommended_ticket_scope": (
                    "Re-run synthesize --packet --provider openai --confirm for live canary evidence."
                ),
                "forbidden_actions": ["auto_promote_ticket"],
            }
        )
    return suggestions


def evaluate_synthesis_artifact(
    artifact: dict[str, Any],
    *,
    artifact_path: Path | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Evaluate a synthesis artifact deterministically without network calls."""
    project_root = root or repo_root()
    try:
        resolved = resolve_synthesis_packet_run_artifact(
            artifact,
            artifact_path=artifact_path,
            root=project_root,
        )
    except GovernorOperatorSurfaceError as exc:
        raise OpenAISynthesisEvaluatorError(str(exc)) from exc

    packet = resolved["packet"]
    output = resolved["output"]
    throughput = dict(resolved.get("throughput") or {})
    provider = str(output.get("provider") or throughput.get("provider") or "unknown")
    model = throughput.get("model")
    packet_id = str(packet.get("packet_id") or output.get("packet_id") or "unknown")

    grounding = evaluate_synthesis_grounding(output, packet=packet)
    quality_signals = {
        "grounding_failed": bool(grounding.get("needs_human_review")),
        "contradiction_threshold_exceeded": bool(
            packet.get("contradiction_threshold_exceeded")
        ),
        "drift_warning_active": bool(packet.get("drift_warning_active")),
        "quality_threshold_failed": bool(packet.get("quality_threshold_failed")),
    }
    review_threshold = evaluate_synthesis_review_threshold(
        provider=provider,
        throughput=throughput or {
            "reports_completed": 0,
            "claim_count": len(packet.get("claims") or []),
        },
        quality_signals=quality_signals,
        root=project_root,
    )
    governor_review = evaluate_synthesis_governor(
        packet=packet,
        output=output,
        provider_id=provider,
        root=project_root,
        write_ledger=False,
        write_instruction=False,
        update_circuit=False,
    )
    governor_verdict = str(governor_review.get("governor_verdict") or "NO-GO")
    grounding_passed = bool(grounding.get("grounding_passed"))
    no_accepted_graph_writes = bool(resolved.get("no_accepted_graph_writes", True))
    run_status = str(resolved.get("run_status") or "unknown")
    evaluator_verdict = compute_evaluator_verdict(
        run_status=run_status,
        grounding_passed=grounding_passed,
        governor_verdict=governor_verdict,
        no_accepted_graph_writes=no_accepted_graph_writes,
    )
    missing_gates = _public_safe_missing_gates(missing_live_openai_http_gates(root=project_root))
    live_status = build_public_safe_live_status(root=project_root)

    return {
        "schema_version": EVALUATOR_SCHEMA_VERSION,
        "status": "completed",
        "command": COMMAND,
        "evaluator_verdict": evaluator_verdict,
        "source_artifact_kind": resolved.get("artifact_kind"),
        "provider": provider,
        "model": model,
        "packet_id": packet_id,
        "token_usage": dict(output.get("usage") or {}),
        "cost_estimate_available": _cost_estimate_available(output),
        "grounding_passed": grounding_passed,
        "flagged_sentence_count": len(grounding.get("flagged_sentences") or []),
        "review_reasons": list(review_threshold.get("reasons") or []),
        "review_tier": review_threshold.get("review_tier"),
        "governor_verdict": governor_verdict,
        "governor_failure_reasons": list(governor_review.get("failure_reasons") or []),
        "no_accepted_graph_writes": no_accepted_graph_writes,
        "run_status": run_status,
        "live_http_gates_missing": missing_gates,
        "live_http_status": live_status,
        "remediation_suggestions": build_remediation_suggestions(
            evaluator_verdict=evaluator_verdict,
            grounding_passed=grounding_passed,
            governor_verdict=governor_verdict,
            governor_reasons=list(governor_review.get("failure_reasons") or []),
            review_reasons=list(review_threshold.get("reasons") or []),
            provider=provider,
            missing_gates=missing_gates,
        ),
        "operator_commands": {
            "evaluate": EVALUATOR_OPERATOR_COMMAND,
            "synthesize_canary": (
                "python -m rge.cli synthesize --packet "
                "fixtures/synthesis/grounded_evidence_packet_dry_run.json "
                "--provider openai --confirm --load-operator-env "
                "--output-dir data/tmp/openai_synthesis_canary"
            ),
        },
        "evaluated_at": utc_now_iso(),
    }


def write_evaluator_artifact(
    artifact: dict[str, Any],
    *,
    root: Path | None = None,
    artifact_path: Path | str | None = None,
) -> Path:
    project_root = root or repo_root()
    resolved = (
        Path(artifact_path) if artifact_path else default_evaluator_artifact_path(root=project_root)
    )
    if not resolved.is_absolute():
        resolved = project_root / resolved
    payload = dict(artifact)
    payload["artifact_written_at"] = utc_now_iso()
    violations = _private_value_violations(payload, label="openai_synthesis_evaluator_artifact")
    if violations:
        raise OpenAISynthesisEvaluatorError(
            "Evaluator artifact blocked by private-field policy: "
            + "; ".join(violations[:5])
        )
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return resolved


def run_openai_synthesis_evaluator(
    *,
    input_artifact: Path,
    root: Path | None = None,
    write_artifact: bool = True,
    output_artifact: Path | str | None = None,
) -> dict[str, Any]:
    project_root = root or repo_root()
    resolved_input = (
        input_artifact if input_artifact.is_absolute() else project_root / input_artifact
    )
    payload = load_synthesis_artifact(resolved_input, root=project_root)
    result = evaluate_synthesis_artifact(
        payload,
        artifact_path=resolved_input,
        root=project_root,
    )
    result["input_artifact_path"] = _operator_safe_artifact_ref(resolved_input, project_root)
    if write_artifact:
        out_path = write_evaluator_artifact(
            result,
            root=project_root,
            artifact_path=output_artifact,
        )
        result["artifact_path"] = _operator_safe_artifact_ref(out_path, project_root)
    return result


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="scripts/run_openai_synthesis_evaluator.py",
        description="Evaluate a synthesis output artifact without live HTTP.",
    )
    parser.add_argument(
        "--artifact",
        required=True,
        help="Path to synthesis_packet_run or candidate synthesis output JSON.",
    )
    parser.add_argument(
        "--artifact-out",
        default=str(DEFAULT_ARTIFACT_REL),
        help="Gitignored evaluator artifact output path.",
    )
    parser.add_argument(
        "--no-write-artifact",
        action="store_true",
        help="Skip writing gitignored evaluator artifact.",
    )
    args = parser.parse_args(argv)
    try:
        result = run_openai_synthesis_evaluator(
            input_artifact=Path(args.artifact),
            write_artifact=not args.no_write_artifact,
            output_artifact=Path(args.artifact_out),
        )
    except OpenAISynthesisEvaluatorError as exc:
        print(json.dumps({"status": "error", "command": COMMAND, "detail": str(exc)}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0 if result.get("evaluator_verdict") in {"GO", "PARTIAL"} else 1
