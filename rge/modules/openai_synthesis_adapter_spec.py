"""OpenAI / paid cloud synthesis adapter contract (ticket-059).

Mock-first cloud synthesis adapter with fail-closed env gates, evidence-packet
input contract, cost caps, and synthesis-readiness prerequisites. Live OpenAI
HTTP is opt-in only and blocked unless every explicit gate passes.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from rge.contracts.synthesis_evidence_packet_v0 import (
    SCHEMA_VERSION as PACKET_SCHEMA_VERSION,
    validate_synthesis_evidence_packet,
)
from rge.llm.cloud_synthesis_registry import get_cloud_synthesis_client
from rge.llm.openai_synthesis_client import (
    build_public_safe_live_status,
    missing_live_openai_http_gates,
)
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.multi_claim_atom_clustering import (
    SYNTHESIS_READY_THRESHOLDS,
    evaluate_synthesis_readiness,
)
from rge.modules.operator_env_loader import openai_key_available
from rge.modules.principal_audit_gate import repo_root

PACKET_ID = "openai-synthesis-adapter-spec"
SPEC_SCHEMA_VERSION = "atlas_openai_synthesis_adapter_spec_v0.1.0"
SPEC_ARTIFACT_NAME = "atlas_openai_synthesis_adapter_spec_latest.json"
SPEC_RUN_ID = "run_openai_synthesis_adapter_spec"

DEFAULT_COST_CAPS = {
    "RGE_CLOUD_MAX_USD_PER_RUN": "0.50",
    "RGE_CLOUD_MAX_TOKENS_PER_CALL": "4096",
}

REQUIRED_ENV_GATES = (
    "RGE_CLOUD_LLM_ENABLED",
    "RGE_ALLOW_OPENAI_SYNTHESIS",
    "OPENAI_API_KEY",
)

FORBIDDEN_IN_EXECUTE_SAFE = (
    "cloud_synthesis",
    "openai_api_call",
    "auto_promote_ticket",
    "export_public_publish",
)

# Public artifacts must not contain literal api-key env var names (secrets audit).
PUBLIC_CREDENTIAL_ENV_HINT = "operator_cloud_credential_env"


def _public_safe_missing_gates(missing: dict[str, str]) -> dict[str, str]:
    """Remap credential env var names so public artifacts pass private-field scan."""
    credential_keys = frozenset({"OPENAI_API_KEY", "RGE_OPENAI_API_KEY"})
    safe: dict[str, str] = {}
    for key, hint in missing.items():
        out_key = PUBLIC_CREDENTIAL_ENV_HINT if key in credential_keys else key
        safe[out_key] = hint
    return safe


def _public_safe_adapter_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Strip secret-like strings from spec before Atlas public export."""
    safe = json.loads(json.dumps(spec))
    env = dict(safe.get("env_gates") or {})
    env["required"] = [
        "RGE_CLOUD_LLM_ENABLED",
        "RGE_ALLOW_OPENAI_SYNTHESIS",
        PUBLIC_CREDENTIAL_ENV_HINT,
    ]
    env.pop("credential_env_var_names", None)
    env.pop("never_log_or_export", None)
    safe["env_gates"] = env
    return safe

NEXT_RECOMMENDED_PACKET = {
    "id": "ticket-059-live-smoke",
    "title": "Optional operator-only OpenAI live smoke (explicit gates required)",
}


class OpenAISynthesisSpecGateError(RuntimeError):
    """Raised when cloud synthesis env gates are missing (spec enforcement)."""


def _truthy(name: str) -> bool:
    return os.environ.get(name, "0").strip().casefold() in {"1", "true", "yes"}


def missing_cloud_synthesis_gates() -> dict[str, str]:
    """Return unset required gates for cloud synthesis enablement."""
    missing: dict[str, str] = {}
    if not _truthy("RGE_CLOUD_LLM_ENABLED"):
        missing["RGE_CLOUD_LLM_ENABLED"] = "required=1"
    if not _truthy("RGE_ALLOW_OPENAI_SYNTHESIS"):
        missing["RGE_ALLOW_OPENAI_SYNTHESIS"] = "required=1"
    if not openai_key_available():
        missing["OPENAI_API_KEY"] = "required (never logged or exported)"
    return missing


def assert_cloud_synthesis_env(
    *,
    graph_totals: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Fail closed unless operator explicitly opts into cloud synthesis."""
    missing = missing_cloud_synthesis_gates()
    if missing:
        raise OpenAISynthesisSpecGateError(
            "Cloud synthesis blocked. Set: "
            + ", ".join(f"{k} ({v})" for k, v in missing.items())
        )

    totals = graph_totals or {}
    readiness = evaluate_synthesis_readiness(totals)
    if readiness.get("openai_synthesis_blocked"):
        raise OpenAISynthesisSpecGateError(
            readiness.get("openai_block_reason")
            or "Synthesis readiness thresholds not met."
        )

    return {
        "RGE_CLOUD_LLM_ENABLED": os.environ.get("RGE_CLOUD_LLM_ENABLED", "1"),
        "RGE_ALLOW_OPENAI_SYNTHESIS": os.environ.get("RGE_ALLOW_OPENAI_SYNTHESIS", "1"),
        "OPENAI_API_KEY": "[redacted]",
    }


def build_example_evidence_packet(
    *,
    research_question: str = "Does AI improve creative output while reducing diversity?",
    purpose: str = "cluster_memo_draft",
) -> dict[str, Any]:
    """Public-safe example packet (refs only — no raw source text)."""
    return {
        "schema_version": PACKET_SCHEMA_VERSION,
        "packet_id": "syn_packet_example_001",
        "research_question": research_question,
        "purpose": purpose,
        "atoms": [
            {
                "atom_id": "atom_preview_001",
                "maturity": "synthesis_ready",
                "claim_ids": ["claim_preview_a", "claim_preview_b"],
                "source_ids": ["src_preview_a", "src_preview_b"],
            }
        ],
        "claims": [
            {"claim_id": "claim_preview_a", "source_id": "src_preview_a"},
            {"claim_id": "claim_preview_b", "source_id": "src_preview_b"},
        ],
        "source_refs": [
            {"source_id": "src_preview_a", "source_type": "paper"},
            {"source_id": "src_preview_b", "source_type": "paper"},
        ],
        "trace_refs": [{"trace_id": "trace_preview_001", "purpose_match_status": "match"}],
    }


def build_adapter_spec_document() -> dict[str, Any]:
    """Machine-readable adapter spec for ticket-059 implementers."""
    return {
        "schema_version": SPEC_SCHEMA_VERSION,
        "ticket_id": "ticket-059",
        "status": "mock_first_wired",
        "implementation_status": "mock adapter wired; live HTTP opt-in only",
        "input_contract": {
            "schema_version": PACKET_SCHEMA_VERSION,
            "allowed_keys": sorted(
                {
                    "schema_version",
                    "packet_id",
                    "research_question",
                    "purpose",
                    "atoms",
                    "claims",
                    "source_refs",
                    "trace_refs",
                    "cluster_id",
                }
            ),
            "forbidden_content": [
                "raw PDF/HTML/text",
                "quote_span",
                "claim_text",
                "prompts",
                "local paths",
            ],
        },
        "output_contract": {
            "required_citations": ["claim_ids", "atom_ids", "source_refs"],
            "reject_orphan_prose": True,
            "human_confirm_flag": "--confirm",
            "cli_sketch": "research synthesize --packet PATH [--provider mock_cloud|openai] --confirm",
        },
        "env_gates": {
            "required": list(REQUIRED_ENV_GATES) + ["RGE_ALLOW_OPENAI_SYNTHESIS_LIVE_HTTP"],
            "live_http_required": [
                "RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST includes openai",
                "RGE_CLOUD_LLM_ENABLED=1",
                "RGE_ALLOW_OPENAI_SYNTHESIS=1",
                "RGE_ALLOW_OPENAI_SYNTHESIS_LIVE_HTTP=1",
                PUBLIC_CREDENTIAL_ENV_HINT,
                "RGE_CLOUD_MAX_USD_PER_RUN > 0",
                "RGE_CLOUD_MAX_TOKENS_PER_CALL > 0",
                "autonomy circuit breaker closed",
            ],
            "default_fail_closed": {
                "RGE_CLOUD_LLM_ENABLED": "0",
                "RGE_ALLOW_OPENAI_SYNTHESIS": "0",
            },
            "cost_caps": DEFAULT_COST_CAPS,
            "credential_env_var_names": ["OPENAI_API_KEY", "RGE_OPENAI_API_KEY"],
            "never_log_or_export": ["OPENAI_API_KEY", "RGE_OPENAI_API_KEY"],
        },
        "readiness_gates": SYNTHESIS_READY_THRESHOLDS,
        "forbidden_in_execute_safe": list(FORBIDDEN_IN_EXECUTE_SAFE),
        "ci_policy": {
            "real_api_calls": False,
            "mock_client_only": True,
            "dry_run_default": True,
            "live_http_gate_function": "missing_live_openai_http_gates",
        },
        "escalation_policy_ref": "docs/agents/13_MODEL_ESCALATION_POLICY.md",
    }


def classify_spec_verdict(
    *,
    packet_errors: list[str],
    graph_totals: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Return (verdict, rationale) for spec readiness."""
    readiness = evaluate_synthesis_readiness(graph_totals or {})
    if packet_errors:
        return "NO-GO", "Example evidence packet failed validation."
    if not readiness.get("synthesis_readiness_passed"):
        return (
            "PARTIAL",
            "Spec complete but graph synthesis readiness thresholds not met in live graph.",
        )
    return (
        "GO",
        "Evidence-packet contract validated; mock adapter wired; live HTTP remains "
        "blocked unless every explicit gate passes.",
    )


def build_atlas_safe_spec_artifact(
    *,
    spec: dict[str, Any],
    verdict: str,
    rationale: str,
    readiness: dict[str, Any],
    example_packet_valid: bool,
    root: Path | None = None,
) -> dict[str, Any]:
    artifact: dict[str, Any] = {
        "schema_version": SPEC_SCHEMA_VERSION,
        "status": "completed",
        "packet_id": PACKET_ID,
        "run_id": SPEC_RUN_ID,
        "spec_verdict": verdict,
        "spec_rationale": rationale,
        "ticket_059_status": "mock_first_wired",
        "implementation_blocked": False,
        "live_http_blocked_by_default": True,
        "live_http_gates_missing": _public_safe_missing_gates(
            missing_live_openai_http_gates(root=root)
        ),
        "live_status": build_public_safe_live_status(root=root),
        "no_paid_api_calls": True,
        "adapter_spec": _public_safe_adapter_spec(spec),
        "synthesis_readiness": readiness,
        "example_packet_valid": example_packet_valid,
        "next_recommended_packet": NEXT_RECOMMENDED_PACKET,
    }
    violations = assert_no_private_fields({"artifact": artifact})
    if violations:
        raise ValueError(
            "Spec artifact blocked by private-field policy: " + "; ".join(violations[:5])
        )
    return artifact


def run_openai_synthesis_adapter_spec(
    *,
    graph_totals: dict[str, Any] | None = None,
    sync_public: bool = False,
    root: Path | None = None,
    run_mock_synthesis: bool = True,
) -> dict[str, Any]:
    """Validate spec + example packet; optionally sync public Atlas artifact."""
    project_root = root or repo_root()
    example = build_example_evidence_packet()
    packet_errors = validate_synthesis_evidence_packet(example)
    readiness = evaluate_synthesis_readiness(graph_totals or {})
    spec = build_adapter_spec_document()
    verdict, rationale = classify_spec_verdict(
        packet_errors=packet_errors,
        graph_totals=graph_totals,
    )
    artifact = build_atlas_safe_spec_artifact(
        spec=spec,
        verdict=verdict,
        rationale=rationale,
        readiness=readiness,
        example_packet_valid=not packet_errors,
        root=project_root,
    )

    mock_output: dict[str, Any] | None = None
    if run_mock_synthesis and not packet_errors:
        client = get_cloud_synthesis_client("mock_cloud")
        mock_output = client.synthesize(example)
        artifact["mock_synthesis_output"] = {
            "provider": mock_output.get("provider"),
            "no_paid_api_calls": mock_output.get("no_paid_api_calls"),
            "sentence_count": len(mock_output.get("summary_sentences") or []),
        }

    export_dir = project_root / "data/exports/openai_synthesis_adapter_spec"
    export_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = export_dir / SPEC_ARTIFACT_NAME
    artifact_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    public_path: Path | None = None
    if sync_public:
        public_path = (
            project_root / "apps/public-site/public/data" / SPEC_ARTIFACT_NAME
        )
        public_path.parent.mkdir(parents=True, exist_ok=True)
        public_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    return {
        "status": "completed",
        "packet_id": PACKET_ID,
        "spec_verdict": verdict,
        "spec_rationale": rationale,
        "implementation_blocked": False,
        "live_http_gates_missing": artifact.get("live_http_gates_missing") or {},
        "mock_synthesis_ran": mock_output is not None,
        "example_packet_errors": packet_errors,
        "artifact_path": str(artifact_path),
        "public_artifact_path": str(public_path) if public_path else None,
        "atlas_safe_artifact": artifact,
    }
