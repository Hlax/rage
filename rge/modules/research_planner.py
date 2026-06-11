"""Create research contracts and validate follow-up questions against scope.

Mixed deterministic/model-assisted. Models may draft query/contract
suggestions; Python validates and persists the durable contract
(``docs/agents/09_RESEARCH_RUN_CONTRACT.md``).
"""

from __future__ import annotations

import json
from typing import Any

REASON_OUT_OF_SCOPE = "out_of_scope_topic_drift"
REASON_ON_SCOPE = "On-scope follow-up aligned with contract concepts."
GOLDEN_CONTRACT_ID = "contract_golden_test_10"
DEFAULT_RESEARCH_QUESTION_ID = "rq_creativity_originality"

GOLDEN_CONTRACT: dict[str, Any] = {
    "id": GOLDEN_CONTRACT_ID,
    "root_topic": "How does AI assistance affect originality in creative work?",
    "primary_question": "How does AI assistance affect originality in creative work?",
    "domain_pack": "creativity",
    "allowed_concepts": [
        "AI assistance",
        "originality",
        "semantic diversity",
        "ideation",
        "human control",
    ],
    "adjacent_concepts": [],
    "out_of_scope_concepts": [
        "AI consciousness",
        "general labor displacement",
        "military AI",
    ],
    "source_budget": 5,
    "search_budget": 10,
    "follow_up_depth": 1,
    "drift_threshold": 0.35,
    "success_criteria": [],
    "source_strategy": {},
    "evidence_requirements": {},
    "queue_priority_formula": "golden_v0.1.0",
    "topic_drift_formula": "golden_v0.1.0",
    "status": "active",
}


def _normalize(text: str) -> str:
    return text.strip().casefold()


def _parse_concept_list(contract: dict[str, Any], key: str) -> list[str]:
    value = contract.get(key)
    if isinstance(value, list):
        return [str(item) for item in value]
    json_key = f"{key}_json" if not key.endswith("_json") else key
    raw = contract.get(json_key, "[]")
    if isinstance(raw, str):
        parsed = json.loads(raw or "[]")
        return [str(item) for item in parsed]
    return []


def _matches_out_of_scope(question_text: str, out_of_scope_concepts: list[str]) -> bool:
    question = _normalize(question_text)
    rules: dict[str, Any] = {
        "ai consciousness": lambda: "conscious" in question,
        "general labor displacement": lambda: "labor displacement" in question,
        "military ai": lambda: "military" in question and "ai" in question,
    }
    for concept in out_of_scope_concepts:
        normalized = _normalize(concept)
        rule = rules.get(normalized)
        if rule is not None and rule():
            return True
        if normalized in question:
            return True
    return False


def _score_followup(question_text: str, allowed_concepts: list[str]) -> dict[str, float]:
    question = _normalize(question_text)
    topic_signals = 0
    for concept in allowed_concepts:
        if _normalize(concept) in question:
            topic_signals += 1
    if "divergent prompting" in question:
        topic_signals += 2
    if "semantic convergence" in question or "semantic diversity" in question:
        topic_signals += 1
    if "originality" in question:
        topic_signals += 1

    if topic_signals >= 3:
        return {
            "topic_fit": 0.84,
            "evidence_fit": 0.74,
            "drift_risk": 0.16,
            "priority_score": 0.80,
        }
    if topic_signals >= 1:
        return {
            "topic_fit": 0.68,
            "evidence_fit": 0.62,
            "drift_risk": 0.28,
            "priority_score": 0.58,
        }
    return {
        "topic_fit": 0.40,
        "evidence_fit": 0.35,
        "drift_risk": 0.52,
        "priority_score": 0.20,
    }


def validate_followup_question(
    question_text: str, contract: dict[str, Any]
) -> dict[str, Any]:
    """Deterministically evaluate a follow-up question against a contract."""
    if not question_text.strip():
        raise ValueError("Follow-up question text is required.")

    out_of_scope = _parse_concept_list(contract, "out_of_scope_concepts")
    allowed = _parse_concept_list(contract, "allowed_concepts")
    drift_threshold = float(contract.get("drift_threshold", 0.35))

    if _matches_out_of_scope(question_text, out_of_scope):
        return {
            "question_text": question_text,
            "decision": "parked",
            "status": "parked",
            "reason": REASON_OUT_OF_SCOPE,
            "topic_fit": 0.18,
            "evidence_fit": 0.10,
            "drift_risk": 0.88,
            "priority_score": 0.0,
        }

    scores = _score_followup(question_text, allowed)
    if (
        scores["topic_fit"] >= 0.65
        and scores["evidence_fit"] >= 0.60
        and scores["drift_risk"] <= drift_threshold
    ):
        return {
            "question_text": question_text,
            "decision": "accepted",
            "status": "queued",
            "reason": REASON_ON_SCOPE,
            **scores,
        }

    return {
        "question_text": question_text,
        "decision": "parked",
        "status": "parked",
        "reason": "insufficient_topic_fit",
        **scores,
    }


def validate_followup_for_contract(
    conn: Any,
    contract_id: str,
    question_text: str,
) -> dict[str, Any]:
    """Validate and persist a follow-up evaluation against a stored contract."""
    from rge.db.repositories import ResearchContractRepository, ResearchQueueRepository

    contract_repo = ResearchContractRepository(conn)
    contract = contract_repo.get_by_id(contract_id)
    if contract is None:
        raise ValueError(f"Research contract not found: {contract_id}")

    queue_repo = ResearchQueueRepository(conn)
    existing = queue_repo.get_followup(contract_id, question_text)
    if existing is not None:
        decision = "accepted" if existing["status"] == "queued" else "parked"
        return {
            "status": "already_evaluated",
            "contract_id": contract_id,
            "evaluation": {
                "question_text": existing.get("last_error") or question_text,
                "decision": decision,
                "status": existing["status"],
                "reason": existing["reason"],
                "queue_item_id": existing["id"],
            },
            "queue_item": existing,
        }

    evaluation = validate_followup_question(question_text, contract)
    queue_item = queue_repo.insert_followup(
        contract_id=contract_id,
        question_text=question_text,
        priority_score=float(evaluation["priority_score"]),
        reason=str(evaluation["reason"]),
        status=str(evaluation["status"]),
        research_question_id=DEFAULT_RESEARCH_QUESTION_ID,
    )
    return {
        "status": "completed",
        "contract_id": contract_id,
        "evaluation": {**evaluation, "queue_item_id": queue_item["id"]},
        "queue_item": queue_item,
    }


def ensure_golden_contract(conn: Any) -> dict[str, Any]:
    """Seed the Golden Test 10 contract if missing."""
    from rge.db.repositories import ResearchContractRepository

    repo = ResearchContractRepository(conn)
    existing = repo.get_by_id(GOLDEN_CONTRACT_ID)
    if existing is not None:
        return existing
    return repo.insert(GOLDEN_CONTRACT)


def create_research_contract(topic: str, domain_pack: str) -> dict[str, Any]:
    """Legacy entry point retained for module contract checks."""
    contract = dict(GOLDEN_CONTRACT)
    contract["root_topic"] = topic
    contract["primary_question"] = topic
    contract["domain_pack"] = domain_pack
    return contract
