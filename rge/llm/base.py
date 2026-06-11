"""Stable model-client interface for the Research Graph Engine.

All model clients (mock, Ollama, future providers) implement ``ModelClient``.
Clients return typed candidate objects only. They must not write to SQLite,
shell, Git, public exports, or accepted graph tables; Python validators and
repositories own all durable writes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from rge.llm.schemas import (
    CandidateClaimBatch_v0_1,
    CandidateConceptLinkBatch_v0_1,
    CandidateContradictionBatch_v0_1,
    CandidateImprovementTicket_v0_1,
    CandidateRelationshipBatch_v0_1,
    CandidateRunSummary_v0_1,
)


@dataclass(frozen=True)
class ModelCallMetadata:
    """Runtime metadata recorded for every structured model call.

    Surfaces in node reports / model_invocations so model, schema, and prompt
    changes stay auditable. Raw responses are never public-exported.
    """

    provider: str  # "mock" | "ollama"
    model: str
    task_name: str
    schema_version: str
    prompt_template_version: str
    base_url: str | None = None
    temperature: float = 0.0
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ModelClient(ABC):
    """Interface every model client must implement.

    Each method requests one structured candidate output. ``schema_version``
    is required so parsers can fail closed on mismatch.
    """

    provider: str = "abstract"

    @abstractmethod
    def extract_claims(
        self,
        chunk: dict[str, Any],
        contract: dict[str, Any],
        domain_pack: str,
        schema_version: str,
    ) -> CandidateClaimBatch_v0_1:
        """Propose candidate claims for one source chunk."""

    @abstractmethod
    def link_concepts(
        self,
        claims: list[dict[str, Any]],
        domain_pack: str,
        schema_version: str,
    ) -> CandidateConceptLinkBatch_v0_1:
        """Propose concept links for candidate/accepted claims."""

    @abstractmethod
    def draft_relationships(
        self,
        claims: list[dict[str, Any]],
        concepts: list[dict[str, Any]],
        domain_pack: str,
        schema_version: str,
    ) -> CandidateRelationshipBatch_v0_1:
        """Propose relationship drafts between concepts."""

    @abstractmethod
    def detect_contradictions(
        self,
        claims: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
        domain_pack: str,
        schema_version: str,
    ) -> CandidateContradictionBatch_v0_1:
        """Propose contradiction/qualification links between evidence edges."""

    @abstractmethod
    def draft_run_summary(
        self,
        run_report_packet: dict[str, Any],
        schema_version: str,
    ) -> CandidateRunSummary_v0_1:
        """Draft a small run summary from a run report packet."""

    @abstractmethod
    def draft_ticket(
        self,
        report_packet: dict[str, Any],
        schema_version: str,
    ) -> CandidateImprovementTicket_v0_1:
        """Draft first-pass improvement ticket wording from report evidence."""
