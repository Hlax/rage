"""Live source expansion: OpenAlex + arXiv discovery with Unpaywall OA enrichment.

Operator-gated proof for improved source diversity, resolver breakdown in Atlas,
and visible blocked/unavailable sources. Abstract-first; no PDF downloads.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.live_arbitrary_source_health import (
    LIVE_NETWORK_BACKENDS,
    LIVE_NETWORK_RESOLVER_QUERY,
    LOCAL_SAFE_ARBITRARY_QUESTION,
    _execute_source_health_proof_pipeline,
    assert_live_source_health_smoke_env,
)
from rge.modules.source_resolver import resolve_work_candidates

PACKET_ID = "live-source-expansion"
LIVE_SOURCE_EXPANSION_RUN_ID = "run_live_network_source_expansion"
EXPANDED_DISCOVERY_BACKENDS = LIVE_NETWORK_BACKENDS

NEXT_RECOMMENDED_PACKET = {
    "id": "local-model-extraction-comparison",
    "title": "Local Model Extraction Comparison",
}


def assert_live_source_expansion_smoke_env() -> dict[str, str]:
    """Fail closed unless operator opts into live source expansion smoke."""
    combined = assert_live_source_health_smoke_env()
    allow = os.environ.get("RGE_ALLOW_LIVE_SOURCE_EXPANSION_SMOKE", "0").strip().casefold()
    if allow not in {"1", "true", "yes"}:
        raise RuntimeError(
            "Live source expansion smoke requires RGE_ALLOW_LIVE_SOURCE_EXPANSION_SMOKE=1."
        )
    combined["RGE_ALLOW_LIVE_SOURCE_EXPANSION_SMOKE"] = allow
    return combined


def resolve_live_expanded_network_source_records(
    *,
    question: str = LOCAL_SAFE_ARBITRARY_QUESTION,
    resolver_query: str = LIVE_NETWORK_RESOLVER_QUERY,
    domain_pack: str = "creativity",
    limit: int = 5,
    backends: tuple[str, ...] = EXPANDED_DISCOVERY_BACKENDS,
    enrich_unpaywall: bool = True,
) -> dict[str, Any]:
    """Resolve live sources across OpenAlex/arXiv with optional Unpaywall enrichment."""
    assert_live_source_expansion_smoke_env()
    resolved = resolve_work_candidates(
        query=resolver_query,
        domain_pack=domain_pack,
        limit=limit,
        backends=list(backends),
        fixture_mode=False,
        enrich_unpaywall=enrich_unpaywall,
    )
    records = list(resolved.get("records") or [])
    if len(records) > limit:
        resolved["records"] = records[:limit]
        resolved["resolved_count"] = limit
    resolved["research_question"] = question
    resolved["resolver_query"] = resolver_query
    resolved["source_expansion_enabled"] = True
    return resolved


def build_source_expansion_summary(
    resolved: dict[str, Any],
    *,
    source_health: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Aggregate public-safe source expansion metrics for Atlas artifacts."""
    from collections import Counter

    records = list(resolved.get("records") or [])
    backend_counts = dict(resolved.get("backend_counts") or {})
    unpaywall_skipped = list(resolved.get("unpaywall_skipped") or [])
    skip_reason_counts = Counter(
        str(item.get("reason") or "unknown") for item in unpaywall_skipped
    )
    enrichment_backend_counts: Counter[str] = Counter()
    doi_backed_count = 0
    unpaywall_enriched_count = 0
    for record in records:
        if record.get("doi"):
            doi_backed_count += 1
        backends = list(record.get("enrichment_backends") or [])
        if "unpaywall" in backends:
            unpaywall_enriched_count += 1
        for backend in backends:
            enrichment_backend_counts[backend] += 1

    persisted = source_health or {}
    resolver_source_counts = dict(persisted.get("resolver_source_counts") or {})
    source_diversity_count = len(resolver_source_counts) or len(
        {str(record.get("source_kind") or record.get("resolver_backend") or "") for record in records}
        - {""}
    )
    failure_reason_counts = dict(persisted.get("failure_reason_counts") or {})
    availability_counts = dict(persisted.get("availability_counts") or {})

    summary = {
        "discovery_backends": list(resolved.get("backends") or []),
        "enrich_unpaywall": bool(resolved.get("enrich_unpaywall")),
        "resolver_breakdown": backend_counts,
        "persisted_resolver_source_counts": resolver_source_counts,
        "source_diversity_count": source_diversity_count,
        "doi_backed_count": doi_backed_count,
        "unpaywall_enriched_count": unpaywall_enriched_count,
        "unpaywall_skipped_counts": dict(skip_reason_counts),
        "enrichment_backend_counts": dict(enrichment_backend_counts),
        "availability_counts": availability_counts,
        "blocked_source_reason_counts": failure_reason_counts,
        "blocked_sources_visible": bool(failure_reason_counts),
        "resolved_count": int(resolved.get("resolved_count") or len(records)),
    }
    violations = assert_no_private_fields({"source_expansion_summary": summary})
    if violations:
        raise ValueError(
            "Source expansion summary blocked by private-field policy: "
            + "; ".join(violations[:5])
        )
    return summary


def classify_source_expansion_verdict(
    summary: dict[str, Any],
    *,
    pipeline_result: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Return (verdict, rationale) for live source expansion proof."""
    if int(summary.get("resolved_count") or 0) < 1:
        return "NO-GO", "Expanded resolver returned zero live source records."

    diversity = int(summary.get("source_diversity_count") or 0)
    breakdown = summary.get("resolver_breakdown") or {}
    active_backends = sum(1 for count in breakdown.values() if int(count or 0) >= 1)

    if diversity < 2 or active_backends < 2:
        return (
            "PARTIAL",
            "Live discovery works but resolver diversity is below the two-backend target.",
        )

    if summary.get("enrich_unpaywall") and int(summary.get("doi_backed_count") or 0) >= 1:
        if not summary.get("unpaywall_skipped_counts") and int(
            summary.get("unpaywall_enriched_count") or 0
        ) == 0:
            return (
                "PARTIAL",
                "DOI-backed records were discovered but Unpaywall enrichment did not attach.",
            )

    pipeline = pipeline_result or {}
    accepted = int((pipeline.get("run_report") or {}).get("claims_accepted") or 0)
    if accepted >= 1:
        return (
            "GO",
            "Expanded OpenAlex/arXiv discovery with Unpaywall enrichment produced "
            "multi-backend source diversity and quote-backed evidence.",
        )

    if int(summary.get("resolved_count") or 0) >= 2:
        return (
            "PARTIAL",
            "Source diversity improved but accepted abstract evidence remains thin.",
        )

    return "NO-GO", "Expanded resolver did not yield usable source health evidence."


def enrich_atlas_artifact_for_source_expansion(
    artifact: dict[str, Any],
    *,
    verdict: str,
    rationale: str,
) -> dict[str, Any]:
    """Attach source-expansion verdict metadata to an Atlas-safe run artifact."""
    enriched = dict(artifact)
    enriched["packet_id"] = PACKET_ID
    enriched["source_expansion_verdict"] = verdict
    enriched["source_expansion_rationale"] = rationale
    enriched["next_recommended_packet"] = NEXT_RECOMMENDED_PACKET
    violations = assert_no_private_fields({"atlas_safe_run_artifact": enriched})
    if violations:
        raise ValueError(
            "Source expansion Atlas artifact blocked by private-field policy: "
            + "; ".join(violations[:5])
        )
    return enriched


def sync_source_expansion_artifact_to_public_site(
    artifact: dict[str, Any],
    *,
    public_path: Path,
) -> dict[str, Any]:
    """Copy validated source-expansion run artifact into public-site preview data."""
    if not artifact.get("source_expansion_summary"):
        raise ValueError("source_expansion_summary must be present on artifact.")
    verdict = str(artifact.get("source_expansion_verdict") or "")
    if verdict in {"", "PENDING"}:
        raise ValueError("source_expansion_verdict must be set before public sync.")
    violations = assert_no_private_fields({"artifact": artifact})
    if violations:
        raise ValueError(
            "Source expansion artifact failed public-safe validation: "
            + "; ".join(violations[:5])
        )
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return {
        "status": "completed",
        "output_path": str(public_path),
        "source_expansion_verdict": verdict,
        "source_diversity_count": (
            (artifact.get("source_expansion_summary") or {}).get("source_diversity_count")
        ),
    }


def run_live_source_expansion_smoke(
    conn: Any,
    *,
    question: str = LOCAL_SAFE_ARBITRARY_QUESTION,
    resolver_query: str = LIVE_NETWORK_RESOLVER_QUERY,
    domain_pack: str = "creativity",
    output_dir: Path | None = None,
    limit: int = 5,
    client: Any | None = None,
) -> dict[str, Any]:
    """Operator-gated live source expansion proof on a temp DB."""
    os.environ.setdefault("RGE_LLM_MODE", "mock")
    resolved = resolve_live_expanded_network_source_records(
        question=question,
        resolver_query=resolver_query,
        domain_pack=domain_pack,
        limit=limit,
    )
    pipeline = _execute_source_health_proof_pipeline(
        conn,
        resolved=resolved,
        question=question,
        domain_pack=domain_pack,
        run_id=LIVE_SOURCE_EXPANSION_RUN_ID,
        output_dir=output_dir,
        client=client,
        include_graph_proof=True,
        live_abstract_mode=True,
        resolver_mode="live_network_source_expansion",
    )
    expansion_summary = dict(
        (pipeline.get("atlas_safe_artifact") or {}).get("source_expansion_summary") or {}
    )
    if not expansion_summary:
        expansion_summary = build_source_expansion_summary(
            resolved,
            source_health=dict(pipeline.get("source_health") or {}),
        )
    verdict, rationale = classify_source_expansion_verdict(
        expansion_summary,
        pipeline_result=pipeline,
    )
    atlas_artifact = enrich_atlas_artifact_for_source_expansion(
        dict(pipeline.get("atlas_safe_artifact") or {}),
        verdict=verdict,
        rationale=rationale,
    )
    return {
        **pipeline,
        "atlas_safe_artifact": atlas_artifact,
        "source_expansion_summary": expansion_summary,
        "source_expansion_verdict": verdict,
        "source_expansion_rationale": rationale,
    }


def required_env_setup_commands() -> list[str]:
    return [
        '$env:RGE_ALLOW_LIVE_SOURCE_EXPANSION_SMOKE = "1"',
        '$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"',
        '$env:RGE_ALLOW_SOURCE_NETWORK = "1"',
        '$env:OPENALEX_MAILTO = "operator@example.com"',
        '$env:RGE_LLM_MODE = "mock"',
        "python scripts/run_live_source_expansion_smoke.py --sync-public",
    ]
