"""Detect and preserve contradictions between evidence edges.

Model-assisted, validated. Reads active relationships and accepted claims
across the domain so a contradiction source can qualify an earlier edge
without deleting or flattening opposing claims.
"""

from __future__ import annotations

import os
from typing import Any

from rge.config import load_config
from rge.llm.mock_client import MockModelClient
from rge.llm.mode import effective_llm_mode
from rge.llm.registry import get_model_client
from rge.modules.manual_source_fixtures import (
    contradiction_claim_hints_for_manual_source,
    contradiction_fixture_for_manual_source,
    manual_text_lacks_contradiction_fixture,
    resolve_manual_source_fixture,
)
from rge.modules.relationship_builder import VALID_STANCES

OPPOSING_CLAIM_FRAGMENT = "reduced semantic diversity"
QUALIFYING_CLAIM_FRAGMENT = "increased idea diversity"
VALID_CLASSIFICATIONS = frozenset(
    {"qualifies", "apparent_contradiction_metric_or_condition_difference"}
)

REJECTION_MISSING_BASE_RELATIONSHIP = "missing_base_relationship"
REJECTION_MISSING_NEW_RELATIONSHIP = "missing_new_relationship"
REJECTION_INVALID_STANCE = "invalid_stance"
REJECTION_INVALID_CLASSIFICATION = "invalid_classification"
REJECTION_MISSING_QUALIFYING_CLAIM = "missing_qualifying_claim"
REJECTION_MISSING_OPPOSING_CLAIM = "missing_opposing_claim"
REJECTION_SAME_CLAIM_PAIR = "same_claim_pair"

_MANUAL_TEXT_NO_CONTRADICTION_FIXTURE_ERROR = (
    "manual_text source has no checksum-pinned detect_contradictions fixture in "
    "fixtures/manual_source_fixture_map.json. Use mock detect-contradictions only for "
    "checksum-pinned synthnote sources, or pass --live-manual-contradiction-fallthrough "
    "with RGE_LLM_MODE=ollama and RGE_ALLOW_LIVE_LLM=1 on a gitignored evidence DB."
)


def _normalize(text: str) -> str:
    return text.strip().casefold()


def claim_dicts_as_objects(claim_dicts: list[dict[str, Any]]) -> list[Any]:
    """Wrap probe-local claim dicts for validators that read attribute fields."""
    return [type("Claim", (), claim)() for claim in claim_dicts]


def find_relationship_by_triple(
    relationships: list[dict[str, Any]],
    *,
    subject_concept: str,
    predicate: str,
    object_concept: str,
) -> dict[str, Any] | None:
    """Match a probe-local relationship dict by subject/predicate/object triple."""
    subject_key = _normalize(subject_concept)
    predicate_key = _normalize(predicate)
    object_key = _normalize(object_concept)
    for relationship in relationships:
        if (
            _normalize(str(relationship.get("subject_concept", ""))) == subject_key
            and _normalize(str(relationship.get("predicate", ""))) == predicate_key
            and _normalize(str(relationship.get("object_concept", ""))) == object_key
        ):
            return relationship
    return None


def contradiction_rejection_diagnostic(
    candidate: dict[str, Any],
    *,
    rejection_reason: str | None = None,
    source_claim_ids: set[str] | None = None,
    domain_claim_ids: set[str] | None = None,
    relationship_triples: set[tuple[str, str, str]] | None = None,
) -> str:
    """Human-readable note for a rejected contradiction candidate (probe reporting)."""
    reason = rejection_reason or REJECTION_INVALID_CLASSIFICATION
    source_ids = source_claim_ids or set()
    domain_ids = domain_claim_ids or set()
    triples = relationship_triples or set()

    if reason == REJECTION_MISSING_BASE_RELATIONSHIP:
        triple = (
            candidate.get("base_subject_concept"),
            candidate.get("base_predicate"),
            candidate.get("base_object_concept"),
        )
        return (
            "base relationship triple "
            f"{triple!r} does not match any probe-local relationship "
            f"(allowed triples: {sorted(triples)})"
        )
    if reason == REJECTION_MISSING_NEW_RELATIONSHIP:
        triple = (
            candidate.get("new_subject_concept"),
            candidate.get("new_predicate"),
            candidate.get("new_object_concept"),
        )
        return (
            "new relationship triple "
            f"{triple!r} does not match any probe-local relationship "
            f"(allowed triples: {sorted(triples)})"
        )
    if reason == REJECTION_INVALID_STANCE:
        return "qualification_stance must be one of supports, contradicts, or qualifies"
    if reason == REJECTION_INVALID_CLASSIFICATION:
        return (
            "contradiction_classification must be qualifies or "
            "apparent_contradiction_metric_or_condition_difference"
        )
    if reason == REJECTION_MISSING_QUALIFYING_CLAIM:
        return (
            "qualifying claim could not be resolved from source claims "
            f"(expected fragment {QUALIFYING_CLAIM_FRAGMENT!r} or id in {sorted(source_ids)})"
        )
    if reason == REJECTION_MISSING_OPPOSING_CLAIM:
        return (
            "opposing claim could not be resolved from domain claims "
            f"(expected fragment {OPPOSING_CLAIM_FRAGMENT!r} or id in {sorted(domain_ids)})"
        )
    if reason == REJECTION_SAME_CLAIM_PAIR:
        return "qualifying_claim_id and opposing_claim_id must differ"
    return f"rejected with reason {reason!r}"


def resolve_relationship_pair_for_probe(
    candidate: dict[str, Any],
    relationships: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Resolve base/new relationship dicts for one contradiction candidate."""
    base_relationship = find_relationship_by_triple(
        relationships,
        subject_concept=str(candidate.get("base_subject_concept", "")),
        predicate=str(candidate.get("base_predicate", "")),
        object_concept=str(candidate.get("base_object_concept", "")),
    )
    new_relationship = find_relationship_by_triple(
        relationships,
        subject_concept=str(candidate.get("new_subject_concept", "")),
        predicate=str(candidate.get("new_predicate", "")),
        object_concept=str(candidate.get("new_object_concept", "")),
    )
    return base_relationship, new_relationship


def validate_contradiction_probe_batch(
    candidates: list[dict[str, Any]],
    *,
    source_claims: list[Any],
    domain_claims: list[Any],
    relationships: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Validate contradiction candidates against probe-local relationship dicts."""
    if not candidates:
        return {"accepted": [], "rejected": []}
    first = candidates[0]
    base_relationship, new_relationship = resolve_relationship_pair_for_probe(
        first,
        relationships,
    )
    return validate_contradiction_candidates(
        candidates,
        source_claims=source_claims,
        domain_claims=domain_claims,
        base_relationship=base_relationship,
        new_relationship=new_relationship,
    )


def _resolve_qualifying_claim_id(
    source_claims: list[Any],
    candidate: dict[str, Any],
) -> str | None:
    proposed = candidate.get("qualifying_claim_id")
    claim_ids = {claim.id for claim in source_claims}
    if proposed and proposed in claim_ids:
        return proposed
    for claim in source_claims:
        if QUALIFYING_CLAIM_FRAGMENT in claim.claim_text.casefold():
            return claim.id
    for claim in source_claims:
        lowered = claim.claim_text.casefold()
        if "human-ai co-creativity" in lowered and "songwriting" in lowered:
            return claim.id
    return source_claims[0].id if source_claims else None


def _resolve_opposing_claim_id(
    domain_claims: list[Any],
    candidate: dict[str, Any],
) -> str | None:
    proposed = candidate.get("opposing_claim_id")
    claim_ids = {claim.id for claim in domain_claims}
    if proposed and proposed in claim_ids:
        return proposed
    for claim in domain_claims:
        if OPPOSING_CLAIM_FRAGMENT in claim.claim_text.casefold():
            return claim.id
    return None


def validate_contradiction_candidates(
    candidates: list[dict[str, Any]],
    *,
    source_claims: list[Any],
    domain_claims: list[Any],
    base_relationship: dict[str, Any] | None,
    new_relationship: dict[str, Any] | None,
) -> dict[str, list[dict[str, Any]]]:
    """Validate proposed contradiction links before persistence."""
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for candidate in candidates:
        stance = (candidate.get("qualification_stance") or "").strip().casefold()
        classification = (
            candidate.get("contradiction_classification") or ""
        ).strip()
        if base_relationship is None:
            rejected.append(
                {**candidate, "rejection_reason": "missing_base_relationship"}
            )
            continue
        if new_relationship is None:
            rejected.append(
                {**candidate, "rejection_reason": "missing_new_relationship"}
            )
            continue
        if stance not in VALID_STANCES:
            rejected.append({**candidate, "rejection_reason": "invalid_stance"})
            continue
        if classification not in VALID_CLASSIFICATIONS:
            rejected.append(
                {**candidate, "rejection_reason": "invalid_classification"}
            )
            continue

        qualifying_claim_id = _resolve_qualifying_claim_id(source_claims, candidate)
        opposing_claim_id = _resolve_opposing_claim_id(domain_claims, candidate)
        if qualifying_claim_id is None:
            rejected.append(
                {**candidate, "rejection_reason": "missing_qualifying_claim"}
            )
            continue
        if opposing_claim_id is None:
            rejected.append({**candidate, "rejection_reason": "missing_opposing_claim"})
            continue
        if qualifying_claim_id == opposing_claim_id:
            rejected.append({**candidate, "rejection_reason": "same_claim_pair"})
            continue

        accepted.append(
            {
                **candidate,
                "qualification_stance": stance,
                "qualifying_claim_id": qualifying_claim_id,
                "opposing_claim_id": opposing_claim_id,
                "base_relationship_id": base_relationship["id"],
                "new_relationship_id": new_relationship["id"],
            }
        )

    return {"accepted": accepted, "rejected": rejected}


def _pipeline_model_client(config=None):
    cfg = config if config is not None else load_config()
    return get_model_client(cfg, mode=effective_llm_mode(cfg))


def _apply_contradiction_claim_hints(
    candidates: list[dict[str, Any]],
    *,
    source_claims: list[Any],
    domain_claims: list[Any],
    hints: dict[str, str],
) -> list[dict[str, Any]]:
    """Resolve placeholder claim IDs using pack-defined text fragments."""
    qualifying_fragment = hints.get("qualifying", "").casefold()
    opposing_fragment = hints.get("opposing", "").casefold()
    resolved: list[dict[str, Any]] = []

    for candidate in candidates:
        item = dict(candidate)
        if item.get("qualifying_claim_id") == "placeholder" and qualifying_fragment:
            for claim in source_claims:
                if qualifying_fragment in claim.claim_text.casefold():
                    item["qualifying_claim_id"] = claim.id
                    break
        if item.get("opposing_claim_id") == "placeholder" and opposing_fragment:
            for claim in domain_claims:
                if opposing_fragment in claim.claim_text.casefold():
                    item["opposing_claim_id"] = claim.id
                    break
        resolved.append(item)
    return resolved


def _is_staged_fetch_spine_source(source: Any | None) -> bool:
    if source is None:
        return False
    title = str(getattr(source, "title", "") or "").casefold()
    return "human-ai co-creativity" in title and "songwriting" in title


def _default_contradiction_fixture_for_source(source: Any | None) -> str:
    mapped = contradiction_fixture_for_manual_source(source)
    if mapped:
        return mapped
    if manual_text_lacks_contradiction_fixture(source):
        raise ValueError(_MANUAL_TEXT_NO_CONTRADICTION_FIXTURE_ERROR)
    if _is_staged_fetch_spine_source(source):
        return "staged_fetch_detect_contradictions.json"
    return "contradiction_detection_creativity_diversity.json"


def propose_contradictions(
    claim_dicts: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    domain_pack: str,
    *,
    client: Any | None = None,
    fixture_name: str | None = None,
    source: Any | None = None,
    live_manual_contradiction_fallthrough: bool = False,
    live_staged_detect_fallthrough: bool = False,
    live_staged_rank2_detect_fallthrough: bool = False,
) -> list[dict[str, Any]]:
    """Propose contradiction/qualification links via the configured model client."""
    config = load_config()
    model_client = client if client is not None else _pipeline_model_client(config)
    detect_kwargs: dict[str, Any] = {
        "claims": claim_dicts,
        "relationships": relationships,
        "domain_pack": domain_pack,
        "schema_version": config.llm_schema_version,
    }
    if live_manual_contradiction_fallthrough:
        detect_kwargs["manual_text_arbitrary_live"] = True
    if isinstance(model_client, MockModelClient):
        detect_kwargs["fixture_name"] = fixture_name or _default_contradiction_fixture_for_source(
            source
        )
    batch = model_client.detect_contradictions(**detect_kwargs)

    return [item.model_dump() for item in batch.items]


def detect_contradictions_for_source(
    conn: Any,
    source_id: str,
    *,
    fixture_name: str | None = None,
    live_manual_contradiction_fallthrough: bool = False,
    live_staged_detect_fallthrough: bool = False,
    live_staged_rank2_detect_fallthrough: bool = False,
    client: Any | None = None,
    config: Any | None = None,
) -> dict[str, Any]:
    """Detect contradictions for a source against existing graph edges."""
    from rge.db.repositories import (
        ClaimRepository,
        RelationshipEvidenceRepository,
        RelationshipRepository,
        SourceRepository,
    )

    claim_repo = ClaimRepository(conn)
    source_claims = claim_repo.list_for_source(source_id, status="accepted")
    if not source_claims:
        raise ValueError(f"No accepted claims found for source: {source_id}")

    source_record = SourceRepository(conn).get_by_id(source_id)
    domain_pack = source_claims[0].domain
    relationship_repo = RelationshipRepository(conn)
    evidence_repo = RelationshipEvidenceRepository(conn)
    domain_claims = claim_repo.list_accepted_for_domain(domain_pack)
    active_relationships = relationship_repo.list_active()

    existing_qualifications = evidence_repo.list_for_source(source_id)
    if any(row["stance"] == "qualifies" for row in existing_qualifications):
        return {
            "status": "already_detected",
            "source_id": source_id,
            "qualification_count": len(existing_qualifications),
        }

    claim_dicts = [
        {
            "id": claim.id,
            "claim_text": claim.claim_text,
            "source_id": claim.source_id,
            "domain": claim.domain,
        }
        for claim in domain_claims
    ]
    cfg = config if config is not None else load_config()
    if live_manual_contradiction_fallthrough and (
        live_staged_detect_fallthrough or live_staged_rank2_detect_fallthrough
    ):
        raise ValueError(
            "live_manual_contradiction_fallthrough and staged detect fallthrough flags "
            "are mutually exclusive."
        )
    if live_staged_detect_fallthrough and live_staged_rank2_detect_fallthrough:
        raise ValueError(
            "live_staged_detect_fallthrough and live_staged_rank2_detect_fallthrough "
            "are mutually exclusive."
        )
    if live_staged_rank2_detect_fallthrough:
        from rge.modules.staged_spine_heuristics import is_staged_rank2_fetch_spine_source

        if fixture_name:
            raise ValueError(
                "live_staged_rank2_detect_fallthrough cannot be combined with --fixture; "
                "live Ollama contradiction detection uses domain graph context."
            )
        if not is_staged_rank2_fetch_spine_source(source_record):
            raise ValueError(
                "live_staged_rank2_detect_fallthrough requires staged OpenAlex rank-2 "
                "ingest source title (constraint management marker)."
            )
        model_client = client or get_model_client(cfg, mode="ollama")
    elif live_staged_detect_fallthrough:
        if fixture_name:
            raise ValueError(
                "live_staged_detect_fallthrough cannot be combined with --fixture; "
                "live Ollama contradiction detection uses domain graph context."
            )
        if not _is_staged_fetch_spine_source(source_record):
            raise ValueError(
                "live_staged_detect_fallthrough requires staged OpenAlex ingest source title "
                "(human-ai co-creativity / songwriting marker)."
            )
        model_client = client or get_model_client(cfg, mode="ollama")
    elif live_manual_contradiction_fallthrough:
        if not manual_text_lacks_contradiction_fixture(source_record):
            raise ValueError(
                "live_manual_contradiction_fallthrough requires a manual_text source "
                "absent from fixtures/manual_source_fixture_map.json "
                "detect_contradictions entries."
            )
        model_client = client or get_model_client(cfg, mode="ollama")
    else:
        model_client = client

    proposed = propose_contradictions(
        claim_dicts,
        active_relationships,
        domain_pack,
        fixture_name=fixture_name,
        source=source_record,
        client=model_client,
        live_manual_contradiction_fallthrough=live_manual_contradiction_fallthrough,
    )
    hints = contradiction_claim_hints_for_manual_source(source_record)
    if hints:
        proposed = _apply_contradiction_claim_hints(
            proposed,
            source_claims=source_claims,
            domain_claims=domain_claims,
            hints=hints,
        )

    base_relationship = None
    new_relationship = None
    if proposed:
        first = proposed[0]
        base_relationship = relationship_repo.find_active_by_triple(
            subject_concept=first["base_subject_concept"],
            predicate=first["base_predicate"],
            object_concept=first["base_object_concept"],
        )
        new_relationship = relationship_repo.find_active_by_triple(
            subject_concept=first["new_subject_concept"],
            predicate=first["new_predicate"],
            object_concept=first["new_object_concept"],
        )

    validated = validate_contradiction_candidates(
        proposed,
        source_claims=source_claims,
        domain_claims=domain_claims,
        base_relationship=base_relationship,
        new_relationship=new_relationship,
    )

    qualification_ids: list[str] = []
    for candidate in validated["accepted"]:
        classification = candidate["contradiction_classification"]
        metadata_patch = {
            "contradiction_classification": classification,
            "qualifies_relationship_id": candidate["new_relationship_id"],
        }
        relationship_repo.merge_domain_metadata(
            candidate["base_relationship_id"],
            metadata_patch,
        )
        relationship_repo.merge_domain_metadata(
            candidate["new_relationship_id"],
            {
                "contradiction_classification": classification,
                "qualifies_relationship_id": candidate["base_relationship_id"],
            },
        )
        evidence = evidence_repo.insert(
            relationship_id=candidate["base_relationship_id"],
            claim_id=candidate["qualifying_claim_id"],
            stance=candidate["qualification_stance"],
            relevance_score=0.75,
        )
        qualification_ids.append(evidence["id"])

    return {
        "status": "completed" if qualification_ids else "no_qualifications",
        "source_id": source_id,
        "qualification_count": len(qualification_ids),
        "qualification_ids": qualification_ids,
        "rejected_count": len(validated["rejected"]),
        "rejected": validated["rejected"],
    }


def assert_contradiction_checksum_not_in_fixture_map(checksum: str) -> None:
    """Refuse sources whose detect_contradictions task is pinned to mock manual fixtures."""
    from rge.modules.live_extraction_write import LiveExtractionWriteError

    if resolve_manual_source_fixture(checksum, "detect_contradictions"):
        raise LiveExtractionWriteError(
            f"Source checksum {checksum!r} is listed in "
            "fixtures/manual_source_fixture_map.json for detect_contradictions; use mock "
            "detect-contradictions for checksum-pinned manual sources."
        )


def detect_contradictions_manual_live_fallthrough(
    conn: Any,
    source_id: str,
    *,
    config: Any | None = None,
    skip_health_check: bool = False,
    client: Any | None = None,
) -> dict[str, Any]:
    """Live Ollama contradiction detection for manual_text sources absent from the fixture map."""
    from rge.db.repositories import RelationshipEvidenceRepository, RelationshipRepository, SourceRepository
    from rge.modules.live_extraction_write import LiveExtractionWriteError
    from rge.modules.live_probe import assert_live_probe_env, assert_ollama_health

    cfg = assert_live_probe_env(config, command="detect-contradictions")
    health = assert_ollama_health(cfg) if not skip_health_check else {}

    source = SourceRepository(conn).get_by_id(source_id)
    if source is None:
        raise LiveExtractionWriteError(f"Source not found: {source_id}")
    if getattr(source, "source_type", None) != "manual_text":
        raise LiveExtractionWriteError(
            "live_manual_contradiction_fallthrough requires source_type manual_text."
        )

    checksum = getattr(source, "raw_text_checksum", None)
    if not checksum:
        raise LiveExtractionWriteError(f"Source {source_id} has no raw_text_checksum.")
    assert_contradiction_checksum_not_in_fixture_map(str(checksum))

    model_client = client or get_model_client(cfg, mode="ollama")
    result = detect_contradictions_for_source(
        conn,
        source_id,
        live_manual_contradiction_fallthrough=True,
        client=model_client,
        config=cfg,
    )
    relationships = RelationshipRepository(conn).list_active()
    qualifications = [
        row
        for row in RelationshipEvidenceRepository(conn).list_for_source(source_id)
        if row["stance"] == "qualifies"
    ]
    return {
        "status": result["status"],
        "command": "detect-contradictions",
        "live_manual_contradiction_fallthrough": True,
        "source_id": source_id,
        "source_title": source.title,
        "source_type": source.source_type,
        "raw_text_checksum": checksum,
        "fixture_map_match": not manual_text_lacks_contradiction_fixture(source),
        "db_writes": result.get("qualification_count", 0) > 0,
        "provider": model_client.provider,
        "model": getattr(model_client, "model", "unknown"),
        "llm_schema_version": cfg.llm_schema_version,
        "effective_llm_mode": "ollama",
        "health": health,
        "qualification_count": result.get("qualification_count", 0),
        "qualification_ids": result.get("qualification_ids", []),
        "qualifications": qualifications,
        "active_relationships": relationships,
        "rejected_count": result.get("rejected_count", 0),
        "rejected": result.get("rejected", []),
    }


def assert_live_staged_detect_live_env(
    config: Any | None = None,
    *,
    command: str = "detect-contradictions",
) -> Any:
    """Require staged-family live LLM opt-in in addition to standard live probe gates."""
    from rge.modules.live_extraction_write import LiveExtractionWriteError
    from rge.modules.live_probe import assert_live_probe_env

    allow = os.environ.get("RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM", "0").strip().casefold()
    if allow not in ("1", "true", "yes"):
        raise LiveExtractionWriteError(
            f"{command} live staged detect fallthrough requires "
            "RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM=1."
        )
    return assert_live_probe_env(config, command=command)


def detect_contradictions_staged_live_fallthrough(
    conn: Any,
    source_id: str,
    *,
    config: Any | None = None,
    skip_health_check: bool = False,
    client: Any | None = None,
) -> dict[str, Any]:
    """Live Ollama contradiction detection for staged OpenAlex ingest sources (no auto-mock)."""
    from rge.db.repositories import (
        RelationshipEvidenceRepository,
        RelationshipRepository,
        SourceRepository,
    )
    from rge.modules.live_extraction_write import LiveExtractionWriteError
    from rge.modules.live_probe import assert_ollama_health
    from rge.modules.relationship_builder import is_staged_fetch_spine_source

    cfg = assert_live_staged_detect_live_env(config, command="detect-contradictions")
    health = assert_ollama_health(cfg) if not skip_health_check else {}

    source = SourceRepository(conn).get_by_id(source_id)
    if source is None:
        raise LiveExtractionWriteError(f"Source not found: {source_id}")
    if not is_staged_fetch_spine_source(source):
        raise LiveExtractionWriteError(
            "live_staged_detect_fallthrough requires staged OpenAlex ingest source title "
            "(human-ai co-creativity / songwriting marker)."
        )

    model_client = client or get_model_client(cfg, mode="ollama")
    result = detect_contradictions_for_source(
        conn,
        source_id,
        live_staged_detect_fallthrough=True,
        client=model_client,
        config=cfg,
    )
    relationships = RelationshipRepository(conn).list_active()
    qualifications = [
        row
        for row in RelationshipEvidenceRepository(conn).list_for_source(source_id)
        if row["stance"] == "qualifies"
    ]
    return {
        "status": result["status"],
        "command": "detect-contradictions",
        "live_manual_contradiction_fallthrough": False,
        "live_staged_detect_fallthrough": True,
        "source_id": source_id,
        "source_title": source.title,
        "source_type": source.source_type,
        "raw_text_checksum": getattr(source, "raw_text_checksum", None),
        "fixture_map_match": not manual_text_lacks_contradiction_fixture(source),
        "db_writes": result.get("qualification_count", 0) > 0,
        "provider": model_client.provider,
        "model": getattr(model_client, "model", "unknown"),
        "llm_schema_version": cfg.llm_schema_version,
        "effective_llm_mode": "ollama",
        "health": health,
        "qualification_count": result.get("qualification_count", 0),
        "qualification_ids": result.get("qualification_ids", []),
        "qualifications": qualifications,
        "active_relationships": relationships,
        "rejected_count": result.get("rejected_count", 0),
        "rejected": result.get("rejected", []),
    }


def assert_live_staged_rank2_detect_live_env(
    config: Any | None = None,
    *,
    command: str = "detect-contradictions",
) -> Any:
    """Require rank-2 staged-family live LLM opt-in in addition to live probe gates."""
    from rge.modules.live_extraction_write import LiveExtractionWriteError
    from rge.modules.live_probe import assert_live_probe_env

    allow = os.environ.get(
        "RGE_ALLOW_LIVE_STAGED_RANK2_DETECT_LIVE_LLM", "0"
    ).strip().casefold()
    if allow not in ("1", "true", "yes"):
        raise LiveExtractionWriteError(
            f"{command} live staged rank-2 detect fallthrough requires "
            "RGE_ALLOW_LIVE_STAGED_RANK2_DETECT_LIVE_LLM=1."
        )
    return assert_live_probe_env(config, command=command)


def detect_contradictions_staged_rank2_live_fallthrough(
    conn: Any,
    source_id: str,
    *,
    config: Any | None = None,
    skip_health_check: bool = False,
    client: Any | None = None,
) -> dict[str, Any]:
    """Live Ollama contradiction detection for rank-2 staged OpenAlex ingest sources."""
    from rge.db.repositories import (
        RelationshipEvidenceRepository,
        RelationshipRepository,
        SourceRepository,
    )
    from rge.modules.live_extraction_write import LiveExtractionWriteError
    from rge.modules.live_probe import assert_ollama_health
    from rge.modules.staged_spine_heuristics import is_staged_rank2_fetch_spine_source

    cfg = assert_live_staged_rank2_detect_live_env(config, command="detect-contradictions")
    health = assert_ollama_health(cfg) if not skip_health_check else {}

    source = SourceRepository(conn).get_by_id(source_id)
    if source is None:
        raise LiveExtractionWriteError(f"Source not found: {source_id}")
    if not is_staged_rank2_fetch_spine_source(source):
        raise LiveExtractionWriteError(
            "live_staged_rank2_detect_fallthrough requires staged OpenAlex rank-2 "
            "ingest source title (constraint management marker)."
        )

    model_client = client or get_model_client(cfg, mode="ollama")
    result = detect_contradictions_for_source(
        conn,
        source_id,
        live_staged_rank2_detect_fallthrough=True,
        client=model_client,
        config=cfg,
    )
    relationships = RelationshipRepository(conn).list_active()
    qualifications = [
        row
        for row in RelationshipEvidenceRepository(conn).list_for_source(source_id)
        if row["stance"] == "qualifies"
    ]
    return {
        "status": result["status"],
        "command": "detect-contradictions",
        "live_manual_contradiction_fallthrough": False,
        "live_staged_detect_fallthrough": False,
        "live_staged_rank2_detect_fallthrough": True,
        "source_id": source_id,
        "source_title": source.title,
        "source_type": source.source_type,
        "raw_text_checksum": getattr(source, "raw_text_checksum", None),
        "fixture_map_match": not manual_text_lacks_contradiction_fixture(source),
        "db_writes": result.get("qualification_count", 0) > 0,
        "provider": model_client.provider,
        "model": getattr(model_client, "model", "unknown"),
        "llm_schema_version": cfg.llm_schema_version,
        "effective_llm_mode": "ollama",
        "health": health,
        "qualification_count": result.get("qualification_count", 0),
        "qualification_ids": result.get("qualification_ids", []),
        "qualifications": qualifications,
        "active_relationships": relationships,
        "rejected_count": result.get("rejected_count", 0),
        "rejected": result.get("rejected", []),
    }


def detect_contradictions(
    claims: list[dict[str, Any]], relationships: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Legacy entry point for module contract checks."""
    proposed = propose_contradictions(claims, relationships, "creativity")
    base = next(
        (
            rel
            for rel in relationships
            if _normalize(rel.get("predicate", "")) == "may_reduce"
        ),
        None,
    )
    new = next(
        (
            rel
            for rel in relationships
            if _normalize(rel.get("predicate", "")) == "may_increase"
        ),
        None,
    )
    source_claims = [type("Claim", (), claim)() for claim in claims]
    domain_claims = source_claims
    validated = validate_contradiction_candidates(
        proposed,
        source_claims=source_claims,
        domain_claims=domain_claims,
        base_relationship=base,
        new_relationship=new,
    )
    return validated["accepted"]
