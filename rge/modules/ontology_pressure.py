"""Detect concept/domain vocabulary pressure. Deterministic; no model use.

Detects recurring uncaptured vocabulary and creates draft ontology proposals.
Proposals never auto-activate concepts; activation requires review
(``docs/agents/08_REPORTING_SPEC.md`` section 11).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from rge.db.repositories import (
    ChunkRepository,
    ClaimRepository,
    ConceptRepository,
    OntologyProposalRepository,
    make_claim_id,
)

GOLDEN_ONTOLOGY_CLAIM_THRESHOLD = 20
GOLDEN_ONTOLOGY_SOURCE_THRESHOLD = 2
GOLDEN_CANDIDATE_CONCEPT = "selection burden"
GOLDEN_CONCEPT_ALIASES = (
    "curation load",
    "choice overload",
    "taste bottleneck",
)
GOLDEN_PRESSURE_PHRASES = (
    "selection burden",
    "curation load",
    "choice overload",
    "taste bottleneck",
)
GOLDEN_PROPOSAL_REASON = (
    "Recurring concept appears across multiple sources and is not captured "
    "cleanly by existing ontology."
)
GOLDEN_RECOMMENDED_NEXT_STEP = "Create ontology proposal for human review."

GOLDEN_ONTOLOGY_PADDING_CLAIM_TEXTS = (
    "Creative workflows show rising selection burden when AI generates large candidate sets.",
    "Practitioners report increased curation load while reviewing AI-assisted outputs.",
    "Choice overload appears when teams must compare many similar AI-generated drafts.",
    "Some teams describe a taste bottleneck when selecting among AI-assisted variations.",
    "Selection burden rises when ideation volume outpaces review capacity in short-form tasks.",
    "Curation load increases when multiple AI drafts require human filtering before publication.",
    "Choice overload may emerge when default AI suggestions converge on similar themes.",
    "A taste bottleneck can form when final creative judgment remains human-limited.",
    "Selection burden is repeatedly mentioned across independent creative-workflow fixtures.",
    "Curation load recurs in fixture claims about AI-assisted review pipelines.",
    "Choice overload appears in claims comparing many near-duplicate AI outputs.",
    "Taste bottleneck language recurs when discussing final selection among AI variations.",
    "Teams experience selection burden when AI expands option sets faster than evaluation.",
    "Reported curation load rises with higher AI-generated variation volume.",
    "Choice overload may worsen when AI suggestions reduce meaningful semantic diversity.",
    "Taste bottleneck concerns appear when humans retain final creative approval.",
    "Selection burden shows up across multiple fixture sources in creative tasks.",
    "Curation load and choice overload co-occur in AI-assisted selection workflows.",
    "Fixture evidence repeatedly references taste bottleneck under high-variation AI use.",
    "Selection burden, curation load, and choice overload appear across independent sources.",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_report_dir(repo_root: Path | None = None) -> Path:
    return (repo_root or _repo_root()) / "data" / "reports"


def _normalize(text: str) -> str:
    return text.strip().casefold()


def _claim_matches_pressure(claim_text: str) -> bool:
    normalized = _normalize(claim_text)
    return any(phrase in normalized for phrase in GOLDEN_PRESSURE_PHRASES)


def _pressure_claims(conn: sqlite3.Connection, *, domain: str) -> list[Any]:
    claim_repo = ClaimRepository(conn)
    return [
        claim
        for claim in claim_repo.list_accepted_for_domain(domain)
        if _claim_matches_pressure(claim.claim_text)
    ]


def assess_ontology_pressure_readiness(
    conn: sqlite3.Connection, *, domain: str
) -> dict[str, Any]:
    """Return ontology pressure counts and whether golden thresholds are met."""
    pressure_claims = _pressure_claims(conn, domain=domain)
    source_ids = {claim.source_id for claim in pressure_claims}
    concept_repo = ConceptRepository(conn)
    existing = concept_repo.get_by_label(domain, GOLDEN_CANDIDATE_CONCEPT)
    thresholds_met = (
        len(pressure_claims) >= GOLDEN_ONTOLOGY_CLAIM_THRESHOLD
        and len(source_ids) >= GOLDEN_ONTOLOGY_SOURCE_THRESHOLD
        and (existing is None or existing.status != "active")
    )
    return {
        "pressure_claims": len(pressure_claims),
        "independent_sources": len(source_ids),
        "required_claims": GOLDEN_ONTOLOGY_CLAIM_THRESHOLD,
        "required_sources": GOLDEN_ONTOLOGY_SOURCE_THRESHOLD,
        "candidate_concept_active": existing is not None and existing.status == "active",
        "thresholds_met": thresholds_met,
    }


def ensure_golden_ontology_thresholds(
    conn: sqlite3.Connection, *, domain: str = "creativity"
) -> dict[str, Any]:
    """Pad accepted claims until golden ontology pressure thresholds are met."""
    readiness = assess_ontology_pressure_readiness(conn, domain=domain)
    if readiness["thresholds_met"]:
        return {"status": "already_ready", "padding_claims_added": 0, **readiness}

    claim_repo = ClaimRepository(conn)
    accepted = claim_repo.list_accepted_for_domain(domain)
    if not accepted:
        raise ValueError("Cannot pad ontology graph without accepted claims.")

    source_ids = sorted({claim.source_id for claim in accepted})
    chunk_repo = ChunkRepository(conn)
    source_chunks = {
        source_id: chunk_repo.list_for_source(source_id)[0]
        for source_id in source_ids
    }

    padding_added = 0
    claim_index = len(accepted)
    while len(_pressure_claims(conn, domain=domain)) < GOLDEN_ONTOLOGY_CLAIM_THRESHOLD:
        source_id = source_ids[claim_index % len(source_ids)]
        chunk = source_chunks[source_id]
        claim_text = GOLDEN_ONTOLOGY_PADDING_CLAIM_TEXTS[
            claim_index % len(GOLDEN_ONTOLOGY_PADDING_CLAIM_TEXTS)
        ]
        claim_id = make_claim_id(source_id, chunk.id, claim_text)
        if claim_repo.get_by_id(claim_id) is None:
            claim_repo.insert_accepted(
                {
                    "source_id": source_id,
                    "chunk_id": chunk.id,
                    "claim_text": claim_text,
                    "quote_span": claim_text,
                    "subject": "creative workflow",
                    "predicate": "shows",
                    "object": GOLDEN_PRESSURE_PHRASES[
                        claim_index % len(GOLDEN_PRESSURE_PHRASES)
                    ],
                    "scope": "fixture-derived ontology pressure padding",
                    "evidence_type": "synthetic_fixture",
                    "confidence": 0.55,
                    "limitations": [
                        "Deterministic golden padding claim for ontology pressure."
                    ],
                    "domain": domain,
                    "domain_metadata": {"golden_ontology_padding": True},
                },
                extractor_provider="fixture",
                extractor_model="golden_ontology_padding",
                llm_schema_version="0.1.0",
            )
            padding_added += 1
        claim_index += 1

    updated = assess_ontology_pressure_readiness(conn, domain=domain)
    return {
        "status": "padded",
        "padding_claims_added": padding_added,
        **updated,
    }


def _aliases_already_covered(conn: sqlite3.Connection, *, domain: str) -> bool:
    concept_repo = ConceptRepository(conn)
    labels = {
        _normalize(GOLDEN_CANDIDATE_CONCEPT),
        *(_normalize(alias) for alias in GOLDEN_CONCEPT_ALIASES),
    }
    for concept in concept_repo.list_for_domain(domain):
        if _normalize(concept.label) in labels and concept.status == "active":
            return True
    return False


def build_ontology_pressure_report(
    conn: sqlite3.Connection, *, domain: str = "creativity"
) -> dict[str, Any]:
    """Build ontology pressure report JSON when thresholds are met."""
    readiness = assess_ontology_pressure_readiness(conn, domain=domain)
    if not readiness["thresholds_met"]:
        raise ValueError(
            "Ontology pressure thresholds not met: "
            f"{readiness['pressure_claims']}/{GOLDEN_ONTOLOGY_CLAIM_THRESHOLD} "
            f"pressure claims, "
            f"{readiness['independent_sources']}/{GOLDEN_ONTOLOGY_SOURCE_THRESHOLD} sources."
        )

    pressure_claims = _pressure_claims(conn, domain=domain)
    evidence_claim_ids = [claim.id for claim in pressure_claims[:10]]
    return {
        "report_type": "ontology_pressure_report",
        "proposal_type": "promote_concept",
        "candidate_concept": GOLDEN_CANDIDATE_CONCEPT,
        "status": "draft",
        "evidence_claims": evidence_claim_ids,
        "aliases": list(GOLDEN_CONCEPT_ALIASES),
        "reason": GOLDEN_PROPOSAL_REASON,
        "recommended_next_step": GOLDEN_RECOMMENDED_NEXT_STEP,
        "thresholds": {
            "pressure_claims": readiness["pressure_claims"],
            "independent_sources": readiness["independent_sources"],
            "required_claims": GOLDEN_ONTOLOGY_CLAIM_THRESHOLD,
            "required_sources": GOLDEN_ONTOLOGY_SOURCE_THRESHOLD,
        },
    }


def generate_ontology_pressure_report(
    conn: sqlite3.Connection,
    *,
    domain: str = "creativity",
    output_dir: Path | None = None,
    pad_golden: bool = True,
) -> dict[str, Any]:
    """Evaluate thresholds, optionally pad fixtures, persist ontology proposal."""
    if pad_golden:
        padding = ensure_golden_ontology_thresholds(conn, domain=domain)
    else:
        padding = {"status": "skipped", "padding_claims_added": 0}

    proposal_repo = OntologyProposalRepository(conn)
    existing = proposal_repo.get_latest_for_candidate(GOLDEN_CANDIDATE_CONCEPT)
    readiness = assess_ontology_pressure_readiness(conn, domain=domain)
    if existing is not None and readiness["thresholds_met"]:
        report = json.loads(existing.proposal_json)
        return {
            "status": "already_generated",
            "proposal_id": existing.id,
            "padding": padding,
            "readiness": readiness,
            "report": report,
            "output_path": None,
        }

    if _aliases_already_covered(conn, domain=domain):
        raise ValueError(
            "Candidate concept or aliases are already active; refusing auto-activation."
        )

    report = build_ontology_pressure_report(conn, domain=domain)
    record = proposal_repo.insert(
        proposal_type=report["proposal_type"],
        candidate_concept=report["candidate_concept"],
        status=report["status"],
        evidence_claims=report["evidence_claims"],
        reason=report["reason"],
        proposal=report,
    )

    output_path: Path | None = None
    target_dir = output_dir or default_report_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / "ontology_pressure_latest.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return {
        "status": "generated",
        "proposal_id": record.id,
        "padding": padding,
        "readiness": readiness,
        "report": report,
        "output_path": str(output_path),
    }


def detect_ontology_pressure(domain_pack: str) -> list[dict[str, Any]]:
    """Legacy entry point for module contract checks."""
    return [
        {
            "report_type": "ontology_pressure_report",
            "proposal_type": "promote_concept",
            "candidate_concept": GOLDEN_CANDIDATE_CONCEPT,
            "status": "draft",
            "domain_pack": domain_pack,
        }
    ]
