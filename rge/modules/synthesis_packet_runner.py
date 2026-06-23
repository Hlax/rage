"""Run cloud synthesis on an evidence packet (mock-first; candidate output only)."""

from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rge.config import load_config
from rge.contracts.synthesis_evidence_packet_v0 import (
    assert_synthesis_packet_operator_safe,
    validate_grounded_synthesis_packet,
    validate_synthesis_evidence_packet,
)
from rge.llm.cloud_synthesis_providers import normalize_provider_id
from rge.llm.cloud_synthesis_registry import (
    CloudSynthesisRegistryError,
    get_cloud_synthesis_client,
    resolve_requested_provider,
)
from rge.llm.openai_synthesis_client import (
    CloudSynthesisGateError,
    missing_live_openai_http_gates,
)
from rge.modules.autonomous_synthesis_governor import (
    _private_value_violations,
    _safe_rel,
    evaluate_synthesis_governor,
    utc_now_iso,
)
from rge.modules.operator_env_loader import load_operator_env
from rge.modules.principal_audit_gate import repo_root
from rge.modules.synthesis_grounding import evaluate_synthesis_grounding
from rge.modules.synthesis_review_threshold_policy import evaluate_synthesis_review_threshold

COMMAND = "synthesize"
OUTPUT_SCHEMA_VERSION = "synthesis_packet_run_v0.1.0"
DEFAULT_EXPORT_DIR_REL = Path("data/exports/synthesis_packets")
GROUNDED_PACKET_FIXTURE_REL = Path("fixtures/synthesis/grounded_evidence_packet_dry_run.json")


class SynthesisPacketError(RuntimeError):
    """Raised when synthesis packet execution cannot proceed safely."""


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_output_path(path: Path, root: Path) -> str:
    rel = _safe_rel(path, root)
    if rel.startswith("..") or ":" in rel:
        return path.name
    return rel


def _scalar_count(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> int:
    row = conn.execute(query, params).fetchone()
    return int(row[0]) if row else 0


def collect_db_throughput_snapshot(conn: Any) -> dict[str, int]:
    """Collect graph counters for synthesis throughput reporting."""
    claim_count = _scalar_count(conn, "SELECT COUNT(*) FROM claims")
    return {
        "sources_processed": _scalar_count(
            conn,
            "SELECT COUNT(*) FROM sources WHERE status IN ('ingested', 'parsed')",
        ),
        "reports_completed": _scalar_count(conn, "SELECT COUNT(*) FROM run_reports"),
        "claim_count": claim_count,
        "concept_link_count": _scalar_count(conn, "SELECT COUNT(*) FROM claim_concepts"),
        "relationship_count": _scalar_count(
            conn,
            "SELECT COUNT(*) FROM relationships WHERE status = 'active'",
        ),
        "qualification_count": _scalar_count(
            conn,
            """
            SELECT COUNT(*) FROM relationship_evidence
            WHERE stance = 'qualifies'
            """,
        ),
        "card_count": _scalar_count(
            conn,
            "SELECT COUNT(*) FROM public_cards WHERE is_public_safe = 1",
        ),
    }


def load_synthesis_packet(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SynthesisPacketError(f"Unable to read synthesis packet: {path}") from exc
    if not isinstance(payload, dict):
        raise SynthesisPacketError("Synthesis packet must be a JSON object.")
    return payload


def validate_synthesis_packet(
    packet: dict[str, Any],
    *,
    provider_id: str,
) -> list[str]:
    errors = list(validate_synthesis_evidence_packet(packet))
    errors.extend(assert_synthesis_packet_operator_safe(packet))
    resolved = normalize_provider_id(provider_id)
    if resolved == "openai":
        errors.extend(validate_grounded_synthesis_packet(packet))
    return errors


def build_throughput_metrics(
    *,
    started_at: str,
    completed_at: str,
    elapsed_seconds: float,
    provider: str,
    mode: str,
    model: str | None,
    cloud_call_made: bool,
    estimated_cost_usd: float | None,
    packet: dict[str, Any],
    db_snapshot: dict[str, int] | None = None,
) -> dict[str, Any]:
    snapshot = dict(db_snapshot or {})
    if not snapshot:
        snapshot = {
            "sources_processed": len(packet.get("source_refs") or []),
            "reports_completed": 0,
            "claim_count": len(packet.get("claims") or []),
            "concept_link_count": 0,
            "relationship_count": 0,
            "qualification_count": 0,
            "card_count": 0,
        }
    return {
        "started_at": started_at,
        "completed_at": completed_at,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "sources_processed": int(snapshot.get("sources_processed") or 0),
        "reports_completed": int(snapshot.get("reports_completed") or 0),
        "claim_count": int(snapshot.get("claim_count") or 0),
        "concept_link_count": int(snapshot.get("concept_link_count") or 0),
        "relationship_count": int(snapshot.get("relationship_count") or 0),
        "qualification_count": int(snapshot.get("qualification_count") or 0),
        "card_count": int(snapshot.get("card_count") or 0),
        "provider": provider,
        "mode": mode,
        "model": model,
        "cloud_call_made": cloud_call_made,
        "estimated_cost_usd": estimated_cost_usd,
    }


def _resolve_mode_and_model(provider_id: str) -> tuple[str, str | None]:
    config = load_config()
    resolved = normalize_provider_id(provider_id)
    if resolved == "openai":
        return "cloud_openai", config.openai_model
    if resolved == "mock_cloud":
        return config.test_llm_mode or "mock", "mock_cloud"
    return config.llm_mode, None


def run_synthesis_packet(
    *,
    packet_path: Path | None = None,
    packet: dict[str, Any] | None = None,
    provider: str | None = None,
    output_dir: Path | None = None,
    db_path: Path | None = None,
    confirm: bool = False,
    apply_operator_env: bool = False,
    root: Path | None = None,
    evaluate_governor: bool = True,
) -> dict[str, Any]:
    """Validate packet, call cloud synthesis client, emit candidate output + throughput."""
    project_root = root or repo_root()
    if apply_operator_env:
        load_operator_env(apply=True, repo_root=project_root)

    packet_payload = dict(packet) if packet is not None else None
    if packet_payload is None:
        if packet_path is None:
            raise SynthesisPacketError("packet or packet_path is required")
        resolved_path = packet_path if packet_path.is_absolute() else project_root / packet_path
        packet_payload = load_synthesis_packet(resolved_path)

    provider_id = normalize_provider_id(provider or resolve_requested_provider())
    if provider_id == "openai" and not confirm:
        raise SynthesisPacketError(
            "OpenAI synthesis requires explicit --confirm (human opt-in)."
        )
    if provider_id == "openai" and missing_live_openai_http_gates(root=project_root):
        raise CloudSynthesisGateError(
            "Live OpenAI synthesis blocked before request construction: "
            + ", ".join(missing_live_openai_http_gates(root=project_root))
        )

    validation_errors = validate_synthesis_packet(packet_payload, provider_id=provider_id)
    if validation_errors:
        raise SynthesisPacketError(
            "Packet validation failed: " + "; ".join(validation_errors[:8])
        )

    started_mono = time.monotonic()
    started_at = _iso_now()
    client = get_cloud_synthesis_client(provider_id)
    output = client.synthesize(packet_payload)
    completed_at = _iso_now()
    elapsed_seconds = time.monotonic() - started_mono

    mode, model = _resolve_mode_and_model(provider_id)
    cloud_call_made = not bool(output.get("no_paid_api_calls", True))
    estimated_cost_usd = output.get("cost_estimate_usd")
    if estimated_cost_usd is not None:
        try:
            estimated_cost_usd = float(estimated_cost_usd)
        except (TypeError, ValueError):
            estimated_cost_usd = None

    db_snapshot: dict[str, int] | None = None
    if db_path is not None:
        from rge.db.connection import ensure_database

        conn = ensure_database(db_path if db_path.is_absolute() else project_root / db_path)
        try:
            db_snapshot = collect_db_throughput_snapshot(conn)
        finally:
            conn.close()

    throughput = build_throughput_metrics(
        started_at=started_at,
        completed_at=completed_at,
        elapsed_seconds=elapsed_seconds,
        provider=str(output.get("provider") or provider_id),
        mode=mode,
        model=model,
        cloud_call_made=cloud_call_made,
        estimated_cost_usd=estimated_cost_usd,
        packet=packet_payload,
        db_snapshot=db_snapshot,
    )

    grounding = evaluate_synthesis_grounding(output, packet=packet_payload)
    quality_signals = {
        "grounding_failed": bool(grounding.get("needs_human_review")),
        "contradiction_threshold_exceeded": bool(
            packet_payload.get("contradiction_threshold_exceeded")
        ),
        "drift_warning_active": bool(packet_payload.get("drift_warning_active")),
        "quality_threshold_failed": bool(packet_payload.get("quality_threshold_failed")),
    }
    review_threshold = evaluate_synthesis_review_threshold(
        provider=str(output.get("provider") or provider_id),
        throughput=throughput,
        quality_signals=quality_signals,
        root=project_root,
    )

    governor_review: dict[str, Any] | None = None
    if evaluate_governor:
        governor_review = evaluate_synthesis_governor(
            packet=packet_payload,
            output=output,
            provider_id=str(output.get("provider") or provider_id),
            root=project_root,
            write_ledger=False,
            write_instruction=False,
            update_circuit=False,
        )

    export_root = output_dir or (project_root / DEFAULT_EXPORT_DIR_REL)
    export_root.mkdir(parents=True, exist_ok=True)
    packet_id = str(packet_payload.get("packet_id") or "unknown")
    output_path = export_root / f"synthesis_output_{packet_id}.json"
    result = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "status": "completed",
        "command": COMMAND,
        "packet_id": packet_id,
        "provider": str(output.get("provider") or provider_id),
        "candidate_output": output,
        "throughput": throughput,
        "review_threshold": review_threshold,
        "governor_verdict": (governor_review or {}).get("governor_verdict"),
        "grounding": {
            "needs_human_review": grounding.get("needs_human_review"),
            "grounding_passed": grounding.get("grounding_passed"),
            "flagged_sentence_count": len(grounding.get("flagged_sentences") or []),
        },
        "no_accepted_graph_writes": True,
        "output_path": _safe_output_path(output_path, project_root),
        "completed_at": utc_now_iso(),
    }
    violations = _private_value_violations(result, label="synthesis_packet_run")
    if violations:
        raise SynthesisPacketError(
            "Synthesis packet result blocked by private-field policy: "
            + "; ".join(violations[:5])
        )
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def run_synthesis_packet_command(
    *,
    packet: str | Path,
    provider: str | None = None,
    output_dir: str | Path | None = None,
    db: str | Path | None = None,
    confirm: bool = False,
    load_operator_env_flag: bool = False,
    root: Path | None = None,
) -> tuple[dict[str, Any], int]:
    project_root = root or repo_root()
    try:
        result = run_synthesis_packet(
            packet_path=Path(packet),
            provider=provider,
            output_dir=Path(output_dir) if output_dir else None,
            db_path=Path(db) if db else None,
            confirm=confirm,
            apply_operator_env=load_operator_env_flag,
            root=project_root,
        )
        return result, 0
    except CloudSynthesisGateError as exc:
        return {
            "status": "blocked",
            "command": COMMAND,
            "detail": str(exc),
            "live_http_gates_missing": missing_live_openai_http_gates(root=project_root),
        }, 2
    except (SynthesisPacketError, CloudSynthesisRegistryError) as exc:
        return {"status": "error", "command": COMMAND, "detail": str(exc)}, 1
