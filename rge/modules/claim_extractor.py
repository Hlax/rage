"""Produce structured candidate claims from chunks. Model-assisted.

Flow:

    extract_claims_for_source(...)
    -> rge.llm.registry.get_model_client(...)
    -> client.extract_claims(...) returns CandidateClaimBatch
    -> claim_validator validates quote spans / scope / source IDs
    -> Python writes accepted/rejected claims
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rge.config import load_config
from rge.llm.mock_client import MockModelClient
from rge.llm.mode import effective_llm_mode
from rge.llm.registry import get_model_client
from rge.llm.schemas import CandidateClaimBatch_v0_1
from rge.modules.claim_validator import locate_quote_offsets, validate_candidate_claims
from rge.modules.manual_source_fixtures import (
    extract_fixture_for_manual_source,
    manual_text_lacks_extract_fixture,
)
from rge.safety.prompt_injection import source_text_has_prompt_injection_fixture

_REPO_ROOT = Path(__file__).resolve().parents[2]

_MANUAL_TEXT_NO_FIXTURE_ERROR = (
    "manual_text source has no checksum fixture in "
    "fixtures/manual_source_fixture_map.json. Use extract-claims "
    "--live-manual-fallthrough with RGE_LLM_MODE=ollama and RGE_ALLOW_LIVE_LLM=1 "
    "on a gitignored evidence --db, or ingest a checksum-pinned test source."
)


def _candidate_to_dict(item: Any) -> dict[str, Any]:
    return item.model_dump()


def _is_creativity_diversity_chunk(chunk_text: str) -> bool:
    lowered = chunk_text.casefold()
    return (
        "ai-assisted brainstorming" in lowered
        and "semantic diversity" in lowered
        and "idea quality" in lowered
    )


def _is_staged_fetch_spine_chunk(chunk_text: str) -> bool:
    lowered = chunk_text.casefold()
    return "human-ai co-creativity" in lowered and "songwriting" in lowered


def _pipeline_model_client(config=None):
    cfg = config if config is not None else load_config()
    return get_model_client(cfg, mode=effective_llm_mode(cfg))


def extract_candidate_claims(
    chunk: dict[str, Any],
    contract: dict[str, Any],
    domain_pack: str,
    *,
    fixture_name: str | None = None,
    client=None,
    source: Any | None = None,
) -> list[dict[str, Any]]:
    """Extract candidate claims from one chunk via the configured model client."""
    config = load_config()
    model_client = client or _pipeline_model_client(config)
    extract_kwargs: dict[str, Any] = {
        "chunk": chunk,
        "contract": contract,
        "domain_pack": domain_pack,
        "schema_version": config.llm_schema_version,
    }
    if isinstance(model_client, MockModelClient):
        extract_kwargs["fixture_name"] = (
            fixture_name or _default_fixture_for_source_chunk(source, chunk)
        )
    batch: CandidateClaimBatch_v0_1 = model_client.extract_claims(**extract_kwargs)

    candidates: list[dict[str, Any]] = []
    for item in batch.items:
        candidate = _candidate_to_dict(item)
        candidate["source_id"] = chunk["source_id"]
        candidate["chunk_id"] = chunk["id"]
        candidates.append(candidate)
    return candidates


def _default_fixture_for_source_chunk(
    source: Any | None,
    chunk: dict[str, Any],
) -> str:
    mapped = extract_fixture_for_manual_source(source)
    if mapped:
        return mapped
    if manual_text_lacks_extract_fixture(source):
        raise ValueError(_MANUAL_TEXT_NO_FIXTURE_ERROR)
    return _default_fixture_for_chunk(chunk)


def _default_fixture_for_chunk(chunk: dict[str, Any]) -> str:
    chunk_text = chunk.get("chunk_text", "")
    if source_text_has_prompt_injection_fixture(chunk_text):
        return "claim_extraction_prompt_injection.json"
    if _is_staged_fetch_spine_chunk(chunk_text):
        return "staged_fetch_extract_claims.json"
    if _is_creativity_diversity_chunk(chunk_text):
        return "claim_extraction_creativity_scoped.json"
    return "claim_extraction_valid_and_missing_quote.json"


def extract_and_validate_for_chunk(
    chunk: dict[str, Any],
    *,
    domain_pack: str,
    fixture_name: str | None = None,
    client=None,
    source: Any | None = None,
    live_manual_fallthrough: bool = False,
) -> dict[str, list[dict[str, Any]]]:
    """Extract candidates for one chunk and validate them deterministically."""
    contract: dict[str, Any] = {"domain_pack": domain_pack}
    if live_manual_fallthrough:
        contract["manual_text_arbitrary_live"] = True
    candidates = extract_candidate_claims(
        chunk,
        contract,
        domain_pack,
        fixture_name=fixture_name,
        client=client,
        source=source,
    )
    return validate_candidate_claims(
        candidates,
        chunk_text=chunk["chunk_text"],
        domain_pack=domain_pack,
    )


def extract_claims_for_source(
    conn: Any,
    source_id: str,
    *,
    fixture_name: str | None = None,
    live_manual_fallthrough: bool = False,
    client: Any | None = None,
    config: Any | None = None,
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

    cfg = config if config is not None else load_config()
    if live_manual_fallthrough:
        if not manual_text_lacks_extract_fixture(source):
            raise ValueError(
                "live_manual_fallthrough requires a manual_text source absent from "
                "fixtures/manual_source_fixture_map.json."
            )
        model_client = client or get_model_client(cfg, mode="ollama")
    else:
        model_client = client or _pipeline_model_client(cfg)

    accepted_ids: list[str] = []
    rejected_ids: list[str] = []
    extractor_provider = model_client.provider
    extractor_model = getattr(model_client, "model", "unknown")

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
            client=model_client,
            source=source,
            live_manual_fallthrough=live_manual_fallthrough,
        )
        for claim in result["accepted"]:
            char_start, char_end = locate_quote_offsets(
                str(claim["quote_span"]), chunk_dict["chunk_text"]
            )
            if char_start is not None:
                claim["quote_char_start"] = char_start
                claim["quote_char_end"] = char_end
        for claim in result["accepted"]:
            record = claim_repo.insert_accepted(
                claim,
                extractor_provider=extractor_provider,
                extractor_model=extractor_model,
                llm_schema_version=cfg.llm_schema_version,
            )
            accepted_ids.append(record.id)
        for claim in result["rejected"]:
            record = claim_repo.insert_rejected(
                claim,
                rejection_reason=claim["rejection_reason"],
                extractor_provider=extractor_provider,
                extractor_model=extractor_model,
                llm_schema_version=cfg.llm_schema_version,
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
