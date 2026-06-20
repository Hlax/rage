"""Abstract-first quote-grounded evidence cards (MVP-P2).

Uses resolver records with available abstract text, runs quote-first extraction
through the existing claim validator, and returns evidence cards labeled
``abstract_only``. No full-text fetch required.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from rge.modules.claim_extractor import extract_and_validate_for_chunk
from rge.modules.purpose_gating import evaluate_text_purpose_fit
from rge.modules.source_resolver.evidence import explain_source_evidence
from rge.modules.source_resolver.status import (
    ABSTRACT_AVAILABLE,
    EXTRACTABLE,
    CLEAN_TEXT_READY,
    METADATA_ONLY,
    OA_PDF_AVAILABLE,
    OA_TEI_AVAILABLE,
)

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
ABSTRACT_EVIDENCE_BASIS = "abstract_only"
EXTRACTABLE_STATUSES = frozenset(
    {
        ABSTRACT_AVAILABLE,
        OA_PDF_AVAILABLE,
        OA_TEI_AVAILABLE,
        CLEAN_TEXT_READY,
        EXTRACTABLE,
    }
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_report_dir(repo_root: Path | None = None) -> Path:
    return (repo_root or _repo_root()) / "data" / "reports"


def abstract_chunk_id(source_id: str) -> str:
    safe = source_id.replace(":", "_")
    return f"abstract_{safe}"


def build_abstract_chunk(
    record: dict[str, Any],
    *,
    domain_pack: str | None = None,
) -> dict[str, Any] | None:
    """Build a single-chunk view over abstract text for quote validation."""
    abstract_text = str(record.get("abstract_text") or "").strip()
    if not abstract_text:
        return None
    source_id = str(record.get("source_id") or record.get("provider_id") or "unknown")
    return {
        "id": abstract_chunk_id(source_id),
        "source_id": source_id,
        "chunk_index": 0,
        "chunk_text": abstract_text,
        "domain_pack": domain_pack or record.get("domain_pack") or "creativity",
    }


def _fixture_for_abstract(abstract_text: str) -> str:
    lowered = abstract_text.casefold()
    if "human-ai" in lowered and "songwriting" in lowered:
        return "abstract_quote_first_openalex.json"
    if "idea diversity" in lowered and "divergent" in lowered:
        return "abstract_quote_first_creativity.json"
    return "abstract_quote_first_creativity.json"


def extract_abstract_evidence_card(
    record: dict[str, Any],
    *,
    domain_pack: str | None = None,
    question: str | None = None,
    fixture_name: str | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    """Extract quote-grounded claims from one resolver record's abstract."""
    evidence_summary = explain_source_evidence(record)
    source_id = str(record.get("source_id") or "")
    status = str(record.get("source_status") or METADATA_ONLY)
    pack = domain_pack or str(record.get("domain_pack") or "creativity")

    if status not in EXTRACTABLE_STATUSES or not evidence_summary["can_extract_abstract_claims"]:
        return {
            "source_id": source_id,
            "title": record.get("title"),
            "source_status": status,
            "evidence_basis": None,
            "status": "skipped",
            "skip_reason": "abstract_missing_or_not_extractable",
            "evidence_summary": evidence_summary,
            "accepted_claims": [],
            "rejected_claims": [],
            "recommendation": evidence_summary.get("extraction_recommendation"),
        }

    chunk = build_abstract_chunk(record, domain_pack=pack)
    if chunk is None:
        return {
            "source_id": source_id,
            "title": record.get("title"),
            "source_status": status,
            "evidence_basis": None,
            "status": "skipped",
            "skip_reason": "empty_abstract_text",
            "evidence_summary": evidence_summary,
            "accepted_claims": [],
            "rejected_claims": [],
        }

    source_purpose_fit = (
        evaluate_text_purpose_fit(
            f"{record.get('title') or ''} {chunk['chunk_text']}",
            question=question,
            domain_pack=pack,
            evidence_ref=source_id,
        )
        if question
        else {
            "purpose_match_status": "not_evaluated",
            "decision": "not_evaluated",
            "why_evidence_downgraded_or_rejected": "",
        }
    )
    if source_purpose_fit["decision"] == "rejected":
        return {
            "source_id": source_id,
            "title": record.get("title"),
            "source_status": status,
            "evidence_basis": None,
            "status": "skipped",
            "skip_reason": "purpose_mismatch",
            "purpose_match_status": source_purpose_fit["purpose_match_status"],
            "purpose_gate_decision": source_purpose_fit["decision"],
            "purpose_gate_reason": source_purpose_fit["why_evidence_downgraded_or_rejected"],
            "evidence_summary": evidence_summary,
            "accepted_claims": [],
            "rejected_claims": [],
        }

    resolved_fixture = fixture_name or _fixture_for_abstract(chunk["chunk_text"])
    validation = extract_and_validate_for_chunk(
        chunk,
        domain_pack=pack,
        fixture_name=resolved_fixture,
        client=client,
    )
    accepted = []
    purpose_rejected = []
    for claim in validation.get("accepted", []):
        item = dict(claim)
        item["evidence_basis"] = ABSTRACT_EVIDENCE_BASIS
        claim_purpose_fit = (
            evaluate_text_purpose_fit(
                str(item.get("claim_text") or ""),
                question=question,
                domain_pack=pack,
                evidence_ref=str(item.get("id") or item.get("claim_id") or ""),
            )
            if question
            else source_purpose_fit
        )
        item["purpose_match_status"] = claim_purpose_fit["purpose_match_status"]
        item["purpose_gate_decision"] = claim_purpose_fit["decision"]
        item["purpose_gate_reason"] = claim_purpose_fit.get(
            "why_evidence_downgraded_or_rejected",
            "",
        )
        if claim_purpose_fit["decision"] in {"accepted", "not_evaluated"}:
            accepted.append(item)
        else:
            purpose_rejected.append(
                {
                    **item,
                    "status": "rejected",
                    "rejection_reason": "purpose_mismatch",
                    "rejection_details": item["purpose_gate_reason"],
                }
            )
    rejected = list(validation.get("rejected", []))
    rejected.extend(purpose_rejected)

    return {
        "source_id": source_id,
        "title": record.get("title"),
        "source_status": status,
        "evidence_basis": ABSTRACT_EVIDENCE_BASIS,
        "status": "completed",
        "abstract_char_count": len(chunk["chunk_text"]),
        "fixture_name": resolved_fixture,
        "purpose_match_status": source_purpose_fit["purpose_match_status"],
        "purpose_gate_decision": source_purpose_fit["decision"],
        "purpose_gate_reason": source_purpose_fit.get("why_evidence_downgraded_or_rejected") or "",
        "accepted_claims": accepted,
        "rejected_claims": rejected,
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "evidence_summary": evidence_summary,
        "recommend_full_text": len(accepted) == 0 and status in {OA_PDF_AVAILABLE, OA_TEI_AVAILABLE},
    }


def generate_abstract_evidence_cards(
    records: list[dict[str, Any]],
    *,
    domain_pack: str | None = None,
    question: str | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    """Generate abstract evidence cards for many resolved source records."""
    cards: list[dict[str, Any]] = []
    for record in records:
        cards.append(
            extract_abstract_evidence_card(
                record,
                domain_pack=domain_pack,
                question=question,
                client=client,
            )
        )
    completed = [card for card in cards if card.get("status") == "completed"]
    skipped = [card for card in cards if card.get("status") == "skipped"]
    total_accepted = sum(int(card.get("accepted_count") or 0) for card in completed)
    total_rejected = sum(int(card.get("rejected_count") or 0) for card in completed)
    purpose_mismatch_count = sum(
        1
        for card in cards
        if card.get("purpose_match_status") == "mismatch"
        or card.get("purpose_gate_decision") in {"rejected", "downgraded"}
    )
    return {
        "evidence_basis": ABSTRACT_EVIDENCE_BASIS,
        "card_count": len(cards),
        "completed_count": len(completed),
        "skipped_count": len(skipped),
        "accepted_claims_total": total_accepted,
        "rejected_claims_total": total_rejected,
        "purpose_mismatch_count": purpose_mismatch_count,
        "cards": cards,
    }


def run_generate_abstract_evidence_command(
    *,
    query: str | None,
    domain_pack: str,
    limit: int,
    fixture_mode: bool,
    records: list[dict[str, Any]] | None = None,
    output_dir: Path | None = None,
) -> tuple[dict[str, Any], int]:
    """CLI handler: resolve sources then extract abstract evidence cards."""
    from rge.modules.source_resolver import resolve_work_candidates

    if records is None:
        resolved = resolve_work_candidates(
            query=query or "",
            domain_pack=domain_pack,
            limit=limit,
            fixture_mode=fixture_mode,
        )
        records = list(resolved.get("records") or [])

    result = generate_abstract_evidence_cards(
        records,
        domain_pack=domain_pack,
        question=query or "",
    )
    payload = {
        "command": "generate-abstract-evidence",
        "status": "ok",
        "domain_pack": domain_pack,
        "fixture_mode": fixture_mode,
        "source_count": len(records),
        **result,
    }

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "abstract_evidence_latest.json"
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        payload["output_path"] = str(out_path)

    return payload, 0
