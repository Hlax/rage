"""Explicit live Ollama extraction with validated DB writes (operator opt-in).

Unlike report-only live probes, this module persists accepted/rejected claims
only after the existing Python validator gate. Requires live LLM opt-in and
refuses checksum-pinned manual fixture sources so mock fixture lookup cannot
masquerade as inference.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from rge.config import RgeConfig, load_config
from rge.db.connection import DEFAULT_DB_PATH
from rge.llm.registry import get_model_client
from rge.modules.claim_extractor import extract_claims_for_source
from rge.modules.live_probe import LiveProbeGateError, assert_live_probe_env, assert_ollama_health
from rge.modules.manual_source_fixtures import (
    manual_text_lacks_extract_fixture,
    resolve_manual_source_fixture,
)

DEFAULT_LIVE_EVIDENCE_DB = (
    Path(__file__).resolve().parents[2] / "data" / "db" / "live_research_evidence.sqlite"
)


class LiveExtractionWriteError(Exception):
    """Live extraction write failed (gate, fixture map, or persistence)."""


def assert_checksum_not_in_fixture_map(checksum: str) -> None:
    """Refuse sources whose bytes are pinned to mock manual fixtures."""
    if resolve_manual_source_fixture(checksum, "extract_claims"):
        raise LiveExtractionWriteError(
            f"Source checksum {checksum!r} is listed in "
            "fixtures/manual_source_fixture_map.json; use mock extract-claims "
            "for checksum-pinned manual sources."
        )


def _build_live_extraction_payload(
    *,
    conn: Any,
    source_id: str,
    result: dict[str, Any],
    command: str,
    model_client: Any,
    cfg: RgeConfig,
    health: dict[str, Any],
    live_manual_fallthrough: bool,
    live_staged_fallthrough: bool = False,
    live_staged_rank2_fallthrough: bool = False,
) -> dict[str, Any]:
    from rge.db.repositories import ChunkRepository, ClaimRepository, SourceRepository

    source = SourceRepository(conn).get_by_id(source_id)
    if source is None:
        raise LiveExtractionWriteError(f"Source not found: {source_id}")

    checksum = getattr(source, "raw_text_checksum", None)
    claim_repo = ClaimRepository(conn)
    chunk_repo = ChunkRepository(conn)
    chunks_by_id = {chunk.id: chunk for chunk in chunk_repo.list_for_source(source_id)}
    accepted = claim_repo.list_for_source(source_id, status="accepted")
    rejected = claim_repo.list_for_source(source_id, status="rejected")

    accepted_payload: list[dict[str, Any]] = []
    for claim in accepted:
        quotes = claim_repo.list_quotes_for_claim(claim.id)
        chunk = chunks_by_id.get(claim.chunk_id)
        accepted_payload.append(
            {
                "id": claim.id,
                "claim_text": claim.claim_text,
                "scope": claim.scope,
                "subject": claim.subject,
                "predicate": claim.predicate,
                "object": claim.object,
                "chunk_id": claim.chunk_id,
                "quote_spans": [row["quote_text"] for row in quotes],
                "quote_char_ranges": [
                    {"char_start": row.get("char_start"), "char_end": row.get("char_end")}
                    for row in quotes
                ],
                "chunk_text_preview": (
                    (chunk.chunk_text[:120] + "…")
                    if chunk and len(chunk.chunk_text) > 120
                    else (chunk.chunk_text if chunk else None)
                ),
            }
        )

    rejected_payload = [
        {
            "id": claim.id,
            "claim_text": claim.claim_text,
            "rejection_reason": claim.rejection_reason,
        }
        for claim in rejected
    ]

    return {
        "status": result["status"],
        "command": command,
        "live_manual_fallthrough": live_manual_fallthrough,
        "live_staged_fallthrough": live_staged_fallthrough,
        "live_staged_rank2_fallthrough": live_staged_rank2_fallthrough,
        "source_id": source_id,
        "source_title": source.title,
        "source_type": source.source_type,
        "raw_text_checksum": checksum,
        "fixture_map_match": not manual_text_lacks_extract_fixture(source),
        "db_writes": True,
        "provider": model_client.provider,
        "model": getattr(model_client, "model", "unknown"),
        "llm_schema_version": cfg.llm_schema_version,
        "effective_llm_mode": "ollama",
        "health": health,
        "accepted_count": result["accepted_count"],
        "rejected_count": result["rejected_count"],
        "accepted_claims": accepted_payload,
        "rejected_claims": rejected_payload,
    }


def assert_live_staged_extract_live_env(
    config: RgeConfig | None = None,
    *,
    command: str = "extract-claims",
) -> RgeConfig:
    """Require staged-family live LLM opt-in in addition to standard live probe gates."""
    allow = os.environ.get("RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM", "0").strip().casefold()
    if allow not in ("1", "true", "yes"):
        raise LiveExtractionWriteError(
            f"{command} live staged fallthrough requires "
            "RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM=1."
        )
    return assert_live_probe_env(config, command=command)


def extract_claims_manual_live_fallthrough(
    conn: Any,
    source_id: str,
    *,
    config: RgeConfig | None = None,
    skip_health_check: bool = False,
    client: Any | None = None,
) -> dict[str, Any]:
    """Live Ollama extraction for manual_text sources absent from the fixture map."""
    from rge.db.repositories import SourceRepository

    cfg = assert_live_probe_env(config, command="extract-claims")
    health = assert_ollama_health(cfg) if not skip_health_check else {}

    source = SourceRepository(conn).get_by_id(source_id)
    if source is None:
        raise LiveExtractionWriteError(f"Source not found: {source_id}")
    if getattr(source, "source_type", None) != "manual_text":
        raise LiveExtractionWriteError(
            "live_manual_fallthrough requires source_type manual_text."
        )

    checksum = getattr(source, "raw_text_checksum", None)
    if not checksum:
        raise LiveExtractionWriteError(f"Source {source_id} has no raw_text_checksum.")
    assert_checksum_not_in_fixture_map(str(checksum))

    model_client = client or get_model_client(cfg, mode="ollama")
    result = extract_claims_for_source(
        conn,
        source_id,
        live_manual_fallthrough=True,
        client=model_client,
        config=cfg,
    )
    return _build_live_extraction_payload(
        conn=conn,
        source_id=source_id,
        result=result,
        command="extract-claims",
        model_client=model_client,
        cfg=cfg,
        health=health,
        live_manual_fallthrough=True,
        live_staged_fallthrough=False,
    )


def assert_live_staged_rank2_extract_live_env(
    config: RgeConfig | None = None,
    *,
    command: str = "extract-claims",
) -> RgeConfig:
    """Require rank-2 staged-family live LLM opt-in in addition to live probe gates."""
    allow = os.environ.get(
        "RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM", "0"
    ).strip().casefold()
    if allow not in ("1", "true", "yes"):
        raise LiveExtractionWriteError(
            f"{command} live staged rank-2 fallthrough requires "
            "RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM=1."
        )
    return assert_live_probe_env(config, command=command)


def extract_claims_staged_rank2_live_fallthrough(
    conn: Any,
    source_id: str,
    *,
    config: RgeConfig | None = None,
    skip_health_check: bool = False,
    client: Any | None = None,
) -> dict[str, Any]:
    """Live Ollama extraction for rank-2 staged OpenAlex ingest sources."""
    from rge.db.repositories import ChunkRepository, SourceRepository
    from rge.modules.claim_extractor import extract_claims_for_source
    from rge.modules.staged_spine_heuristics import source_has_staged_rank2_fetch_spine

    cfg = assert_live_staged_rank2_extract_live_env(config, command="extract-claims")
    health = assert_ollama_health(cfg) if not skip_health_check else {}

    source = SourceRepository(conn).get_by_id(source_id)
    if source is None:
        raise LiveExtractionWriteError(f"Source not found: {source_id}")

    chunks = ChunkRepository(conn).list_for_source(source_id)
    if not source_has_staged_rank2_fetch_spine(chunks):
        raise LiveExtractionWriteError(
            "live_staged_rank2_fallthrough requires staged OpenAlex rank-2 ingest "
            "chunk text (constraint management marker)."
        )

    model_client = client or get_model_client(cfg, mode="ollama")
    result = extract_claims_for_source(
        conn,
        source_id,
        live_staged_rank2_fallthrough=True,
        client=model_client,
        config=cfg,
    )
    return _build_live_extraction_payload(
        conn=conn,
        source_id=source_id,
        result=result,
        command="extract-claims",
        model_client=model_client,
        cfg=cfg,
        health=health,
        live_manual_fallthrough=False,
        live_staged_fallthrough=False,
        live_staged_rank2_fallthrough=True,
    )


def extract_claims_staged_live_fallthrough(
    conn: Any,
    source_id: str,
    *,
    config: RgeConfig | None = None,
    skip_health_check: bool = False,
    client: Any | None = None,
) -> dict[str, Any]:
    """Live Ollama extraction for staged OpenAlex ingest sources (no auto-mock fixture)."""
    from rge.db.repositories import ChunkRepository, SourceRepository
    from rge.modules.claim_extractor import (
        extract_claims_for_source,
        source_has_staged_fetch_spine,
    )

    cfg = assert_live_staged_extract_live_env(config, command="extract-claims")
    health = assert_ollama_health(cfg) if not skip_health_check else {}

    source = SourceRepository(conn).get_by_id(source_id)
    if source is None:
        raise LiveExtractionWriteError(f"Source not found: {source_id}")

    chunks = ChunkRepository(conn).list_for_source(source_id)
    if not source_has_staged_fetch_spine(chunks):
        raise LiveExtractionWriteError(
            "live_staged_fallthrough requires staged OpenAlex ingest chunk text "
            "(human-ai co-creativity / songwriting marker)."
        )

    model_client = client or get_model_client(cfg, mode="ollama")
    result = extract_claims_for_source(
        conn,
        source_id,
        live_staged_fallthrough=True,
        client=model_client,
        config=cfg,
    )
    return _build_live_extraction_payload(
        conn=conn,
        source_id=source_id,
        result=result,
        command="extract-claims",
        model_client=model_client,
        cfg=cfg,
        health=health,
        live_manual_fallthrough=False,
        live_staged_fallthrough=True,
        live_staged_rank2_fallthrough=False,
    )


def extract_claims_live_for_source(
    conn: Any,
    source_id: str,
    *,
    config: RgeConfig | None = None,
    skip_health_check: bool = False,
) -> dict[str, Any]:
    """Run live Ollama extraction, validate, and persist claims for one source."""
    payload = extract_claims_manual_live_fallthrough(
        conn,
        source_id,
        config=config,
        skip_health_check=skip_health_check,
    )
    payload["command"] = "extract-claims-live"
    payload["live_manual_fallthrough"] = False
    return payload


def default_live_evidence_db() -> Path:
    return DEFAULT_LIVE_EVIDENCE_DB


def resolve_live_evidence_db(path: Path | str | None) -> Path:
    if path is None:
        return DEFAULT_LIVE_EVIDENCE_DB
    return Path(path)


def is_default_graph_db(db_path: Path) -> bool:
    return db_path.resolve() == DEFAULT_DB_PATH.resolve()
