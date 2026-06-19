"""Full-text quote-grounded evidence extraction."""

from __future__ import annotations

from typing import Any

from rge.modules.claim_extractor import extract_and_validate_for_chunk
from rge.modules.selective_fulltext import FULL_TEXT_CLEAN_TEXT_READY

FULLTEXT_EVIDENCE_BASIS = "full_text"


def fulltext_chunk_id(source_id: str) -> str:
    safe = source_id.replace(":", "_")
    return f"fulltext_{safe}"


def _fixture_for_fulltext(text: str) -> str:
    lowered = text.casefold()
    if "human-ai co-creativity" in lowered and "songwriting" in lowered:
        return "fulltext_quote_first_openalex.json"
    return "fulltext_quote_first_openalex.json"


def build_fulltext_chunk(
    *,
    source_id: str,
    clean_text: str,
    domain_pack: str,
) -> dict[str, Any]:
    return {
        "id": fulltext_chunk_id(source_id),
        "source_id": source_id,
        "chunk_index": 0,
        "chunk_text": clean_text,
        "domain_pack": domain_pack,
    }


def extract_fulltext_evidence_card(
    acquisition: dict[str, Any],
    *,
    domain_pack: str = "creativity",
    fixture_name: str | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    """Extract quote-grounded claims from parsed full-text acquisition."""
    source_id = str(acquisition.get("source_id") or "")
    status = str(acquisition.get("acquisition_status") or "")
    if status != FULL_TEXT_CLEAN_TEXT_READY:
        return {
            "source_id": source_id,
            "evidence_basis": None,
            "status": "skipped",
            "skip_reason": "full_text_not_clean",
            "accepted_claims": [],
            "rejected_claims": [],
        }
    clean_text = str(acquisition.get("clean_text") or "")
    if not clean_text.strip():
        return {
            "source_id": source_id,
            "evidence_basis": None,
            "status": "skipped",
            "skip_reason": "empty_clean_text",
            "accepted_claims": [],
            "rejected_claims": [],
        }
    chunk = build_fulltext_chunk(
        source_id=source_id,
        clean_text=clean_text,
        domain_pack=domain_pack,
    )
    resolved_fixture = fixture_name or _fixture_for_fulltext(clean_text)
    validation = extract_and_validate_for_chunk(
        chunk,
        domain_pack=domain_pack,
        fixture_name=resolved_fixture,
        client=client,
    )
    accepted = []
    for claim in validation.get("accepted", []):
        item = dict(claim)
        item["evidence_basis"] = FULLTEXT_EVIDENCE_BASIS
        accepted.append(item)
    return {
        "source_id": source_id,
        "evidence_basis": FULLTEXT_EVIDENCE_BASIS,
        "status": "completed",
        "parser_backend": (acquisition.get("parse") or {}).get("parser_backend"),
        "fixture_name": resolved_fixture,
        "accepted_claims": accepted,
        "rejected_claims": list(validation.get("rejected", [])),
        "accepted_count": len(accepted),
        "rejected_count": len(validation.get("rejected", [])),
    }


def generate_fulltext_evidence_cards(
    acquisitions: list[dict[str, Any]],
    *,
    domain_pack: str = "creativity",
    client: Any | None = None,
) -> dict[str, Any]:
    cards = [
        extract_fulltext_evidence_card(item, domain_pack=domain_pack, client=client)
        for item in acquisitions
    ]
    completed = [card for card in cards if card.get("status") == "completed"]
    return {
        "evidence_basis": FULLTEXT_EVIDENCE_BASIS,
        "card_count": len(cards),
        "completed_count": len(completed),
        "accepted_claims_total": sum(int(card.get("accepted_count") or 0) for card in completed),
        "rejected_claims_total": sum(int(card.get("rejected_count") or 0) for card in completed),
        "cards": cards,
    }
