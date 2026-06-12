"""Link claims to concepts and domain metadata. Model-assisted, validated.

Uses domain pack ontology/aliases (e.g. ``domain_packs/creativity/``) to map
claims to canonical concepts without duplicates. Domain-specific values live
in ``domain_metadata``, validated by the domain pack, never hardcoded here.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from rge.config import load_config
from rge.llm.mock_client import MockModelClient
from rge.llm.mode import effective_llm_mode
from rge.llm.registry import get_model_client

REPO_ROOT = Path(__file__).resolve().parents[2]

_GENERIC_ONLY_LABELS = frozenset({"ai", "creativity"})

REJECTION_WEAK_CONCEPT_MAPPING = "weak_concept_mapping"

SUPPLEMENTAL_CREATIVITY_CONCEPTS = (
    {
        "ontology_id": "concept_brainstorming",
        "label": "brainstorming",
        "definition": "Generating multiple candidate ideas before selection or refinement.",
        "status": "candidate",
    },
    {
        "ontology_id": "concept_ideation",
        "label": "ideation",
        "definition": "The creative phase of generating ideas and possibilities.",
        "status": "candidate",
    },
    {
        "ontology_id": "concept_creativity_domain",
        "label": "creativity",
        "definition": "The domain of human and AI-assisted creative work.",
        "status": "candidate",
    },
)


def _parse_ontology_concepts(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    concepts: list[dict[str, Any]] = []
    for block in re.split(r"\n  - id:", text)[1:]:
        concept: dict[str, Any] = {}
        block = f"id:{block}"
        for key in ("id", "label", "status", "definition"):
            match = re.search(rf"^\s*{key}: (.+)$", block, re.MULTILINE)
            if match:
                concept[key] = match.group(1).strip()
        if concept.get("id") and concept.get("label"):
            concepts.append(concept)
    return concepts


def load_domain_pack_concepts(domain_pack: str) -> list[dict[str, Any]]:
    """Load ontology concepts for a domain pack from YAML stubs."""
    if domain_pack != "creativity":
        raise ValueError(f"Unsupported domain pack for concept linking: {domain_pack}")
    ontology_path = REPO_ROOT / "domain_packs" / domain_pack / "ontology.yaml"
    concepts = _parse_ontology_concepts(ontology_path)
    existing_labels = {concept["label"].casefold() for concept in concepts}
    for supplemental in SUPPLEMENTAL_CREATIVITY_CONCEPTS:
        if supplemental["label"].casefold() not in existing_labels:
            concepts.append(
                {
                    "id": supplemental["ontology_id"],
                    "label": supplemental["label"],
                    "definition": supplemental["definition"],
                    "status": supplemental["status"],
                }
            )
    return concepts


def _normalize_label(label: str) -> str:
    return label.strip().casefold()


def ontology_labels_for_pack(domain_pack: str) -> list[str]:
    """Sorted unique concept labels from the domain pack ontology."""
    concepts = load_domain_pack_concepts(domain_pack)
    return sorted({str(concept["label"]) for concept in concepts if concept.get("label")})


def link_rejection_diagnostic(
    link: dict[str, Any],
    *,
    rejection_reason: str | None = None,
    ontology_labels: list[str] | None = None,
) -> str:
    """Human-readable note for a rejected concept link (probe reporting only)."""
    reason = rejection_reason or REJECTION_WEAK_CONCEPT_MAPPING
    if reason != REJECTION_WEAK_CONCEPT_MAPPING:
        return f"rejected with reason {reason!r}"

    if not link.get("claim_id"):
        return "claim_id is missing or empty"
    if not link.get("concept_label"):
        return "concept_label is missing or empty"
    if link.get("confidence") is None:
        return "confidence is required"

    label = _normalize_label(str(link.get("concept_label", "")))
    if label in _GENERIC_ONLY_LABELS:
        return (
            "batch needs at least two specific concept labels "
            "(not only generic 'ai' or 'creativity')"
        )

    allowed = (
        {_normalize_label(item) for item in ontology_labels}
        if ontology_labels
        else set()
    )
    if allowed and label not in allowed:
        return (
            f"concept_label {link.get('concept_label')!r} is not in the domain "
            "ontology label list exposed to the probe"
        )

    return (
        "batch needs at least two distinct specific concept labels across all "
        "proposed links"
    )


def validate_concept_links(
    links: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Validate proposed concept links before persistence."""
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    labels = {_normalize_label(link.get("concept_label", "")) for link in links}
    labels.discard("")
    specific_labels = labels - _GENERIC_ONLY_LABELS
    if len(specific_labels) < 2:
        for link in links:
            rejected.append(
                {
                    **link,
                    "rejection_reason": "weak_concept_mapping",
                }
            )
        return {"accepted": accepted, "rejected": rejected}

    for link in links:
        if not link.get("claim_id") or not link.get("concept_label"):
            rejected.append({**link, "rejection_reason": "weak_concept_mapping"})
            continue
        if link.get("confidence") is None:
            rejected.append({**link, "rejection_reason": "weak_concept_mapping"})
            continue
        accepted.append(link)

    return {"accepted": accepted, "rejected": rejected}


def _pipeline_model_client(config=None):
    cfg = config if config is not None else load_config()
    return get_model_client(cfg, mode=effective_llm_mode(cfg))


def _resolve_link_claim_ids(
    links: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    *,
    diversity_heuristic: bool,
) -> list[dict[str, Any]]:
    """Attach claim_id to model links; preserve model ids when present."""
    if not claims:
        return links

    default_claim_id = claims[0].get("id")
    if diversity_heuristic:
        for claim in claims:
            if "reduced semantic diversity" in claim.get("claim_text", ""):
                default_claim_id = claim["id"]
                break

    resolved: list[dict[str, Any]] = []
    for item in links:
        link = dict(item)
        claim_id = link.get("claim_id")
        if not claim_id or claim_id == "placeholder":
            link["claim_id"] = default_claim_id
        resolved.append(link)
    return resolved


def propose_concept_links(
    claims: list[dict[str, Any]],
    domain_pack: str,
    *,
    client: Any | None = None,
    fixture_name: str | None = None,
    diversity_heuristic: bool = False,
) -> list[dict[str, Any]]:
    """Propose concept links via the model client without persistence."""
    config = load_config()
    model_client = client if client is not None else _pipeline_model_client(config)
    link_kwargs: dict[str, Any] = {
        "claims": claims,
        "domain_pack": domain_pack,
        "schema_version": config.llm_schema_version,
    }
    if isinstance(model_client, MockModelClient):
        link_kwargs["fixture_name"] = (
            fixture_name or "concept_linking_creativity_diversity.json"
        )
    batch = model_client.link_concepts(**link_kwargs)
    links = [item.model_dump() for item in batch.items]
    return _resolve_link_claim_ids(
        links,
        claims,
        diversity_heuristic=diversity_heuristic,
    )


def link_claim_concepts(
    claims: list[dict[str, Any]],
    domain_pack: str,
    *,
    fixture_name: str | None = None,
) -> list[dict[str, Any]]:
    """Propose concept links for claims via the configured model client."""
    return propose_concept_links(
        claims,
        domain_pack,
        fixture_name=fixture_name,
        diversity_heuristic=True,
    )


def link_concepts_for_source(
    conn: Any,
    source_id: str,
    *,
    fixture_name: str | None = None,
) -> dict[str, Any]:
    """Link accepted claims for a source to domain concepts and persist links."""
    from rge.db.repositories import ClaimConceptRepository, ClaimRepository, ConceptRepository

    claim_repo = ClaimRepository(conn)
    source_claims = claim_repo.list_for_source(source_id, status="accepted")
    if not source_claims:
        raise ValueError(f"No accepted claims found for source: {source_id}")

    domain_pack = source_claims[0].domain
    concept_repo = ConceptRepository(conn)
    concept_repo.ensure_domain_concepts(domain_pack)

    link_repo = ClaimConceptRepository(conn)
    if link_repo.count_for_source(source_id) > 0:
        existing = link_repo.list_for_source(source_id)
        return {
            "status": "already_linked",
            "source_id": source_id,
            "link_count": len(existing),
            "link_ids": [link["id"] for link in existing],
        }

    claim_dicts = [
        {
            "id": claim.id,
            "claim_text": claim.claim_text,
            "subject": claim.subject,
            "object": claim.object,
            "domain": claim.domain,
        }
        for claim in source_claims
    ]
    proposed = link_claim_concepts(claim_dicts, domain_pack, fixture_name=fixture_name)
    validated = validate_concept_links(proposed)

    link_ids: list[str] = []
    for link in validated["accepted"]:
        concept = concept_repo.get_by_label(domain_pack, link["concept_label"])
        if concept is None:
            continue
        record = link_repo.insert(
            claim_id=link["claim_id"],
            concept_id=concept.id,
            role=link.get("role") or "context",
            confidence=float(link["confidence"]),
            domain_metadata=link.get("domain_metadata") or {},
        )
        link_ids.append(record["id"])

    return {
        "status": "completed",
        "source_id": source_id,
        "link_count": len(link_ids),
        "link_ids": link_ids,
        "rejected_link_count": len(validated["rejected"]),
    }
