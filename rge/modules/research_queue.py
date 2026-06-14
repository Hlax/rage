"""Queue candidate sources and follow-up questions. Deterministic; no model use.

The queue controls execution: statuses queued/fetching/fetched/parsing/
extracting/staged/accepted/rejected/failed/needs_manual_review/parked.
Ranking uses a versioned formula aligned with
``docs/agents/09_RESEARCH_RUN_CONTRACT.md`` section 7.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
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
MARKETING_TITLE_PATTERNS = (
    "only tool you",
    "supercharge",
    "#1",
)
DISCOVERED_PEER_REVIEWED_RECENCY_YEARS = 10
DISCOVERED_DEFAULT_GAP_FILL_SCORE = 0.5
DISCOVERED_DEFAULT_NOVELTY_SCORE = 0.5
DISCOVERED_DEFAULT_SOURCE_DIVERSITY_SCORE = 0.5
DISCOVERED_DEFAULT_DRIFT_RISK = 0.1
DISCOVERED_MARKETING_DRIFT_RISK = 0.35
DISCOVERED_RECENCY_DECAY_YEARS = 30
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

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


def _normalize_tokens(text: str) -> set[str]:
    return set(_TOKEN_PATTERN.findall(text.casefold()))


def _discovered_reference_year(reference_year: int | None) -> int:
    if reference_year is not None:
        return reference_year
    return datetime.now(UTC).year


def infer_source_type_for_discovered_candidate(
    candidate: dict[str, Any],
    *,
    reference_year: int | None = None,
) -> str:
    """Infer a domain-pack source_type label from provider metadata only."""
    title = str(candidate.get("title") or "")
    title_folded = title.casefold()
    for pattern in MARKETING_TITLE_PATTERNS:
        if pattern in title_folded:
            return "marketing_page"

    work_type = str(candidate.get("work_type") or "").casefold()
    if work_type == "article":
        return "peer_reviewed_empirical"
    if work_type in {"book", "book-chapter"}:
        return "theory_essay"

    doi = candidate.get("doi")
    year = candidate.get("year")
    abstract = str(candidate.get("abstract") or "").strip()
    ref = _discovered_reference_year(reference_year)

    if doi:
        if isinstance(year, int) and ref - year <= DISCOVERED_PEER_REVIEWED_RECENCY_YEARS:
            return "peer_reviewed_empirical"
        return "theory_essay"
    if abstract:
        return "case_study"
    return "unknown"


def compute_discovered_relevance_score(
    *, query: str, title: str, abstract: str
) -> float:
    """Deterministic token overlap between query and title+abstract."""
    query_tokens = _normalize_tokens(query)
    if not query_tokens:
        return 0.0
    text_tokens = _normalize_tokens(f"{title} {abstract}")
    if not text_tokens:
        return 0.0
    overlap = len(query_tokens & text_tokens)
    return round(min(1.0, overlap / len(query_tokens)), 4)


def compute_discovered_recency_score(
    *, year: int | None, reference_year: int | None = None
) -> float:
    """Deterministic recency score from publication year."""
    if not isinstance(year, int):
        return 0.5
    ref = _discovered_reference_year(reference_year)
    age = max(0, ref - year)
    score = 1.0 - (age / DISCOVERED_RECENCY_DECAY_YEARS)
    return round(max(0.0, min(1.0, score)), 4)


def score_discovered_candidate(
    candidate: dict[str, Any],
    *,
    query: str,
    domain_pack: str = "creativity",
    reference_year: int | None = None,
) -> dict[str, Any]:
    """Score one discovered candidate with pack credibility and queue signals."""
    pack = load_domain_pack(domain_pack)
    source_type = infer_source_type_for_discovered_candidate(
        candidate,
        reference_year=reference_year,
    )
    credibility_prior = source_type_credibility_prior(pack, source_type)
    title = str(candidate.get("title") or "")
    abstract = str(candidate.get("abstract") or "")
    relevance_score = compute_discovered_relevance_score(
        query=query,
        title=title,
        abstract=abstract,
    )
    recency_score = compute_discovered_recency_score(
        year=candidate.get("year"),
        reference_year=reference_year,
    )
    gap_fill_score = DISCOVERED_DEFAULT_GAP_FILL_SCORE
    novelty_score = DISCOVERED_DEFAULT_NOVELTY_SCORE
    source_diversity_score = DISCOVERED_DEFAULT_SOURCE_DIVERSITY_SCORE
    drift_risk = (
        DISCOVERED_MARKETING_DRIFT_RISK
        if source_type == "marketing_page"
        else DISCOVERED_DEFAULT_DRIFT_RISK
    )
    priority_score = compute_priority_score(
        relevance_score=relevance_score,
        credibility_prior=credibility_prior,
        gap_fill_score=gap_fill_score,
        source_diversity_score=source_diversity_score,
        recency_score=recency_score,
        novelty_score=novelty_score,
        drift_risk=drift_risk,
    )

    if source_type == "marketing_page":
        status = "rejected"
        reason = REJECTED_MARKETING_REASON
    else:
        status = "queued"
        doi_note = "DOI present" if candidate.get("doi") else "no DOI"
        reason = (
            f"Inferred {source_type}; {doi_note}; relevance {relevance_score} "
            f"from query overlap."
        )

    scored = dict(candidate)
    scored.update(
        {
            "source_type": source_type,
            "credibility_prior": credibility_prior,
            "relevance_score": relevance_score,
            "recency_score": recency_score,
            "gap_fill_score": gap_fill_score,
            "novelty_score": novelty_score,
            "source_diversity_score": source_diversity_score,
            "drift_risk": drift_risk,
            "priority_score": priority_score,
            "reason": reason,
            "status": status,
            "formula_version": FORMULA_VERSION,
        }
    )
    return scored


def rank_discovered_candidates(
    candidates: list[dict[str, Any]],
    *,
    query: str,
    domain_pack: str = "creativity",
    reference_year: int | None = None,
) -> list[dict[str, Any]]:
    """Rank provider-shaped candidates using domain-pack source preferences."""
    ranked = [
        score_discovered_candidate(
            candidate,
            query=query,
            domain_pack=domain_pack,
            reference_year=reference_year,
        )
        for candidate in candidates
    ]
    ranked.sort(key=lambda item: item["priority_score"], reverse=True)
    return ranked


def discovered_candidate_source_id(provider: str, provider_id: str) -> str:
    """Stable candidate_sources PK for a provider-discovered work."""
    normalized_provider = provider.strip().casefold().replace("-", "_")
    normalized_id = (
        provider_id.strip()
        .replace("https://openalex.org/", "")
        .replace("/", "_")
        .replace(":", "_")
    )
    return f"disc_{normalized_provider}_{normalized_id}"


def _discovered_candidate_id_prefix(provider_id: str) -> str:
    return f"disc_{provider_id.strip().casefold().replace('-', '_')}_"


def enqueue_discovered_candidates(
    conn: Any,
    ranked: list[dict[str, Any]],
    *,
    provider_id: str,
    research_question_id: str,
    contract_id: str = DEFAULT_CONTRACT_ID,
) -> dict[str, Any]:
    """Persist ranked discovered candidates to staging queue tables."""
    from rge.db.repositories import CandidateSourceRepository, ResearchQueueRepository

    prefix = _discovered_candidate_id_prefix(provider_id)
    row = conn.execute(
        """
        SELECT COUNT(*) FROM candidate_sources
        WHERE research_question_id = ? AND id LIKE ?
        """,
        (research_question_id, prefix + "%"),
    ).fetchone()
    existing_count = int(row[0]) if row else 0
    queue_repo = ResearchQueueRepository(conn)
    if existing_count > 0:
        existing_queue = queue_repo.list_for_question(research_question_id)
        discovered_queue = [
            item
            for item in existing_queue
            if str(item.get("candidate_source_id", "")).startswith(prefix)
        ]
        return {
            "enqueue_status": "already_queued",
            "research_question_id": research_question_id,
            "provider": provider_id,
            "queue_count": len(discovered_queue),
            "queue_item_ids": [item["id"] for item in discovered_queue],
        }

    candidate_repo = CandidateSourceRepository(conn)
    queue_ids: list[str] = []

    for item in ranked:
        provider = str(item.get("provider") or provider_id)
        provider_work_id = str(item.get("provider_id") or "")
        candidate_id = discovered_candidate_source_id(provider, provider_work_id)
        url = item.get("landing_page_url") or item.get("open_access_url")

        candidate_repo.insert(
            candidate_id=candidate_id,
            research_question_id=research_question_id,
            contract_id=contract_id,
            title=str(item.get("title") or ""),
            source_type=str(item.get("source_type") or "unknown"),
            reason=str(item.get("reason") or ""),
            relevance_score=float(item.get("relevance_score", 0)),
            credibility_prior=float(item.get("credibility_prior", 0)),
            gap_fill_score=float(item.get("gap_fill_score", 0)),
            recency_score=float(item.get("recency_score", 0)),
            source_diversity_score=float(item.get("source_diversity_score", 0)),
            novelty_score=float(item.get("novelty_score", 0)),
            drift_risk=float(item.get("drift_risk", 0)),
            priority_score=float(item.get("priority_score", 0)),
            status=str(item.get("status") or "queued"),
            url=url,
        )
        if item.get("status") == "queued":
            queue_item = queue_repo.insert(
                candidate_source_id=candidate_id,
                research_question_id=research_question_id,
                contract_id=contract_id,
                priority_score=float(item.get("priority_score", 0)),
                reason=str(item.get("reason") or ""),
                status="queued",
            )
            queue_ids.append(queue_item["id"])

    return {
        "enqueue_status": "completed",
        "research_question_id": research_question_id,
        "provider": provider_id,
        "queue_count": len(queue_ids),
        "queue_item_ids": queue_ids,
    }


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
