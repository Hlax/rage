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
BRIDGE_COMMAND = "bridge_evaluator_instruction_draft"
EVALUATOR_SCHEMA_VERSION = "openai_synthesis_evaluator_v0.1.0"
DEFAULT_ARTIFACT_REL = Path("data/reports/openai_synthesis_evaluator_latest.json")
EVALUATOR_OPERATOR_COMMAND = (
    "python scripts/run_openai_synthesis_evaluator.py "
    "--artifact data/tmp/openai_synthesis_canary/"
    "synthesis_output_syn_packet_grounded_dry_run_fixture.json"
)
SYNTHESIS_CANARY_OUTPUT_REL = Path(
    "data/tmp/openai_synthesis_canary/"
    "synthesis_output_syn_packet_grounded_dry_run_fixture.json"
)
LIVE_CANARY_OPERATOR_COMMAND = (
    "python -m rge.cli synthesize --packet "
    "fixtures/synthesis/grounded_evidence_packet_dry_run.json "
    "--provider openai --confirm --load-operator-env "
    "--output-dir data/tmp/openai_synthesis_canary"
)
BRIDGE_INSTRUCTION_DRAFT_COMMAND = (
    "python scripts/run_openai_synthesis_evaluator.py "
    "--bridge-instruction-draft "
    f"--evaluator-artifact {DEFAULT_ARTIFACT_REL.as_posix()}"
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


def openai_synthesis_evaluator_cli_wired(*, root: Path | None = None) -> bool:
    project_root = root or repo_root()
    return (
        (project_root / "scripts/run_openai_synthesis_evaluator.py").is_file()
        and (project_root / "rge/modules/openai_synthesis_evaluator.py").is_file()
    )


def load_evaluator_artifact(
    *,
    root: Path | None = None,
    artifact_path: Path | str | None = None,
) -> dict[str, Any] | None:
    project_root = root or repo_root()
    resolved = (
        Path(artifact_path) if artifact_path else default_evaluator_artifact_path(root=project_root)
    )
    if not resolved.is_absolute():
        resolved = project_root / resolved
    if not resolved.is_file():
        return None
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _evaluator_operator_commands() -> dict[str, str]:
    return {
        "evaluate_mock": EVALUATOR_OPERATOR_COMMAND,
        "live_canary": LIVE_CANARY_OPERATOR_COMMAND,
        "bridge_instruction_draft": BRIDGE_INSTRUCTION_DRAFT_COMMAND,
    }


def inspect_openai_synthesis_evaluator_plan_status(
    *,
    root: Path | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    """Read evaluator artifact and live-gate summary for operator plan surfaces."""
    del branch
    project_root = root or repo_root()
    cli_wired = openai_synthesis_evaluator_cli_wired(root=project_root)
    artifact_path = default_evaluator_artifact_path(root=project_root)
    rel_artifact = _operator_safe_artifact_ref(artifact_path, project_root)
    missing_gates = _public_safe_missing_gates(
        missing_live_openai_http_gates(root=project_root)
    )
    live_status = build_public_safe_live_status(root=project_root)
    operator_commands = _evaluator_operator_commands()
    base: dict[str, Any] = {
        "status": "not_applicable",
        "cli_wired": cli_wired,
        "artifact_path": rel_artifact,
        "live_synthesis_verdict": None,
        "live_http_gates_summary": live_status,
        "live_http_gates_missing": sorted(missing_gates.keys()),
        "live_http_review_gated": True,
        "review_artifact_recommended": False,
        "live_canary_recommended": False,
        "bridge_instruction_draft_recommended": False,
        "operator_commands": operator_commands,
        "env_setup": ['$env:RGE_LLM_MODE = "mock"'],
    }
    if not cli_wired:
        return base

    payload = load_evaluator_artifact(root=project_root, artifact_path=artifact_path)
    if payload is None:
        canary_exists = (project_root / SYNTHESIS_CANARY_OUTPUT_REL).is_file()
        return {
            **base,
            "status": "missing",
            "review_artifact_recommended": True,
            "live_canary_recommended": canary_exists,
            "operator_commands": operator_commands,
        }

    live_synthesis_verdict = str(payload.get("evaluator_verdict") or "UNKNOWN")
    live_canary_recommended = (
        live_synthesis_verdict == "GO"
        and not missing_gates
        and str(payload.get("provider") or "") == "openai"
    )
    return {
        **base,
        "status": "available",
        "live_synthesis_verdict": live_synthesis_verdict,
        "governor_verdict": payload.get("governor_verdict"),
        "grounding_passed": payload.get("grounding_passed"),
        "provider": payload.get("provider"),
        "packet_id": payload.get("packet_id"),
        "review_artifact_recommended": False,
        "live_canary_recommended": live_canary_recommended,
        "bridge_instruction_draft_recommended": live_synthesis_verdict in {"PARTIAL", "NO-GO"},
        "artifact_written_at": payload.get("artifact_written_at"),
        "input_artifact_path": payload.get("input_artifact_path"),
        "operator_commands": operator_commands,
    }


def _instruction_packet_filename(packet_id: str) -> str:
    import re
    from datetime import datetime, timezone

    safe_packet_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", packet_id).strip("-") or "packet"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}_{safe_packet_id}.md"


def _extract_citation_refs(synthesis_artifact: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    claim_refs: set[str] = set()
    atom_refs: set[str] = set()
    source_refs: set[str] = set()
    try:
        resolved = resolve_synthesis_packet_run_artifact(synthesis_artifact)
        output = resolved.get("output") or {}
    except GovernorOperatorSurfaceError:
        output = synthesis_artifact
    for sentence in output.get("summary_sentences") or []:
        if not isinstance(sentence, dict):
            continue
        claim_refs.update(str(item) for item in (sentence.get("claim_ids") or []) if item)
        atom_refs.update(str(item) for item in (sentence.get("atom_ids") or []) if item)
        source_refs.update(str(item) for item in (sentence.get("source_refs") or []) if item)
    return sorted(claim_refs), sorted(atom_refs), sorted(source_refs)


def _primary_remediation_suggestion(evaluator: dict[str, Any]) -> dict[str, Any]:
    suggestions = [
        row for row in (evaluator.get("remediation_suggestions") or []) if isinstance(row, dict)
    ]
    if not suggestions:
        return {}
    verdict = str(evaluator.get("evaluator_verdict") or "")
    if verdict == "GO":
        for row in suggestions:
            if "improvement handoff" in str(row.get("problem") or "").casefold():
                return row
        return {}
    if verdict in {"PARTIAL", "NO-GO"}:
        for row in suggestions:
            problem = str(row.get("problem") or "").casefold()
            if "grounding" in problem or "governor" in problem or "gates" in problem:
                return row
        return suggestions[0]
    return suggestions[0]


def build_evaluator_instruction_packet_text(
    evaluator: dict[str, Any],
    *,
    packet_id: str,
    claim_refs: list[str],
    atom_refs: list[str],
    source_refs: list[str],
    evaluator_artifact_ref: str,
) -> str:
    suggestion = _primary_remediation_suggestion(evaluator)
    evaluator_verdict = str(evaluator.get("evaluator_verdict") or "UNKNOWN")
    summary = suggestion.get("problem") or (
        f"OpenAI synthesis evaluator recorded verdict {evaluator_verdict} for packet {packet_id}."
    )
    build_title = suggestion.get("recommended_ticket_scope") or (
        f"Remediate live OpenAI synthesis finding for {packet_id}"
    )
    likely_files = list(suggestion.get("expected_files") or [])
    if not likely_files:
        likely_files = list(suggestion.get("affected_modules") or [])
    acceptance = [
        "Evaluator remediation preserves mock-first defaults and no accepted graph writes.",
        "Grounding and governor checks pass on the grounded dry-run fixture.",
        "Relevant unit tests and safety audit pass.",
    ]
    if evaluator_verdict in {"PARTIAL", "NO-GO"}:
        acceptance.insert(
            0,
            "Address evaluator grounding/governor failure reasons before another live canary.",
        )
    tests = [
        "python -m pytest tests/unit/test_openai_synthesis_evaluator.py",
        "python -m pytest tests/unit/test_openai_synthesis_adapter_contract.py",
        "python -m rge.modules.safety_auditor --audit full",
    ]
    non_goals = [
        "Do not auto-merge, auto-push, auto-publish, or promote tickets.",
        "Do not copy paid-model output directly into implementation files.",
        "Do not edit TICKET_QUEUE.md or tickets/ from evaluator output.",
    ]
    rollback = (
        "Delete the evaluator instruction packet and draft ticket; rerun synthesize --packet "
        "and the evaluator bridge after remediation."
    )
    return "\n".join(
        [
            f"# Autonomous Synthesis Instruction Packet: {packet_id}",
            "",
            "## Summary",
            str(summary),
            "",
            "## Evidence Artifact",
            evaluator_artifact_ref,
            "",
            "## Citations",
            f"- Claim refs: {', '.join(claim_refs) or 'none'}",
            f"- Atom refs: {', '.join(atom_refs) or 'none'}",
            f"- Source refs: {', '.join(source_refs) or 'none'}",
            "",
            "## Recommended Build Packet",
            str(build_title),
            "",
            "## Files Likely Affected",
            *[f"- `{item}`" for item in likely_files],
            "",
            "## Acceptance Criteria",
            *[f"- {item}" for item in acceptance],
            "",
            "## Tests To Run",
            *[f"- `{item}`" for item in tests],
            "",
            "## Explicit Non-Goals",
            *[f"- {item}" for item in non_goals],
            "",
            "## Safety Notes",
            "- This packet was generated from a public-safe OpenAI synthesis evaluator artifact.",
            "- Paid-model output must not directly modify code, queues, Git, or public exports.",
            f"- Evaluator verdict: {evaluator_verdict}.",
            f"- Governor verdict: {evaluator.get('governor_verdict') or 'UNKNOWN'}.",
            "",
            "## Rollback Plan",
            rollback,
            "",
        ]
    )


def write_evaluator_instruction_packet(
    evaluator: dict[str, Any],
    *,
    synthesis_artifact: dict[str, Any],
    evaluator_artifact_ref: str,
    root: Path | None = None,
) -> Path:
    from rge.modules.autonomous_synthesis_governor import instruction_packet_dir

    project_root = root or repo_root()
    packet_id = str(evaluator.get("packet_id") or "unknown_packet")
    claim_refs, atom_refs, source_refs = _extract_citation_refs(synthesis_artifact)
    text = build_evaluator_instruction_packet_text(
        evaluator,
        packet_id=packet_id,
        claim_refs=claim_refs,
        atom_refs=atom_refs,
        source_refs=source_refs,
        evaluator_artifact_ref=evaluator_artifact_ref,
    )
    out_dir = instruction_packet_dir(root=project_root)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / _instruction_packet_filename(packet_id)
    path.write_text(text, encoding="utf-8")
    return path


def bridge_evaluator_to_instruction_draft(
    *,
    evaluator_artifact: Path | dict[str, Any],
    synthesis_artifact: Path | dict[str, Any] | None = None,
    write_draft: bool | None = None,
    dry_run: bool = False,
    root: Path | None = None,
) -> dict[str, Any]:
    """Convert evaluator artifact to instruction packet and optional draft ticket."""
    from rge.modules.atlas_snapshot_builder import assert_no_private_fields
    from rge.modules.instruction_packet_ticket_draft import (
        _draft_ticket_name,
        build_draft_ticket_payload,
        draft_ticket_dir,
        parse_instruction_packet_text,
        validate_instruction_packet_for_draft,
        write_draft_status_report,
    )

    project_root = root or repo_root()
    if isinstance(evaluator_artifact, dict):
        evaluator = dict(evaluator_artifact)
        evaluator_ref = str(
            evaluator.get("artifact_path") or evaluator.get("input_artifact_path") or "evaluator.json"
        )
    else:
        resolved_evaluator = (
            evaluator_artifact
            if evaluator_artifact.is_absolute()
            else project_root / evaluator_artifact
        )
        evaluator = json.loads(resolved_evaluator.read_text(encoding="utf-8"))
        evaluator_ref = _operator_safe_artifact_ref(resolved_evaluator, project_root)

    if synthesis_artifact is None:
        input_ref = str(evaluator.get("input_artifact_path") or "")
        if input_ref:
            candidate = project_root / input_ref
            if not candidate.is_file():
                candidate = project_root / "fixtures/synthesis/grounded_evidence_packet_dry_run.json"
        else:
            candidate = project_root / "fixtures/synthesis/grounded_evidence_packet_dry_run.json"
        synthesis_payload = load_synthesis_artifact(candidate, root=project_root)
    elif isinstance(synthesis_artifact, dict):
        synthesis_payload = synthesis_artifact
    else:
        synthesis_payload = load_synthesis_artifact(synthesis_artifact, root=project_root)

    evaluator_verdict = str(evaluator.get("evaluator_verdict") or "NO-GO")
    should_write_draft = (
        write_draft
        if write_draft is not None
        else evaluator_verdict in {"PARTIAL", "NO-GO"}
    )

    packet_path = write_evaluator_instruction_packet(
        evaluator,
        synthesis_artifact=synthesis_payload,
        evaluator_artifact_ref=evaluator_ref,
        root=project_root,
    )
    rel_packet_path = _operator_safe_artifact_ref(packet_path, project_root)
    parsed = parse_instruction_packet_text(packet_path.read_text(encoding="utf-8"))
    validation = validate_instruction_packet_for_draft(
        packet_path=packet_path,
        parsed=parsed,
        root=project_root,
        source="evaluator",
    )

    result: dict[str, Any] = {
        "schema_version": EVALUATOR_SCHEMA_VERSION,
        "status": "completed",
        "command": BRIDGE_COMMAND,
        "evaluator_verdict": evaluator_verdict,
        "instruction_packet_path": rel_packet_path,
        "draft_ticket_path": None,
        "draft_written": False,
        "validation_passed": bool(validation.get("passed")),
        "validation_reasons": list(validation.get("reasons") or []),
        "dry_run": dry_run,
    }

    if not validation.get("passed"):
        result["status"] = "rejected"
        write_draft_status_report(
            {
                "verdict": "NO-GO",
                "status": "rejected",
                "source_instruction_packet": rel_packet_path,
                "validation_reasons": validation.get("reasons") or [],
            },
            root=project_root,
        )
        return result

    if not should_write_draft:
        result["follow_up"] = (
            "Evaluator GO: instruction packet written; draft ticket skipped by default. "
            "Pass write_draft=True to create a documented follow-up draft."
        )
        write_draft_status_report(
            {
                "verdict": "GO",
                "status": "instruction_packet_only",
                "source_instruction_packet": rel_packet_path,
                "draft_ticket_path": None,
            },
            root=project_root,
        )
        return result

    draft_payload = build_draft_ticket_payload(
        parsed=parsed,
        instruction_packet_path=rel_packet_path,
        validation=validation,
        root=project_root,
        evaluator_artifact=evaluator,
        draft_source="openai_synthesis_evaluator_bridge",
    )
    draft_dir = draft_ticket_dir(root=project_root)
    draft_dir.mkdir(parents=True, exist_ok=True)
    draft_path = draft_dir / _draft_ticket_name(str(parsed.get("packet_id") or "packet"))

    if not dry_run:
        violations = assert_no_private_fields({"draft_ticket": draft_payload})
        if violations:
            result["status"] = "rejected"
            result["validation_reasons"] = violations[:5]
            return result
        draft_path.write_text(json.dumps(draft_payload, indent=2) + "\n", encoding="utf-8")
        result["draft_ticket_path"] = _operator_safe_artifact_ref(draft_path, project_root)
        result["draft_written"] = True

    write_draft_status_report(
        {
            "verdict": "GO",
            "status": "dry_run" if dry_run else "completed",
            "source_instruction_packet": rel_packet_path,
            "draft_ticket_path": result.get("draft_ticket_path"),
            "recommended_files": draft_payload.get("expected_files") or [],
            "acceptance_criteria_count": len(draft_payload.get("acceptance_criteria") or []),
            "dry_run": dry_run,
        },
        root=project_root,
    )
    return result


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


def run_openai_synthesis_evaluator_execute_safe_hook(
    *,
    root: Path | None = None,
    branch: str | None = None,
) -> dict[str, Any] | None:
    """Seed gitignored evaluator artifact when plan recommends mock evaluate."""
    from rge.modules.synthesis_packet_runner import (
        GROUNDED_PACKET_FIXTURE_REL,
        run_synthesis_packet,
    )

    project_root = root or repo_root()
    status = inspect_openai_synthesis_evaluator_plan_status(
        root=project_root,
        branch=branch,
    )
    if not status.get("review_artifact_recommended"):
        return None
    if not status.get("cli_wired"):
        return {"status": "skipped", "detail": "evaluator CLI not wired"}

    input_path = project_root / SYNTHESIS_CANARY_OUTPUT_REL
    mock_synthesized = False
    if not input_path.is_file():
        fixture = project_root / GROUNDED_PACKET_FIXTURE_REL
        if not fixture.is_file():
            return {
                "status": "skipped",
                "detail": f"fixture missing: {GROUNDED_PACKET_FIXTURE_REL.as_posix()}",
            }
        try:
            output_dir = project_root / SYNTHESIS_CANARY_OUTPUT_REL.parent
            run_result = run_synthesis_packet(
                packet_path=fixture,
                provider="mock_cloud",
                output_dir=output_dir,
                root=project_root,
            )
            output_rel = str(run_result.get("output_path") or "")
            if not output_rel:
                return {"status": "error", "detail": "mock synthesis missing output_path"}
            input_path = Path(output_rel)
            if not input_path.is_absolute():
                input_path = project_root / input_path
            mock_synthesized = True
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    try:
        result = run_openai_synthesis_evaluator(
            input_artifact=input_path,
            root=project_root,
            write_artifact=True,
        )
    except (OpenAISynthesisEvaluatorError, ValueError, RuntimeError) as exc:
        return {"status": "error", "detail": str(exc)}

    return {
        "status": "completed",
        "live_synthesis_verdict": result.get("evaluator_verdict"),
        "artifact_path": result.get("artifact_path"),
        "input_artifact_path": result.get("input_artifact_path"),
        "mock_synthesized": mock_synthesized,
        "live_http_used": False,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="scripts/run_openai_synthesis_evaluator.py",
        description="Evaluate a synthesis output artifact without live HTTP.",
    )
    parser.add_argument(
        "--artifact",
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
    parser.add_argument(
        "--bridge-instruction-draft",
        action="store_true",
        help="Convert evaluator artifact into instruction packet and optional draft ticket.",
    )
    parser.add_argument(
        "--evaluator-artifact",
        help="Evaluator JSON for --bridge-instruction-draft (defaults to --artifact-out).",
    )
    parser.add_argument(
        "--synthesis-artifact",
        help="Optional synthesis packet run JSON when bridging from evaluator artifact only.",
    )
    parser.add_argument(
        "--write-draft",
        action="store_true",
        help="Force draft ticket write when bridging (default for PARTIAL/NO-GO only).",
    )
    parser.add_argument(
        "--no-write-draft",
        action="store_true",
        help="Skip draft ticket write when bridging (default for GO).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate bridge handoff without writing draft ticket JSON.",
    )
    parser.add_argument(
        "--root",
        help="Optional repository root override for bridge writes.",
    )
    args = parser.parse_args(argv)
    project_root = Path(args.root) if args.root else None
    try:
        if args.bridge_instruction_draft:
            evaluator_path = Path(
                args.evaluator_artifact or args.artifact_out or DEFAULT_ARTIFACT_REL
            )
            synthesis_path = Path(args.synthesis_artifact) if args.synthesis_artifact else None
            write_draft: bool | None = None
            if args.write_draft:
                write_draft = True
            elif args.no_write_draft:
                write_draft = False
            result = bridge_evaluator_to_instruction_draft(
                evaluator_artifact=evaluator_path,
                synthesis_artifact=synthesis_path,
                write_draft=write_draft,
                dry_run=args.dry_run,
                root=project_root,
            )
            print(json.dumps(result, indent=2))
            if result.get("status") == "rejected":
                return 1
            return 0

        if not args.artifact:
            parser.error("--artifact is required unless --bridge-instruction-draft is set")
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
