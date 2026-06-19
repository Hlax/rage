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
from rge.modules.claim_validator import (
    REJECTION_ZERO_QUOTEABLE,
    locate_quote_offsets,
    validate_candidate_claims,
)
from rge.modules.manual_source_fixtures import (
    extract_fixture_for_manual_source,
    manual_text_lacks_extract_fixture,
)
from rge.modules.text_quality_gate import assess_chunk_extractability, gate_source_for_extraction
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


def _is_staged_rank2_fetch_spine_chunk(chunk_text: str) -> bool:
    return "constraint management" in chunk_text.casefold()


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


def _mock_fixture_profile_for_chunk(
    source: Any | None,
    chunk: dict[str, Any],
) -> str | None:
    """Return a checksum-pinned mock fixture when the chunk matches a known profile."""
    mapped = extract_fixture_for_manual_source(source)
    if mapped:
        return mapped
    if source is not None and manual_text_lacks_extract_fixture(source):
        return None
    chunk_text = str(chunk.get("chunk_text") or "")
    if source_text_has_prompt_injection_fixture(chunk_text):
        return "claim_extraction_prompt_injection.json"
    if _is_staged_fetch_spine_chunk(chunk_text):
        return "staged_fetch_extract_claims.json"
    if _is_staged_rank2_fetch_spine_chunk(chunk_text):
        return "staged_fetch_second_candidate_extract_claims.json"
    if _is_creativity_diversity_chunk(chunk_text):
        return "claim_extraction_creativity_scoped.json"
    return None


def _default_fixture_for_chunk(chunk: dict[str, Any]) -> str:
    return _mock_fixture_profile_for_chunk(None, chunk) or (
        "claim_extraction_valid_and_missing_quote.json"
    )


def source_has_staged_fetch_spine(chunks: list[Any]) -> bool:
    """Return True when any chunk matches the staged OpenAlex fetch spine marker."""
    return any(_is_staged_fetch_spine_chunk(c.chunk_text) for c in chunks)


def extract_and_validate_for_chunk(
    chunk: dict[str, Any],
    *,
    domain_pack: str,
    fixture_name: str | None = None,
    client=None,
    source: Any | None = None,
    live_manual_fallthrough: bool = False,
    live_staged_fallthrough: bool = False,
    live_staged_rank2_fallthrough: bool = False,
    live_staged_ingest_fallthrough: bool = False,
    skip_quoteability_gate: bool = False,
) -> dict[str, list[dict[str, Any]]]:
    """Extract candidates for one chunk and validate them deterministically."""
    chunk_text = str(chunk.get("chunk_text") or "")
    pinned_fixture = fixture_name or _mock_fixture_profile_for_chunk(source, chunk)
    using_live_fallthrough = (
        live_manual_fallthrough
        or live_staged_fallthrough
        or live_staged_rank2_fallthrough
        or live_staged_ingest_fallthrough
    )
    if (
        not skip_quoteability_gate
        and pinned_fixture is None
        and not using_live_fallthrough
    ):
        assessment = assess_chunk_extractability(chunk_text)
        if not assessment["extractable"]:
            return {
                "accepted": [],
                "rejected": [
                    {
                        "source_id": chunk.get("source_id"),
                        "chunk_id": chunk.get("id"),
                        "claim_text": "",
                        "quote_span": "",
                        "rejection_reason": REJECTION_ZERO_QUOTEABLE,
                        "quality_gate": assessment,
                    }
                ],
            }
        contract_quote_hints = assessment.get("quoteable_spans") or []
    else:
        contract_quote_hints = []

    contract: dict[str, Any] = {"domain_pack": domain_pack}
    if contract_quote_hints:
        contract["quoteable_span_hints"] = contract_quote_hints[:3]
    if live_manual_fallthrough:
        contract["manual_text_arbitrary_live"] = True
    if live_staged_ingest_fallthrough:
        contract["staged_ingest_arbitrary_live"] = True
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
    live_staged_fallthrough: bool = False,
    live_staged_rank2_fallthrough: bool = False,
    live_staged_ingest_fallthrough: bool = False,
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
    cfg = config if config is not None else load_config()
    using_mock_fixture = (
        fixture_name is not None
        or (
            not live_manual_fallthrough
            and not live_staged_fallthrough
            and not live_staged_rank2_fallthrough
            and not live_staged_ingest_fallthrough
            and effective_llm_mode(cfg) == "mock"
        )
    )
    using_live_fallthrough = (
        live_manual_fallthrough
        or live_staged_fallthrough
        or live_staged_rank2_fallthrough
        or live_staged_ingest_fallthrough
    )
    quality_gate = gate_source_for_extraction(source, chunks)
    if (
        not using_mock_fixture
        and not using_live_fallthrough
        and not quality_gate["allowed"]
    ):
        rejected = claim_repo.insert_rejected(
            {
                "source_id": source_id,
                "chunk_id": chunks[0].id,
                "claim_text": "",
                "quote_span": "",
                "subject": "",
                "predicate": "",
                "object": "",
                "scope": "",
                "evidence_type": "blocked",
                "confidence": 0.0,
                "limitations": [],
                "domain": source.domain,
            },
            rejection_reason=str(quality_gate["reason"]),
            extractor_provider="quality_gate",
            extractor_model="text_quality_gate",
            llm_schema_version=cfg.llm_schema_version,
        )
        return {
            "status": "blocked_by_quality_gate",
            "source_id": source_id,
            "quality_gate": quality_gate,
            "accepted_count": 0,
            "rejected_count": 1,
            "accepted_claim_ids": [],
            "rejected_claim_ids": [rejected.id],
        }

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

    if live_manual_fallthrough and (
        live_staged_fallthrough
        or live_staged_rank2_fallthrough
        or live_staged_ingest_fallthrough
    ):
        raise ValueError(
            "live_manual_fallthrough cannot be combined with staged live fallthrough."
        )
    if sum(
        (
            live_staged_fallthrough,
            live_staged_rank2_fallthrough,
            live_staged_ingest_fallthrough,
        )
    ) > 1:
        raise ValueError(
            "Only one staged live fallthrough flag may be set per extraction run."
        )

    if live_staged_rank2_fallthrough:
        from rge.modules.staged_spine_heuristics import source_has_staged_rank2_fetch_spine

        if fixture_name:
            raise ValueError(
                "live_staged_rank2_fallthrough cannot be combined with --fixture; "
                "live Ollama extraction uses the ingested chunk text."
            )
        if not source_has_staged_rank2_fetch_spine(chunks):
            raise ValueError(
                "live_staged_rank2_fallthrough requires staged OpenAlex rank-2 ingest "
                "chunk text (constraint management marker)."
            )
        model_client = client or get_model_client(cfg, mode="ollama")
    elif live_staged_ingest_fallthrough:
        from rge.modules.staged_spine_heuristics import (
            MIN_STAGED_INGEST_TEXT_CHARS,
            is_staged_ingest_source,
            staged_ingest_has_sufficient_text,
        )

        if fixture_name:
            raise ValueError(
                "live_staged_ingest_fallthrough cannot be combined with --fixture; "
                "live Ollama extraction uses the ingested chunk text."
            )
        if not is_staged_ingest_source(source, conn=conn):
            raise ValueError(
                "live_staged_ingest_fallthrough requires an ingest-staged OpenAlex source."
            )
        if not staged_ingest_has_sufficient_text(chunks):
            raise ValueError(
                "live_staged_ingest_fallthrough requires staged ingest chunk text "
                f"of at least {MIN_STAGED_INGEST_TEXT_CHARS} characters."
            )
        model_client = client or get_model_client(cfg, mode="ollama")
    elif live_staged_fallthrough:
        if fixture_name:
            raise ValueError(
                "live_staged_fallthrough cannot be combined with --fixture; "
                "live Ollama extraction uses the ingested chunk text."
            )
        if not source_has_staged_fetch_spine(chunks):
            raise ValueError(
                "live_staged_fallthrough requires staged OpenAlex ingest chunk text "
                "(human-ai co-creativity / songwriting marker)."
            )
        model_client = client or get_model_client(cfg, mode="ollama")
    elif live_manual_fallthrough:
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
            live_staged_fallthrough=live_staged_fallthrough,
            live_staged_rank2_fallthrough=live_staged_rank2_fallthrough,
            live_staged_ingest_fallthrough=live_staged_ingest_fallthrough,
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
