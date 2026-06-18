"""Deterministic research quality evaluation for autonomous researcher loop (ticket-332).

Scores observable research dimensions from run artifacts — not command exit codes alone.
"""

from __future__ import annotations

from typing import Any

QUALITY_SCHEMA_VERSION = "research_quality_eval_v0"

WEAKNESS_DIMENSIONS: tuple[str, ...] = (
    "weak_claim_extraction",
    "weak_source_linkage",
    "weak_concept_domain_linkage",
    "missing_hypotheses",
    "missing_follow_up_questions",
    "poor_contradiction_handling",
    "weak_ticket_generation",
    "weak_run_lineage",
)

WEAKNESS_LABELS: dict[str, str] = {
    "weak_claim_extraction": "weak claim extraction",
    "weak_source_linkage": "weak source linkage",
    "weak_concept_domain_linkage": "weak concept/domain linkage",
    "missing_hypotheses": "missing hypotheses",
    "missing_follow_up_questions": "missing follow-up questions",
    "poor_contradiction_handling": "poor contradiction handling",
    "weak_ticket_generation": "weak ticket generation",
    "weak_run_lineage": "weak run lineage",
}

RECOMMENDED_TICKET_TEMPLATES: dict[str, dict[str, Any]] = {
    "weak_ticket_generation": {
        "title": "Autonomous loop quality-driven improvement ticket seeding v0",
        "problem": (
            "The autonomous researcher loop observes rejection failure modes in run "
            "reports but suppresses golden-covered modes when generating improvement "
            "tickets, leaving ticket_ids empty and blocking self-upgrade closure."
        ),
        "affected_modules": [
            "rge/modules/ticket_writer.py",
            "rge/modules/research_quality_evaluator.py",
            "rge/modules/autonomous_researcher_loop.py",
        ],
        "expected_files": [
            "rge/modules/ticket_writer.py",
            "tests/unit/test_autonomous_researcher_loop_proof.py",
        ],
        "acceptance_criteria": [
            "Autonomous loop emits at least one actionable draft improvement ticket "
            "from observed non-golden failure modes OR documents explicit operator "
            "seed path when all modes are golden-covered.",
            "Quality evaluator weakest dimension maps to seeded ticket failure_reason.",
            "Golden tests remain mock-only; no auto-promotion to queue.",
        ],
        "test_plan": [
            "pytest tests/unit/test_autonomous_researcher_loop_proof.py",
            "pytest tests/golden/test_20_improvement_tickets.py",
        ],
        "non_goals": [
            "Auto-promote improvement tickets without human --confirm.",
            "Live Ollama ticket drafting.",
            "Public routes or schema migrations.",
        ],
        "risk_level": "medium",
        "rollback_plan": "Revert ticket seeding hook; restore golden-covered suppression only.",
    },
    "missing_hypotheses": {
        "title": "Surface theory candidates in autonomous loop Atlas inspection",
        "problem": (
            "Research runs may create theory candidates in DB but the autonomous loop "
            "Atlas snapshot and quality verdict do not treat missing hypotheses as a "
            "first-class weakness signal."
        ),
        "affected_modules": [
            "rge/modules/atlas_snapshot_builder.py",
            "rge/modules/theory_generator.py",
        ],
        "expected_files": [
            "rge/modules/atlas_snapshot_builder.py",
            "tests/unit/test_autonomous_researcher_loop_proof.py",
        ],
        "acceptance_criteria": [
            "Atlas snapshot or loop report exposes theory/hypothesis population counts.",
            "Quality evaluator missing_hypotheses score reflects DB theory_candidates.",
        ],
        "test_plan": ["pytest tests/unit/test_autonomous_researcher_loop_proof.py"],
        "non_goals": ["Public theory UI.", "Live model theory generation."],
        "risk_level": "low",
        "rollback_plan": "Revert atlas projection fields only.",
    },
    "weak_run_lineage": {
        "title": "Strengthen run lineage fields on autonomous loop export path",
        "problem": (
            "Atlas runs[] lack research_question_id or parent lineage on some export "
            "paths, weakening autonomous follow-up question seeding."
        ),
        "affected_modules": ["rge/modules/atlas_snapshot_builder.py"],
        "expected_files": [
            "rge/modules/atlas_snapshot_builder.py",
            "tests/unit/test_autonomous_researcher_loop_proof.py",
        ],
        "acceptance_criteria": [
            "All runs in fixture autonomous loop export include research_question_id.",
        ],
        "test_plan": ["pytest tests/unit/test_autonomous_researcher_loop_proof.py"],
        "non_goals": ["Schema migrations.", "Public run lineage UI."],
        "risk_level": "low",
        "rollback_plan": "Revert lineage projection changes.",
    },
}


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _score_claim_extraction(run_result: dict[str, Any]) -> tuple[int, str]:
    accepted = int(run_result.get("claims_accepted") or 0)
    rejected = int(run_result.get("claims_rejected") or 0)
    total = accepted + rejected
    if accepted < 1:
        return 0, "No accepted claims — extraction produced no usable evidence."
    if total == 0:
        return 0, "No claims recorded."
    reject_ratio = rejected / total
    if reject_ratio >= 0.75:
        return 25, f"High rejection ratio ({reject_ratio:.0%})."
    if reject_ratio >= 0.5:
        return 45, f"Elevated rejection ratio ({reject_ratio:.0%})."
    return 85, f"{accepted} accepted / {rejected} rejected claims."


def _score_source_linkage(coherence_report: dict[str, Any]) -> tuple[int, str]:
    population = coherence_report.get("population") or {}
    linkage = coherence_report.get("linkage") or {}
    cards = int(population.get("cards") or 0)
    with_meta = int(linkage.get("cards_with_public_source_metadata") or 0)
    ratio = _ratio(with_meta, cards)
    if cards == 0:
        return 0, "No cards exported."
    if ratio < 0.5:
        return 30, f"Only {with_meta}/{cards} cards expose public source metadata."
    if ratio < 1.0:
        return 60, f"{with_meta}/{cards} cards have source metadata."
    return 90, f"All {cards} cards linked to source metadata."


def _score_concept_linkage(coherence_report: dict[str, Any]) -> tuple[int, str]:
    population = coherence_report.get("population") or {}
    linkage = coherence_report.get("linkage") or {}
    domain = coherence_report.get("domain") or {}
    cards = int(population.get("cards") or 0)
    with_concepts = int(linkage.get("cards_with_concepts") or 0)
    coverage = float(domain.get("node_domain_coverage_ratio") or 0.0)
    card_ratio = _ratio(with_concepts, cards)
    if cards == 0:
        return 0, "No cards to evaluate concept linkage."
    score = int(min(card_ratio, coverage if coverage > 0 else card_ratio) * 100)
    if score < 50:
        return score, f"Weak concept linkage ({with_concepts}/{cards} cards; coverage {coverage:.0%})."
    if score < 80:
        return score, f"Partial concept/domain linkage ({with_concepts}/{cards} cards)."
    return score, f"Strong concept linkage ({with_concepts}/{cards} cards)."


def _score_hypotheses(run_report: dict[str, Any]) -> tuple[int, str]:
    count = int(run_report.get("theory_candidates_created") or 0)
    if count >= 1:
        return 90, f"{count} theory candidate(s) created."
    return 25, "No theory candidates created — hypotheses missing from loop output."


def _score_follow_up_questions(coherence_report: dict[str, Any]) -> tuple[int, str]:
    count = int((coherence_report.get("population") or {}).get("follow_up_questions") or 0)
    if count >= 1:
        return 90, f"{count} follow-up question(s) populated."
    return 20, "follow_up_questions[] empty — no seeded follow-up research."


def _score_contradiction_handling(
    run_result: dict[str, Any],
    atlas_snapshot: dict[str, Any],
) -> tuple[int, str]:
    relationships = int(run_result.get("relationships_active") or 0)
    qualifies = 0
    for edge in atlas_snapshot.get("edges") or []:
        metadata = edge.get("domain_metadata") or {}
        if metadata.get("contradiction_classification"):
            qualifies += 1
    if relationships >= 2 and qualifies >= 1:
        return 90, "Contradiction qualification present on relationship graph."
    if relationships >= 1:
        return 55, "Relationships exist but no contradiction qualification detected."
    return 15, "No active relationships — contradiction handling not exercised."


def _score_ticket_generation(
    run_result: dict[str, Any],
    run_report: dict[str, Any],
    improvement_result: dict[str, Any] | None,
) -> tuple[int, str]:
    ticket_ids = run_result.get("ticket_ids") or []
    if ticket_ids:
        return 95, f"{len(ticket_ids)} improvement ticket(s) generated."
    status = (improvement_result or {}).get("status", "")
    failure_modes = run_report.get("top_failure_modes") or []
    actionable = [
        mode
        for mode in failure_modes
        if int(mode.get("count") or 0) >= 1
    ]
    if status == "skipped_golden_covered" and actionable:
        reasons = ", ".join(str(m.get("reason")) for m in actionable[:3])
        return 10, (
            "Improvement tickets suppressed (golden-covered) despite observable "
            f"failure modes: {reasons}."
        )
    if not actionable:
        return 70, "No failure modes to ticket — generation not required."
    return 30, "Failure modes present but no improvement tickets emitted."


def _score_run_lineage(coherence_report: dict[str, Any]) -> tuple[int, str]:
    lineage = coherence_report.get("lineage") or {}
    run_count = int(lineage.get("run_count") or 0)
    with_question = int(lineage.get("runs_with_research_question_id") or 0)
    if run_count == 0:
        return 0, "No runs in atlas snapshot."
    ratio = _ratio(with_question, run_count)
    if ratio >= 1.0:
        return 90, "All runs include research_question_id."
    if ratio >= 0.5:
        return 55, f"{with_question}/{run_count} runs include research_question_id."
    return 25, f"Run lineage weak — {with_question}/{run_count} runs have question ids."


def evaluate_research_quality(
    *,
    run_result: dict[str, Any],
    run_report: dict[str, Any],
    atlas_snapshot: dict[str, Any],
    coherence_report: dict[str, Any],
    improvement_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Score research dimensions and return GO/PARTIAL/NO-GO quality verdict."""
    dimension_scores: dict[str, dict[str, Any]] = {}

    scorers: list[tuple[str, tuple[int, str]]] = [
        ("weak_claim_extraction", _score_claim_extraction(run_result)),
        ("weak_source_linkage", _score_source_linkage(coherence_report)),
        ("weak_concept_domain_linkage", _score_concept_linkage(coherence_report)),
        ("missing_hypotheses", _score_hypotheses(run_report)),
        ("missing_follow_up_questions", _score_follow_up_questions(coherence_report)),
        (
            "poor_contradiction_handling",
            _score_contradiction_handling(run_result, atlas_snapshot),
        ),
        (
            "weak_ticket_generation",
            _score_ticket_generation(run_result, run_report, improvement_result),
        ),
        ("weak_run_lineage", _score_run_lineage(coherence_report)),
    ]

    for dimension, (score, detail) in scorers:
        dimension_scores[dimension] = {
            "score": score,
            "label": WEAKNESS_LABELS[dimension],
            "detail": detail,
        }

    weakest = min(dimension_scores, key=lambda key: dimension_scores[key]["score"])
    weakest_score = dimension_scores[weakest]["score"]

    coherence_verdict = coherence_report.get("overall_coherence_verdict", "fail")
    run_ok = run_result.get("status") == "completed"
    has_claims = int(run_result.get("claims_accepted") or 0) >= 1

    if not run_ok or not has_claims or coherence_verdict == "fail":
        quality_verdict = "NO-GO"
        quality_detail = (
            "Loop did not produce usable research output or atlas coherence failed."
        )
    elif weakest == "weak_ticket_generation" and weakest_score <= 15:
        quality_verdict = "PARTIAL"
        quality_detail = (
            "Research and atlas inspection are useful, but the loop cannot seed a "
            "next improvement ticket from observed failures."
        )
    elif weakest_score >= 80 and coherence_verdict == "pass":
        quality_verdict = "GO"
        quality_detail = (
            "Loop produces useful research, passes atlas coherence, and weakest "
            "dimension is acceptable."
        )
    else:
        quality_verdict = "PARTIAL"
        quality_detail = (
            f"Loop runs with useful output but weakest dimension is "
            f"{WEAKNESS_LABELS[weakest]} ({weakest_score}/100)."
        )

    return {
        "quality_schema_version": QUALITY_SCHEMA_VERSION,
        "research_quality_verdict": quality_verdict,
        "research_quality_detail": quality_detail,
        "weakest_dimension": weakest,
        "weakest_dimension_label": WEAKNESS_LABELS[weakest],
        "weakest_dimension_score": weakest_score,
        "dimension_scores": dimension_scores,
        "coherence_verdict": coherence_verdict,
    }


def recommend_improvement_ticket(
    quality: dict[str, Any],
    *,
    queue_ticket_id: str,
    evidence: list[str],
) -> dict[str, Any]:
    """Build a human-seedable improvement ticket JSON from quality evaluation."""
    weakness = quality["weakest_dimension"]
    template = RECOMMENDED_TICKET_TEMPLATES.get(
        weakness,
        RECOMMENDED_TICKET_TEMPLATES["weak_ticket_generation"],
    )
    return {
        "id": queue_ticket_id,
        "title": template["title"],
        "problem": template["problem"],
        "evidence": list(evidence),
        "affected_modules": list(template["affected_modules"]),
        "expected_files": list(template["expected_files"]),
        "acceptance_criteria": list(template["acceptance_criteria"]),
        "test_plan": list(template["test_plan"]),
        "non_goals": list(template["non_goals"]),
        "risk_level": template["risk_level"],
        "rollback_plan": template["rollback_plan"],
        "status": "proposed",
        "category": "Phase 3 / autonomous researcher loop",
        "source_weakness": weakness,
        "source_quality_verdict": quality["research_quality_verdict"],
    }
