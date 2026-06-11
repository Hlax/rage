"""Deterministic mock model client for golden tests and fixture mode.

Returns fixture-style outputs with no randomness, no time dependence, and no
network or model dependency. Same input -> same output, always. Golden tests
force this client with ``RGE_LLM_MODE=mock`` so the suite never requires
Ollama to be installed or running.

Like every model client, this returns typed candidate objects only and never
writes to the database or any other system surface.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rge.llm.base import ModelCallMetadata, ModelClient
from rge.llm.schemas import (
    CandidateClaimBatch_v0_1,
    CandidateConceptLinkBatch_v0_1,
    CandidateImprovementTicket_v0_1,
    CandidateRelationshipBatch_v0_1,
    CandidateRunSummary_v0_1,
    validate_schema_version,
)

PROMPT_TEMPLATE_VERSION = "0.1.0"

# Repo-root fixtures directory (editable install / source checkout layout).
DEFAULT_FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "llm_outputs"

DEFAULT_CLAIM_EXTRACTION_FIXTURE = "claim_extraction_valid_and_missing_quote.json"
DEFAULT_CONCEPT_LINKING_FIXTURE = "concept_linking_creativity_diversity.json"
DEFAULT_RELATIONSHIP_DRAFTING_FIXTURE = "relationship_drafting_creativity_diversity.json"


class MockModelClient(ModelClient):
    provider = "mock"
    model = "mock"

    def __init__(self, fixtures_dir: Path | None = None) -> None:
        self.fixtures_dir = (
            fixtures_dir if fixtures_dir is not None else DEFAULT_FIXTURES_DIR
        )

    def _metadata(self, task_name: str, schema_version: str) -> ModelCallMetadata:
        return ModelCallMetadata(
            provider=self.provider,
            model=self.model,
            task_name=task_name,
            schema_version=schema_version,
            prompt_template_version=PROMPT_TEMPLATE_VERSION,
        )

    def _load_fixture(self, filename: str) -> dict[str, Any]:
        path = self.fixtures_dir / filename
        return json.loads(path.read_text(encoding="utf-8"))

    def extract_claims(
        self,
        chunk: dict[str, Any],
        contract: dict[str, Any],
        domain_pack: str,
        schema_version: str,
        fixture_name: str = DEFAULT_CLAIM_EXTRACTION_FIXTURE,
    ) -> CandidateClaimBatch_v0_1:
        raw = self._load_fixture(fixture_name)
        validate_schema_version(raw.get("schema_version", ""), schema_version)
        return CandidateClaimBatch_v0_1.model_validate(raw)

    def link_concepts(
        self,
        claims: list[dict[str, Any]],
        domain_pack: str,
        schema_version: str,
        fixture_name: str = DEFAULT_CONCEPT_LINKING_FIXTURE,
    ) -> CandidateConceptLinkBatch_v0_1:
        raw = self._load_fixture(fixture_name)
        validate_schema_version(raw.get("schema_version", ""), schema_version)
        return CandidateConceptLinkBatch_v0_1.model_validate(raw)

    def draft_relationships(
        self,
        claims: list[dict[str, Any]],
        concepts: list[dict[str, Any]],
        domain_pack: str,
        schema_version: str,
        fixture_name: str = DEFAULT_RELATIONSHIP_DRAFTING_FIXTURE,
    ) -> CandidateRelationshipBatch_v0_1:
        raw = self._load_fixture(fixture_name)
        validate_schema_version(raw.get("schema_version", ""), schema_version)
        return CandidateRelationshipBatch_v0_1.model_validate(raw)

    def draft_run_summary(
        self,
        run_report_packet: dict[str, Any],
        schema_version: str,
    ) -> CandidateRunSummary_v0_1:
        summary = CandidateRunSummary_v0_1(
            summary_text="Deterministic mock run summary."
        )
        validate_schema_version(summary.schema_version, schema_version)
        return summary

    def draft_ticket(
        self,
        report_packet: dict[str, Any],
        schema_version: str,
    ) -> CandidateImprovementTicket_v0_1:
        ticket = CandidateImprovementTicket_v0_1(
            title="Deterministic mock ticket draft",
            problem="Placeholder ticket draft produced by the mock model client.",
        )
        validate_schema_version(ticket.schema_version, schema_version)
        return ticket
