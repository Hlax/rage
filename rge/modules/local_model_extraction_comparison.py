"""Local model extraction comparison on the same live abstracts.

Evaluation-only operator packet: compare deterministic mock abstract extraction
against local Qwen/Ollama on identical live abstract chunks. No accepted DB
writes; public artifacts expose aggregate counts and quote-validity rates only.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from rge.config import RgeConfig, load_config
from rge.llm.registry import get_model_client
from rge.modules.abstract_evidence import (
    build_abstract_chunk,
    extract_and_validate_live_abstract_chunk,
)
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.claim_extractor import extract_and_validate_for_chunk
from rge.modules.claim_validator import locate_quote_offsets
from rge.modules.live_probe import assert_live_probe_env, assert_ollama_health
from rge.modules.live_source_expansion import (
    LOCAL_SAFE_ARBITRARY_QUESTION,
    LIVE_NETWORK_RESOLVER_QUERY,
    resolve_live_expanded_network_source_records,
)
from rge.modules.principal_audit_gate import repo_root

PACKET_ID = "local-model-extraction-comparison"
COMPARISON_SCHEMA_VERSION = "atlas_local_model_extraction_comparison_v0.1.0"
COMPARISON_ARTIFACT_NAME = "atlas_local_model_extraction_comparison_latest.json"
COMPARISON_RUN_ID = "run_local_model_extraction_comparison"

NEXT_RECOMMENDED_PACKET = {
    "id": "multi-claim-atom-clustering",
    "title": "Multi-Claim Atom Clustering",
}

# Local Ollama readiness stays PARTIAL until quote-validity meets mock baseline.
QUOTE_VALIDITY_READINESS_THRESHOLD = 0.95


class LocalModelExtractionComparisonGateError(RuntimeError):
    """Raised when operator env gates for extraction comparison are missing."""


def assert_local_model_extraction_comparison_env(
    config: RgeConfig | None = None,
) -> tuple[RgeConfig, dict[str, str]]:
    """Fail closed unless operator opts into live abstract extraction comparison."""
    from rge.modules.live_source_expansion import assert_live_source_expansion_smoke_env

    combined = assert_live_source_expansion_smoke_env()
    allow = os.environ.get(
        "RGE_ALLOW_LOCAL_MODEL_EXTRACTION_COMPARISON", "0"
    ).strip().casefold()
    if allow not in {"1", "true", "yes"}:
        raise LocalModelExtractionComparisonGateError(
            "Local model extraction comparison requires "
            "RGE_ALLOW_LOCAL_MODEL_EXTRACTION_COMPARISON=1."
        )
    combined["RGE_ALLOW_LOCAL_MODEL_EXTRACTION_COMPARISON"] = allow
    cfg = assert_live_probe_env(
        config,
        command="local-model-extraction-comparison",
    )
    combined["RGE_LLM_MODE"] = cfg.llm_mode
    combined["RGE_ALLOW_LIVE_LLM"] = os.environ.get("RGE_ALLOW_LIVE_LLM", "1")
    return cfg, combined


def required_env_setup_commands() -> list[str]:
    return [
        '$env:RGE_ALLOW_LOCAL_MODEL_EXTRACTION_COMPARISON = "1"',
        '$env:RGE_ALLOW_LIVE_SOURCE_EXPANSION_SMOKE = "1"',
        '$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"',
        '$env:RGE_ALLOW_SOURCE_NETWORK = "1"',
        '$env:OPENALEX_MAILTO = "operator@example.com"',
        '$env:RGE_LLM_MODE = "ollama"',
        '$env:RGE_ALLOW_LIVE_LLM = "1"',
        "python scripts/run_local_model_extraction_comparison.py --sync-public",
    ]


def quote_span_is_literal_in_chunk(quote_span: str, chunk_text: str) -> bool:
    start, _end = locate_quote_offsets(quote_span, chunk_text)
    return start is not None


def summarize_extraction_validation(
    validation: dict[str, list[dict[str, Any]]],
    *,
    chunk_text: str,
    backend: str,
) -> dict[str, Any]:
    """Public-safe extraction summary (no claim text or quote spans)."""
    accepted = list(validation.get("accepted") or [])
    rejected = list(validation.get("rejected") or [])
    quote_valid = sum(
        1
        for claim in accepted
        if quote_span_is_literal_in_chunk(
            str(claim.get("quote_span") or ""), chunk_text
        )
    )
    rejection_counts = Counter(
        str(item.get("rejection_reason") or "unknown") for item in rejected
    )
    accepted_count = len(accepted)
    return {
        "backend": backend,
        "accepted_count": accepted_count,
        "rejected_count": len(rejected),
        "quote_valid_accepted_count": quote_valid,
        "quote_validity_rate": (
            round(quote_valid / accepted_count, 4) if accepted_count else None
        ),
        "rejection_reason_counts": dict(rejection_counts),
    }


def _quality_vs_mock(
    mock_summary: dict[str, Any],
    ollama_summary: dict[str, Any],
) -> str:
    mock_accepted = int(mock_summary.get("accepted_count") or 0)
    ollama_accepted = int(ollama_summary.get("accepted_count") or 0)
    mock_rate = mock_summary.get("quote_validity_rate")
    ollama_rate = ollama_summary.get("quote_validity_rate")

    if ollama_accepted < mock_accepted:
        return "thinner"
    if ollama_accepted > mock_accepted:
        return "better"
    if ollama_rate is not None and mock_rate is not None:
        if ollama_rate < mock_rate:
            return "worse_quote_validity"
        if ollama_rate > mock_rate:
            return "better_quote_validity"
    return "comparable"


def compare_extractions_on_chunk(
    chunk: dict[str, Any],
    *,
    domain_pack: str,
    ollama_client: Any,
) -> dict[str, Any]:
    """Compare mock deterministic vs local Ollama extraction on one abstract chunk."""
    chunk_text = str(chunk.get("chunk_text") or "")
    mock_validation = extract_and_validate_live_abstract_chunk(
        chunk,
        domain_pack=domain_pack,
    )
    ollama_validation = extract_and_validate_for_chunk(
        chunk,
        domain_pack=domain_pack,
        client=ollama_client,
        live_abstract_ollama_fallthrough=True,
        skip_quoteability_gate=True,
    )
    mock_summary = summarize_extraction_validation(
        mock_validation,
        chunk_text=chunk_text,
        backend="mock_deterministic",
    )
    ollama_summary = summarize_extraction_validation(
        ollama_validation,
        chunk_text=chunk_text,
        backend="local_ollama",
    )
    quality = _quality_vs_mock(mock_summary, ollama_summary)
    return {
        "chunk_ref": str(chunk.get("id") or ""),
        "abstract_char_count": len(chunk_text),
        "mock_deterministic": mock_summary,
        "local_ollama": ollama_summary,
        "comparison": {
            "accepted_delta": int(ollama_summary["accepted_count"])
            - int(mock_summary["accepted_count"]),
            "local_thinner_than_mock": int(ollama_summary["accepted_count"])
            < int(mock_summary["accepted_count"]),
            "local_worse_quote_validity": (
                ollama_summary.get("quote_validity_rate") is not None
                and mock_summary.get("quote_validity_rate") is not None
                and ollama_summary["quote_validity_rate"]
                < mock_summary["quote_validity_rate"]
            ),
            "quality_vs_mock": quality,
        },
    }


def build_comparison_aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per-abstract comparison rows into Atlas-safe summary metrics."""
    if not rows:
        return {
            "compared_abstract_count": 0,
            "mock_total_accepted": 0,
            "local_ollama_total_accepted": 0,
            "mock_quote_validity_rate": None,
            "local_ollama_quote_validity_rate": None,
            "local_thinner_count": 0,
            "local_better_count": 0,
            "quality_vs_mock_overall": "unknown",
            "ollama_rejection_reason_totals": {},
        }

    mock_accepted = sum(
        int(row["mock_deterministic"]["accepted_count"]) for row in rows
    )
    ollama_accepted = sum(
        int(row["local_ollama"]["accepted_count"]) for row in rows
    )
    mock_quote_valid = sum(
        int(row["mock_deterministic"]["quote_valid_accepted_count"]) for row in rows
    )
    ollama_quote_valid = sum(
        int(row["local_ollama"]["quote_valid_accepted_count"]) for row in rows
    )
    quality_counts = Counter(
        str(row["comparison"]["quality_vs_mock"]) for row in rows
    )
    ollama_rejection_totals: Counter[str] = Counter()
    for row in rows:
        for reason, count in (
            row["local_ollama"].get("rejection_reason_counts") or {}
        ).items():
            ollama_rejection_totals[reason] += int(count)

    thinner = int(quality_counts.get("thinner", 0))
    better = int(quality_counts.get("better", 0)) + int(
        quality_counts.get("better_quote_validity", 0)
    )
    if thinner > better and thinner >= len(rows) // 2:
        overall = "thinner"
    elif better > thinner:
        overall = "better"
    elif mock_accepted == ollama_accepted:
        overall = "comparable"
    else:
        overall = "mixed"

    return {
        "compared_abstract_count": len(rows),
        "mock_total_accepted": mock_accepted,
        "local_ollama_total_accepted": ollama_accepted,
        "mock_quote_validity_rate": (
            round(mock_quote_valid / mock_accepted, 4) if mock_accepted else None
        ),
        "local_ollama_quote_validity_rate": (
            round(ollama_quote_valid / ollama_accepted, 4)
            if ollama_accepted
            else None
        ),
        "local_thinner_count": thinner,
        "local_better_count": better,
        "quality_vs_mock_overall": overall,
        "quality_vs_mock_counts": dict(quality_counts),
        "ollama_rejection_reason_totals": dict(ollama_rejection_totals),
    }


def classify_comparison_verdict(
    aggregate: dict[str, Any],
    *,
    ollama_health: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Return (verdict, rationale) for the extraction comparison run."""
    compared = int(aggregate.get("compared_abstract_count") or 0)
    if compared < 1:
        return "NO-GO", "No live abstract chunks were available for comparison."

    health = ollama_health or {}
    if health and not health.get("reachable"):
        return "NO-GO", "Ollama was not reachable during comparison."

    mock_accepted = int(aggregate.get("mock_total_accepted") or 0)
    ollama_accepted = int(aggregate.get("local_ollama_total_accepted") or 0)
    overall = str(aggregate.get("quality_vs_mock_overall") or "unknown")

    if mock_accepted >= 1 and compared >= 2:
        return (
            "GO",
            "Mock and local Ollama extractions were compared on the same live "
            f"abstracts ({compared} chunks). Local model quality vs mock: {overall}.",
        )

    if compared >= 1:
        return (
            "PARTIAL",
            "Comparison ran but mock baseline or abstract coverage remains thin.",
        )

    return "NO-GO", "Comparison did not produce usable abstract metrics."


def classify_local_model_readiness(
    aggregate: dict[str, Any],
    *,
    comparison_verdict: str,
) -> tuple[str, str]:
    """Return (readiness_status, notes) — PARTIAL unless quote-validity threshold met."""
    if comparison_verdict == "NO-GO":
        return "NO-GO", "Comparison verdict is NO-GO; local model not ready."

    ollama_rate = aggregate.get("local_ollama_quote_validity_rate")
    mock_rate = aggregate.get("mock_quote_validity_rate")
    ollama_accepted = int(aggregate.get("local_ollama_total_accepted") or 0)

    if ollama_accepted < 1:
        return (
            "PARTIAL",
            "Local Ollama produced no accepted claims; quote-validity gate not met.",
        )

    if ollama_rate is None:
        return (
            "PARTIAL",
            "Accepted local claims lack measurable quote-validity rate.",
        )

    threshold = mock_rate if mock_rate is not None else QUOTE_VALIDITY_READINESS_THRESHOLD
    if float(ollama_rate) >= float(threshold):
        return (
            "GO",
            f"Local Ollama quote-validity {ollama_rate} meets threshold {threshold}.",
        )

    return (
        "PARTIAL",
        f"Local Ollama quote-validity {ollama_rate} below threshold {threshold}; "
        "readiness remains PARTIAL until quote spans are literal on live abstracts.",
    )


def build_atlas_safe_comparison_artifact(
    *,
    aggregate: dict[str, Any],
    rows: list[dict[str, Any]],
    verdict: str,
    rationale: str,
    ollama_model: str | None = None,
    research_question: str = LOCAL_SAFE_ARBITRARY_QUESTION,
    resolver_query: str = LIVE_NETWORK_RESOLVER_QUERY,
) -> dict[str, Any]:
    """Build public-safe Atlas bundle for local model extraction comparison."""
    readiness_status, readiness_notes = classify_local_model_readiness(
        aggregate,
        comparison_verdict=verdict,
    )
    artifact: dict[str, Any] = {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "status": "completed",
        "packet_id": PACKET_ID,
        "run_id": COMPARISON_RUN_ID,
        "research_question": research_question,
        "resolver_query": resolver_query,
        "comparison_verdict": verdict,
        "comparison_rationale": rationale,
        "evaluation_only": True,
        "no_db_writes": True,
        "ollama_model": ollama_model,
        "comparison_aggregate": aggregate,
        "abstract_comparisons": rows,
        "local_model_readiness": {
            "status": readiness_status,
            "quote_validity_threshold": QUOTE_VALIDITY_READINESS_THRESHOLD,
            "notes": readiness_notes,
            "requires_literal_quote_spans": True,
            "unsupported_claims_rejected": True,
        },
        "next_recommended_packet": NEXT_RECOMMENDED_PACKET,
    }
    violations = assert_no_private_fields({"artifact": artifact})
    if violations:
        raise ValueError(
            "Comparison artifact blocked by private-field policy: "
            + "; ".join(violations[:5])
        )
    return artifact


def sync_comparison_artifact_to_public_site(
    artifact: dict[str, Any],
    *,
    public_path: Path,
) -> dict[str, Any]:
    """Copy validated comparison artifact into public-site preview data."""
    if artifact.get("schema_version") != COMPARISON_SCHEMA_VERSION:
        raise ValueError(
            f"schema_version must be {COMPARISON_SCHEMA_VERSION!r}."
        )
    verdict = str(artifact.get("comparison_verdict") or "")
    if verdict in {"", "PENDING"}:
        raise ValueError("comparison_verdict must be set before public sync.")
    aggregate = artifact.get("comparison_aggregate") or {}
    if int(aggregate.get("compared_abstract_count") or 0) < 1:
        raise ValueError("comparison_aggregate.compared_abstract_count must be >= 1.")
    violations = assert_no_private_fields({"artifact": artifact})
    if violations:
        raise ValueError(
            "Comparison artifact failed public-safe validation: "
            + "; ".join(violations[:5])
        )
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return {
        "status": "completed",
        "output_path": str(public_path),
        "comparison_verdict": verdict,
        "compared_abstract_count": aggregate.get("compared_abstract_count"),
    }


def run_local_model_extraction_comparison(
    *,
    question: str = LOCAL_SAFE_ARBITRARY_QUESTION,
    resolver_query: str = LIVE_NETWORK_RESOLVER_QUERY,
    domain_pack: str = "creativity",
    limit: int = 5,
    output_dir: Path | None = None,
    client: Any | None = None,
    skip_health_check: bool = False,
) -> dict[str, Any]:
    """Operator-gated mock vs Ollama extraction comparison on live abstracts."""
    cfg, env_gates = assert_local_model_extraction_comparison_env()
    health = (
        assert_ollama_health(cfg) if not skip_health_check else {}
    )
    ollama_client = client or get_model_client(cfg, mode="ollama")

    resolved = resolve_live_expanded_network_source_records(
        question=question,
        resolver_query=resolver_query,
        domain_pack=domain_pack,
        limit=limit,
    )
    records = list(resolved.get("records") or [])

    rows: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        chunk = build_abstract_chunk(record)
        if chunk is None:
            continue
        row = compare_extractions_on_chunk(
            chunk,
            domain_pack=domain_pack,
            ollama_client=ollama_client,
        )
        row["source_ref"] = f"source_{index:03d}"
        row["resolver_backend"] = str(
            record.get("source_kind")
            or record.get("resolver_backend")
            or "unknown"
        )
        rows.append(row)

    aggregate = build_comparison_aggregate(rows)
    verdict, rationale = classify_comparison_verdict(aggregate, ollama_health=health)
    artifact = build_atlas_safe_comparison_artifact(
        aggregate=aggregate,
        rows=rows,
        verdict=verdict,
        rationale=rationale,
        ollama_model=str(health.get("model") or cfg.local_llm or ""),
        research_question=question,
        resolver_query=resolver_query,
    )

    root = repo_root()
    out_dir = output_dir or (
        root / "data" / "exports" / "local_model_extraction_comparison"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = out_dir / COMPARISON_ARTIFACT_NAME
    artifact_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

    try:
        operator_artifact_ref = artifact_path.relative_to(root).as_posix()
    except ValueError:
        operator_artifact_ref = f"{out_dir.name}/{COMPARISON_ARTIFACT_NAME}"

    return {
        "packet_id": PACKET_ID,
        "comparison_verdict": verdict,
        "comparison_rationale": rationale,
        "compared_abstract_count": aggregate.get("compared_abstract_count"),
        "quality_vs_mock_overall": aggregate.get("quality_vs_mock_overall"),
        "mock_total_accepted": aggregate.get("mock_total_accepted"),
        "local_ollama_total_accepted": aggregate.get("local_ollama_total_accepted"),
        "ollama_health": health,
        "env_gates": env_gates,
        "artifact_path": str(artifact_path),
        "operator_artifact_ref": operator_artifact_ref,
        "atlas_safe_artifact": artifact,
        "next_recommended_packet": NEXT_RECOMMENDED_PACKET,
    }
