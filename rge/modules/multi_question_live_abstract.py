"""Multi-question live abstract evidence runs with purpose-gating proof.

Runs 3–5 operator-gated live abstract evidence quality smokes (one temp DB per
question), validates cross-question purpose routing, and emits a public-safe
Atlas bundle with per-question artifacts. Mock LLM only; no paid APIs; no PDFs.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rge.db.connection import ensure_database
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.live_arbitrary_source_health import (
    LIVE_SOURCE_HEALTH_ARTIFACT_NAME,
    build_live_abstract_evidence_quality_summary,
    classify_live_abstract_evidence_quality_verdict,
    run_live_network_abstract_evidence_quality_smoke,
)
from rge.modules.principal_audit_gate import repo_root
from rge.modules.purpose_gating import (
    evaluate_text_purpose_fit,
    required_concept_family_for_question,
)
from rge.modules.research_purpose import classify_research_purpose
from rge.modules.source_resolver.query_expansion import openalex_safe_query

PACKET_ID = "multi-question-live-abstract-runs"
MULTI_QUESTION_BUNDLE_SCHEMA_VERSION = "atlas_multi_question_live_abstract_v0.1.0"
MULTI_QUESTION_BUNDLE_NAME = "atlas_multi_question_live_abstract_latest.json"
GENERIC_DIVERSITY_FIXTURE_TEXT = (
    "Generative AI assistance may increase ideation output in brainstorming tasks "
    "while reducing semantic diversity across creative alternatives."
)

NEXT_RECOMMENDED_PACKET = {
    "id": "live-source-expansion",
    "title": "Live Source Expansion",
}


@dataclass(frozen=True)
class MultiQuestionLiveAbstractProfile:
    question_id: str
    question: str
    resolver_query: str
    purpose_family: str | None
    gate_mode: str


MULTI_QUESTION_LIVE_ABSTRACT_PROFILES: tuple[MultiQuestionLiveAbstractProfile, ...] = (
    MultiQuestionLiveAbstractProfile(
        question_id="mq_ai_human_creativity",
        question="How does AI affect human creativity?",
        resolver_query="human AI creativity",
        purpose_family=None,
        gate_mode="open",
    ),
    MultiQuestionLiveAbstractProfile(
        question_id="mq_ai_assistance_diversity",
        question=(
            "Does AI assistance improve idea quality while reducing semantic diversity?"
        ),
        resolver_query="AI assistance idea diversity creativity",
        purpose_family=None,
        gate_mode="open",
    ),
    MultiQuestionLiveAbstractProfile(
        question_id="mq_cocreation_agency",
        question=(
            "How does human-AI co-creation affect author agency and creative control?"
        ),
        resolver_query="human AI co-creation agency creative control",
        purpose_family="agency_cocreation",
        gate_mode="strict",
    ),
    MultiQuestionLiveAbstractProfile(
        question_id="mq_artist_style_originality",
        question=(
            "How do artists and designers preserve originality and visual style "
            "when using AI tools?"
        ),
        resolver_query="artist designer originality visual style AI",
        purpose_family="style_originality",
        gate_mode="strict",
    ),
    MultiQuestionLiveAbstractProfile(
        question_id="mq_ai_creativity_benchmark",
        question="How should AI creativity be evaluated and benchmarked?",
        resolver_query="AI creativity evaluation benchmark",
        purpose_family=None,
        gate_mode="open",
    ),
)


def profile_as_dict(profile: MultiQuestionLiveAbstractProfile) -> dict[str, Any]:
    return {
        "question_id": profile.question_id,
        "question": profile.question,
        "resolver_query": profile.resolver_query,
        "openalex_safe_query": openalex_safe_query(profile.resolver_query),
        "purpose_family": profile.purpose_family,
        "gate_mode": profile.gate_mode,
        "purpose": classify_research_purpose(
            profile.question,
            domain="creativity",
            question_id=profile.question_id,
        ),
    }


def assert_live_multi_question_abstract_smoke_env() -> dict[str, str]:
    """Fail closed unless operator opts into multi-question live abstract smoke."""
    from rge.modules.live_arbitrary_source_health import (
        assert_live_abstract_evidence_quality_smoke_env,
    )

    combined = assert_live_abstract_evidence_quality_smoke_env()
    allow = os.environ.get("RGE_ALLOW_LIVE_MULTI_QUESTION_ABSTRACT_SMOKE", "0").strip().casefold()
    if allow not in {"1", "true", "yes"}:
        raise RuntimeError(
            "Multi-question live abstract smoke requires "
            "RGE_ALLOW_LIVE_MULTI_QUESTION_ABSTRACT_SMOKE=1."
        )
    combined["RGE_ALLOW_LIVE_MULTI_QUESTION_ABSTRACT_SMOKE"] = allow
    return combined


def validate_generic_diversity_blocked_on_strict_questions(
    *,
    domain_pack: str = "creativity",
    generic_text: str = GENERIC_DIVERSITY_FIXTURE_TEXT,
) -> dict[str, Any]:
    """Prove generic AI/diversity evidence fails strict purpose-gated questions."""
    results: list[dict[str, Any]] = []
    for profile in MULTI_QUESTION_LIVE_ABSTRACT_PROFILES:
        decision = evaluate_text_purpose_fit(
            generic_text,
            question=profile.question,
            domain_pack=domain_pack,
            evidence_ref="generic_diversity_fixture",
        )
        results.append(
            {
                "question_id": profile.question_id,
                "gate_mode": profile.gate_mode,
                "purpose_family": profile.purpose_family,
                "purpose_match_status": decision.get("purpose_match_status"),
                "decision": decision.get("decision"),
                "why": decision.get("why_evidence_downgraded_or_rejected"),
            }
        )

    strict_blocked = all(
        item["decision"] == "rejected"
        for item in results
        if item["gate_mode"] == "strict"
    )
    open_allowed = all(
        item["decision"] != "rejected"
        for item in results
        if item["gate_mode"] == "open"
    )
    return {
        "generic_text_preview": generic_text[:120],
        "per_question_decisions": results,
        "strict_questions_reject_generic": strict_blocked,
        "open_questions_allow_generic": open_allowed,
        "purpose_routing_valid": strict_blocked and open_allowed,
    }


def _public_question_run_summary(
    profile: MultiQuestionLiveAbstractProfile,
    *,
    pipeline_result: dict[str, Any],
    quality_summary: dict[str, Any],
    evidence_verdict: str,
    evidence_rationale: str,
    operator_artifact_ref: str | None,
) -> dict[str, Any]:
    artifact = dict(pipeline_result.get("atlas_safe_artifact") or {})
    trace = dict(artifact.get("trace_summary") or {})
    return {
        "question_id": profile.question_id,
        "question": profile.question,
        "resolver_query": profile.resolver_query,
        "gate_mode": profile.gate_mode,
        "purpose_family": profile.purpose_family,
        "evidence_quality_verdict": evidence_verdict,
        "evidence_quality_rationale": evidence_rationale,
        "live_source_count": int(quality_summary.get("live_source_count") or 0),
        "abstract_availability_count": int(
            quality_summary.get("abstract_availability_count") or 0
        ),
        "claims_accepted": int(quality_summary.get("claims_accepted") or 0),
        "claims_rejected": int(quality_summary.get("claims_rejected") or 0),
        "purpose_fit_status_counts": dict(
            quality_summary.get("purpose_fit_status_counts") or {}
        ),
        "purpose_gate_decision_counts": dict(
            quality_summary.get("purpose_gate_decision_counts") or {}
        ),
        "evidence_atom_count": int(quality_summary.get("evidence_atom_count") or 0),
        "relationship_count": int(quality_summary.get("relationship_count") or 0),
        "trace_summary": {
            "trace_count": int(trace.get("trace_count") or 0),
            "preview_row_count": len(trace.get("atlas_trace_preview") or []),
        },
        "operator_artifact_ref": operator_artifact_ref,
        "atlas_artifact_public_safe": assert_no_private_fields({"artifact": artifact})
        == [],
    }


def build_multi_question_atlas_bundle(
    question_runs: list[dict[str, Any]],
    *,
    purpose_routing_validation: dict[str, Any],
    verdict: str | None = None,
    rationale: str | None = None,
) -> dict[str, Any]:
    """Build public-safe multi-question Atlas bundle."""
    bundle = {
        "schema_version": MULTI_QUESTION_BUNDLE_SCHEMA_VERSION,
        "status": "completed",
        "packet_id": PACKET_ID,
        "question_count": len(question_runs),
        "multi_question_verdict": verdict,
        "multi_question_rationale": rationale,
        "purpose_routing_validation": {
            "purpose_routing_valid": purpose_routing_validation.get(
                "purpose_routing_valid"
            ),
            "strict_questions_reject_generic": purpose_routing_validation.get(
                "strict_questions_reject_generic"
            ),
            "open_questions_allow_generic": purpose_routing_validation.get(
                "open_questions_allow_generic"
            ),
        },
        "question_runs": question_runs,
        "aggregate": {
            "questions_with_live_sources": sum(
                1 for run in question_runs if int(run.get("live_source_count") or 0) >= 1
            ),
            "questions_with_accepted_claims": sum(
                1 for run in question_runs if int(run.get("claims_accepted") or 0) >= 1
            ),
            "total_accepted_claims": sum(
                int(run.get("claims_accepted") or 0) for run in question_runs
            ),
            "total_rejected_claims": sum(
                int(run.get("claims_rejected") or 0) for run in question_runs
            ),
        },
        "next_recommended_packet": NEXT_RECOMMENDED_PACKET,
    }
    violations = assert_no_private_fields({"bundle": bundle})
    if violations:
        raise ValueError(
            "Multi-question Atlas bundle blocked by private-field policy: "
            + "; ".join(violations[:5])
        )
    return bundle


def classify_multi_question_verdict(
    question_runs: list[dict[str, Any]],
    *,
    purpose_routing_validation: dict[str, Any],
) -> tuple[str, str]:
    """Return (verdict, rationale) for multi-question live abstract proof."""
    if not purpose_routing_validation.get("purpose_routing_valid"):
        return (
            "NO-GO",
            "Generic AI/diversity evidence must be rejected on strict agency/style "
            "questions and allowed on open questions.",
        )

    with_sources = [
        run for run in question_runs if int(run.get("live_source_count") or 0) >= 1
    ]
    if len(with_sources) < len(MULTI_QUESTION_LIVE_ABSTRACT_PROFILES):
        return (
            "PARTIAL",
            "One or more questions failed live source discovery.",
        )

    with_accepted = [
        run for run in question_runs if int(run.get("claims_accepted") or 0) >= 1
    ]
    strict_runs = [
        run
        for run in question_runs
        if run.get("gate_mode") == "strict"
    ]
    strict_with_purpose_counts = [
        run
        for run in strict_runs
        if run.get("purpose_fit_status_counts")
        or run.get("purpose_gate_decision_counts")
    ]

    if len(with_accepted) >= 3 and len(strict_with_purpose_counts) == len(strict_runs):
        return (
            "GO",
            "Each question resolved live sources with purpose-fit counts; strict "
            "agency/style questions route separately from open creativity questions.",
        )

    if with_sources:
        return (
            "PARTIAL",
            "Live discovery works across questions but accepted quote-backed evidence "
            "is thin on one or more purpose-gated runs.",
        )

    return "NO-GO", "Multi-question live abstract runs produced no usable evidence."


def run_live_multi_question_abstract_smoke(
    *,
    output_dir: Path,
    profiles: tuple[MultiQuestionLiveAbstractProfile, ...] = MULTI_QUESTION_LIVE_ABSTRACT_PROFILES,
    domain_pack: str = "creativity",
    limit: int = 5,
    root: Path | None = None,
) -> dict[str, Any]:
    """Run operator-gated multi-question live abstract evidence quality proof."""
    assert_live_multi_question_abstract_smoke_env()
    os.environ.setdefault("RGE_LLM_MODE", "mock")
    project_root = root or repo_root()
    output_dir.mkdir(parents=True, exist_ok=True)

    purpose_routing_validation = validate_generic_diversity_blocked_on_strict_questions(
        domain_pack=domain_pack,
    )
    question_runs: list[dict[str, Any]] = []

    for profile in profiles:
        question_dir = output_dir / profile.question_id
        question_dir.mkdir(parents=True, exist_ok=True)
        db_path = question_dir / f"{profile.question_id}.sqlite"
        conn = ensure_database(db_path)
        try:
            pipeline = run_live_network_abstract_evidence_quality_smoke(
                conn,
                question=profile.question,
                resolver_query=profile.resolver_query,
                domain_pack=domain_pack,
                output_dir=question_dir,
                limit=limit,
            )
        finally:
            conn.close()

        quality_summary = dict(pipeline.get("evidence_quality_summary") or {})
        if not quality_summary:
            quality_summary = build_live_abstract_evidence_quality_summary(pipeline)
        evidence_verdict = str(pipeline.get("evidence_quality_verdict") or "NO-GO")
        evidence_rationale = str(pipeline.get("evidence_quality_rationale") or "")
        try:
            operator_artifact_ref = (
                question_dir / LIVE_SOURCE_HEALTH_ARTIFACT_NAME
            ).relative_to(project_root).as_posix()
        except ValueError:
            operator_artifact_ref = (
                f"{profile.question_id}/{LIVE_SOURCE_HEALTH_ARTIFACT_NAME}"
            )
        question_runs.append(
            _public_question_run_summary(
                profile,
                pipeline_result=pipeline,
                quality_summary=quality_summary,
                evidence_verdict=evidence_verdict,
                evidence_rationale=evidence_rationale,
                operator_artifact_ref=operator_artifact_ref,
            )
        )

    verdict, rationale = classify_multi_question_verdict(
        question_runs,
        purpose_routing_validation=purpose_routing_validation,
    )
    bundle = build_multi_question_atlas_bundle(
        question_runs,
        purpose_routing_validation=purpose_routing_validation,
        verdict=verdict,
        rationale=rationale,
    )
    bundle_path = output_dir / MULTI_QUESTION_BUNDLE_NAME
    bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    return {
        "status": "completed",
        "packet_id": PACKET_ID,
        "verdict": verdict,
        "rationale": rationale,
        "purpose_routing_validation": purpose_routing_validation,
        "question_runs": question_runs,
        "bundle_path": str(bundle_path),
        "output_dir": str(output_dir),
        "profiles": [profile_as_dict(profile) for profile in profiles],
    }


def sync_multi_question_bundle_to_public_site(
    bundle_path: Path,
    *,
    public_path: Path,
) -> dict[str, Any]:
    """Copy validated multi-question bundle into public-site preview data."""
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    violations = assert_no_private_fields({"bundle": bundle})
    if violations:
        raise ValueError(
            "Multi-question bundle failed public-safe validation: "
            + "; ".join(violations[:5])
        )
    if bundle.get("schema_version") != MULTI_QUESTION_BUNDLE_SCHEMA_VERSION:
        raise ValueError(
            f"schema_version must be {MULTI_QUESTION_BUNDLE_SCHEMA_VERSION!r}."
        )
    if not bundle.get("question_runs"):
        raise ValueError("question_runs must be non-empty.")

    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    return {
        "status": "completed",
        "input_path": str(bundle_path),
        "output_path": str(public_path),
        "question_count": bundle.get("question_count"),
        "verdict_field": "aggregate",
    }


def required_env_setup_commands() -> list[str]:
    return [
        '$env:RGE_ALLOW_LIVE_MULTI_QUESTION_ABSTRACT_SMOKE = "1"',
        '$env:RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE = "1"',
        '$env:RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE = "1"',
        '$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"',
        '$env:RGE_ALLOW_SOURCE_NETWORK = "1"',
        '$env:OPENALEX_MAILTO = "operator@example.com"',
        '$env:RGE_LLM_MODE = "mock"',
        "python scripts/run_multi_question_live_abstract_smoke.py --sync-public",
    ]


def list_profile_purpose_families() -> list[dict[str, Any]]:
    """Expose required concept families per profile for tests/docs."""
    return [
        {
            "question_id": profile.question_id,
            "question": profile.question,
            "families": required_concept_family_for_question(
                profile.question,
                domain_pack="creativity",
            ).get("families"),
            "gate_mode": profile.gate_mode,
        }
        for profile in MULTI_QUESTION_LIVE_ABSTRACT_PROFILES
    ]
