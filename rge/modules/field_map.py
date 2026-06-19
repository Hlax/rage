"""Field-map research report from metadata pulls (MVP-P3).

Pulls resolved source metadata, clusters by lightweight token similarity,
selects representative top sources, extracts abstract-grounded evidence, and
synthesizes a field report distinguishing metadata conclusions from quote-grounded
abstract evidence.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from rge.modules.abstract_evidence import (
    ABSTRACT_EVIDENCE_BASIS,
    generate_abstract_evidence_cards,
)
from rge.modules.failure_recommender import recommend_from_abstract_evidence_run
from rge.modules.research_queue import compute_discovered_relevance_score
from rge.modules.source_resolver import resolve_work_candidates
from rge.modules.source_resolver.status import METADATA_ONLY

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
DEFAULT_TOP_SOURCES = 5
DEFAULT_MAX_CANDIDATES = 20
CLUSTER_STOPWORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "and",
        "or",
        "of",
        "in",
        "to",
        "for",
        "with",
        "on",
        "by",
        "from",
        "is",
        "are",
        "was",
        "were",
        "be",
        "this",
        "that",
        "using",
        "use",
        "ai",
        "paper",
        "study",
    }
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_report_dir(repo_root: Path | None = None) -> Path:
    return (repo_root or _repo_root()) / "data" / "reports"


def tokenize(text: str) -> list[str]:
    tokens = _TOKEN_PATTERN.findall(text.casefold())
    return [token for token in tokens if token not in CLUSTER_STOPWORDS and len(token) > 2]


def cluster_key_for_record(record: dict[str, Any], *, query: str) -> str:
    """Deterministic pseudo-cluster id from title/abstract tokens."""
    blob = " ".join(
        [
            str(record.get("title") or ""),
            str(record.get("abstract_text") or ""),
            query,
        ]
    )
    tokens = tokenize(blob)
    if not tokens:
        return "cluster_unspecified"
    counts = Counter(tokens)
    top = [token for token, _ in counts.most_common(3)]
    return "cluster_" + "_".join(top)


def rank_field_map_records(
    records: list[dict[str, Any]],
    *,
    query: str,
    top_n: int = DEFAULT_TOP_SOURCES,
) -> list[dict[str, Any]]:
    scored: list[tuple[float, dict[str, Any]]] = []
    for record in records:
        title = str(record.get("title") or "")
        abstract = str(record.get("abstract_text") or "")
        relevance = compute_discovered_relevance_score(
            query=query,
            title=title,
            abstract=abstract,
        )
        status_bonus = 0.0 if record.get("source_status") == METADATA_ONLY else 0.15
        year = record.get("year")
        recency_bonus = 0.05 if isinstance(year, int) and year >= 2020 else 0.0
        score = relevance + status_bonus + recency_bonus
        scored.append((score, record))
    scored.sort(key=lambda item: (-item[0], str(item[1].get("source_id") or "")))
    ranked = []
    for score, record in scored[: max(1, top_n)]:
        item = dict(record)
        item["field_map_score"] = round(score, 4)
        ranked.append(item)
    return ranked


def build_field_clusters(
    records: list[dict[str, Any]],
    *,
    query: str,
) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = cluster_key_for_record(record, query=query)
        buckets[key].append(record)
    clusters = []
    for cluster_id, members in sorted(buckets.items(), key=lambda item: (-len(item[1]), item[0])):
        clusters.append(
            {
                "cluster_id": cluster_id,
                "member_count": len(members),
                "representative_titles": [
                    str(item.get("title") or "") for item in members[:3]
                ],
                "source_ids": [str(item.get("source_id") or "") for item in members],
            }
        )
    return clusters


def synthesize_field_report(
    *,
    query: str,
    domain_pack: str,
    records: list[dict[str, Any]],
    ranked_sources: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    abstract_evidence: dict[str, Any],
    improvement_recommendation: dict[str, Any],
) -> dict[str, Any]:
    metadata_only_ids = [
        str(record.get("source_id") or "")
        for record in records
        if record.get("source_status") == METADATA_ONLY
    ]
    quote_claims = []
    for card in abstract_evidence.get("cards") or []:
        for claim in card.get("accepted_claims") or []:
            quote_claims.append(
                {
                    "source_id": card.get("source_id"),
                    "claim_text": claim.get("claim_text"),
                    "quote_span": claim.get("quote_span"),
                    "evidence_basis": ABSTRACT_EVIDENCE_BASIS,
                }
            )

    weak_areas = []
    if metadata_only_ids:
        weak_areas.append(
            f"{len(metadata_only_ids)} sources have metadata only (no abstract evidence)."
        )
    if abstract_evidence.get("accepted_claims_total", 0) == 0:
        weak_areas.append("No quote-grounded abstract claims accepted in this run.")

    return {
        "report_type": "field_map",
        "topic": query,
        "domain_pack": domain_pack,
        "metadata_record_count": len(records),
        "cluster_count": len(clusters),
        "clusters": clusters,
        "top_sources": [
            {
                "source_id": item.get("source_id"),
                "title": item.get("title"),
                "source_status": item.get("source_status"),
                "field_map_score": item.get("field_map_score"),
                "year": item.get("year"),
            }
            for item in ranked_sources
        ],
        "quote_grounded_claims": quote_claims,
        "metadata_only_source_ids": metadata_only_ids,
        "weak_evidence_areas": weak_areas,
        "evidence_label": ABSTRACT_EVIDENCE_BASIS,
        "abstract_evidence_summary": {
            "accepted_claims_total": abstract_evidence.get("accepted_claims_total", 0),
            "rejected_claims_total": abstract_evidence.get("rejected_claims_total", 0),
            "skipped_count": abstract_evidence.get("skipped_count", 0),
        },
        "improvement_recommendation": {
            "recommended_packet": improvement_recommendation.get("recommended_packet"),
            "rationale": improvement_recommendation.get("rationale"),
            "dominant_signal": improvement_recommendation.get("dominant_signal"),
        },
        "disclaimer": (
            "Metadata-level cluster assignments are heuristic. Only quote_grounded_claims "
            "are abstract-only evidence, not full-text proof."
        ),
    }


def generate_field_map_report(
    *,
    query: str,
    domain_pack: str = "creativity",
    max_candidates: int = DEFAULT_MAX_CANDIDATES,
    top_sources: int = DEFAULT_TOP_SOURCES,
    fixture_mode: bool = False,
    backends: list[str] | None = None,
) -> dict[str, Any]:
    """End-to-end field-map run on resolver records."""
    resolved = resolve_work_candidates(
        query=query,
        domain_pack=domain_pack,
        limit=max_candidates,
        fixture_mode=fixture_mode,
        backends=backends,
    )
    records = list(resolved.get("records") or [])
    clusters = build_field_clusters(records, query=query)
    ranked = rank_field_map_records(records, query=query, top_n=top_sources)
    abstract_evidence = generate_abstract_evidence_cards(ranked, domain_pack=domain_pack)
    statuses = [str(record.get("source_status") or "") for record in records]
    improvement = recommend_from_abstract_evidence_run(
        abstract_evidence,
        source_statuses=statuses,
    )
    report = synthesize_field_report(
        query=query,
        domain_pack=domain_pack,
        records=records,
        ranked_sources=ranked,
        clusters=clusters,
        abstract_evidence=abstract_evidence,
        improvement_recommendation=improvement,
    )
    return {
        "command": "generate-field-map",
        "status": "ok",
        "fixture_mode": fixture_mode,
        "resolver": {
            "resolved_count": resolved.get("resolved_count", 0),
            "backend_counts": resolved.get("backend_counts", {}),
        },
        "field_map_report": report,
        "abstract_evidence": abstract_evidence,
        "improvement_recommendation": improvement,
    }


def run_generate_field_map_command(
    *,
    query: str | None,
    domain_pack: str,
    max_candidates: int,
    top_sources: int,
    fixture_mode: bool,
    output_dir: Path | None = None,
) -> tuple[dict[str, Any], int]:
    if not query and not fixture_mode:
        return {
            "command": "generate-field-map",
            "status": "error",
            "reason": "missing_query",
            "detail": "--query is required unless --fixture-mode is set.",
        }, 1

    effective_query = query or "AI assisted creativity and idea diversity"
    payload = generate_field_map_report(
        query=effective_query,
        domain_pack=domain_pack,
        max_candidates=max_candidates,
        top_sources=top_sources,
        fixture_mode=fixture_mode,
    )
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "field_map_latest.json"
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        payload["output_path"] = str(out_path)
    return payload, 0
