"""Deterministic autonomy governor for cloud synthesis outputs.

Paid/cloud models may draft synthesis prose and build instructions, but this
module owns the safety decision before anything can move downstream.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rge.contracts.synthesis_evidence_packet_v0 import (
    SCHEMA_VERSION_GROUNDED,
    assert_synthesis_packet_operator_safe,
    atom_text_by_id,
    claim_text_by_id,
    is_refs_only_packet,
    validate_grounded_synthesis_packet,
)
from rge.llm.cloud_synthesis_registry import normalize_provider_id
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.multi_claim_atom_clustering import evaluate_synthesis_readiness
from rge.modules.principal_audit_gate import repo_root
from rge.modules.synthesis_grounding import evaluate_synthesis_grounding
from rge.safety.public_export_policy import FORBIDDEN_VALUE_PATTERNS

GOVERNOR_SCHEMA_VERSION = "autonomous_synthesis_governor_v0.1.0"
LEDGER_SCHEMA_VERSION = "autonomous_synthesis_governor_ledger_v0.1.0"
CIRCUIT_SCHEMA_VERSION = "autonomy_circuit_breaker_v0.1.0"

GOVERNOR_PACKET_ID = "autonomous-synthesis-safety-governor"
DEFAULT_LEDGER_REL = Path("data/operator/autonomous_synthesis_governor_ledger.json")
DEFAULT_CIRCUIT_REL = Path("data/operator/autonomy_circuit_breaker.json")
DEFAULT_INSTRUCTION_DIR_REL = Path("data/operator/instruction_packets")
DEFAULT_CIRCUIT_AUDIT_REL = Path("data/operator/autonomy_circuit_breaker_audit.jsonl")
DEFAULT_CIRCUIT_STATUS_REPORT_REL = Path(
    "data/operator/autonomy_circuit_breaker_status_latest.json"
)
DEFAULT_ATLAS_ARTIFACT_REL = Path(
    "apps/public-site/public/data/atlas_synthesis_human_review_latest.json"
)
GOVERNOR_CLI_SCRIPT = "scripts/run_autonomous_synthesis_governor.py"
DEFAULT_FAILURE_THRESHOLD = 3
HUMAN_REVIEW_ARTIFACT_SCHEMA = "atlas_synthesis_human_review_v0.1.0"
GROUNDED_PACKET_FIXTURE_REL = Path("fixtures/synthesis/grounded_evidence_packet_dry_run.json")
SYNTHESIS_OUTPUT_GLOBS = (
    "**/synthesis_output.json",
    "**/*synthesis*output*.json",
)
ARTIFACT_SEARCH_REL_PATHS = (
    DEFAULT_ATLAS_ARTIFACT_REL,
    Path("data/exports/synthesis_human_review_ui/atlas_synthesis_human_review_latest.json"),
)


class GovernorOperatorSurfaceError(RuntimeError):
    """Raised when governor operator CLI inputs or gates are invalid."""

FORBIDDEN_ACTION_PATTERNS = (
    re.compile(r"\bgit\s+(?:merge|push)\b", re.IGNORECASE),
    re.compile(r"\b(?:auto-)?(?:merge|push|publish)\b", re.IGNORECASE),
    re.compile(r"\bpromote(?:\s+\w+){0,3}\s+(?:ticket|queue)\b", re.IGNORECASE),
)
FORBIDDEN_GATE_WEAKENING_PATTERNS = (
    re.compile(r"\bincrease\s+(?:the\s+)?budget\b", re.IGNORECASE),
    re.compile(r"\bweaken\s+(?:the\s+)?gates?\b", re.IGNORECASE),
    re.compile(r"\bdisable\s+(?:the\s+)?(?:safety|budget|grounding)\b", re.IGNORECASE),
)
RAW_DOCUMENT_PATTERNS = (
    re.compile(r"<!doctype\s+html", re.IGNORECASE),
    re.compile(r"<html[\s>]", re.IGNORECASE),
    re.compile(r"<body[\s>]", re.IGNORECASE),
    re.compile(r"%PDF-\d", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:system|developer)\s+prompt\b", re.IGNORECASE),
)
LOCAL_PATH_PATTERNS = (
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"/(?:Users|home)/[A-Za-z0-9_.-]+"),
    re.compile(r"(?:^|[\"' ])data/sources/"),
    re.compile(r"(?:^|[\"' ])fixtures/sources/"),
)
UNSAFE_DIR_PREFIXES = (
    "rge/",
    "apps/",
    "tests/",
    "tickets/",
    ".github/",
    ".env",
    "README.md",
    "docs/",
)
SAFE_DIRTY_PREFIXES = (
    "data/operator/",
    "data/reports/operator_autonomous_loop/",
    "agent_reports/",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "0").strip().casefold() in {"1", "true", "yes"}


def _operator_path(root: Path, rel: Path) -> Path:
    return root / rel


def circuit_breaker_path(*, root: Path | None = None) -> Path:
    return _operator_path(root or repo_root(), DEFAULT_CIRCUIT_REL)


def ledger_path(*, root: Path | None = None) -> Path:
    return _operator_path(root or repo_root(), DEFAULT_LEDGER_REL)


def instruction_packet_dir(*, root: Path | None = None) -> Path:
    return _operator_path(root or repo_root(), DEFAULT_INSTRUCTION_DIR_REL)


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _iter_values(value: object, prefix: str = "") -> list[tuple[str, object]]:
    rows: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            rows.append((path, item))
            rows.extend(_iter_values(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            rows.extend(_iter_values(item, f"{prefix}[{index}]"))
    return rows


def _private_value_violations(payload: dict[str, Any], *, label: str) -> list[str]:
    violations: list[str] = []
    for key_path, item in _iter_values(payload):
        if not isinstance(item, str):
            continue
        for pattern in (*FORBIDDEN_VALUE_PATTERNS, *RAW_DOCUMENT_PATTERNS, *LOCAL_PATH_PATTERNS):
            if pattern.search(item):
                violations.append(
                    f"{label}.{key_path} contains forbidden content matching {pattern.pattern!r}"
                )
    return violations


def empty_circuit_state() -> dict[str, Any]:
    return {
        "schema_version": CIRCUIT_SCHEMA_VERSION,
        "status": "closed",
        "consecutive_synthesis_failures": 0,
        "consecutive_unsupported_outputs": 0,
        "latest_stop_reason": None,
        "opened_at": None,
        "updated_at": None,
    }


def load_circuit_breaker(*, root: Path | None = None) -> dict[str, Any]:
    path = circuit_breaker_path(root=root)
    payload = _load_json(path) if path.is_file() else None
    if payload is None or payload.get("schema_version") != CIRCUIT_SCHEMA_VERSION:
        return empty_circuit_state()
    state = empty_circuit_state()
    state.update(payload)
    return state


def save_circuit_breaker(state: dict[str, Any], *, root: Path | None = None) -> Path:
    path = circuit_breaker_path(root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    state["schema_version"] = CIRCUIT_SCHEMA_VERSION
    state["updated_at"] = utc_now_iso()
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return path


def _failure_threshold() -> int:
    raw = os.environ.get("RGE_SYNTHESIS_GOVERNOR_FAILURE_THRESHOLD", "").strip()
    if not raw:
        return DEFAULT_FAILURE_THRESHOLD
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_FAILURE_THRESHOLD


def update_circuit_breaker(
    *,
    verdict: str | None = None,
    failure_reasons: list[str] | None = None,
    root: Path | None = None,
    safety_auditor_passed: bool | None = None,
    verify_passed: bool | None = None,
    public_safe_export_scan_passed: bool | None = None,
    paid_budget_exceeded: bool = False,
    dirty_paths: list[str] | None = None,
) -> dict[str, Any]:
    """Persist breaker state and open it on repeated or hard safety failures."""
    project_root = root or repo_root()
    state = load_circuit_breaker(root=project_root)
    reasons = list(failure_reasons or [])
    threshold = _failure_threshold()

    if verdict == "GO":
        state["consecutive_synthesis_failures"] = 0
        state["consecutive_unsupported_outputs"] = 0
    elif verdict in {"PARTIAL", "NO-GO"}:
        state["consecutive_synthesis_failures"] = int(
            state.get("consecutive_synthesis_failures") or 0
        ) + 1
        if any("unsupported" in reason.casefold() for reason in reasons):
            state["consecutive_unsupported_outputs"] = int(
                state.get("consecutive_unsupported_outputs") or 0
            ) + 1
        else:
            state["consecutive_unsupported_outputs"] = 0

    hard_reasons: list[str] = []
    if safety_auditor_passed is False:
        hard_reasons.append("safety_auditor_failed")
    if verify_passed is False:
        hard_reasons.append("verify_red")
    if public_safe_export_scan_passed is False:
        hard_reasons.append("public_safe_export_scan_failed")
    if paid_budget_exceeded:
        hard_reasons.append("paid_run_budget_exceeded")
    unsafe_dirty = dirty_paths_in_unsafe_paths(dirty_paths or [])
    if unsafe_dirty:
        hard_reasons.append("dirty_tree_in_unsafe_paths: " + ", ".join(unsafe_dirty[:5]))
    if int(state.get("consecutive_synthesis_failures") or 0) >= threshold:
        hard_reasons.append("consecutive_synthesis_failures_threshold")
    if int(state.get("consecutive_unsupported_outputs") or 0) >= threshold:
        hard_reasons.append("consecutive_unsupported_outputs_threshold")

    if hard_reasons:
        state["status"] = "open"
        state["latest_stop_reason"] = hard_reasons[0]
        state["opened_at"] = state.get("opened_at") or utc_now_iso()
    elif state.get("status") != "open":
        state["status"] = "closed"
        if reasons:
            state["latest_stop_reason"] = reasons[0]

    save_circuit_breaker(state, root=project_root)
    return state


def dirty_paths_in_unsafe_paths(dirty_paths: list[str]) -> list[str]:
    unsafe: list[str] = []
    for raw in dirty_paths:
        path = raw[3:].strip() if len(raw) > 3 and raw[:2].strip() else raw.strip()
        normalized = path.replace("\\", "/")
        if any(normalized.startswith(prefix) for prefix in SAFE_DIRTY_PREFIXES):
            continue
        if any(normalized.startswith(prefix) for prefix in UNSAFE_DIR_PREFIXES):
            unsafe.append(normalized)
    return unsafe


def load_governor_ledger(*, root: Path | None = None) -> dict[str, Any]:
    path = ledger_path(root=root)
    payload = _load_json(path) if path.is_file() else None
    if payload is None or payload.get("schema_version") != LEDGER_SCHEMA_VERSION:
        return {"schema_version": LEDGER_SCHEMA_VERSION, "reviews": []}
    reviews = payload.get("reviews")
    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "reviews": [row for row in reviews if isinstance(row, dict)] if isinstance(reviews, list) else [],
    }


def save_governor_ledger(ledger: dict[str, Any], *, root: Path | None = None) -> Path:
    path = ledger_path(root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    ledger["schema_version"] = LEDGER_SCHEMA_VERSION
    path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    return path


def _provider_allowlist(provider_id: str) -> tuple[bool, str]:
    raw = (
        os.environ.get("RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST")
        or os.environ.get("RGE_CLOUD_PROVIDER_ALLOWLIST")
        or ""
    ).strip()
    if not raw:
        return False, "provider allowlist missing: set RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST"
    allowed = {item.strip().casefold() for item in raw.split(",") if item.strip()}
    return provider_id.casefold() in allowed, raw


def evaluate_budget_gate(
    *,
    provider_id: str | None = None,
    output: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved = normalize_provider_id(provider_id or (output or {}).get("provider"))
    reasons: list[str] = []
    max_usd_raw = os.environ.get("RGE_CLOUD_MAX_USD_PER_RUN", "").strip()
    max_tokens_raw = os.environ.get("RGE_CLOUD_MAX_TOKENS_PER_CALL", "").strip()
    allowlisted, allowlist_raw = _provider_allowlist(resolved)
    if not allowlisted:
        reasons.append(f"provider {resolved!r} not in explicit allowlist")
    if not max_usd_raw:
        reasons.append("RGE_CLOUD_MAX_USD_PER_RUN is required")
    if not max_tokens_raw:
        reasons.append("RGE_CLOUD_MAX_TOKENS_PER_CALL is required")

    max_usd: float | None = None
    max_tokens: int | None = None
    try:
        max_usd = float(max_usd_raw) if max_usd_raw else None
        max_tokens = int(float(max_tokens_raw)) if max_tokens_raw else None
    except ValueError:
        reasons.append("cloud budget caps must be numeric")
    if max_usd is not None and max_usd <= 0:
        reasons.append("RGE_CLOUD_MAX_USD_PER_RUN must be > 0")
    if max_tokens is not None and max_tokens <= 0:
        reasons.append("RGE_CLOUD_MAX_TOKENS_PER_CALL must be > 0")

    usage = (output or {}).get("usage") if isinstance((output or {}).get("usage"), dict) else {}
    cost_estimate = (output or {}).get("cost_estimate_usd")
    recorded_cost = usage.get("usd") or usage.get("cost_usd") or cost_estimate
    no_paid_api_calls = bool((output or {}).get("no_paid_api_calls"))
    if output is not None and not no_paid_api_calls:
        if recorded_cost is None and not usage:
            reasons.append("run-level cost estimate or recorded usage is required")
        elif recorded_cost is not None:
            try:
                cost_value = float(recorded_cost)
            except (TypeError, ValueError):
                reasons.append("recorded cost must be numeric")
            else:
                if max_usd is not None and cost_value > max_usd:
                    reasons.append(
                        f"recorded cost {cost_value} exceeds RGE_CLOUD_MAX_USD_PER_RUN {max_usd}"
                    )
    return {
        "passed": not reasons,
        "reasons": reasons,
        "provider_id": resolved,
        "provider_allowlist": allowlist_raw,
        "max_usd_per_run": max_usd,
        "max_tokens_per_call": max_tokens,
        "recorded_cost_usd": recorded_cost,
        "no_paid_api_calls": no_paid_api_calls,
    }


def evaluate_input_gate(
    packet: dict[str, Any],
    *,
    graph_totals: dict[str, Any] | None = None,
    allow_low_maturity: bool = False,
) -> dict[str, Any]:
    reasons: list[str] = []
    metrics: dict[str, Any] = {}
    reasons.extend(validate_grounded_synthesis_packet(packet))
    reasons.extend(assert_synthesis_packet_operator_safe(packet))
    reasons.extend(_private_value_violations(packet, label="packet"))
    if is_refs_only_packet(packet):
        reasons.append("packet is refs-only")
    if not packet.get("trace_refs"):
        reasons.append("packet has no trace refs")
    if not packet.get("source_refs"):
        reasons.append("packet has no source refs")
    if not packet.get("claims"):
        reasons.append("packet has no claim grounding rows")
    if not packet.get("atoms"):
        reasons.append("packet has no atom grounding rows")
    if str(packet.get("schema_version") or "") != SCHEMA_VERSION_GROUNDED:
        reasons.append("packet is not grounded schema")
    # Grounding metadata is represented by text-backed claim/atom rows plus source/trace refs.
    if not claim_text_by_id(packet) or not atom_text_by_id(packet):
        reasons.append("packet has no grounding metadata")
    if graph_totals is not None and not allow_low_maturity:
        readiness = evaluate_synthesis_readiness(graph_totals)
        metrics["synthesis_readiness"] = readiness
        if readiness.get("openai_synthesis_blocked"):
            reasons.append(
                readiness.get("openai_block_reason")
                or "graph metrics below synthesis readiness threshold"
            )
    return {"passed": not reasons, "reasons": reasons, "metrics": metrics}


def _validate_output_citations(
    output: dict[str, Any],
    *,
    packet: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []
    allowed_claims = {str(row.get("claim_id")) for row in packet.get("claims") or [] if isinstance(row, dict) and row.get("claim_id")}
    allowed_atoms = {str(row.get("atom_id")) for row in packet.get("atoms") or [] if isinstance(row, dict) and row.get("atom_id")}
    allowed_sources = {str(row.get("source_id")) for row in packet.get("source_refs") or [] if isinstance(row, dict) and row.get("source_id")}
    sentences = output.get("summary_sentences") or []
    if not sentences:
        reasons.append("output contains no summary_sentences")
    for index, sentence in enumerate(sentences):
        if not isinstance(sentence, dict):
            reasons.append(f"summary_sentences[{index}] must be an object")
            continue
        text = str(sentence.get("text") or "").strip()
        claim_ids = [str(v) for v in (sentence.get("claim_ids") or []) if v]
        atom_ids = [str(v) for v in (sentence.get("atom_ids") or []) if v]
        source_refs = [str(v) for v in (sentence.get("source_refs") or []) if v]
        if not text:
            reasons.append(f"summary_sentences[{index}] missing text")
        if not claim_ids and not atom_ids:
            reasons.append(f"summary_sentences[{index}] missing claim_ids and atom_ids")
        if not source_refs:
            reasons.append(f"summary_sentences[{index}] missing source_refs")
        for claim_id in claim_ids:
            if claim_id not in allowed_claims:
                reasons.append(f"summary_sentences[{index}] cites missing claim_id {claim_id}")
        for atom_id in atom_ids:
            if atom_id not in allowed_atoms:
                reasons.append(f"summary_sentences[{index}] cites missing atom_id {atom_id}")
        for source_ref in source_refs:
            if source_ref not in allowed_sources:
                reasons.append(f"summary_sentences[{index}] cites missing source_ref {source_ref}")
    return reasons


def _output_policy_violations(output: dict[str, Any]) -> list[str]:
    reasons = _private_value_violations(output, label="output")
    for key_path, item in _iter_values(output):
        if not isinstance(item, str):
            continue
        for pattern in FORBIDDEN_ACTION_PATTERNS:
            if pattern.search(item):
                reasons.append(f"output.{key_path} attempts forbidden merge/push/publish/promote action")
        for pattern in FORBIDDEN_GATE_WEAKENING_PATTERNS:
            if pattern.search(item):
                reasons.append(f"output.{key_path} asks to weaken gates or increase budget")
    return reasons


def evaluate_output_gate(
    output: dict[str, Any],
    *,
    packet: dict[str, Any],
) -> dict[str, Any]:
    reasons = _validate_output_citations(output, packet=packet)
    reasons.extend(_output_policy_violations(output))
    grounding = evaluate_synthesis_grounding(output, packet=packet)
    for row in grounding.get("sentence_results") or []:
        if not row.get("grounded"):
            reasons.extend(str(issue) for issue in row.get("issues") or [])
    if grounding.get("needs_human_review"):
        reasons.append("output contains unsupported sentence text")
    return {
        "passed": not reasons,
        "reasons": reasons,
        "grounding": grounding,
    }


def _review_id(packet_id: str, output: dict[str, Any]) -> str:
    basis = json.dumps(
        {
            "packet_id": packet_id,
            "packet_sha256": output.get("packet_sha256"),
            "sentences": output.get("summary_sentences"),
        },
        sort_keys=True,
        default=str,
    )
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()
    return f"syn_gov_{digest[:12]}"


def _instruction_packet_name(packet_id: str) -> str:
    safe_packet_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", packet_id).strip("-") or "packet"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}_{safe_packet_id}.md"


def write_instruction_packet(
    *,
    packet: dict[str, Any],
    output: dict[str, Any],
    governor_result: dict[str, Any],
    root: Path | None = None,
) -> Path:
    project_root = root or repo_root()
    out_dir = instruction_packet_dir(root=project_root)
    out_dir.mkdir(parents=True, exist_ok=True)
    packet_id = str(packet.get("packet_id") or output.get("packet_id") or "synthesis_packet")
    path = out_dir / _instruction_packet_name(packet_id)

    claim_refs = sorted(
        {
            str(claim_id)
            for sentence in output.get("summary_sentences") or []
            if isinstance(sentence, dict)
            for claim_id in sentence.get("claim_ids") or []
        }
    )
    atom_refs = sorted(
        {
            str(atom_id)
            for sentence in output.get("summary_sentences") or []
            if isinstance(sentence, dict)
            for atom_id in sentence.get("atom_ids") or []
        }
    )
    source_refs = sorted(
        {
            str(source_ref)
            for sentence in output.get("summary_sentences") or []
            if isinstance(sentence, dict)
            for source_ref in sentence.get("source_refs") or []
        }
    )
    summary = " ".join(
        str(sentence.get("text") or "").strip()
        for sentence in output.get("summary_sentences") or []
        if isinstance(sentence, dict)
    ).strip()
    recommended = output.get("recommended_build_packet")
    if not isinstance(recommended, dict):
        recommended = {}
    likely_files = recommended.get("files_likely_affected") or recommended.get("expected_files") or [
        "rge/modules/",
        "tests/unit/",
        "agent_reports/",
    ]
    acceptance = recommended.get("acceptance_criteria") or [
        "Implementation preserves deterministic governor checks.",
        "No paid-model prose is applied directly as code.",
        "Relevant unit tests and safety audit pass.",
    ]
    tests = recommended.get("tests_to_run") or [
        "python -m pytest tests/unit/test_autonomous_synthesis_governor.py",
        "python -m rge.modules.safety_auditor --audit full",
    ]
    non_goals = recommended.get("non_goals") or [
        "Do not auto-merge, auto-push, auto-publish, or promote tickets.",
        "Do not copy paid-model output directly into implementation files.",
    ]
    rollback = recommended.get("rollback_plan") or (
        "Delete this instruction packet and rerun the governor after fixing the cited synthesis output."
    )
    lines = [
        f"# Autonomous Synthesis Instruction Packet: {packet_id}",
        "",
        "## Summary",
        summary or "No synthesis summary text was available.",
        "",
        "## Citations",
        f"- Claim refs: {', '.join(claim_refs) or 'none'}",
        f"- Atom refs: {', '.join(atom_refs) or 'none'}",
        f"- Source refs: {', '.join(source_refs) or 'none'}",
        "",
        "## Recommended Build Packet",
        str(recommended.get("title") or "Review the synthesis finding and draft a scoped implementation ticket."),
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
        "- This packet is a draft for local agents; it is not a ticket promotion.",
        "- Paid-model output must not directly modify code, queues, Git, or public exports.",
        f"- Governor verdict: {governor_result.get('governor_verdict')}.",
        "",
        "## Rollback Plan",
        rollback,
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def evaluate_synthesis_governor(
    *,
    packet: dict[str, Any],
    output: dict[str, Any] | None = None,
    graph_totals: dict[str, Any] | None = None,
    allow_low_maturity: bool = False,
    provider_id: str | None = None,
    root: Path | None = None,
    write_ledger: bool = True,
    write_instruction: bool = True,
    update_circuit: bool = True,
) -> dict[str, Any]:
    project_root = root or repo_root()
    reasons: list[str] = []
    metrics: dict[str, Any] = {}
    circuit = load_circuit_breaker(root=project_root)
    if circuit.get("status") == "open":
        reasons.append(f"circuit breaker open: {circuit.get('latest_stop_reason')}")

    input_gate = evaluate_input_gate(
        packet,
        graph_totals=graph_totals,
        allow_low_maturity=allow_low_maturity,
    )
    budget_gate = evaluate_budget_gate(provider_id=provider_id, output=output)
    metrics["input_gate"] = input_gate
    metrics["budget_gate"] = budget_gate
    reasons.extend(input_gate["reasons"])
    reasons.extend(budget_gate["reasons"])

    output_gate: dict[str, Any] | None = None
    if output is not None:
        output_gate = evaluate_output_gate(output, packet=packet)
        metrics["output_gate"] = output_gate
        reasons.extend(output_gate["reasons"])

    verdict = "GO" if not reasons else "NO-GO"
    if verdict != "GO" and input_gate.get("passed") and output is None:
        verdict = "PARTIAL"
    if verdict != "GO" and output_gate and output_gate.get("passed") and not budget_gate.get("passed"):
        verdict = "NO-GO"

    packet_id = str(packet.get("packet_id") or (output or {}).get("packet_id") or "unknown")
    reviewed_at = utc_now_iso()
    review = {
        "schema_version": GOVERNOR_SCHEMA_VERSION,
        "review_id": _review_id(packet_id, output or {"packet_id": packet_id}),
        "packet_id": packet_id,
        "reviewed_at": reviewed_at,
        "review_mode": "automated",
        "governor_verdict": verdict,
        "auto_signed_off": verdict == "GO",
        "status": "auto_signed_off" if verdict == "GO" else "flagged",
        "failure_reasons": reasons,
        "metrics": metrics,
        "forbidden_downstream_actions": [
            "auto_merge",
            "auto_push",
            "auto_publish",
            "auto_promote_ticket",
        ],
    }

    instruction_path: Path | None = None
    if verdict == "GO" and output is not None and write_instruction:
        instruction_path = write_instruction_packet(
            packet=packet,
            output=output,
            governor_result=review,
            root=project_root,
        )
        review["latest_instruction_packet"] = _safe_rel(instruction_path, project_root)

    if write_ledger:
        ledger = load_governor_ledger(root=project_root)
        existing = [
            row for row in ledger.get("reviews", []) if row.get("review_id") != review["review_id"]
        ]
        existing.append(review)
        ledger["reviews"] = existing
        save_governor_ledger(ledger, root=project_root)

    if update_circuit:
        circuit = update_circuit_breaker(
            verdict=verdict,
            failure_reasons=reasons,
            root=project_root,
            paid_budget_exceeded=any("exceeds RGE_CLOUD_MAX_USD_PER_RUN" in r for r in reasons),
        )
    review["circuit_breaker"] = {
        "status": circuit.get("status"),
        "latest_stop_reason": circuit.get("latest_stop_reason"),
        "consecutive_synthesis_failures": circuit.get("consecutive_synthesis_failures", 0),
        "consecutive_unsupported_outputs": circuit.get("consecutive_unsupported_outputs", 0),
    }
    return review


def attach_governor_review_to_output(
    output: dict[str, Any],
    governor_review: dict[str, Any],
) -> dict[str, Any]:
    output["review_mode"] = "automated"
    output["governor_verdict"] = governor_review.get("governor_verdict")
    output["auto_signed_off"] = bool(governor_review.get("auto_signed_off"))
    output["automated_review_status"] = governor_review.get("status")
    output["governor_review"] = {
        "schema_version": GOVERNOR_SCHEMA_VERSION,
        "review_id": governor_review.get("review_id"),
        "review_mode": "automated",
        "governor_verdict": governor_review.get("governor_verdict"),
        "status": governor_review.get("status"),
        "failure_reasons": list(governor_review.get("failure_reasons") or []),
        "latest_instruction_packet": governor_review.get("latest_instruction_packet"),
        "cost_summary": public_safe_cost_summary(governor_review),
    }
    return output


def public_safe_cost_summary(governor_review: dict[str, Any]) -> dict[str, Any]:
    budget = ((governor_review.get("metrics") or {}).get("budget_gate") or {})
    return {
        "provider_id": budget.get("provider_id"),
        "max_usd_per_run": budget.get("max_usd_per_run"),
        "max_tokens_per_call": budget.get("max_tokens_per_call"),
        "recorded_cost_usd": budget.get("recorded_cost_usd"),
        "no_paid_api_calls": budget.get("no_paid_api_calls"),
    }


def apply_governor_status_to_review_queue(
    review_queue: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in review_queue:
        copy = dict(row)
        review = copy.get("governor_review") if isinstance(copy.get("governor_review"), dict) else {}
        verdict = str(copy.get("governor_verdict") or review.get("governor_verdict") or "")
        auto_signed = bool(copy.get("auto_signed_off") or review.get("status") == "auto_signed_off")
        copy["review_mode"] = str(copy.get("review_mode") or review.get("review_mode") or "manual")
        copy["governor_verdict"] = verdict or "UNKNOWN"
        copy["auto_signed_off"] = auto_signed
        copy["automated_review_status"] = (
            "auto_signed_off" if auto_signed and verdict == "GO" else "flagged"
        )
        if auto_signed and verdict == "GO":
            copy["sign_off_status"] = "signed_off"
            copy["sign_off_id"] = str(review.get("review_id") or "auto_governor")
            copy["signed_off_at"] = str(review.get("reviewed_at") or "")
        enriched.append(copy)
    return enriched


def circuit_breaker_audit_path(*, root: Path | None = None) -> Path:
    return _operator_path(root or repo_root(), DEFAULT_CIRCUIT_AUDIT_REL)


def circuit_breaker_status_report_path(*, root: Path | None = None) -> Path:
    return _operator_path(root or repo_root(), DEFAULT_CIRCUIT_STATUS_REPORT_REL)


def refresh_circuit_breaker_status_report(*, root: Path | None = None) -> dict[str, Any]:
    """Read-only circuit breaker inspection; writes a public-safe status report."""
    project_root = root or repo_root()
    guidance = build_circuit_breaker_operator_guidance(root=project_root)
    payload = {
        "schema_version": CIRCUIT_SCHEMA_VERSION,
        "recorded_at": utc_now_iso(),
        "command": "inspect_circuit_breaker",
        "read_only": True,
        "circuit_breaker_guidance": guidance,
        "circuit_breaker_status": guidance.get("circuit_breaker_status"),
    }
    violations = assert_no_private_fields({"circuit_breaker_status_report": payload})
    if violations:
        raise ValueError(
            "Circuit breaker status report blocked: " + "; ".join(violations[:5])
        )
    path = circuit_breaker_status_report_path(root=project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    payload["status_report_path"] = _safe_rel(path, project_root)
    return payload


def append_circuit_breaker_audit_record(
    record: dict[str, Any],
    *,
    root: Path | None = None,
) -> Path:
    project_root = root or repo_root()
    path = circuit_breaker_audit_path(root=project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(record)
    payload.setdefault("recorded_at", utc_now_iso())
    payload.setdefault("schema_version", CIRCUIT_SCHEMA_VERSION)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return path


def build_circuit_breaker_operator_guidance(*, root: Path | None = None) -> dict[str, Any]:
    """Public-safe circuit breaker dashboard guidance for Atlas/operator surfaces."""
    project_root = root or repo_root()
    circuit = load_circuit_breaker(root=project_root)
    ledger = ledger_path(root=project_root)
    audit = circuit_breaker_audit_path(root=project_root)
    status = str(circuit.get("status") or "closed")
    guidance = {
        "schema_version": GOVERNOR_SCHEMA_VERSION,
        "circuit_breaker_status": status,
        "reason_opened": circuit.get("latest_stop_reason") if status == "open" else None,
        "consecutive_synthesis_failures": int(circuit.get("consecutive_synthesis_failures") or 0),
        "consecutive_unsupported_outputs": int(
            circuit.get("consecutive_unsupported_outputs") or 0
        ),
        "opened_at": circuit.get("opened_at"),
        "latest_ledger_path": _safe_rel(ledger, project_root) if ledger.is_file() else None,
        "latest_audit_log_path": _safe_rel(audit, project_root) if audit.is_file() else None,
        "reset_instructions": (
            "Circuit breaker is open. Inspect the latest stop reason and ledger, "
            "fix the underlying synthesis/safety issue, then run the explicit local "
            f"reset command: python {GOVERNOR_CLI_SCRIPT} --reset-circuit-breaker "
            "--confirm-reset --operator <label>. Reset is local-only and writes an "
            "audit record; it does not auto-merge, auto-push, auto-publish, or promote tickets."
        ),
        "forbidden_actions": [
            "auto_merge",
            "auto_push",
            "auto_publish",
            "auto_promote_ticket",
        ],
    }
    violations = assert_no_private_fields({"circuit_breaker_guidance": guidance})
    if violations:
        raise ValueError(
            "Circuit breaker guidance blocked: " + "; ".join(violations[:5])
        )
    return guidance


def reset_circuit_breaker(
    *,
    root: Path | None = None,
    operator_label: str = "operator",
    reason: str = "",
    confirm: bool = False,
) -> dict[str, Any]:
    """Explicit local-only circuit breaker reset with audit record."""
    if not confirm:
        raise GovernorOperatorSurfaceError(
            "Circuit breaker reset requires --confirm-reset (local operator action)."
        )
    project_root = root or repo_root()
    previous = load_circuit_breaker(root=project_root)
    if str(previous.get("status") or "closed") != "open":
        return {
            "status": "skipped",
            "detail": "Circuit breaker is already closed.",
            "circuit_breaker": previous,
        }
    audit_record = {
        "event": "circuit_breaker_reset",
        "operator_label": operator_label,
        "reason": reason or "operator_confirmed_reset",
        "previous_status": previous.get("status"),
        "previous_stop_reason": previous.get("latest_stop_reason"),
        "previous_consecutive_synthesis_failures": previous.get(
            "consecutive_synthesis_failures"
        ),
        "previous_consecutive_unsupported_outputs": previous.get(
            "consecutive_unsupported_outputs"
        ),
        "previous_opened_at": previous.get("opened_at"),
    }
    audit_path = append_circuit_breaker_audit_record(audit_record, root=project_root)
    reset_state = empty_circuit_state()
    reset_state["latest_stop_reason"] = "operator_reset"
    reset_state["updated_at"] = utc_now_iso()
    save_circuit_breaker(reset_state, root=project_root)
    return {
        "status": "completed",
        "detail": "Circuit breaker reset locally; failure history preserved in audit log.",
        "audit_record_path": _safe_rel(audit_path, project_root),
        "circuit_breaker": reset_state,
    }


def _artifact_is_stale(artifact_path: Path, *, root: Path) -> bool:
    if not artifact_path.is_file():
        return True
    artifact_mtime = artifact_path.stat().st_mtime
    exports_dir = root / "data/exports"
    if not exports_dir.is_dir():
        return False
    for pattern in SYNTHESIS_OUTPUT_GLOBS:
        for path in exports_dir.glob(pattern):
            if path.is_file() and path.stat().st_mtime > artifact_mtime:
                return True
    return False


def _validate_human_review_artifact(payload: dict[str, Any], *, label: str) -> list[str]:
    reasons: list[str] = []
    if str(payload.get("schema_version") or "") != HUMAN_REVIEW_ARTIFACT_SCHEMA:
        reasons.append(f"{label} schema_version must be {HUMAN_REVIEW_ARTIFACT_SCHEMA!r}")
    summary = payload.get("review_summary") or {}
    if int(summary.get("total_outputs") or 0) < 1:
        reasons.append(f"{label} review_summary.total_outputs must be >= 1")
    if not isinstance(payload.get("review_queue"), list):
        reasons.append(f"{label} review_queue must be a list")
    return reasons


def _pick_review_row(review_queue: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [row for row in review_queue if isinstance(row, dict)]
    if not candidates:
        return None
    for row in candidates:
        if (
            row.get("review_status") == "grounding_passed"
            and not row.get("auto_signed_off")
            and row.get("governor_verdict") != "GO"
        ):
            return row
    for row in candidates:
        if row.get("review_status") == "grounding_passed":
            return row
    return candidates[0]


def _resolve_packet_for_output(
    output: dict[str, Any],
    *,
    root: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    packet: dict[str, Any] | None = None
    if output_path is not None:
        sibling = output_path.parent / "grounded_packet.json"
        if sibling.is_file():
            packet = _load_json(sibling)
    if packet is None:
        fixture = root / GROUNDED_PACKET_FIXTURE_REL
        packet = _load_json(fixture) if fixture.is_file() else None
    if packet is None:
        raise GovernorOperatorSurfaceError(
            "No grounded packet found for synthesis output (expected grounded_packet.json "
            f"adjacent to output or fixture at {GROUNDED_PACKET_FIXTURE_REL.as_posix()})."
        )
    packet_errors = validate_grounded_synthesis_packet(packet)
    if packet_errors:
        raise GovernorOperatorSurfaceError(
            "Grounded packet failed validation: " + "; ".join(packet_errors[:5])
        )
    if is_refs_only_packet(packet):
        raise GovernorOperatorSurfaceError("Grounded packet is refs-only.")
    return packet


def _resolve_output_from_review_row(
    row: dict[str, Any],
    *,
    root: Path,
) -> tuple[dict[str, Any], Path | None]:
    source_ref = str(row.get("operator_output_ref") or "").strip()
    output_path: Path | None = None
    output: dict[str, Any] | None = None
    if source_ref:
        candidate = root / source_ref
        if candidate.is_file():
            output = _load_json(candidate)
            output_path = candidate
    if output is None and row.get("summary_sentences"):
        output = {
            "schema_version": "synthesis_output_v0.1.0",
            "packet_id": row.get("packet_id"),
            "packet_sha256": row.get("packet_sha256"),
            "provider": row.get("provider"),
            "summary_sentences": row.get("summary_sentences") or [],
            "review_status": row.get("review_status"),
            "needs_human_review": row.get("needs_human_review"),
            "governor_verdict": row.get("governor_verdict"),
            "auto_signed_off": row.get("auto_signed_off"),
            "governor_review": row.get("governor_review") or {},
        }
    if output is None or not output.get("summary_sentences"):
        raise GovernorOperatorSurfaceError(
            "Review row has no readable synthesis output (missing operator_output_ref)."
        )
    return output, output_path


def discover_latest_synthesis_artifact(
    *,
    root: Path | None = None,
    artifact_path: Path | None = None,
    latest: bool = False,
) -> dict[str, Any]:
    """Find the latest synthesis review artifact or synthesis output safely."""
    project_root = root or repo_root()
    if artifact_path is not None:
        resolved = artifact_path if artifact_path.is_absolute() else project_root / artifact_path
        if not resolved.is_file():
            raise GovernorOperatorSurfaceError(f"Artifact not found: {_safe_rel(resolved, project_root)}")
        payload = _load_json(resolved)
        if payload is None:
            raise GovernorOperatorSurfaceError(
                f"Artifact is unreadable or invalid JSON: {_safe_rel(resolved, project_root)}"
            )
        return {
            "artifact_path": _safe_rel(resolved, project_root),
            "artifact_kind": "human_review" if "review_queue" in payload else "synthesis_output",
            "artifact_payload": payload,
            "stale": _artifact_is_stale(resolved, root=project_root),
        }

    if not latest:
        raise GovernorOperatorSurfaceError(
            "No artifact specified. Pass --artifact PATH or --latest."
        )

    candidates: list[tuple[float, Path, str]] = []
    for rel in ARTIFACT_SEARCH_REL_PATHS:
        path = project_root / rel
        if path.is_file():
            candidates.append((path.stat().st_mtime, path, "human_review"))
    exports_dir = project_root / "data/exports"
    if exports_dir.is_dir():
        for pattern in SYNTHESIS_OUTPUT_GLOBS:
            for path in exports_dir.glob(pattern):
                if path.is_file():
                    candidates.append((path.stat().st_mtime, path, "synthesis_output"))
    if not candidates:
        raise GovernorOperatorSurfaceError(
            "No synthesis review artifact or synthesis output found."
        )
    candidates.sort(key=lambda row: row[0], reverse=True)
    _, selected, kind = candidates[0]
    payload = _load_json(selected)
    if payload is None:
        raise GovernorOperatorSurfaceError(
            f"Latest artifact is unreadable or invalid JSON: {_safe_rel(selected, project_root)}"
        )
    return {
        "artifact_path": _safe_rel(selected, project_root),
        "artifact_kind": kind,
        "artifact_payload": payload,
        "stale": _artifact_is_stale(selected, root=project_root),
    }


def resolve_governor_inputs_from_artifact(
    discovery: dict[str, Any],
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Resolve packet/output/review row from a discovered artifact."""
    project_root = root or repo_root()
    payload = discovery.get("artifact_payload") or {}
    artifact_path = Path(discovery.get("artifact_path") or "")
    reasons: list[str] = []
    if discovery.get("stale"):
        reasons.append("artifact is stale relative to newer synthesis exports")
    if discovery.get("artifact_kind") == "human_review":
        reasons.extend(_validate_human_review_artifact(payload, label="artifact"))
        review_queue = payload.get("review_queue") or []
        row = _pick_review_row(review_queue)
        if row is None:
            raise GovernorOperatorSurfaceError("Human-review artifact has no review_queue rows.")
        output, output_path = _resolve_output_from_review_row(row, root=project_root)
        packet = _resolve_packet_for_output(output, root=project_root, output_path=output_path)
        input_gate = evaluate_input_gate(packet)
        reasons.extend(input_gate["reasons"])
        if reasons:
            raise GovernorOperatorSurfaceError("; ".join(reasons))
        return {
            "artifact_path": discovery.get("artifact_path"),
            "artifact_kind": "human_review",
            "review_row": row,
            "packet": packet,
            "output": output,
            "output_path": _safe_rel(output_path, project_root) if output_path else None,
        }

    output = payload
    if not output.get("summary_sentences"):
        raise GovernorOperatorSurfaceError("Synthesis output artifact missing summary_sentences.")
    output_path = project_root / artifact_path if artifact_path else None
    packet = _resolve_packet_for_output(
        output,
        root=project_root,
        output_path=output_path if output_path and output_path.is_file() else None,
    )
    input_gate = evaluate_input_gate(packet)
    reasons.extend(input_gate["reasons"])
    if reasons:
        raise GovernorOperatorSurfaceError("; ".join(reasons))
    return {
        "artifact_path": discovery.get("artifact_path"),
        "artifact_kind": "synthesis_output",
        "review_row": None,
        "packet": packet,
        "output": output,
        "output_path": discovery.get("artifact_path"),
    }


def _default_graph_totals() -> dict[str, int]:
    return {
        "multi_claim_atom_count": 2,
        "source_diverse_atom_count": 2,
        "synthesis_ready_cluster_count": 1,
        "weak_atom_count": 0,
    }


def refresh_atlas_after_governor_run(
    *,
    governor_review: dict[str, Any],
    resolved_inputs: dict[str, Any],
    root: Path | None = None,
    sync_public: bool = False,
) -> dict[str, Any]:
    from rge.modules.synthesis_human_review_ui import (
        ARTIFACT_NAME,
        build_atlas_safe_human_review_artifact,
        build_review_entry,
        sync_human_review_artifact_to_public_site,
    )

    project_root = root or repo_root()
    output = dict(resolved_inputs.get("output") or {})
    attach_governor_review_to_output(output, governor_review)
    review_row = build_review_entry(
        output,
        source_path=resolved_inputs.get("output_path"),
    )
    artifact = build_atlas_safe_human_review_artifact([review_row], root=project_root)
    export_dir = project_root / "data/exports/synthesis_human_review_ui"
    export_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = export_dir / ARTIFACT_NAME
    artifact_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    public_path: Path | None = None
    if sync_public:
        public_path = sync_human_review_artifact_to_public_site(artifact, root=project_root)
    return {
        "artifact_path": _safe_rel(artifact_path, project_root),
        "public_artifact_path": _safe_rel(public_path, project_root) if public_path else None,
        "governor_summary": artifact.get("governor_summary") or {},
        "circuit_breaker_guidance": artifact.get("circuit_breaker_guidance") or {},
    }


def run_autonomous_governor_operator_command(
    *,
    artifact_path: Path | None = None,
    latest: bool = False,
    dry_run: bool = False,
    write_instruction_packet: bool = False,
    sync_public: bool = False,
    allow_low_maturity: bool = False,
    reset_circuit_breaker_flag: bool = False,
    confirm_reset: bool = False,
    inspect_circuit_breaker: bool = False,
    operator_label: str = "operator",
    reset_reason: str = "",
    root: Path | None = None,
) -> tuple[dict[str, Any], int]:
    """Run governor operator surface; returns (payload, exit_code)."""
    project_root = root or repo_root()

    if inspect_circuit_breaker or reset_circuit_breaker_flag:
        guidance = build_circuit_breaker_operator_guidance(root=project_root)
        payload: dict[str, Any] = {
            "status": "completed",
            "command": "inspect_circuit_breaker",
            "circuit_breaker_guidance": guidance,
        }
        if reset_circuit_breaker_flag:
            reset_result = reset_circuit_breaker(
                root=project_root,
                operator_label=operator_label,
                reason=reset_reason,
                confirm=confirm_reset,
            )
            payload["reset_result"] = reset_result
            payload["circuit_breaker_guidance"] = build_circuit_breaker_operator_guidance(
                root=project_root
            )
            payload["status"] = reset_result.get("status", "completed")
        return payload, 0 if payload.get("status") != "error" else 1

    circuit = load_circuit_breaker(root=project_root)
    if circuit.get("status") == "open":
        guidance = build_circuit_breaker_operator_guidance(root=project_root)
        return (
            {
                "status": "blocked",
                "command": "run_governor",
                "governor_verdict": "NO-GO",
                "detail": "Circuit breaker is open; inspect and reset before live governor run.",
                "stop_reason": circuit.get("latest_stop_reason"),
                "circuit_breaker_guidance": guidance,
            },
            2,
        )

    discovery = discover_latest_synthesis_artifact(
        root=project_root,
        artifact_path=artifact_path,
        latest=latest or artifact_path is None,
    )
    resolved = resolve_governor_inputs_from_artifact(discovery, root=project_root)
    provider_id = str((resolved.get("output") or {}).get("provider") or "mock_cloud")
    governor_review = evaluate_synthesis_governor(
        packet=resolved["packet"],
        output=resolved["output"],
        graph_totals=_default_graph_totals(),
        allow_low_maturity=allow_low_maturity,
        provider_id=provider_id,
        root=project_root,
        write_ledger=not dry_run,
        write_instruction=not dry_run and write_instruction_packet,
        update_circuit=not dry_run,
    )
    verdict = str(governor_review.get("governor_verdict") or "NO-GO")
    payload = {
        "status": "completed" if verdict == "GO" else "completed_with_review",
        "command": "run_governor",
        "dry_run": dry_run,
        "artifact_path": discovery.get("artifact_path"),
        "artifact_kind": discovery.get("artifact_kind"),
        "governor_verdict": verdict,
        "auto_signed_off": bool(governor_review.get("auto_signed_off")),
        "failure_reasons": list(governor_review.get("failure_reasons") or []),
        "latest_instruction_packet": governor_review.get("latest_instruction_packet"),
        "circuit_breaker": governor_review.get("circuit_breaker") or {},
        "circuit_breaker_guidance": build_circuit_breaker_operator_guidance(root=project_root),
    }
    if verdict != "GO":
        payload["stop_reason"] = (governor_review.get("failure_reasons") or ["governor rejected"])[0]
    if not dry_run and sync_public:
        payload["atlas_refresh"] = refresh_atlas_after_governor_run(
            governor_review=governor_review,
            resolved_inputs=resolved,
            root=project_root,
            sync_public=True,
        )
    exit_code = 0 if verdict == "GO" else 1
    return payload, exit_code


def governor_operator_commands(*, root: Path | None = None) -> dict[str, str]:
    del root
    prefix = f"python {GOVERNOR_CLI_SCRIPT}"
    return {
        "run_governor_latest": f"{prefix} --latest --write-instruction-packet --sync-public",
        "run_governor_dry_run": f"{prefix} --latest --dry-run",
        "inspect_circuit_breaker": f"{prefix} --inspect-circuit-breaker",
        "reset_circuit_breaker": (
            f"{prefix} --reset-circuit-breaker --confirm-reset --operator operator"
        ),
        "instruction_packet_ticket_draft": (
            "python scripts/run_instruction_packet_ticket_draft.py --latest"
        ),
        "instruction_packet_handoff": (
            "python scripts/run_instruction_packet_ticket_draft.py --latest"
        ),
        "local_implementation_handoff": (
            "Inspect the latest draft ticket under data/operator/draft_tickets/ "
            "and implement locally via CLI/IDE agent only."
        ),
        "draft_expected_files_backfill": (
            "python scripts/run_draft_expected_files_backfill.py --latest"
        ),
    }


def summarize_governor_status(review_queue: list[dict[str, Any]], *, root: Path | None = None) -> dict[str, Any]:
    project_root = root or repo_root()
    auto_count = sum(1 for row in review_queue if row.get("auto_signed_off") is True)
    flagged_count = sum(1 for row in review_queue if row.get("governor_verdict") in {"NO-GO", "PARTIAL"})
    latest_instruction = None
    provider_counts: dict[str, int] = {}
    latest_cost_summary: dict[str, Any] | None = None
    for row in review_queue:
        provider = str(row.get("provider") or "unknown")
        provider_counts[provider] = provider_counts.get(provider, 0) + 1
        review = row.get("governor_review") if isinstance(row.get("governor_review"), dict) else {}
        if review.get("latest_instruction_packet"):
            latest_instruction = str(review.get("latest_instruction_packet"))
        cost = review.get("cost_summary")
        if isinstance(cost, dict):
            latest_cost_summary = cost
    circuit = load_circuit_breaker(root=project_root)
    circuit_guidance = build_circuit_breaker_operator_guidance(root=project_root)
    from rge.modules.instruction_packet_ticket_draft import (
        inspect_instruction_packet_ticket_draft_status,
        latest_draft_ticket,
    )

    draft_ticket_status = inspect_instruction_packet_ticket_draft_status(root=project_root)
    draft_status = latest_draft_ticket(root=project_root)
    summary = {
        "schema_version": GOVERNOR_SCHEMA_VERSION,
        "review_mode": "automated",
        "automated_review_verdict": "GO" if flagged_count == 0 and auto_count > 0 else ("NO-GO" if flagged_count > 0 else "UNKNOWN"),
        "auto_signed_off_count": auto_count,
        "flagged_count": flagged_count,
        "circuit_breaker_status": circuit.get("status"),
        "latest_stop_reason": circuit.get("latest_stop_reason"),
        "latest_generated_instruction_packet": latest_instruction,
        "latest_draft_ticket_path": draft_status.get("draft_ticket_path"),
        "draft_ticket_status": draft_status.get("status", "missing"),
        "draft_expected_files_backfill_recommended": draft_ticket_status.get(
            "draft_expected_files_backfill_recommended"
        ),
        "expected_files_backfilled_at": draft_ticket_status.get("expected_files_backfilled_at"),
        "last_patch_revalidation": draft_ticket_status.get("last_patch_revalidation"),
        "instruction_packet_ticket_draft_recommended": bool(
            latest_instruction and draft_status.get("status") != "available"
        ),
        "local_implementation_handoff_recommended": draft_status.get("status") == "available",
        "provider_summary": provider_counts,
        "cost_summary": latest_cost_summary or {},
        "circuit_breaker_guidance": circuit_guidance,
        "forbidden_actions": [
            "auto_merge",
            "auto_push",
            "auto_publish",
            "auto_promote_ticket",
        ],
    }
    violations = assert_no_private_fields({"governor_summary": summary})
    if violations:
        raise ValueError("Governor public summary blocked: " + "; ".join(violations[:5]))
    return summary


def inspect_autonomous_synthesis_governor_plan_status(
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    project_root = root or repo_root()
    artifact_path = project_root / DEFAULT_ATLAS_ARTIFACT_REL
    rel_artifact = _safe_rel(artifact_path, project_root)
    payload = _load_json(artifact_path) if artifact_path.is_file() else None
    circuit = load_circuit_breaker(root=project_root)
    commands = governor_operator_commands(root=project_root)
    circuit_guidance = build_circuit_breaker_operator_guidance(root=project_root)
    from rge.modules.instruction_packet_ticket_draft import (
        inspect_instruction_packet_ticket_draft_status,
    )

    draft_status = inspect_instruction_packet_ticket_draft_status(root=project_root)
    status: dict[str, Any] = {
        "status": "available" if artifact_path.is_file() else "unavailable",
        "artifact_path": rel_artifact,
        "governor_recommended": False,
        "instruction_packet_generation_recommended": False,
        "instruction_packet_handoff_recommended": False,
        "instruction_packet_ticket_draft_recommended": False,
        "local_implementation_handoff_recommended": False,
        "draft_expected_files_backfill_recommended": False,
        "circuit_breaker_inspection_recommended": circuit.get("status") == "open",
        "governor_verdict": "UNKNOWN",
        "auto_signed_off_count": 0,
        "flagged_count": 0,
        "circuit_breaker_status": circuit.get("status"),
        "latest_stop_reason": circuit.get("latest_stop_reason"),
        "latest_generated_instruction_packet": None,
        "latest_draft_ticket_path": draft_status.get("latest_draft_ticket_path"),
        "draft_ticket_status": draft_status.get("draft_ticket_status", "missing"),
        "draft_expected_files_backfill_recommended": draft_status.get(
            "draft_expected_files_backfill_recommended"
        ),
        "circuit_breaker_guidance": circuit_guidance,
        "operator_commands": {
            **commands,
            **(draft_status.get("operator_commands") or {}),
        },
    }
    if not payload:
        status["governor_recommended"] = circuit.get("status") != "open"
        return status
    summary = payload.get("governor_summary") or {}
    sign_off = payload.get("sign_off_summary") or {}
    status.update(
        {
            "governor_verdict": summary.get("automated_review_verdict", "UNKNOWN"),
            "auto_signed_off_count": int(summary.get("auto_signed_off_count") or 0),
            "flagged_count": int(summary.get("flagged_count") or 0),
            "latest_generated_instruction_packet": summary.get(
                "latest_generated_instruction_packet"
            ),
        }
    )
    pending = int(sign_off.get("pending_sign_off_count") or 0)
    status["governor_recommended"] = (
        circuit.get("status") != "open"
        and pending > 0
        and status["governor_verdict"] != "GO"
    )
    status["instruction_packet_generation_recommended"] = (
        circuit.get("status") != "open"
        and status["governor_verdict"] == "GO"
        and status["auto_signed_off_count"] > 0
        and not status["latest_generated_instruction_packet"]
    )
    status["instruction_packet_ticket_draft_recommended"] = (
        circuit.get("status") != "open"
        and status["governor_verdict"] == "GO"
        and bool(status["latest_generated_instruction_packet"])
        and draft_status.get("draft_ticket_status") != "available"
    )
    status["local_implementation_handoff_recommended"] = (
        circuit.get("status") != "open"
        and status["governor_verdict"] == "GO"
        and draft_status.get("draft_ticket_status") == "available"
        and not draft_status.get("draft_expected_files_backfill_recommended")
    )
    status["draft_expected_files_backfill_recommended"] = (
        circuit.get("status") != "open"
        and bool(draft_status.get("draft_expected_files_backfill_recommended"))
    )
    status["instruction_packet_handoff_recommended"] = (
        status["instruction_packet_ticket_draft_recommended"]
        or status["local_implementation_handoff_recommended"]
    )
    return status


def _public_cli_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Strip potentially sensitive nested content before printing CLI JSON."""
    safe = dict(payload)
    for key in ("artifact_payload", "packet", "output", "review_row"):
        safe.pop(key, None)
    return safe


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Autonomous synthesis safety governor operator surface.",
    )
    parser.add_argument("--artifact", type=Path, default=None, help="Explicit artifact path.")
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Discover the latest synthesis review artifact or synthesis output.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Evaluate governor without writing ledger, instruction packet, or circuit state.",
    )
    parser.add_argument(
        "--write-instruction-packet",
        action="store_true",
        help="Write a local instruction packet when governor verdict is GO.",
    )
    parser.add_argument(
        "--sync-public",
        action="store_true",
        help="Refresh the Atlas-safe human-review artifact after a successful governor run.",
    )
    parser.add_argument(
        "--allow-low-maturity",
        action="store_true",
        help="Allow graph metrics below synthesis readiness threshold.",
    )
    parser.add_argument(
        "--inspect-circuit-breaker",
        action="store_true",
        help="Print public-safe circuit breaker guidance.",
    )
    parser.add_argument(
        "--reset-circuit-breaker",
        action="store_true",
        help="Explicit local-only circuit breaker reset (requires --confirm-reset).",
    )
    parser.add_argument(
        "--confirm-reset",
        action="store_true",
        help="Confirm explicit circuit breaker reset.",
    )
    parser.add_argument(
        "--operator",
        default="operator",
        help="Operator label stored in circuit breaker audit records.",
    )
    parser.add_argument(
        "--reset-reason",
        default="",
        help="Optional operator reason for circuit breaker reset audit record.",
    )
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.inspect_circuit_breaker or args.reset_circuit_breaker:
        payload, exit_code = run_autonomous_governor_operator_command(
            inspect_circuit_breaker=args.inspect_circuit_breaker or args.reset_circuit_breaker,
            reset_circuit_breaker_flag=args.reset_circuit_breaker,
            confirm_reset=args.confirm_reset,
            operator_label=args.operator,
            reset_reason=args.reset_reason,
            root=args.root,
        )
        print(json.dumps(_public_cli_payload(payload), indent=2))
        return exit_code

    if not args.artifact and not args.latest:
        run_flags = (
            args.dry_run,
            args.write_instruction_packet,
            args.sync_public,
            args.allow_low_maturity,
        )
        if any(run_flags):
            print(
                json.dumps(
                    {
                        "status": "error",
                        "detail": "Governor run requires --artifact PATH or --latest.",
                    },
                    indent=2,
                )
            )
            return 2
        payload = inspect_autonomous_synthesis_governor_plan_status(root=args.root)
        print(json.dumps(_public_cli_payload(payload), indent=2))
        return 0 if payload.get("circuit_breaker_status") != "open" else 1

    payload, exit_code = run_autonomous_governor_operator_command(
        artifact_path=args.artifact,
        latest=args.latest,
        dry_run=args.dry_run,
        write_instruction_packet=args.write_instruction_packet,
        sync_public=args.sync_public,
        allow_low_maturity=args.allow_low_maturity,
        root=args.root,
    )
    print(json.dumps(_public_cli_payload(payload), indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
