"""Explicit live Ollama extraction with validated DB writes (operator opt-in).

Unlike report-only live probes, this module persists accepted/rejected claims
only after the existing Python validator gate. Requires live LLM opt-in and
refuses checksum-pinned manual fixture sources so mock fixture lookup cannot
masquerade as inference.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rge.config import RgeConfig, load_config
from rge.db.connection import DEFAULT_DB_PATH
from rge.llm.registry import get_model_client
from rge.modules.claim_extractor import extract_claims_for_source
from rge.modules.live_probe import LiveProbeGateError, assert_live_probe_env, assert_ollama_health
from rge.modules.manual_source_fixtures import resolve_manual_source_fixture

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
            "for checksum-pinned manual sources. NM-1 requires a non-fixture source."
        )


def extract_claims_live_for_source(
    conn: Any,
    source_id: str,
    *,
    config: RgeConfig | None = None,
    skip_health_check: bool = False,
) -> dict[str, Any]:
    """Run live Ollama extraction, validate, and persist claims for one source."""
    from rge.db.repositories import ChunkRepository, ClaimRepository, SourceRepository

    cfg = assert_live_probe_env(config, command="extract-claims-live")
    health = assert_ollama_health(cfg) if not skip_health_check else {}

    source = SourceRepository(conn).get_by_id(source_id)
    if source is None:
        raise LiveExtractionWriteError(f"Source not found: {source_id}")

    checksum = getattr(source, "raw_text_checksum", None)
    if not checksum:
        raise LiveExtractionWriteError(f"Source {source_id} has no raw_text_checksum.")
    assert_checksum_not_in_fixture_map(str(checksum))

    model_client = get_model_client(cfg, mode="ollama")
    result = extract_claims_for_source(
        conn,
        source_id,
        fixture_name=None,
    )

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
        "command": "extract-claims-live",
        "source_id": source_id,
        "source_title": source.title,
        "source_type": source.source_type,
        "raw_text_checksum": checksum,
        "fixture_map_match": False,
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


def default_live_evidence_db() -> Path:
    return DEFAULT_LIVE_EVIDENCE_DB


def resolve_live_evidence_db(path: Path | str | None) -> Path:
    if path is None:
        return DEFAULT_LIVE_EVIDENCE_DB
    return Path(path)


def is_default_graph_db(db_path: Path) -> bool:
    return db_path.resolve() == DEFAULT_DB_PATH.resolve()
