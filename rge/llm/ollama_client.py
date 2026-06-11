"""Local Ollama model client boundary.

Defines how the engine will call the local Ollama service (prompt + JSON
schema -> raw response -> JSON parse -> Pydantic validation -> typed candidate
objects). Configuration comes from ``OLLAMA_BASE_URL``, ``RGE_LOCAL_LLM``,
``RGE_LLM_TIMEOUT_SECONDS``, and ``RGE_LLM_TEMPERATURE``.

Phase 0 scope: this ticket establishes the adapter boundary only. Live
inference is intentionally NOT implemented or verified here; structured-task
methods raise ``OllamaNotAvailableInPhase0`` instead of pretending to work.
Nothing in this module performs network I/O at import time, and golden tests
never exercise live calls (they force mock mode).

Like every model client, this returns typed candidate objects only and never
writes to the database or any other system surface.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any

from rge.llm.base import ModelCallMetadata, ModelClient
from rge.llm.schemas import (
    CandidateClaimBatch_v0_1,
    CandidateConceptLinkBatch_v0_1,
    CandidateImprovementTicket_v0_1,
    CandidateRelationshipBatch_v0_1,
    CandidateRunSummary_v0_1,
)

PROMPT_TEMPLATE_VERSION = "0.1.0"


class OllamaNotAvailableInPhase0(NotImplementedError):
    """Raised when a live Ollama structured task is requested in Phase 0."""

    def __init__(self, task_name: str) -> None:
        super().__init__(
            f"Ollama task {task_name!r} is not implemented in Phase 0. "
            "This ticket establishes the adapter boundary only; live "
            "inference arrives with a later ticket. Use RGE_LLM_MODE=mock "
            "for deterministic outputs."
        )


class OllamaModelClient(ModelClient):
    provider = "ollama"

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: int = 60,
        temperature: float = 0.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature

    def _metadata(self, task_name: str, schema_version: str) -> ModelCallMetadata:
        return ModelCallMetadata(
            provider=self.provider,
            model=self.model,
            task_name=task_name,
            schema_version=schema_version,
            prompt_template_version=PROMPT_TEMPLATE_VERSION,
            base_url=self.base_url,
            temperature=self.temperature,
        )

    def health_check(self) -> dict[str, Any]:
        """Check whether local Ollama is reachable and the model is available.

        This is the only method permitted to touch the network, and only when
        explicitly invoked (e.g. by a future ``research model health``
        command). It never pulls models and never raises on an unreachable
        runtime; it reports status instead.
        """
        result: dict[str, Any] = {
            "mode": "ollama",
            "provider": self.provider,
            "base_url": self.base_url,
            "model": self.model,
            "reachable": False,
            "model_available": False,
        }
        try:
            with urllib.request.urlopen(
                f"{self.base_url}/api/tags", timeout=self.timeout_seconds
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
            result["reachable"] = True
            models = {entry.get("name") for entry in payload.get("models", [])}
            result["model_available"] = self.model in models
        except (OSError, ValueError):
            pass
        return result

    def extract_claims(
        self,
        chunk: dict[str, Any],
        contract: dict[str, Any],
        domain_pack: str,
        schema_version: str,
    ) -> CandidateClaimBatch_v0_1:
        raise OllamaNotAvailableInPhase0("claim_extraction")

    def link_concepts(
        self,
        claims: list[dict[str, Any]],
        domain_pack: str,
        schema_version: str,
    ) -> CandidateConceptLinkBatch_v0_1:
        raise OllamaNotAvailableInPhase0("concept_linking")

    def draft_relationships(
        self,
        claims: list[dict[str, Any]],
        concepts: list[dict[str, Any]],
        domain_pack: str,
        schema_version: str,
    ) -> CandidateRelationshipBatch_v0_1:
        raise OllamaNotAvailableInPhase0("relationship_drafting")

    def draft_run_summary(
        self,
        run_report_packet: dict[str, Any],
        schema_version: str,
    ) -> CandidateRunSummary_v0_1:
        raise OllamaNotAvailableInPhase0("run_summary")

    def draft_ticket(
        self,
        report_packet: dict[str, Any],
        schema_version: str,
    ) -> CandidateImprovementTicket_v0_1:
        raise OllamaNotAvailableInPhase0("ticket_drafting")
