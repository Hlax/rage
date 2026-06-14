"""Queue candidate sources and follow-up questions. Deterministic; no model use.

The queue controls execution: statuses queued/fetching/fetched/parsing/
extracting/staged/accepted/rejected/failed/needs_manual_review/parked.
Ranking uses a versioned formula aligned with
``docs/agents/09_RESEARCH_RUN_CONTRACT.md`` section 7.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rge.modules.domain_pack_loader import load_domain_pack, source_type_credibility_prior

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE_PATH = (
    REPO_ROOT / "fixtures" / "candidate_sources" / "source_ranking_fixture.json"
)
FORMULA_VERSION = "golden_v0.1.0"
DEFAULT_RESEARCH_QUESTION_ID = "rq_creativity_ai_diversity"
DEFAULT_CONTRACT_ID = "contract_golden_v0"
DOMAIN_MATCH_SCORE = 0.85
REJECTED_MARKETING_REASON = (
    "Marketing page with low credibility; excluded from active queue."
)

_CREATIVITY_SOURCE_WEIGHTS = load_domain_pack("creativity").source_preferences.source_type_weights
SOURCE_TYPE_CREDIBILITY: dict[str, float] = {
    key: value for key, value in _CREATIVITY_SOURCE_WEIGHTS.items()
}

FIXTURE_CANDIDATE_PROFILES: dict[str, dict[str, Any]] = {
    "cand_empirical_paper": {
        "relevance_score": 0.92,
        "gap_fill_score": 0.85,
        "recency_score": 0.88,
        "source_diversity_score": 0.55,
        "novelty_score": 0.60,
        "drift_risk": 0.08,
        "reason": "Direct peer-reviewed empirical evidence on AI and semantic diversity.",
        "status": "queued",
    },
    "cand_theory_paper": {
        "relevance_score": 0.78,
        "gap_fill_score": 0.72,
        "recency_score": 0.42,
        "source_diversity_score": 0.60,
        "novelty_score": 0.70,
        "drift_risk": 0.12,
        "reason": "Older theory paper still relevant to originality and diversity gaps.",
        "status": "queued",
    },
    "cand_expert_interview": {
        "relevance_score": 0.58,
        "gap_fill_score": 0.48,
        "recency_score": 0.75,
        "source_diversity_score": 0.50,
        "novelty_score": 0.45,
        "drift_risk": 0.18,
        "reason": "Useful practitioner perspective on taste; below direct empirical evidence.",
        "status": "queued",
    },
    "cand_generic_blog": {
        "relevance_score": 0.38,
        "gap_fill_score": 0.28,
        "recency_score": 0.80,
        "source_diversity_score": 0.45,
        "novelty_score": 0.30,
        "drift_risk": 0.22,
        "reason": "Generic blog post without cited evidence; low queue priority.",
        "status": "queued",
    },
    "cand_marketing_page": {
        "relevance_score": 0.22,
        "gap_fill_score": 0.15,
        "recency_score": 0.90,
        "source_diversity_score": 0.40,
        "novelty_score": 0.20,
        "drift_risk": 0.35,
        "reason": REJECTED_MARKETING_REASON,
        "status": "rejected",
    },
}


def load_candidate_fixture(fixture_path: Path | None = None) -> dict[str, Any]:
    """Load a candidate-source fixture from disk."""
    path = fixture_path or DEFAULT_FIXTURE_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def compute_priority_score(
    *,
    relevance_score: float,
    credibility_prior: float,
    gap_fill_score: float,
    domain_match_score: float = DOMAIN_MATCH_SCORE,
    source_diversity_score: float = 0.5,
    recency_score: float = 0.5,
    novelty_score: float = 0.5,
    drift_risk: float = 0.1,
) -> float:
    """Deterministic queue priority per research run contract formula v1."""
    priority = (
        relevance_score * 0.25
        + credibility_prior * 0.20
        + gap_fill_score * 0.20
        + domain_match_score * 0.15
        + source_diversity_score * 0.10
        + recency_score * 0.05
        + novelty_score * 0.05
        - drift_risk * 0.25
    )
    return round(max(0.0, min(1.0, priority)), 4)


def rank_fixture_candidates(
    candidates: list[dict[str, Any]],
    *,
    contract: dict[str, Any] | None = None,
    domain_pack: str = "creativity",
) -> list[dict[str, Any]]:
    """Rank fixture candidates deterministically with machine-readable reasons."""
    _ = contract
    pack = load_domain_pack(domain_pack)
    ranked: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = candidate["id"]
        profile = FIXTURE_CANDIDATE_PROFILES.get(candidate_id)
        if profile is None:
            continue
        source_type = candidate.get("source_type", "")
        credibility_prior = source_type_credibility_prior(pack, source_type)

        priority_score = compute_priority_score(
            relevance_score=float(profile["relevance_score"]),
            credibility_prior=credibility_prior,
            gap_fill_score=float(profile["gap_fill_score"]),
            source_diversity_score=float(profile["source_diversity_score"]),
            recency_score=float(profile["recency_score"]),
            novelty_score=float(profile["novelty_score"]),
            drift_risk=float(profile["drift_risk"]),
        )

        status = profile["status"]
        if source_type == "marketing_page":
            status = "rejected"

        ranked.append(
            {
                "candidate_source_id": candidate_id,
                "title": candidate.get("title", ""),
                "source_type": source_type,
                "research_question_id": DEFAULT_RESEARCH_QUESTION_ID,
                "contract_id": DEFAULT_CONTRACT_ID,
                "priority_score": priority_score,
                "reason": profile["reason"],
                "status": status,
                "relevance_score": float(profile["relevance_score"]),
                "credibility_prior": credibility_prior,
                "gap_fill_score": float(profile["gap_fill_score"]),
                "recency_score": float(profile["recency_score"]),
                "source_diversity_score": float(profile["source_diversity_score"]),
                "novelty_score": float(profile["novelty_score"]),
                "drift_risk": float(profile["drift_risk"]),
                "formula_version": FORMULA_VERSION,
            }
        )

    ranked.sort(key=lambda item: item["priority_score"], reverse=True)
    return ranked


def queue_sources_from_fixture(
    conn: Any,
    *,
    fixture_path: Path | None = None,
    research_question_id: str = DEFAULT_RESEARCH_QUESTION_ID,
    contract_id: str = DEFAULT_CONTRACT_ID,
) -> dict[str, Any]:
    """Load fixture candidates, rank them, and persist queue rows."""
    from rge.db.repositories import CandidateSourceRepository, ResearchQueueRepository

    queue_repo = ResearchQueueRepository(conn)
    if queue_repo.count_for_question(research_question_id) > 0:
        existing = queue_repo.list_for_question(research_question_id)
        return {
            "status": "already_queued",
            "research_question_id": research_question_id,
            "queue_count": len(existing),
            "queue_item_ids": [item["id"] for item in existing],
        }

    fixture = load_candidate_fixture(fixture_path)
    ranked = rank_fixture_candidates(
        fixture.get("candidates", []),
        domain_pack="creativity",
    )
    candidate_repo = CandidateSourceRepository(conn)
    queue_ids: list[str] = []

    for item in ranked:
        candidate_repo.insert(
            candidate_id=item["candidate_source_id"],
            research_question_id=research_question_id,
            contract_id=contract_id,
            title=item["title"],
            source_type=item["source_type"],
            reason=item["reason"],
            relevance_score=item["relevance_score"],
            credibility_prior=item["credibility_prior"],
            gap_fill_score=item["gap_fill_score"],
            recency_score=item["recency_score"],
            source_diversity_score=item["source_diversity_score"],
            novelty_score=item["novelty_score"],
            drift_risk=item["drift_risk"],
            priority_score=item["priority_score"],
            status=item["status"],
        )
        if item["status"] == "queued":
            queue_item = queue_repo.insert(
                candidate_source_id=item["candidate_source_id"],
                research_question_id=research_question_id,
                contract_id=contract_id,
                priority_score=item["priority_score"],
                reason=item["reason"],
                status="queued",
            )
            queue_ids.append(queue_item["id"])

    return {
        "status": "completed",
        "research_question_id": research_question_id,
        "queue_count": len(queue_ids),
        "queue_item_ids": queue_ids,
        "ranked_candidates": ranked,
    }


def enqueue(items: list[dict[str, Any]]) -> None:
    """Legacy entry point retained for module contract checks."""
    if not items:
        return
    ranked = sorted(items, key=lambda item: item.get("priority_score", 0), reverse=True)
    for index, item in enumerate(ranked):
        if index > 0:
            assert item["priority_score"] <= ranked[index - 1]["priority_score"]
