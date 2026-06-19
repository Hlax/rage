"""Live Ollama staged-ingest spine for orchestrator real-data path (ticket-368)."""

from __future__ import annotations

import os
from typing import Any

from rge.llm.mode import effective_llm_mode
from rge.llm.registry import get_model_client
from rge.modules.live_probe import LiveProbeGateError, assert_live_probe_env, assert_ollama_health
from rge.modules.staged_spine_heuristics import is_staged_ingest_source

ORCHESTRATOR_LIVE_LLM_ENV = "RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR_LIVE_LLM"


def _env_flag_enabled(name: str) -> bool:
    value = os.environ.get(name)
    if value is None:
        from rge.config import _merge_env_files

        value = _merge_env_files().get(name, "0")
    return str(value).strip().casefold() in ("1", "true", "yes")


def live_staged_orchestrator_live_llm_enabled() -> bool:
    """Return True when orchestrator may run live Ollama on arbitrary staged ingest."""
    return (
        _env_flag_enabled("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR")
        and _env_flag_enabled(ORCHESTRATOR_LIVE_LLM_ENV)
        and _env_flag_enabled("RGE_ALLOW_LIVE_LLM")
    )


def assert_live_staged_orchestrator_live_llm_env(
    config: Any | None = None,
    *,
    command: str = "run",
) -> Any:
    """Require orchestrator live LLM gates and Ollama mode."""
    if not _env_flag_enabled(ORCHESTRATOR_LIVE_LLM_ENV):
        raise LiveProbeGateError(
            f"{command} staged ingest live spine requires {ORCHESTRATOR_LIVE_LLM_ENV}=1."
        )
    if not _env_flag_enabled("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR"):
        raise LiveProbeGateError(
            f"{command} staged ingest live spine requires "
            "RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=1."
        )
    cfg = assert_live_probe_env(config, command=command)
    if effective_llm_mode(cfg) != "ollama":
        raise LiveProbeGateError(
            f"{command} staged ingest live spine requires RGE_LLM_MODE=ollama."
        )
    return cfg


def run_staged_ingest_live_spine_for_source(
    conn: Any,
    source_id: str,
    *,
    domain: str,
    skip_health_check: bool = True,
    client: Any | None = None,
) -> dict[str, Any]:
    """Run extract→link→build→detect on one ingest-staged source via live Ollama."""
    from rge.db.repositories import SourceRepository
    from rge.modules.claim_extractor import extract_claims_for_source
    from rge.modules.concept_linker import link_concepts_for_source
    from rge.modules.contradiction_detector import detect_contradictions_for_source
    from rge.modules.relationship_builder import build_relationships_for_source

    cfg = assert_live_staged_orchestrator_live_llm_env(command="run")
    health = assert_ollama_health(cfg) if not skip_health_check else {}
    model_client = client or get_model_client(cfg, mode="ollama")

    source = SourceRepository(conn).get_by_id(source_id)
    if source is None:
        raise ValueError(f"Source not found: {source_id}")
    if not is_staged_ingest_source(source, conn=conn):
        raise ValueError(
            f"staged ingest live spine requires ingest-staged source, got {source_id!r}."
        )

    extract_result = extract_claims_for_source(
        conn,
        source_id,
        live_staged_ingest_fallthrough=True,
        client=model_client,
        config=cfg,
    )
    link_result = link_concepts_for_source(
        conn,
        source_id,
        live_staged_ingest_link_fallthrough=True,
        client=model_client,
        config=cfg,
    )
    build_result = build_relationships_for_source(
        conn,
        source_id,
        live_staged_ingest_build_fallthrough=True,
        client=model_client,
        config=cfg,
    )
    detect_result = detect_contradictions_for_source(
        conn,
        source_id,
        live_staged_ingest_detect_fallthrough=True,
        client=model_client,
        config=cfg,
    )

    return {
        "status": "completed",
        "source_id": source_id,
        "domain": domain,
        "spine_mode": "live_staged_ingest",
        "extract": extract_result,
        "link": link_result,
        "build": build_result,
        "detect": detect_result,
        "health": health,
    }
