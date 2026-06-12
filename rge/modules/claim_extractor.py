"""Produce structured candidate claims from chunks. Model-assisted.

Flow:

    extract_claims_for_source(...)
    -> rge.llm.registry.get_model_client(...)
    -> client.extract_claims(...) returns CandidateClaimBatch
    -> claim_validator validates quote spans / scope / source IDs
    -> Python writes accepted/rejected claims
"""

from __future__ import annotations

import os
from typing import Any

from rge.config import load_config
from rge.llm.registry import get_model_client
from rge.llm.schemas import CandidateClaimBatch_v0_1
from rge.modules.claim_validator import validate_candidate_claims
from rge.safety.prompt_injection import source_text_has_prompt_injection_fixture


def _candidate_to_dict(item: Any) -> dict[str, Any]:
    return item.model_dump()


def _is_creativity_diversity_chunk(chunk_text: str) -> bool:
    lowered = chunk_text.casefold()
    return (
        "ai-assisted brainstorming" in lowered
        and "semantic diversity" in lowered
        and "idea quality" in lowered
    )


def extract_candidate_claims(
    chunk: dict[str, Any],
    contract: dict[str, Any],
    domain_pack: str,
    *,
    fixture_name: str | None = None,
) -> list[dict[str, Any]]:
    """Extract candidate claims from one chunk via the configured model client."""
    prior_mode = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    try:
        config = load_config()
        client = get_model_client(config)
        batch: CandidateClaimBatch_v0_1 = client.extract_claims(
            chunk=chunk,
            contract=contract,
            domain_pack=domain_pack,
            schema_version=config.llm_schema_version,
            fixture_name=fixture_name or _default_fixture_for_chunk(chunk),
        )
    finally:
        if prior_mode is None:
            os.environ.pop("RGE_LLM_MODE", None)
        else:
            os.environ["RGE_LLM_MODE"] = prior_mode

    candidates: list[dict[str, Any]] = []
    for item in batch.items:
        candidate = _candidate_to_dict(item)
        candidate["source_id"] = chunk["source_id"]
        candidate["chunk_id"] = chunk["id"]
        candidates.append(candidate)
    return candidates


def _default_fixture_for_chunk(chunk: dict[str, Any]) -> str:
    chunk_text = chunk.get("chunk_text", "")
    if source_text_has_prompt_injection_fixture(chunk_text):
        return "claim_extraction_prompt_injection.json"
    if _is_creativity_diversity_chunk(chunk_text):
        return "claim_extraction_creativity_scoped.json"
    return "claim_extraction_valid_and_missing_quote.json"


def extract_and_validate_for_chunk(
    chunk: dict[str, Any],
    *,
    domain_pack: str,
    fixture_name: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Extract candidates for one chunk and validate them deterministically."""
    contract: dict[str, Any] = {"domain_pack": domain_pack}
    candidates = extract_candidate_claims(
        chunk,
        contract,
        domain_pack,
        fixture_name=fixture_name,
    )
    return validate_candidate_claims(
        candidates,
        chunk_text=chunk["chunk_text"],
    )


def extract_claims_for_source(
    conn: Any,
    source_id: str,
    *,
    fixture_name: str | None = None,
) -> dict[str, Any]:
    """Extract, validate, and persist claims for all chunks of a source."""
    from rge.db.repositories import ChunkRepository, ClaimRepository, SourceRepository

    source = SourceRepository(conn).get_by_id(source_id)
    if source is None:
        raise ValueError(f"Source not found: {source_id}")

    chunks = ChunkRepository(conn).list_for_source(source_id)
    if not chunks:
        raise ValueError(f"Source has no chunks: {source_id}")

    claim_repo = ClaimRepository(conn)
    if claim_repo.count_for_source(source_id) > 0:
        accepted = claim_repo.list_for_source(source_id, status="accepted")
        rejected = claim_repo.list_for_source(source_id, status="rejected")
        return {
            "status": "already_extracted",
            "source_id": source_id,
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "accepted_claim_ids": [claim.id for claim in accepted],
            "rejected_claim_ids": [claim.id for claim in rejected],
        }

    accepted_ids: list[str] = []
    rejected_ids: list[str] = []

    for chunk in chunks:
        chunk_dict = {
            "id": chunk.id,
            "source_id": chunk.source_id,
            "chunk_index": chunk.chunk_index,
            "chunk_text": chunk.chunk_text,
        }
        result = extract_and_validate_for_chunk(
            chunk_dict,
            domain_pack=source.domain,
            fixture_name=fixture_name,
        )
        for claim in result["accepted"]:
            record = claim_repo.insert_accepted(
                claim,
                extractor_provider="mock",
                extractor_model="mock",
                llm_schema_version=load_config().llm_schema_version,
            )
            accepted_ids.append(record.id)
        for claim in result["rejected"]:
            record = claim_repo.insert_rejected(
                claim,
                rejection_reason=claim["rejection_reason"],
                extractor_provider="mock",
                extractor_model="mock",
                llm_schema_version=load_config().llm_schema_version,
            )
            rejected_ids.append(record.id)

    return {
        "status": "completed",
        "source_id": source_id,
        "accepted_count": len(accepted_ids),
        "rejected_count": len(rejected_ids),
        "accepted_claim_ids": accepted_ids,
        "rejected_claim_ids": rejected_ids,
    }
