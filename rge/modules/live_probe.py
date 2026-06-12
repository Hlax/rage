"""Safe local live structured-task probes (report-only, no default DB writes).

Operators use these helpers to prove Ollama/Qwen structured tasks outside CI
without persisting to the default SQLite database or public exports.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rge.config import RgeConfig, load_config
from rge.db.connection import DEFAULT_DB_PATH
from rge.llm.mode import effective_llm_mode, live_llm_enabled
from rge.llm.ollama_client import OllamaStructuredCallError
from rge.llm.registry import get_model_client
from rge.modules.claim_extractor import extract_and_validate_for_chunk
from rge.modules.claim_validator import rejection_diagnostic
from rge.modules.concept_linker import (
    link_rejection_diagnostic,
    ontology_labels_for_pack,
    propose_concept_links,
    validate_concept_links,
)
from rge.modules.contradiction_detector import (
    claim_dicts_as_objects,
    contradiction_rejection_diagnostic,
    propose_contradictions,
    validate_contradiction_probe_batch,
)
from rge.modules.relationship_builder import (
    propose_relationship_drafts,
    relationship_rejection_diagnostic,
    validate_relationship_candidates,
)

DEFAULT_PROBE_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "sources"
    / "live_probe_claim_calibration_short.txt"
)
LEGACY_PROBE_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "sources"
    / "creativity_ai_diversity_short.txt"
)
DEFAULT_PROBE_DOMAIN = "creativity"
DEFAULT_PROBE_CLAIM_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "claims"
    / "live_probe_concept_link_quality_claim.json"
)
DEFAULT_PROBE_RELATIONSHIP_BUNDLE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "probes"
    / "live_probe_relationship_quality_bundle.json"
)
DEFAULT_PROBE_CONTRADICTION_BUNDLE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "probes"
    / "live_probe_contradiction_quality_bundle.json"
)
PROBE_CHUNK_ID = "chunk_live_probe_001"
PROBE_SOURCE_ID = "src_live_probe_001"
PROBE_CLAIM_ID = "claim_live_probe_link_001"


class LiveProbeError(Exception):
    """Probe execution failed (structured call, validation, I/O)."""


class LiveProbeGateError(LiveProbeError):
    """Live opt-in or Ollama health gate failed."""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def live_probes_dir(root: Path | None = None) -> Path:
    base = root if root is not None else repo_root()
    return base / "data" / "reports" / "live_probes"


def resolve_fixture_source(path: Path | None, root: Path | None = None) -> Path:
    base = root if root is not None else repo_root()
    fixture = path if path is not None else DEFAULT_PROBE_FIXTURE
    if not fixture.is_absolute():
        fixture = base / fixture
    return fixture.resolve()


def assert_live_probe_env(
    config: RgeConfig | None = None,
    *,
    command: str = "probe-extract-claims",
) -> RgeConfig:
    cfg = config if config is not None else load_config()
    if cfg.llm_mode != "ollama":
        raise LiveProbeGateError(
            f"{command} requires RGE_LLM_MODE=ollama (got {cfg.llm_mode!r})."
        )
    if not live_llm_enabled(cfg):
        raise LiveProbeGateError(
            f"{command} requires RGE_ALLOW_LIVE_LLM=1 with "
            "RGE_LLM_MODE=ollama. Live probes are opt-in only."
        )
    if effective_llm_mode(cfg) != "ollama":
        raise LiveProbeGateError(
            "effective_llm_mode is not ollama; check RGE_LLM_MODE and "
            "RGE_ALLOW_LIVE_LLM."
        )
    return cfg


def assert_ollama_health(config: RgeConfig) -> dict[str, Any]:
    client = get_model_client(config, mode="ollama")
    health = client.health_check()
    if not health.get("reachable"):
        hint = health.get("action_hint") or "Ollama is not reachable."
        raise LiveProbeGateError(hint)
    if not health.get("model_available"):
        hint = health.get("action_hint") or (
            f"Configured model {health.get('model')!r} is not available locally."
        )
        raise LiveProbeGateError(hint)
    return health


def run_probe_extract_claims(
    *,
    fixture_source: Path | None = None,
    domain_pack: str = DEFAULT_PROBE_DOMAIN,
    root: Path | None = None,
    reports_dir: Path | None = None,
    config: RgeConfig | None = None,
    client: Any | None = None,
    skip_health_check: bool = False,
) -> dict[str, Any]:
    """Run live claim extraction on a fixture chunk; write report only (no DB)."""
    base = root if root is not None else repo_root()
    cfg = assert_live_probe_env(config)
    health = assert_ollama_health(cfg) if not skip_health_check else {}

    fixture_path = resolve_fixture_source(fixture_source, base)
    if not fixture_path.is_file():
        raise LiveProbeError(f"fixture source not found: {fixture_path}")

    chunk_text = fixture_path.read_text(encoding="utf-8")
    chunk = {
        "id": PROBE_CHUNK_ID,
        "source_id": PROBE_SOURCE_ID,
        "chunk_index": 0,
        "chunk_text": chunk_text,
    }

    model_client = client or get_model_client(cfg, mode="ollama")
    try:
        validation = extract_and_validate_for_chunk(
            chunk,
            domain_pack=domain_pack,
            client=model_client,
        )
    except OllamaStructuredCallError as exc:
        raise LiveProbeError(str(exc)) from exc

    accepted = validation["accepted"]
    rejected = validation["rejected"]
    for item in rejected:
        item["validation_diagnostic"] = rejection_diagnostic(
            item,
            chunk_text=chunk_text,
            rejection_reason=item.get("rejection_reason"),
        )
    total = len(accepted) + len(rejected)
    if total == 0:
        raise LiveProbeError(
            "Live probe received no parseable claim candidates from the model."
        )

    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    report: dict[str, Any] = {
        "report_type": "live_probe_report",
        "command": "probe-extract-claims",
        "status": "ok",
        "probe": "claim_extraction",
        "created_at": created_at,
        "fixture_source": str(fixture_path.relative_to(base)).replace("\\", "/"),
        "chunk_id": PROBE_CHUNK_ID,
        "source_id": PROBE_SOURCE_ID,
        "domain_pack": domain_pack,
        "effective_llm_mode": effective_llm_mode(cfg),
        "provider": model_client.provider,
        "model": getattr(model_client, "model", None),
        "base_url": getattr(model_client, "base_url", None),
        "schema_version": cfg.llm_schema_version,
        "health": health,
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "accepted": accepted,
        "rejected": rejected,
        "db_writes": False,
        "default_db_path": str(DEFAULT_DB_PATH).replace("\\", "/"),
    }

    out_dir = reports_dir if reports_dir is not None else live_probes_dir(base)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    report_path = out_dir / f"probe_extract_claims_{stamp}.json"
    try:
        rel_path = report_path.relative_to(base)
        report["report_path"] = str(rel_path).replace("\\", "/")
    except ValueError:
        report["report_path"] = str(report_path).replace("\\", "/")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def default_db_path(root: Path | None = None) -> Path:
    base = root if root is not None else repo_root()
    return (base / DEFAULT_DB_PATH).resolve()


def resolve_claim_fixture(path: Path | None, root: Path | None = None) -> Path:
    base = root if root is not None else repo_root()
    fixture = path if path is not None else DEFAULT_PROBE_CLAIM_FIXTURE
    if not fixture.is_absolute():
        fixture = base / fixture
    return fixture.resolve()


def load_default_probe_claim(root: Path | None = None) -> dict[str, Any]:
    fixture_path = resolve_claim_fixture(None, root)
    if not fixture_path.is_file():
        raise LiveProbeError(f"default probe claim fixture not found: {fixture_path}")
    claim = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not claim.get("id"):
        claim["id"] = PROBE_CLAIM_ID
    return claim


def assign_probe_claim_ids(
    claims: list[dict[str, Any]],
    *,
    prefix: str = "claim_live_probe",
) -> list[dict[str, Any]]:
    """Ensure each claim dict has a stable probe-local id."""
    assigned: list[dict[str, Any]] = []
    for index, claim in enumerate(claims, start=1):
        row = dict(claim)
        if not row.get("id"):
            row["id"] = f"{prefix}_{index:03d}"
        assigned.append(row)
    return assigned


def load_claims_from_probe_report(
    report_path: Path,
    root: Path | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """Load accepted claims from a probe_extract_claims report JSON."""
    base = root if root is not None else repo_root()
    path = report_path if report_path.is_absolute() else (base / report_path)
    path = path.resolve()
    if not path.is_file():
        raise LiveProbeError(f"probe report not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("command") != "probe-extract-claims":
        raise LiveProbeError(
            f"expected probe-extract-claims report, got {payload.get('command')!r}"
        )
    accepted = payload.get("accepted") or []
    if not accepted:
        raise LiveProbeError("probe report contains no accepted claims")

    rel = str(path.relative_to(base)).replace("\\", "/") if path.is_relative_to(base) else str(path)
    return assign_probe_claim_ids(accepted), rel


def _write_live_probe_report(
    *,
    base: Path,
    reports_dir: Path | None,
    filename_prefix: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    out_dir = reports_dir if reports_dir is not None else live_probes_dir(base)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    report_path = out_dir / f"{filename_prefix}_{stamp}.json"
    try:
        rel_path = report_path.relative_to(base)
        report["report_path"] = str(rel_path).replace("\\", "/")
    except ValueError:
        report["report_path"] = str(report_path).replace("\\", "/")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def run_probe_link_concepts(
    *,
    domain_pack: str = DEFAULT_PROBE_DOMAIN,
    claim_fixture: Path | None = None,
    from_report: Path | None = None,
    chain_extract: bool = False,
    chain_fixture_source: Path | None = None,
    root: Path | None = None,
    reports_dir: Path | None = None,
    config: RgeConfig | None = None,
    client: Any | None = None,
    skip_health_check: bool = False,
) -> dict[str, Any]:
    """Run live concept linking on probe claims; write report only (no DB)."""
    base = root if root is not None else repo_root()
    command = "probe-link-concepts"
    cfg = assert_live_probe_env(config, command=command)
    health = assert_ollama_health(cfg) if not skip_health_check else {}

    input_source = "embedded_fixture"
    from_report_path: str | None = None
    chain_report_path: str | None = None
    input_claims: list[dict[str, Any]]

    if chain_extract:
        extract_report = run_probe_extract_claims(
            fixture_source=chain_fixture_source,
            domain_pack=domain_pack,
            root=base,
            reports_dir=reports_dir,
            config=cfg,
            client=client,
            skip_health_check=True,
        )
        input_source = "chain_extract"
        chain_report_path = extract_report.get("report_path")
        accepted = extract_report.get("accepted") or []
        if not accepted:
            raise LiveProbeError(
                "chain-extract produced no accepted claims for concept linking"
            )
        input_claims = assign_probe_claim_ids(accepted)
    elif from_report is not None:
        input_claims, from_report_path = load_claims_from_probe_report(
            from_report,
            base,
        )
        input_source = "from_report"
    elif claim_fixture is not None:
        fixture_path = resolve_claim_fixture(claim_fixture, base)
        if not fixture_path.is_file():
            raise LiveProbeError(f"claim fixture not found: {fixture_path}")
        claim = json.loads(fixture_path.read_text(encoding="utf-8"))
        if not claim.get("id"):
            claim["id"] = PROBE_CLAIM_ID
        input_claims = [claim]
        input_source = "claim_fixture"
    else:
        input_claims = [load_default_probe_claim(base)]
        input_source = "embedded_fixture"

    ontology_labels = ontology_labels_for_pack(domain_pack)
    model_client = client or get_model_client(cfg, mode="ollama")
    try:
        proposed = propose_concept_links(
            input_claims,
            domain_pack,
            client=model_client,
            diversity_heuristic=False,
        )
    except OllamaStructuredCallError as exc:
        raise LiveProbeError(str(exc)) from exc

    validation = validate_concept_links(proposed)
    accepted = validation["accepted"]
    rejected = validation["rejected"]
    for item in rejected:
        item["validation_diagnostic"] = link_rejection_diagnostic(
            item,
            rejection_reason=item.get("rejection_reason"),
            ontology_labels=ontology_labels,
        )

    total = len(accepted) + len(rejected)
    if total == 0:
        raise LiveProbeError(
            "Live probe received no parseable concept-link candidates from the model."
        )

    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    report: dict[str, Any] = {
        "report_type": "live_probe_report",
        "command": command,
        "status": "ok",
        "probe": "concept_linking",
        "created_at": created_at,
        "input_source": input_source,
        "from_report_path": from_report_path,
        "chain_extract_report_path": chain_report_path,
        "input_claims": input_claims,
        "domain_pack": domain_pack,
        "ontology_labels_exposed": ontology_labels,
        "effective_llm_mode": effective_llm_mode(cfg),
        "provider": model_client.provider,
        "model": getattr(model_client, "model", None),
        "base_url": getattr(model_client, "base_url", None),
        "schema_version": cfg.llm_schema_version,
        "health": health,
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "accepted": accepted,
        "rejected": rejected,
        "db_writes": False,
        "default_db_path": str(DEFAULT_DB_PATH).replace("\\", "/"),
    }

    return _write_live_probe_report(
        base=base,
        reports_dir=reports_dir,
        filename_prefix="probe_link_concepts",
        report=report,
    )


def resolve_relationship_bundle(path: Path | None, root: Path | None = None) -> Path:
    base = root if root is not None else repo_root()
    bundle = path if path is not None else DEFAULT_PROBE_RELATIONSHIP_BUNDLE
    if not bundle.is_absolute():
        bundle = base / bundle
    return bundle.resolve()


def concept_dicts_from_links(
    concept_links: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build probe-local concept dicts from accepted concept-link labels."""
    concepts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for link in concept_links:
        label = str(link.get("concept_label", "")).strip()
        if not label or label.casefold() in seen:
            continue
        seen.add(label.casefold())
        concepts.append(
            {"id": f"concept_live_probe_{len(concepts) + 1:03d}", "label": label}
        )
    return concepts


def load_default_relationship_bundle(
    root: Path | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    bundle_path = resolve_relationship_bundle(None, root)
    if not bundle_path.is_file():
        raise LiveProbeError(f"default relationship bundle not found: {bundle_path}")
    return load_relationship_bundle(bundle_path, root)


def load_relationship_bundle(
    bundle_path: Path,
    root: Path | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    base = root if root is not None else repo_root()
    path = bundle_path if bundle_path.is_absolute() else (base / bundle_path)
    path = path.resolve()
    if not path.is_file():
        raise LiveProbeError(f"relationship bundle not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    claim = dict(payload.get("claim") or {})
    if not claim.get("id"):
        claim["id"] = PROBE_CLAIM_ID
    concept_links = list(payload.get("concept_links") or [])
    concepts = list(payload.get("concepts") or [])
    if not concepts and concept_links:
        concepts = concept_dicts_from_links(concept_links)
    if not claim or not concepts:
        raise LiveProbeError("relationship bundle must include claim and concepts")
    return claim, concept_links, concepts


def load_relationship_inputs_from_link_report(
    report_path: Path,
    root: Path | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], str]:
    """Load claim, links, and concepts from a probe-link-concepts report."""
    base = root if root is not None else repo_root()
    path = report_path if report_path.is_absolute() else (base / report_path)
    path = path.resolve()
    if not path.is_file():
        raise LiveProbeError(f"probe report not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("command") != "probe-link-concepts":
        raise LiveProbeError(
            f"expected probe-link-concepts report, got {payload.get('command')!r}"
        )
    accepted_links = payload.get("accepted") or []
    if not accepted_links:
        raise LiveProbeError("probe-link-concepts report contains no accepted links")

    input_claims = payload.get("input_claims") or []
    if not input_claims:
        raise LiveProbeError("probe-link-concepts report missing input_claims")
    claim = dict(input_claims[0])
    if not claim.get("id"):
        claim = assign_probe_claim_ids([claim])[0]

    concepts = concept_dicts_from_links(accepted_links)
    rel = (
        str(path.relative_to(base)).replace("\\", "/")
        if path.is_relative_to(base)
        else str(path)
    )
    return claim, accepted_links, concepts, rel


def run_probe_draft_relationships(
    *,
    domain_pack: str = DEFAULT_PROBE_DOMAIN,
    bundle_fixture: Path | None = None,
    from_report: Path | None = None,
    chain_link: bool = False,
    chain_fixture_source: Path | None = None,
    chain_claim_fixture: Path | None = None,
    root: Path | None = None,
    reports_dir: Path | None = None,
    config: RgeConfig | None = None,
    client: Any | None = None,
    skip_health_check: bool = False,
) -> dict[str, Any]:
    """Run live relationship drafting on probe inputs; write report only (no DB)."""
    base = root if root is not None else repo_root()
    command = "probe-draft-relationships"
    cfg = assert_live_probe_env(config, command=command)
    health = assert_ollama_health(cfg) if not skip_health_check else {}

    input_source = "embedded_bundle"
    from_report_path: str | None = None
    chain_link_report_path: str | None = None
    input_claim: dict[str, Any]
    input_concept_links: list[dict[str, Any]]
    input_concepts: list[dict[str, Any]]

    if chain_link:
        link_report = run_probe_link_concepts(
            domain_pack=domain_pack,
            claim_fixture=chain_claim_fixture,
            chain_extract=chain_fixture_source is not None,
            chain_fixture_source=chain_fixture_source,
            root=base,
            reports_dir=reports_dir,
            config=cfg,
            client=client,
            skip_health_check=True,
        )
        input_source = "chain_link"
        chain_link_report_path = link_report.get("report_path")
        accepted_links = link_report.get("accepted") or []
        if not accepted_links:
            raise LiveProbeError(
                "chain-link produced no accepted concept links for relationship drafting"
            )
        input_claims = link_report.get("input_claims") or []
        if not input_claims:
            raise LiveProbeError("chain-link report missing input_claims")
        input_claim = dict(input_claims[0])
        input_concept_links = accepted_links
        input_concepts = concept_dicts_from_links(accepted_links)
    elif from_report is not None:
        input_claim, input_concept_links, input_concepts, from_report_path = (
            load_relationship_inputs_from_link_report(from_report, base)
        )
        input_source = "from_report"
    elif bundle_fixture is not None:
        input_claim, input_concept_links, input_concepts = load_relationship_bundle(
            bundle_fixture,
            base,
        )
        input_source = "bundle_fixture"
    else:
        input_claim, input_concept_links, input_concepts = (
            load_default_relationship_bundle(base)
        )
        input_source = "embedded_bundle"

    claim_dicts = [input_claim]
    concept_labels = {concept["label"] for concept in input_concepts}
    accepted_claim_ids = {input_claim["id"]}

    model_client = client or get_model_client(cfg, mode="ollama")
    try:
        proposed = propose_relationship_drafts(
            claim_dicts,
            input_concepts,
            domain_pack,
            client=model_client,
            fixture_name="relationship_drafting_live_probe_quality.json",
            diversity_fallback=False,
        )
    except OllamaStructuredCallError as exc:
        raise LiveProbeError(str(exc)) from exc

    validation = validate_relationship_candidates(
        proposed,
        accepted_claim_ids=accepted_claim_ids,
        concept_labels=concept_labels,
    )
    accepted = validation["accepted"]
    rejected = validation["rejected"]
    for item in rejected:
        item["validation_diagnostic"] = relationship_rejection_diagnostic(
            item,
            rejection_reason=item.get("rejection_reason"),
            concept_labels=concept_labels,
            accepted_claim_ids=accepted_claim_ids,
        )

    total = len(accepted) + len(rejected)
    if total == 0:
        raise LiveProbeError(
            "Live probe received no parseable relationship candidates from the model."
        )

    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    report: dict[str, Any] = {
        "report_type": "live_probe_report",
        "command": command,
        "status": "ok",
        "probe": "relationship_drafting",
        "created_at": created_at,
        "input_source": input_source,
        "from_report_path": from_report_path,
        "chain_link_report_path": chain_link_report_path,
        "input_claim": input_claim,
        "input_concept_links": input_concept_links,
        "input_concepts": input_concepts,
        "domain_pack": domain_pack,
        "concept_labels_allowed": sorted(concept_labels),
        "accepted_claim_ids": sorted(accepted_claim_ids),
        "effective_llm_mode": effective_llm_mode(cfg),
        "provider": model_client.provider,
        "model": getattr(model_client, "model", None),
        "base_url": getattr(model_client, "base_url", None),
        "schema_version": cfg.llm_schema_version,
        "health": health,
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "accepted": accepted,
        "rejected": rejected,
        "db_writes": False,
        "default_db_path": str(DEFAULT_DB_PATH).replace("\\", "/"),
    }

    return _write_live_probe_report(
        base=base,
        reports_dir=reports_dir,
        filename_prefix="probe_draft_relationships",
        report=report,
    )


def resolve_contradiction_bundle(path: Path | None, root: Path | None = None) -> Path:
    base = root if root is not None else repo_root()
    bundle = path if path is not None else DEFAULT_PROBE_CONTRADICTION_BUNDLE
    if not bundle.is_absolute():
        bundle = base / bundle
    return bundle.resolve()


def load_contradiction_bundle(
    bundle_path: Path,
    root: Path | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    base = root if root is not None else repo_root()
    path = bundle_path if bundle_path.is_absolute() else (base / bundle_path)
    path = path.resolve()
    if not path.is_file():
        raise LiveProbeError(f"contradiction bundle not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    source_claims = list(payload.get("source_claims") or [])
    domain_claims = list(payload.get("domain_claims") or [])
    relationships = list(payload.get("relationships") or [])
    if not source_claims or not domain_claims or not relationships:
        raise LiveProbeError(
            "contradiction bundle must include source_claims, domain_claims, "
            "and relationships"
        )
    return source_claims, domain_claims, relationships


def load_default_contradiction_bundle(
    root: Path | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    bundle_path = resolve_contradiction_bundle(None, root)
    if not bundle_path.is_file():
        raise LiveProbeError(f"default contradiction bundle not found: {bundle_path}")
    return load_contradiction_bundle(bundle_path, root)


def relationship_triples_from_bundle(
    relationships: list[dict[str, Any]],
) -> set[tuple[str, str, str]]:
    triples: set[tuple[str, str, str]] = set()
    for relationship in relationships:
        subject = str(relationship.get("subject_concept", "")).strip()
        predicate = str(relationship.get("predicate", "")).strip()
        obj = str(relationship.get("object_concept", "")).strip()
        if subject and predicate and obj:
            triples.add((subject, predicate, obj))
    return triples


def merge_qualifying_claim_from_relationship_report(
    relationship_report: dict[str, Any],
    source_claims: list[dict[str, Any]],
    domain_claims: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Overlay qualifying claim from a relationship probe report onto bundle claims."""
    input_claim = dict(relationship_report.get("input_claim") or {})
    if not input_claim:
        raise LiveProbeError("relationship probe report missing input_claim")
    if not input_claim.get("id"):
        input_claim["id"] = PROBE_CLAIM_ID
    qualifying_id = input_claim["id"]
    updated_source = [dict(input_claim)]
    updated_domain: list[dict[str, Any]] = []
    replaced = False
    for claim in domain_claims:
        if claim.get("id") == qualifying_id:
            updated_domain.append(dict(input_claim))
            replaced = True
        else:
            updated_domain.append(dict(claim))
    if not replaced:
        updated_domain.insert(0, dict(input_claim))
    return updated_source, updated_domain


def load_contradiction_inputs_from_relationship_report(
    report_path: Path,
    root: Path | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], str]:
    """Load contradiction inputs using qualifying claim from a relationship probe."""
    base = root if root is not None else repo_root()
    path = report_path if report_path.is_absolute() else (base / report_path)
    path = path.resolve()
    if not path.is_file():
        raise LiveProbeError(f"probe report not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("command") != "probe-draft-relationships":
        raise LiveProbeError(
            f"expected probe-draft-relationships report, got {payload.get('command')!r}"
        )
    default_source, default_domain, relationships = load_default_contradiction_bundle(base)
    source_claims, domain_claims = merge_qualifying_claim_from_relationship_report(
        payload,
        default_source,
        default_domain,
    )
    rel = (
        str(path.relative_to(base)).replace("\\", "/")
        if path.is_relative_to(base)
        else str(path)
    )
    return source_claims, domain_claims, relationships, rel


def run_probe_detect_contradictions(
    *,
    domain_pack: str = DEFAULT_PROBE_DOMAIN,
    bundle_fixture: Path | None = None,
    from_report: Path | None = None,
    chain_relationship: bool = False,
    chain_fixture_source: Path | None = None,
    chain_claim_fixture: Path | None = None,
    chain_bundle_fixture: Path | None = None,
    root: Path | None = None,
    reports_dir: Path | None = None,
    config: RgeConfig | None = None,
    client: Any | None = None,
    skip_health_check: bool = False,
) -> dict[str, Any]:
    """Run live contradiction detection on probe inputs; write report only (no DB)."""
    base = root if root is not None else repo_root()
    command = "probe-detect-contradictions"
    cfg = assert_live_probe_env(config, command=command)
    health = assert_ollama_health(cfg) if not skip_health_check else {}

    input_source = "embedded_bundle"
    from_report_path: str | None = None
    chain_relationship_report_path: str | None = None
    source_claims: list[dict[str, Any]]
    domain_claims: list[dict[str, Any]]
    relationships: list[dict[str, Any]]

    if chain_relationship:
        relationship_report = run_probe_draft_relationships(
            domain_pack=domain_pack,
            bundle_fixture=chain_bundle_fixture,
            chain_link=chain_claim_fixture is not None
            or chain_fixture_source is not None,
            chain_fixture_source=chain_fixture_source,
            chain_claim_fixture=chain_claim_fixture,
            root=base,
            reports_dir=reports_dir,
            config=cfg,
            client=client,
            skip_health_check=True,
        )
        input_source = "chain_relationship"
        chain_relationship_report_path = relationship_report.get("report_path")
        default_source, default_domain, relationships = load_default_contradiction_bundle(
            base
        )
        source_claims, domain_claims = merge_qualifying_claim_from_relationship_report(
            relationship_report,
            default_source,
            default_domain,
        )
    elif from_report is not None:
        source_claims, domain_claims, relationships, from_report_path = (
            load_contradiction_inputs_from_relationship_report(from_report, base)
        )
        input_source = "from_report"
    elif bundle_fixture is not None:
        source_claims, domain_claims, relationships = load_contradiction_bundle(
            bundle_fixture,
            base,
        )
        input_source = "bundle_fixture"
    else:
        source_claims, domain_claims, relationships = load_default_contradiction_bundle(
            base
        )
        input_source = "embedded_bundle"

    source_claim_objects = claim_dicts_as_objects(source_claims)
    domain_claim_objects = claim_dicts_as_objects(domain_claims)
    source_claim_ids = {claim["id"] for claim in source_claims if claim.get("id")}
    domain_claim_ids = {claim["id"] for claim in domain_claims if claim.get("id")}
    relationship_triples = relationship_triples_from_bundle(relationships)

    model_client = client or get_model_client(cfg, mode="ollama")
    try:
        proposed = propose_contradictions(
            domain_claims,
            relationships,
            domain_pack,
            client=model_client,
            fixture_name="contradiction_detection_live_probe_quality.json",
        )
    except OllamaStructuredCallError as exc:
        raise LiveProbeError(str(exc)) from exc

    validation = validate_contradiction_probe_batch(
        proposed,
        source_claims=source_claim_objects,
        domain_claims=domain_claim_objects,
        relationships=relationships,
    )
    accepted = validation["accepted"]
    rejected = validation["rejected"]
    for item in rejected:
        item["validation_diagnostic"] = contradiction_rejection_diagnostic(
            item,
            rejection_reason=item.get("rejection_reason"),
            source_claim_ids=source_claim_ids,
            domain_claim_ids=domain_claim_ids,
            relationship_triples=relationship_triples,
        )

    total = len(accepted) + len(rejected)
    if total == 0:
        raise LiveProbeError(
            "Live probe received no parseable contradiction candidates from the model."
        )

    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    report: dict[str, Any] = {
        "report_type": "live_probe_report",
        "command": command,
        "status": "ok",
        "probe": "contradiction_detection",
        "created_at": created_at,
        "input_source": input_source,
        "from_report_path": from_report_path,
        "chain_relationship_report_path": chain_relationship_report_path,
        "source_claims": source_claims,
        "domain_claims": domain_claims,
        "input_relationships": relationships,
        "domain_pack": domain_pack,
        "relationship_triples_allowed": sorted(relationship_triples),
        "source_claim_ids": sorted(source_claim_ids),
        "domain_claim_ids": sorted(domain_claim_ids),
        "effective_llm_mode": effective_llm_mode(cfg),
        "provider": model_client.provider,
        "model": getattr(model_client, "model", None),
        "base_url": getattr(model_client, "base_url", None),
        "schema_version": cfg.llm_schema_version,
        "health": health,
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "accepted": accepted,
        "rejected": rejected,
        "db_writes": False,
        "default_db_path": str(DEFAULT_DB_PATH).replace("\\", "/"),
    }

    return _write_live_probe_report(
        base=base,
        reports_dir=reports_dir,
        filename_prefix="probe_detect_contradictions",
        report=report,
    )
