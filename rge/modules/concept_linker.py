"""Link claims to concepts and domain metadata. Model-assisted, validated.

Uses domain pack ontology/aliases (e.g. ``domain_packs/creativity/``) to map
claims to canonical concepts without duplicates. Domain-specific values live
in ``domain_metadata``, validated by the domain pack, never hardcoded here.
"""

from __future__ import annotations

import os
from typing import Any

from rge.config import load_config
from rge.llm.mock_client import MockModelClient
from rge.llm.mode import effective_llm_mode
from rge.llm.registry import get_model_client
from rge.modules.domain_pack_loader import (
    DomainPack,
    DomainPackError,
    load_domain_pack,
    resolve_canonical_concept_label,
    validate_link_domain_metadata,
)
from rge.modules.manual_source_fixtures import (
    link_fixture_for_manual_source,
    manual_text_lacks_link_fixture,
    resolve_manual_source_fixture,
)

_GENERIC_ONLY_LABELS = frozenset({"ai", "creativity"})

REJECTION_WEAK_CONCEPT_MAPPING = "weak_concept_mapping"

_MANUAL_TEXT_NO_LINK_FIXTURE_ERROR = (
    "manual_text source has no checksum-pinned link_concepts fixture in "
    "fixtures/manual_source_fixture_map.json. Use mock link-concepts only for "
    "checksum-pinned synthnote sources, or pass --live-manual-link-fallthrough "
    "with RGE_LLM_MODE=ollama and RGE_ALLOW_LIVE_LLM=1 on a gitignored evidence DB."
)


def _normalize_label(label: str) -> str:
    return label.strip().casefold()


def _get_domain_pack(domain_pack: str) -> DomainPack:
    try:
        return load_domain_pack(domain_pack)
    except DomainPackError as exc:
        raise ValueError(str(exc)) from exc


def load_domain_pack_concepts(domain_pack: str) -> list[dict[str, Any]]:
    """Load ontology concepts for a domain pack."""
    from rge.modules.domain_pack_loader import concepts_as_dicts

    pack = _get_domain_pack(domain_pack)
    return concepts_as_dicts(pack)


def ontology_labels_for_pack(domain_pack: str) -> list[str]:
    """Sorted unique canonical concept labels from the domain pack ontology."""
    pack = _get_domain_pack(domain_pack)
    return sorted({concept.label for concept in pack.concepts if concept.label})


def allowed_concept_labels_for_pack(domain_pack: str) -> list[str]:
    """Canonical labels plus pack-defined alias phrases exposed for validation."""
    pack = _get_domain_pack(domain_pack)
    labels = {concept.label for concept in pack.concepts if concept.label}
    for canonical, alias_phrases in pack.aliases.items():
        labels.add(canonical)
        labels.update(alias_phrases)
    return sorted(labels)


def resolve_concept_label(domain_pack: str, concept_label: str) -> str:
    """Map alias phrases to canonical ontology labels using the domain pack."""
    pack = _get_domain_pack(domain_pack)
    return resolve_canonical_concept_label(pack, concept_label)


def normalize_proposed_concept_links(
    links: list[dict[str, Any]],
    domain_pack: str,
) -> list[dict[str, Any]]:
    """Resolve alias phrases to canonical labels before validation/persistence."""
    normalized: list[dict[str, Any]] = []
    for link in links:
        item = dict(link)
        label = item.get("concept_label")
        if label:
            item["concept_label"] = resolve_concept_label(domain_pack, str(label))
        normalized.append(item)
    return normalized


def link_rejection_diagnostic(
    link: dict[str, Any],
    *,
    rejection_reason: str | None = None,
    ontology_labels: list[str] | None = None,
    domain_pack: str | None = None,
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

    allowed: set[str] = set()
    if ontology_labels:
        allowed = {_normalize_label(item) for item in ontology_labels}
    elif domain_pack:
        allowed = {
            _normalize_label(item) for item in allowed_concept_labels_for_pack(domain_pack)
        }
    if allowed and label not in allowed:
        resolved = (
            resolve_concept_label(domain_pack, str(link.get("concept_label", "")))
            if domain_pack
            else str(link.get("concept_label", ""))
        )
        if _normalize_label(resolved) in allowed:
            return (
                f"concept_label {link.get('concept_label')!r} maps to "
                f"{resolved!r} but was not normalized before validation"
            )
        return (
            f"concept_label {link.get('concept_label')!r} is not in the domain "
            "ontology label list exposed to the probe"
        )

    metadata = link.get("domain_metadata") or {}
    if domain_pack and metadata:
        try:
            pack = load_domain_pack(domain_pack)
            ok, message = validate_link_domain_metadata(pack, metadata)
            if not ok and message:
                return message
        except DomainPackError:
            return f"domain pack {domain_pack!r} could not be loaded for metadata validation"

    return (
        "batch needs at least two distinct specific concept labels across all "
        "proposed links"
    )


def validate_concept_links(
    links: list[dict[str, Any]],
    *,
    domain_pack: str | None = None,
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

    pack: DomainPack | None = None
    if domain_pack:
        try:
            pack = load_domain_pack(domain_pack)
        except DomainPackError:
            pack = None

    for link in links:
        if not link.get("claim_id") or not link.get("concept_label"):
            rejected.append({**link, "rejection_reason": "weak_concept_mapping"})
            continue
        if link.get("confidence") is None:
            rejected.append({**link, "rejection_reason": "weak_concept_mapping"})
            continue
        metadata = link.get("domain_metadata") or {}
        if pack is not None and metadata:
            ok, _ = validate_link_domain_metadata(pack, metadata)
            if not ok:
                rejected.append({**link, "rejection_reason": "weak_concept_mapping"})
                continue
        if pack is None and domain_pack and metadata:
            rejected.append({**link, "rejection_reason": "weak_concept_mapping"})
            continue
        accepted.append(link)

    return {"accepted": accepted, "rejected": rejected}


def _pipeline_model_client(config=None):
    cfg = config if config is not None else load_config()
    return get_model_client(cfg, mode=effective_llm_mode(cfg))


def _is_staged_fetch_spine_source(source: Any | None) -> bool:
    if source is None:
        return False
    title = str(getattr(source, "title", "") or "").casefold()
    return "human-ai co-creativity" in title and "songwriting" in title


def is_staged_fetch_spine_source(source: Any | None) -> bool:
    """Return True when source title matches staged OpenAlex fetch spine markers."""
    return _is_staged_fetch_spine_source(source)


def _default_link_fixture_for_source(source: Any | None) -> str:
    mapped = link_fixture_for_manual_source(source)
    if mapped:
        return mapped
    if manual_text_lacks_link_fixture(source):
        raise ValueError(_MANUAL_TEXT_NO_LINK_FIXTURE_ERROR)
    if _is_staged_fetch_spine_source(source):
        return "staged_fetch_link_concepts.json"
    return "concept_linking_creativity_diversity.json"


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
            lowered = str(claim.get("claim_text") or "").casefold()
            if "reduced semantic diversity" in lowered:
                default_claim_id = claim["id"]
                break
            if "human-ai co-creativity" in lowered and "songwriting" in lowered:
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
    source: Any | None = None,
    live_manual_link_fallthrough: bool = False,
    live_staged_link_fallthrough: bool = False,
) -> list[dict[str, Any]]:
    """Propose concept links via the model client without persistence."""
    config = load_config()
    model_client = client if client is not None else _pipeline_model_client(config)
    link_kwargs: dict[str, Any] = {
        "claims": claims,
        "domain_pack": domain_pack,
        "schema_version": config.llm_schema_version,
    }
    if live_manual_link_fallthrough:
        link_kwargs["manual_text_arbitrary_live"] = True
    if isinstance(model_client, MockModelClient):
        link_kwargs["fixture_name"] = fixture_name or _default_link_fixture_for_source(
            source
        )
    batch = model_client.link_concepts(**link_kwargs)
    links = [item.model_dump() for item in batch.items]
    resolved = _resolve_link_claim_ids(
        links,
        claims,
        diversity_heuristic=diversity_heuristic,
    )
    return normalize_proposed_concept_links(resolved, domain_pack)


def link_claim_concepts(
    claims: list[dict[str, Any]],
    domain_pack: str,
    *,
    fixture_name: str | None = None,
    source: Any | None = None,
    client: Any | None = None,
    live_manual_link_fallthrough: bool = False,
    live_staged_link_fallthrough: bool = False,
) -> list[dict[str, Any]]:
    """Propose concept links for claims via the configured model client."""
    return propose_concept_links(
        claims,
        domain_pack,
        fixture_name=fixture_name,
        diversity_heuristic=True,
        source=source,
        client=client,
        live_manual_link_fallthrough=live_manual_link_fallthrough,
        live_staged_link_fallthrough=live_staged_link_fallthrough,
    )


def link_concepts_for_source(
    conn: Any,
    source_id: str,
    *,
    fixture_name: str | None = None,
    live_manual_link_fallthrough: bool = False,
    live_staged_link_fallthrough: bool = False,
    client: Any | None = None,
    config: Any | None = None,
) -> dict[str, Any]:
    """Link accepted claims for a source to domain concepts and persist links."""
    from rge.db.repositories import (
        ClaimConceptRepository,
        ClaimRepository,
        ConceptRepository,
        SourceRepository,
    )

    claim_repo = ClaimRepository(conn)
    source_claims = claim_repo.list_for_source(source_id, status="accepted")
    if not source_claims:
        raise ValueError(f"No accepted claims found for source: {source_id}")

    source_record = SourceRepository(conn).get_by_id(source_id)
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

    cfg = config if config is not None else load_config()
    if live_manual_link_fallthrough and live_staged_link_fallthrough:
        raise ValueError(
            "live_manual_link_fallthrough and live_staged_link_fallthrough are mutually exclusive."
        )
    if live_staged_link_fallthrough:
        if fixture_name:
            raise ValueError(
                "live_staged_link_fallthrough cannot be combined with --fixture; "
                "live Ollama linking uses accepted claims from the source."
            )
        if not is_staged_fetch_spine_source(source_record):
            raise ValueError(
                "live_staged_link_fallthrough requires staged OpenAlex ingest source title "
                "(human-ai co-creativity / songwriting marker)."
            )
        model_client = client or get_model_client(cfg, mode="ollama")
    elif live_manual_link_fallthrough:
        if not manual_text_lacks_link_fixture(source_record):
            raise ValueError(
                "live_manual_link_fallthrough requires a manual_text source absent from "
                "fixtures/manual_source_fixture_map.json link_concepts entries."
            )
        model_client = client or get_model_client(cfg, mode="ollama")
    else:
        model_client = client

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
    proposed = link_claim_concepts(
        claim_dicts,
        domain_pack,
        fixture_name=fixture_name,
        source=source_record,
        client=model_client,
        live_manual_link_fallthrough=live_manual_link_fallthrough,
        live_staged_link_fallthrough=live_staged_link_fallthrough,
    )
    validated = validate_concept_links(proposed, domain_pack=domain_pack)

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
        "rejected_links": validated["rejected"],
    }


def assert_link_checksum_not_in_fixture_map(checksum: str) -> None:
    """Refuse sources whose link_concepts task is pinned to mock manual fixtures."""
    from rge.modules.live_extraction_write import LiveExtractionWriteError

    if resolve_manual_source_fixture(checksum, "link_concepts"):
        raise LiveExtractionWriteError(
            f"Source checksum {checksum!r} is listed in "
            "fixtures/manual_source_fixture_map.json for link_concepts; use mock "
            "link-concepts for checksum-pinned manual sources."
        )


def link_concepts_manual_live_fallthrough(
    conn: Any,
    source_id: str,
    *,
    config: Any | None = None,
    skip_health_check: bool = False,
    client: Any | None = None,
) -> dict[str, Any]:
    """Live Ollama concept linking for manual_text sources absent from the fixture map."""
    from rge.db.repositories import ClaimConceptRepository, SourceRepository
    from rge.modules.live_extraction_write import LiveExtractionWriteError
    from rge.modules.live_probe import LiveProbeGateError, assert_live_probe_env, assert_ollama_health

    cfg = assert_live_probe_env(config, command="link-concepts")
    health = assert_ollama_health(cfg) if not skip_health_check else {}

    source = SourceRepository(conn).get_by_id(source_id)
    if source is None:
        raise LiveExtractionWriteError(f"Source not found: {source_id}")
    if getattr(source, "source_type", None) != "manual_text":
        raise LiveExtractionWriteError(
            "live_manual_link_fallthrough requires source_type manual_text."
        )

    checksum = getattr(source, "raw_text_checksum", None)
    if not checksum:
        raise LiveExtractionWriteError(f"Source {source_id} has no raw_text_checksum.")
    assert_link_checksum_not_in_fixture_map(str(checksum))

    model_client = client or get_model_client(cfg, mode="ollama")
    result = link_concepts_for_source(
        conn,
        source_id,
        live_manual_link_fallthrough=True,
        client=model_client,
        config=cfg,
    )
    links = ClaimConceptRepository(conn).list_for_source(source_id)
    return {
        "status": result["status"],
        "command": "link-concepts",
        "live_manual_link_fallthrough": True,
        "source_id": source_id,
        "source_title": source.title,
        "source_type": source.source_type,
        "raw_text_checksum": checksum,
        "fixture_map_match": not manual_text_lacks_link_fixture(source),
        "db_writes": True,
        "provider": model_client.provider,
        "model": getattr(model_client, "model", "unknown"),
        "llm_schema_version": cfg.llm_schema_version,
        "effective_llm_mode": "ollama",
        "health": health,
        "link_count": result["link_count"],
        "rejected_link_count": result.get("rejected_link_count", 0),
        "links": links,
        "rejected_links": result.get("rejected_links", []),
    }


def assert_live_staged_link_live_env(
    config: Any | None = None,
    *,
    command: str = "link-concepts",
) -> Any:
    """Require staged-family live LLM opt-in in addition to standard live probe gates."""
    from rge.modules.live_extraction_write import LiveExtractionWriteError
    from rge.modules.live_probe import assert_live_probe_env

    allow = os.environ.get("RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM", "0").strip().casefold()
    if allow not in ("1", "true", "yes"):
        raise LiveExtractionWriteError(
            f"{command} live staged link fallthrough requires "
            "RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM=1."
        )
    return assert_live_probe_env(config, command=command)


def link_concepts_staged_live_fallthrough(
    conn: Any,
    source_id: str,
    *,
    config: Any | None = None,
    skip_health_check: bool = False,
    client: Any | None = None,
) -> dict[str, Any]:
    """Live Ollama concept linking for staged OpenAlex ingest sources (no auto-mock fixture)."""
    from rge.db.repositories import ClaimConceptRepository, SourceRepository
    from rge.modules.live_extraction_write import LiveExtractionWriteError
    from rge.modules.live_probe import assert_ollama_health

    cfg = assert_live_staged_link_live_env(config, command="link-concepts")
    health = assert_ollama_health(cfg) if not skip_health_check else {}

    source = SourceRepository(conn).get_by_id(source_id)
    if source is None:
        raise LiveExtractionWriteError(f"Source not found: {source_id}")
    if not is_staged_fetch_spine_source(source):
        raise LiveExtractionWriteError(
            "live_staged_link_fallthrough requires staged OpenAlex ingest source title "
            "(human-ai co-creativity / songwriting marker)."
        )

    model_client = client or get_model_client(cfg, mode="ollama")
    result = link_concepts_for_source(
        conn,
        source_id,
        live_staged_link_fallthrough=True,
        client=model_client,
        config=cfg,
    )
    links = ClaimConceptRepository(conn).list_for_source(source_id)
    return {
        "status": result["status"],
        "command": "link-concepts",
        "live_manual_link_fallthrough": False,
        "live_staged_link_fallthrough": True,
        "source_id": source_id,
        "source_title": source.title,
        "source_type": source.source_type,
        "raw_text_checksum": getattr(source, "raw_text_checksum", None),
        "fixture_map_match": not manual_text_lacks_link_fixture(source),
        "db_writes": True,
        "provider": model_client.provider,
        "model": getattr(model_client, "model", "unknown"),
        "llm_schema_version": cfg.llm_schema_version,
        "effective_llm_mode": "ollama",
        "health": health,
        "link_count": result["link_count"],
        "rejected_link_count": result.get("rejected_link_count", 0),
        "links": links,
        "rejected_links": result.get("rejected_links", []),
    }
