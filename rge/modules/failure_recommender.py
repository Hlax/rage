"""Failure-to-packet recommender for MVP self-improvement loop (MVP-P4).

Classifies dominant bottlenecks from run metrics, source statuses, and rejection
reasons, then recommends the next improvement packet without heavy ticket audit drag.
"""

from __future__ import annotations

from typing import Any

from rge.modules.source_resolver.status import (
    ABSTRACT_AVAILABLE,
    DOWNLOAD_FAILED,
    METADATA_ONLY,
    PARSE_FAILED,
    SOURCE_STATUS_VALUES,
)

# MVP packet ids aligned with rge_strongest_mvp_phased_plan.md
PACKET_SOURCE_RESOLVER = "MVP-P1-source-resolver"
PACKET_ABSTRACT_EVIDENCE = "MVP-P2-abstract-evidence"
PACKET_FIELD_MAP = "MVP-P3-field-map"
PACKET_SELF_IMPROVEMENT = "MVP-P4-self-improvement"
PACKET_SELECTIVE_FULLTEXT = "MVP-P5-selective-fulltext"
PACKET_PDF_PARSER = "MVP-P6-pdf-parser-milestone"
PACKET_DEMO_LOOP = "MVP-P7-demo-loop"
PACKET_EVIDENCE_CARDS = "Phase4-P5-evidence-card-export"
PACKET_WEB_ADAPTER = "Phase4-P6-web-adapter"
PACKET_ASSET_EXPORT = "Phase4-P8-asset-export-candidates"
PACKET_QUALITY_GATES = "Phase4-P3-quality-gates"

REJECTION_UNSUPPORTED = "unsupported_claim"
REJECTION_UNSUPPORTED_WALL = "unsupported_claim_wall"
REJECTION_DIRTY_TEXT = "dirty_text"
REJECTION_ZERO_QUOTES = "zero_quoteable_spans"
REJECTION_ABSTRACT_MISSING = "abstract_missing"
REJECTION_OVERGENERALIZED = "overgeneralized_scope"
REJECTION_RANKER_BAD = "ranker_selected_bad_source"
REJECTION_EXTRACTOR_DRIFT = "extractor_prompt_drift"

PACKET_RECOMMENDATIONS: dict[str, dict[str, Any]] = {
    REJECTION_UNSUPPORTED_WALL: {
        "recommended_packet": PACKET_PDF_PARSER,
        "title": "PDF parser / quote-first extraction milestone",
        "rationale": (
            "High unsupported_claim volume with dirty or parsed PDF text indicates "
            "acquisition/parsing failure rather than ranking failure."
        ),
        "priority": "high",
    },
    REJECTION_DIRTY_TEXT: {
        "recommended_packet": PACKET_PDF_PARSER,
        "title": "PDF parser quality gates",
        "rationale": "Parsed document text failed readability/quoteability gates.",
        "priority": "high",
    },
    PARSE_FAILED: {
        "recommended_packet": PACKET_PDF_PARSER,
        "title": "PDF/TEI parse failure remediation",
        "rationale": "Document parse failures block quote-grounded extraction.",
        "priority": "high",
    },
    DOWNLOAD_FAILED: {
        "recommended_packet": PACKET_SELECTIVE_FULLTEXT,
        "title": "Selective full-text acquisition",
        "rationale": "Fetch failures suggest targeted acquisition policy tuning.",
        "priority": "medium",
    },
    METADATA_ONLY: {
        "recommended_packet": PACKET_SOURCE_RESOLVER,
        "title": "OA resolver / source expansion",
        "rationale": "Many sources lack abstract or OA locations for evidence extraction.",
        "priority": "high",
    },
    REJECTION_ABSTRACT_MISSING: {
        "recommended_packet": PACKET_SOURCE_RESOLVER,
        "title": "Metadata enrichment / source selection",
        "rationale": "Selected sources lack abstracts for abstract-first evidence.",
        "priority": "medium",
    },
    REJECTION_ZERO_QUOTES: {
        "recommended_packet": PACKET_QUALITY_GATES,
        "title": "Text quality / quoteability gates",
        "rationale": "Text exists but yielded zero quoteable spans for grounding.",
        "priority": "high",
    },
    "blocked_by_quality_gate": {
        "recommended_packet": PACKET_QUALITY_GATES,
        "title": "Acquisition quality gate remediation",
        "rationale": "Extraction blocked before LLM due to dirty or unextractable source text.",
        "priority": "high",
    },
    "webpage_dirty_text": {
        "recommended_packet": PACKET_WEB_ADAPTER,
        "title": "Web adapter clean-text normalization",
        "rationale": "Webpage HTML normalized to dirty_text; improve extraction adapter or source selection.",
        "priority": "medium",
    },
    "asset_export_backlog": {
        "recommended_packet": PACKET_ASSET_EXPORT,
        "title": "Derived asset export candidates",
        "rationale": "Evidence atoms exist but no conservative eval/style export candidates were derived.",
        "priority": "low",
    },
    REJECTION_UNSUPPORTED: {
        "recommended_packet": PACKET_ABSTRACT_EVIDENCE,
        "title": "Quote-first extraction / validator calibration",
        "rationale": "Claims failed quote grounding — tighten quote-first extraction.",
        "priority": "high",
    },
    REJECTION_RANKER_BAD: {
        "recommended_packet": PACKET_FIELD_MAP,
        "title": "Ranking / query expansion",
        "rationale": "Candidate quality problem — improve field-map ranking before parsers.",
        "priority": "medium",
    },
    REJECTION_EXTRACTOR_DRIFT: {
        "recommended_packet": PACKET_ABSTRACT_EVIDENCE,
        "title": "Extractor prompt drift remediation",
        "rationale": "Model outputs diverged from quote-first contract.",
        "priority": "medium",
    },
    REJECTION_OVERGENERALIZED: {
        "recommended_packet": PACKET_ABSTRACT_EVIDENCE,
        "title": "Scope-preserving abstract claims",
        "rationale": "Accepted path blocked by overgeneralized claims — narrow extraction.",
        "priority": "medium",
    },
    "weak_synthesis": {
        "recommended_packet": PACKET_FIELD_MAP,
        "title": "Field-map synthesis / concept linking",
        "rationale": "Accepted claims exist but synthesis/report quality is weak.",
        "priority": "medium",
    },
    "pdf_parser_unavailable": {
        "recommended_packet": PACKET_PDF_PARSER,
        "title": "PDF parser backend availability",
        "rationale": (
            "PDF sources report pdf_unavailable parser backend — install or enable "
            "PyMuPDF/pypdf/GROBID path."
        ),
        "priority": "medium",
    },
}


def _count_map(items: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        key = str(item)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _dominant_key(counts: dict[str, int]) -> str | None:
    if not counts:
        return None
    return max(counts.items(), key=lambda item: (item[1], item[0]))[0]


def classify_dominant_bottleneck(
    *,
    rejection_reasons: list[str] | None = None,
    source_statuses: list[str] | None = None,
    run_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return dominant failure signal and supporting counts."""
    metrics = run_metrics or {}
    rejection_counts = _count_map(list(rejection_reasons or []))
    status_counts = _count_map(list(source_statuses or []))

    for reason, count in metrics.get("rejection_counts", {}).items():
        rejection_counts[str(reason)] = rejection_counts.get(str(reason), 0) + int(count)
    for status, count in metrics.get("source_status_counts", {}).items():
        status_counts[str(status)] = status_counts.get(str(status), 0) + int(count)

    accepted = int(metrics.get("claims_accepted") or metrics.get("accepted_claims") or 0)
    rejected = int(metrics.get("claims_rejected") or metrics.get("rejected_claims") or 0)
    total_claims = accepted + rejected
    unsupported = rejection_counts.get(REJECTION_UNSUPPORTED, 0)
    if total_claims >= 5 and unsupported / total_claims >= 0.8:
        rejection_counts[REJECTION_UNSUPPORTED_WALL] = unsupported

    metadata_only_count = status_counts.get(METADATA_ONLY, 0)
    abstract_available_count = status_counts.get(ABSTRACT_AVAILABLE, 0)
    if metadata_only_count > abstract_available_count and metadata_only_count >= 2:
        status_counts[METADATA_ONLY] = metadata_only_count

    dominant_rejection = _dominant_key(rejection_counts)
    dominant_status = _dominant_key(status_counts)

    signal = dominant_rejection or dominant_status
    signal_kind = "rejection_reason" if dominant_rejection else "source_status"
    if (
        dominant_rejection == REJECTION_UNSUPPORTED
        and dominant_status in {PARSE_FAILED, DOWNLOAD_FAILED}
    ):
        signal = dominant_status
        signal_kind = "source_status"

    if accepted >= 3 and rejected <= 1 and not signal:
        signal = "weak_synthesis"
        signal_kind = "synthesis"

    return {
        "dominant_signal": signal,
        "signal_kind": signal_kind,
        "rejection_counts": rejection_counts,
        "source_status_counts": status_counts,
        "claims_accepted": accepted,
        "claims_rejected": rejected,
    }


def recommend_improvement_packet(
    *,
    rejection_reasons: list[str] | None = None,
    source_statuses: list[str] | None = None,
    run_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Recommend the next MVP improvement packet from run evidence."""
    classification = classify_dominant_bottleneck(
        rejection_reasons=rejection_reasons,
        source_statuses=source_statuses,
        run_metrics=run_metrics,
    )
    signal = classification.get("dominant_signal")
    template = PACKET_RECOMMENDATIONS.get(str(signal or ""))
    if template is None:
        template = {
            "recommended_packet": PACKET_DEMO_LOOP,
            "title": "Demo loop polish / diagnostics",
            "rationale": (
                "No dominant MVP failure signal matched known classes; inspect run "
                "artifacts and extend failure taxonomy."
            ),
            "priority": "low",
        }

    return {
        "status": "ok",
        "dominant_signal": signal,
        "signal_kind": classification.get("signal_kind"),
        "classification": classification,
        "recommended_packet": template["recommended_packet"],
        "recommendation_title": template["title"],
        "rationale": template["rationale"],
        "priority": template["priority"],
        "known_signals": sorted(set(SOURCE_STATUS_VALUES) | set(PACKET_RECOMMENDATIONS)),
    }


def recommend_from_abstract_evidence_run(
    abstract_evidence_result: dict[str, Any],
    *,
    source_statuses: list[str] | None = None,
) -> dict[str, Any]:
    """Build packet recommendation from an abstract evidence card run."""
    rejection_reasons: list[str] = []
    for card in abstract_evidence_result.get("cards") or []:
        for claim in card.get("rejected_claims") or []:
            reason = claim.get("rejection_reason")
            if reason:
                rejection_reasons.append(str(reason))
        if card.get("status") == "skipped" and card.get("skip_reason") == "abstract_missing_or_not_extractable":
            rejection_reasons.append(REJECTION_ABSTRACT_MISSING)

    metrics = {
        "claims_accepted": abstract_evidence_result.get("accepted_claims_total", 0),
        "claims_rejected": abstract_evidence_result.get("rejected_claims_total", 0),
    }
    recommendation = recommend_improvement_packet(
        rejection_reasons=rejection_reasons,
        source_statuses=source_statuses,
        run_metrics=metrics,
    )
    recommendation["source_run"] = "abstract_evidence"
    return recommendation


def recommend_from_run_report(run_report: dict[str, Any]) -> dict[str, Any]:
    """Build packet recommendation from a persisted run report JSON."""
    from rge.modules.acquisition_quality import failure_modes_from_acquisition_summary

    rejection_reasons: list[str] = []
    for item in run_report.get("top_failure_modes") or []:
        reason = item.get("reason")
        count = int(item.get("count") or 0)
        if reason:
            rejection_reasons.extend([str(reason)] * count)

    summary = run_report.get("acquisition_quality_summary") or {}
    for mode in failure_modes_from_acquisition_summary(summary):
        rejection_reasons.extend([str(mode["reason"])] * int(mode["count"]))

    source_statuses: list[str] = []
    for status, count in summary.get("acquisition_status_counts", {}).items():
        source_statuses.extend([str(status)] * int(count))

    metrics: dict[str, Any] = {
        "claims_accepted": run_report.get("claims_accepted", 0),
        "claims_rejected": run_report.get("claims_rejected", 0),
        "source_status_counts": summary.get("acquisition_status_counts") or {},
    }
    recommendation = recommend_improvement_packet(
        rejection_reasons=rejection_reasons,
        source_statuses=source_statuses,
        run_metrics=metrics,
    )
    recommendation["source_run"] = "run_report"
    return recommendation


def run_recommend_improvement_packet_command(
    *,
    run_report_path: str | None = None,
    abstract_evidence_path: str | None = None,
    fixture_mode: bool = False,
    domain_pack: str = "creativity",
) -> tuple[dict[str, Any], int]:
    """CLI handler for failure-to-packet recommendation."""
    from pathlib import Path

    import json

    from rge.modules.abstract_evidence import generate_abstract_evidence_cards
    from rge.modules.source_resolver import resolve_work_candidates

    payload_base: dict[str, Any] = {"command": "recommend-improvement-packet"}

    if run_report_path:
        report = json.loads(Path(run_report_path).read_text(encoding="utf-8"))
        result = recommend_from_run_report(report)
        return {**payload_base, **result, "input": "run_report"}, 0

    if abstract_evidence_path:
        evidence = json.loads(Path(abstract_evidence_path).read_text(encoding="utf-8"))
        result = recommend_from_abstract_evidence_run(evidence)
        return {**payload_base, **result, "input": "abstract_evidence"}, 0

    if fixture_mode:
        resolved = resolve_work_candidates(
            query="",
            domain_pack=domain_pack,
            limit=10,
            fixture_mode=True,
        )
        evidence = generate_abstract_evidence_cards(resolved.get("records") or [])
        statuses = [
            str(record.get("source_status") or "")
            for record in resolved.get("records") or []
        ]
        result = recommend_from_abstract_evidence_run(
            evidence,
            source_statuses=statuses,
        )
        return {**payload_base, **result, "input": "fixture_mode"}, 0

    return {
        **payload_base,
        "status": "error",
        "reason": "missing_input",
        "detail": (
            "Provide --run-report, --abstract-evidence, or --fixture-mode."
        ),
    }, 1
