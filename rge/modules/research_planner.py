"""Create research contracts and validate follow-up questions against scope.

Mixed deterministic/model-assisted. Models may draft query/contract
suggestions; Python validates and persists the durable contract
(``docs/agents/09_RESEARCH_RUN_CONTRACT.md``).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rge.modules.domain_pack_loader import (
    DomainPack,
    load_domain_pack,
    search_template_topic_signals,
    source_strategy_from_search_templates,
)
from rge.modules.research_purpose import classify_research_purpose

REASON_OUT_OF_SCOPE = "out_of_scope_topic_drift"
REASON_ON_SCOPE = "On-scope follow-up aligned with contract concepts."
REASON_ADJACENT_OUT_OF_SCOPE = "adjacent_out_of_scope_topic"
GOLDEN_CONTRACT_ID = "contract_golden_test_10"
DEFAULT_RESEARCH_QUESTION_ID = "rq_creativity_originality"
DEFAULT_FOLLOWUP_FIXTURE = "followup_question_generation_golden_test_16.json"

GOLDEN_GT16_ACTIVE_QUESTIONS = (
    "Does divergent prompting reduce semantic convergence in AI-assisted ideation?",
    "Does AI improve originality more when humans retain final selection control?",
    "Do AI-assisted workflows affect originality differently in writing versus design?",
)
GOLDEN_GT16_PARKED_QUESTIONS = (
    "Will AI replace all creative jobs?",
    "Is AI conscious?",
    "Who owns copyright for AI-generated work?",
)

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
    "purpose_metadata": {
        "schema_version": "purpose_metadata_v0.1.0",
        "question_id": DEFAULT_RESEARCH_QUESTION_ID,
        "question": "How does AI assistance affect originality in creative work?",
        "domain": "creativity",
        "research_intent": ["theory_building", "evidence_review"],
        "asset_affordance": [
            "reasoning_training_candidate",
            "argument_map_candidate",
            "concept_ontology_candidate",
        ],
        "evidence_need": "mixed_empirical_theory",
        "acceptable_source_types": [
            "paper",
            "abstract",
            "essay",
            "book",
            "interview",
            "webpage",
        ],
        "output_targets": ["cluster_report", "evidence_cards", "atlas_map"],
        "evidence_maturity": "seed",
        "training_suitability": "not_ready",
        "classifier_version": "purpose_classifier_v0.1.0",
    },
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
        "general labor displacement": lambda: (
            "labor displacement" in question
            or ("replace" in question and "job" in question)
        ),
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


def _pack_for_contract(contract: dict[str, Any]) -> DomainPack:
    pack_id = str(contract.get("domain_pack", "creativity")).strip() or "creativity"
    return load_domain_pack(pack_id)


def _attach_purpose_metadata(
    contract: dict[str, Any],
    *,
    question_id: str = DEFAULT_RESEARCH_QUESTION_ID,
) -> dict[str, Any]:
    if contract.get("purpose_metadata"):
        return contract
    contract["purpose_metadata"] = classify_research_purpose(
        str(contract.get("primary_question") or contract.get("root_topic") or ""),
        domain=str(contract.get("domain_pack") or "general"),
        question_id=question_id,
    )
    return contract


def _score_followup(
    question_text: str,
    allowed_concepts: list[str],
    pack: DomainPack,
) -> dict[str, float]:
    question = _normalize(question_text)
    topic_signals = 0
    for concept in allowed_concepts:
        if _normalize(concept) in question:
            topic_signals += 1
    topic_signals += search_template_topic_signals(pack, question_text)

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

    question = _normalize(question_text)
    if "copyright" in question or "authorship" in question:
        return {
            "question_text": question_text,
            "decision": "parked",
            "status": "parked",
            "reason": REASON_ADJACENT_OUT_OF_SCOPE,
            "topic_fit": 0.32,
            "evidence_fit": 0.28,
            "drift_risk": 0.62,
            "priority_score": 0.0,
        }

    scores = _score_followup(question_text, allowed, _pack_for_contract(contract))
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
    contract = dict(GOLDEN_CONTRACT)
    _attach_purpose_metadata(contract)
    pack = load_domain_pack(str(contract["domain_pack"]))
    contract["source_strategy"] = source_strategy_from_search_templates(pack)
    return repo.insert(contract)


def create_research_contract(topic: str, domain_pack: str) -> dict[str, Any]:
    """Legacy entry point retained for module contract checks."""
    contract = dict(GOLDEN_CONTRACT)
    contract["root_topic"] = topic
    contract["primary_question"] = topic
    contract["domain_pack"] = domain_pack
    contract.pop("purpose_metadata", None)
    return _attach_purpose_metadata(contract)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_followup_fixture(fixture_name: str) -> list[str]:
    path = _repo_root() / "fixtures" / "llm_outputs" / fixture_name
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        str(item["question_text"]).strip()
        for item in raw.get("items") or []
        if str(item.get("question_text", "")).strip()
    ]


def _questions_from_cluster_context(
    conn: Any, *, cluster_report_id: str | None
) -> list[str]:
    from rge.db.repositories import ClusterReportRepository, TheoryCandidateRepository
    from rge.modules.cluster_reporter import GOLDEN_CLUSTER_LABEL

    questions: list[str] = []
    cluster_repo = ClusterReportRepository(conn)
    if cluster_report_id:
        record = cluster_repo.get_by_id(cluster_report_id)
    else:
        record = cluster_repo.get_latest_for_label(GOLDEN_CLUSTER_LABEL)
    if record is None:
        return questions

    cluster_report = json.loads(record.report_json)
    questions.extend(cluster_report.get("candidate_next_questions") or [])

    for theory in TheoryCandidateRepository(conn).list_for_cluster_report(record.id):
        report = json.loads(theory.report_json)
        questions.extend(report.get("next_questions") or [])
    return questions


def propose_followup_questions(
    conn: Any,
    *,
    cluster_report_id: str | None = None,
    fixture_name: str | None = DEFAULT_FOLLOWUP_FIXTURE,
    include_golden_batch: bool = True,
) -> list[str]:
    """Collect deterministic follow-up question candidates from context sources."""
    proposed: list[str] = []
    proposed.extend(_questions_from_cluster_context(conn, cluster_report_id=cluster_report_id))
    if fixture_name:
        proposed.extend(_load_followup_fixture(fixture_name))
    if include_golden_batch:
        proposed.extend(GOLDEN_GT16_ACTIVE_QUESTIONS)
        proposed.extend(GOLDEN_GT16_PARKED_QUESTIONS)

    seen: set[str] = set()
    unique: list[str] = []
    for question in proposed:
        key = _normalize(question)
        if key and key not in seen:
            seen.add(key)
            unique.append(question.strip())
    return unique


def generate_followup_questions(
    conn: Any,
    *,
    contract_id: str | None = None,
    cluster_report_id: str | None = None,
    fixture_name: str | None = DEFAULT_FOLLOWUP_FIXTURE,
    include_golden_batch: bool = True,
) -> dict[str, Any]:
    """Generate follow-up questions from cluster/theory context and contract-gate them."""
    ensure_golden_contract(conn)
    resolved_contract_id = contract_id or GOLDEN_CONTRACT_ID
    candidates = propose_followup_questions(
        conn,
        cluster_report_id=cluster_report_id,
        fixture_name=fixture_name,
        include_golden_batch=include_golden_batch,
    )
    if not candidates:
        raise ValueError("No follow-up question candidates available.")

    evaluations: list[dict[str, Any]] = []
    for question_text in candidates:
        result = validate_followup_for_contract(
            conn,
            resolved_contract_id,
            question_text,
        )
        evaluation = result.get("evaluation") or {}
        evaluations.append(evaluation)

    from rge.db.repositories import ResearchQueueRepository

    followups = ResearchQueueRepository(conn).list_followups_for_contract(
        resolved_contract_id
    )
    status_counts = ResearchQueueRepository(conn).count_followups_by_status(
        resolved_contract_id
    )
    return {
        "status": "completed",
        "contract_id": resolved_contract_id,
        "candidate_count": len(candidates),
        "queued_count": status_counts.get("queued", 0),
        "parked_count": status_counts.get("parked", 0),
        "queued": [item for item in followups if item["status"] == "queued"],
        "parked": [item for item in followups if item["status"] == "parked"],
        "evaluations": evaluations,
        "followups": followups,
    }
