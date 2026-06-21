"""Graph maturity / evidence atom upgrade on combined live abstract runs.

Operator-gated proof that accumulates multi-question live abstract claims,
seeds deterministic concept links, re-clusters evidence atoms, and reports
before/after graph maturity metrics with public-safe cluster explanations.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from rge.db.connection import ensure_database
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.atlas_trace import build_graph_connection_metrics
from rge.modules.concept_linker import allowed_concept_labels_for_pack
from rge.modules.domain_pack_loader import load_domain_pack, resolve_canonical_concept_label
from rge.modules.evidence_atoms import cluster_compatible_evidence_atoms
from rge.modules.live_arbitrary_source_health import (
    LIVE_SOURCE_HEALTH_ARTIFACT_NAME,
    build_atlas_safe_run_artifact,
    persist_abstract_evidence_outcomes,
    persist_resolved_source_health,
)
from rge.modules.live_source_expansion import resolve_live_expanded_network_source_records
from rge.modules.multi_question_live_abstract import (
    MULTI_QUESTION_LIVE_ABSTRACT_PROFILES,
    MultiQuestionLiveAbstractProfile,
    assert_live_multi_question_abstract_smoke_env,
)
from rge.modules.principal_audit_gate import repo_root
from rge.modules.purpose_gating import required_concept_family_for_question
from rge.modules.relationship_density_proof import ensure_purpose_gated_relationship_density_proof
from rge.modules.run_evaluator import generate_run_report

PACKET_ID = "graph-maturity-evidence-atom-upgrade"
GRAPH_MATURITY_SCHEMA_VERSION = "atlas_graph_maturity_evidence_atom_upgrade_v0.1.0"
GRAPH_MATURITY_ARTIFACT_NAME = "atlas_graph_maturity_evidence_atom_upgrade_latest.json"
GRAPH_MATURITY_RUN_ID = "run_graph_maturity_evidence_atom_upgrade"

NEXT_RECOMMENDED_PACKET = {
    "id": "web-adapter-scrapling-proof",
    "title": "Web Adapter / Scrapling Proof",
}


class GraphMaturityGateError(RuntimeError):
    """Raised when operator env gates for graph maturity upgrade are missing."""


def assert_live_graph_maturity_evidence_atom_upgrade_env() -> dict[str, str]:
    """Fail closed unless operator opts into graph maturity upgrade smoke."""
    from rge.modules.live_source_expansion import assert_live_source_expansion_smoke_env

    combined = assert_live_source_expansion_smoke_env()
    combined.update(assert_live_multi_question_abstract_smoke_env())
    allow = os.environ.get(
        "RGE_ALLOW_LIVE_GRAPH_MATURITY_EVIDENCE_ATOM_UPGRADE", "0"
    ).strip().casefold()
    if allow not in {"1", "true", "yes"}:
        raise GraphMaturityGateError(
            "Graph maturity evidence atom upgrade requires "
            "RGE_ALLOW_LIVE_GRAPH_MATURITY_EVIDENCE_ATOM_UPGRADE=1."
        )
    combined["RGE_ALLOW_LIVE_GRAPH_MATURITY_EVIDENCE_ATOM_UPGRADE"] = allow
    return combined


def required_env_setup_commands() -> list[str]:
    return [
        '$env:RGE_ALLOW_LIVE_GRAPH_MATURITY_EVIDENCE_ATOM_UPGRADE = "1"',
        '$env:RGE_ALLOW_LIVE_MULTI_QUESTION_ABSTRACT_SMOKE = "1"',
        '$env:RGE_ALLOW_LIVE_SOURCE_EXPANSION_SMOKE = "1"',
        '$env:RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_QUALITY_SMOKE = "1"',
        '$env:RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE = "1"',
        '$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"',
        '$env:RGE_ALLOW_SOURCE_NETWORK = "1"',
        '$env:OPENALEX_MAILTO = "operator@example.com"',
        '$env:RGE_LLM_MODE = "mock"',
        "python scripts/run_graph_maturity_evidence_atom_upgrade.py --sync-public",
    ]


def _match_concepts_in_text(text: str, domain_pack: str) -> list[str]:
    lowered = str(text or "").casefold()
    if not lowered.strip():
        return []
    pack = load_domain_pack(domain_pack)
    matched: set[str] = set()
    for concept in pack.concepts:
        label = str(concept.label or "").strip()
        if label and label.casefold() in lowered:
            matched.add(label)
    for canonical, alias_phrases in pack.aliases.items():
        canonical_label = str(canonical).strip()
        if canonical_label.casefold() in lowered:
            matched.add(resolve_canonical_concept_label(pack, canonical_label))
        for phrase in alias_phrases:
            if str(phrase).casefold() in lowered:
                matched.add(resolve_canonical_concept_label(pack, canonical_label))
    allowed = {label.casefold(): label for label in allowed_concept_labels_for_pack(domain_pack)}
    return sorted(
        allowed.get(label.casefold(), label)
        for label in matched
        if label.casefold() in allowed or label in allowed.values()
    )


def seed_deterministic_concepts_for_claims(
    conn: sqlite3.Connection,
    *,
    domain_pack: str,
    claim_ids: list[str] | None = None,
    question: str | None = None,
) -> dict[str, Any]:
    """Seed claim_concepts rows from domain-pack keyword matching (no LLM)."""
    from rge.db.repositories import ClaimConceptRepository, ConceptRepository

    concept_repo = ConceptRepository(conn)
    concept_repo.ensure_domain_concepts(domain_pack)
    link_repo = ClaimConceptRepository(conn)

    params: list[Any] = [domain_pack]
    where = "status = 'accepted' AND domain = ?"
    if claim_ids is not None:
        if not claim_ids:
            return {"seeded_link_count": 0, "claims_touched": 0, "skipped_existing": 0}
        where += f" AND id IN ({','.join('?' for _ in claim_ids)})"
        params.extend(claim_ids)

    rows = conn.execute(
        f"""
        SELECT id, claim_text, scope
        FROM claims
        WHERE {where}
        ORDER BY id
        """,
        tuple(params),
    ).fetchall()

    requirement = (
        required_concept_family_for_question(question, domain_pack=domain_pack)
        if question
        else None
    )
    fallback_concepts: list[str] = []
    if requirement:
        for family in requirement.get("families") or []:
            fallback_concepts.extend(list(family.get("required_concepts") or []))
    fallback_concepts = fallback_concepts[:2]

    seeded = 0
    skipped_existing = 0
    claims_touched = 0
    for row in rows:
        claim_id = str(row["id"])
        existing = conn.execute(
            "SELECT COUNT(*) FROM claim_concepts WHERE claim_id = ?",
            (claim_id,),
        ).fetchone()
        if int(existing[0] if existing else 0) > 0:
            skipped_existing += 1
            continue

        combined_text = f"{row['claim_text']} {row['scope']}"
        labels = _match_concepts_in_text(combined_text, domain_pack)
        if not labels and fallback_concepts:
            labels = list(fallback_concepts[:2])
        if not labels:
            labels = ["AI assistance", "creativity"]

        claims_touched += 1
        for label in labels[:3]:
            concept = concept_repo.get_by_label(domain_pack, label)
            if concept is None:
                continue
            link_repo.insert(
                claim_id=claim_id,
                concept_id=str(concept.id),
                role="supports",
                confidence=0.55,
                domain_metadata={
                    "link_source": "deterministic_keyword_seed",
                    "graph_maturity_upgrade": True,
                },
            )
            seeded += 1

    return {
        "seeded_link_count": seeded,
        "claims_touched": claims_touched,
        "skipped_existing": skipped_existing,
    }


def snapshot_graph_maturity_metrics(
    conn: sqlite3.Connection,
    *,
    domain_pack: str,
    question: str | None = None,
) -> dict[str, Any]:
    """Capture graph maturity totals for before/after comparison."""
    metrics = build_graph_connection_metrics(
        conn,
        domain_pack=domain_pack,
        question=question,
    )
    totals = dict(metrics.get("totals") or {})
    atom_rows = conn.execute(
        "SELECT source_claim_ids_json FROM evidence_atoms"
    ).fetchall()
    single_claim_atom_count = 0
    for row in atom_rows:
        claim_ids = json.loads(row["source_claim_ids_json"] or "[]")
        if len(claim_ids) == 1:
            single_claim_atom_count += 1
    claim_count = int(totals.get("claims") or 0)
    relationship_count = int(totals.get("relationships") or 0)
    relationship_density = (
        round(relationship_count / claim_count, 4) if claim_count else 0.0
    )
    return {
        **totals,
        "single_claim_atom_count": single_claim_atom_count,
        "relationship_density": relationship_density,
        "cluster_count": len(metrics.get("clusters") or []),
    }


def explain_cluster_maturity(cluster: dict[str, Any]) -> dict[str, Any]:
    """Public-safe explanation for why a cluster is mature or weak."""
    reasons: list[str] = []
    density = float(cluster.get("relationship_density") or 0.0)
    relationships = int(cluster.get("relationships_per_cluster") or 0)
    orphans = int(cluster.get("orphan_claim_count") or cluster.get("orphan_claims") or 0)
    contradictions = int(
        cluster.get("contradiction_edge_count") or cluster.get("contradiction_edges") or 0
    )
    qualifications = int(
        cluster.get("qualification_edge_count") or cluster.get("qualification_edges") or 0
    )
    atoms = int(cluster.get("atoms_per_cluster") or 0)

    if relationships <= 0:
        reasons.append("No typed relationship edges link claims in this cluster.")
    if orphans > 0:
        reasons.append(f"{orphans} claim(s) lack relationship coverage.")
    if cluster.get("low_relationship_density"):
        reasons.append("Relationship density is below the 0.5 threshold.")

    if (
        relationships >= 1
        and atoms >= 1
        and (contradictions > 0 or qualifications > 0)
        and orphans == 0
    ):
        maturity_label = "synthesis_ready"
        reasons.append(
            "Contradiction or qualification edges exist with full claim coverage."
        )
    elif relationships >= 1 and density >= 0.5 and orphans == 0:
        maturity_label = "promising"
        reasons.append("Relationship density meets the 0.5 threshold.")
    elif relationships >= 1:
        maturity_label = "weak"
        reasons.append("Relationships exist but coverage or density remains thin.")
    else:
        maturity_label = "weak"
        if not reasons:
            reasons.append("Cluster lacks relationship-backed evidence paths.")

    return {
        "cluster_ref": str(cluster.get("cluster_id") or "cluster_unknown"),
        "maturity_label": maturity_label,
        "relationship_density": round(density, 4),
        "relationship_count": relationships,
        "contradiction_edges": contradictions,
        "qualification_edges": qualifications,
        "orphan_claim_count": orphans,
        "reasons": reasons,
    }


def upgrade_graph_evidence_atom_maturity(
    conn: sqlite3.Connection,
    *,
    domain_pack: str,
    question: str,
    claim_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Run deterministic concept seeding and atom re-clustering upgrade pass."""
    before = snapshot_graph_maturity_metrics(
        conn,
        domain_pack=domain_pack,
        question=question,
    )
    concept_seed = seed_deterministic_concepts_for_claims(
        conn,
        domain_pack=domain_pack,
        claim_ids=claim_ids,
        question=question,
    )
    cluster_result = cluster_compatible_evidence_atoms(
        conn,
        domain=domain_pack,
        claim_ids=claim_ids,
        question=question,
        enforce_purpose_gate=False,
    )
    after = snapshot_graph_maturity_metrics(
        conn,
        domain_pack=domain_pack,
        question=question,
    )
    metrics = build_graph_connection_metrics(
        conn,
        domain_pack=domain_pack,
        question=question,
    )
    cluster_explanations = [
        explain_cluster_maturity(cluster)
        for cluster in (metrics.get("clusters") or [])
    ]
    delta = {
        "single_claim_atom_delta": int(after.get("single_claim_atom_count") or 0)
        - int(before.get("single_claim_atom_count") or 0),
        "clustered_atom_delta": int(after.get("clustered_atom_count") or 0)
        - int(before.get("clustered_atom_count") or 0),
        "multi_claim_atom_delta": int(after.get("multi_claim_atom_count") or 0)
        - int(before.get("multi_claim_atom_count") or 0),
        "orphan_claim_delta": int(after.get("orphan_claim_count") or 0)
        - int(before.get("orphan_claim_count") or 0),
        "orphan_atom_delta": int(after.get("orphan_atom_count") or 0)
        - int(before.get("orphan_atom_count") or 0),
        "relationship_density_delta": round(
            float(after.get("relationship_density") or 0.0)
            - float(before.get("relationship_density") or 0.0),
            4,
        ),
    }
    return {
        "before": before,
        "after": after,
        "delta": delta,
        "concept_seed": concept_seed,
        "cluster_result": {
            "clustered_atom_count": int(cluster_result.get("clustered_atom_count") or 0),
            "duplicate_merged_atom_count": int(
                cluster_result.get("duplicate_merged_atom_count") or 0
            ),
            "separate_claim_count": int(cluster_result.get("separate_claim_count") or 0),
        },
        "cluster_explanations": cluster_explanations,
    }


def _ingest_profile_into_maturity_db(
    conn: sqlite3.Connection,
    profile: MultiQuestionLiveAbstractProfile,
    *,
    domain_pack: str,
    limit: int,
    client: Any | None = None,
) -> dict[str, Any]:
    resolved = resolve_live_expanded_network_source_records(
        question=profile.question,
        resolver_query=profile.resolver_query,
        domain_pack=domain_pack,
        limit=limit,
    )
    records = list(resolved.get("records") or [])
    if not records:
        return {
            "question_id": profile.question_id,
            "status": "skipped",
            "reason": "no_records",
            "accepted_claim_ids": [],
        }

    persist_resolved_source_health(
        conn,
        records,
        question=profile.question,
        domain_pack=domain_pack,
    )
    evidence = persist_abstract_evidence_outcomes(
        conn,
        records,
        question=profile.question,
        domain_pack=domain_pack,
        client=client,
        live_abstract_mode=True,
    )
    accepted_claim_ids = list(evidence.get("accepted_claim_ids") or [])
    return {
        "question_id": profile.question_id,
        "question": profile.question,
        "gate_mode": profile.gate_mode,
        "status": "completed",
        "live_source_count": len(records),
        "accepted_claim_count": len(accepted_claim_ids),
        "accepted_claim_ids": accepted_claim_ids,
        "relationship_count": 0,
    }


def classify_graph_maturity_verdict(
    upgrade: dict[str, Any],
    *,
    question_ingest_rows: list[dict[str, Any]],
) -> tuple[str, str]:
    """Return (verdict, rationale) for graph maturity upgrade proof."""
    after = dict(upgrade.get("after") or {})
    delta = dict(upgrade.get("delta") or {})
    total_accepted = sum(
        int(row.get("accepted_claim_count") or 0) for row in question_ingest_rows
    )
    if total_accepted < 1:
        return "NO-GO", "No accepted live abstract claims were accumulated for upgrade."

    density = dict(upgrade.get("density_result") or {})
    improved = any(
        int(delta.get(key) or 0) < 0
        for key in ("single_claim_atom_delta", "orphan_claim_delta", "orphan_atom_delta")
    ) or any(
        int(delta.get(key) or 0) > 0
        for key in (
            "clustered_atom_delta",
            "multi_claim_atom_delta",
            "relationship_density_delta",
        )
    ) or int(density.get("relationship_count") or 0) >= 1

    if (
        total_accepted >= 3
        and int(after.get("relationships") or 0) >= 1
        and int(after.get("multi_claim_atom_count") or 0) >= 1
        and improved
    ):
        return (
            "GO",
            "Multi-question live claims were re-clustered with fewer single-claim atoms "
            "and improved graph maturity metrics.",
        )

    if (
        total_accepted >= 1
        and int(after.get("relationships") or 0) >= 1
        and (upgrade.get("cluster_explanations") or [])
    ):
        return (
            "PARTIAL",
            "Graph maturity upgrade produced relationships and cluster explanations, "
            "but multi-claim atom consolidation remains thin on live abstracts.",
        )

    if improved or int(after.get("clustered_atom_count") or 0) >= 1:
        return (
            "PARTIAL",
            "Graph maturity upgrade ran but clustering or relationship density remains thin.",
        )

    return (
        "NO-GO",
        "Upgrade pass did not improve clustered atoms, relationship density, or orphan counts.",
    )


def build_atlas_safe_graph_maturity_artifact(
    *,
    upgrade: dict[str, Any],
    question_ingest_rows: list[dict[str, Any]],
    verdict: str,
    rationale: str,
    domain_pack: str = "creativity",
) -> dict[str, Any]:
    """Build public-safe Atlas bundle for graph maturity upgrade."""
    after = dict(upgrade.get("after") or {})
    before = dict(upgrade.get("before") or {})
    public_questions = [
        {
            "question_id": row.get("question_id"),
            "gate_mode": row.get("gate_mode"),
            "live_source_count": int(row.get("live_source_count") or 0),
            "accepted_claim_count": int(row.get("accepted_claim_count") or 0),
            "relationship_count": int(row.get("relationship_count") or 0),
        }
        for row in question_ingest_rows
    ]
    artifact: dict[str, Any] = {
        "schema_version": GRAPH_MATURITY_SCHEMA_VERSION,
        "status": "completed",
        "packet_id": PACKET_ID,
        "run_id": GRAPH_MATURITY_RUN_ID,
        "domain_pack": domain_pack,
        "graph_maturity_verdict": verdict,
        "graph_maturity_rationale": rationale,
        "question_ingest_summary": public_questions,
        "question_count": len(public_questions),
        "total_accepted_claims": sum(
            int(row.get("accepted_claim_count") or 0) for row in question_ingest_rows
        ),
        "maturity_before": {
            "single_claim_atom_count": int(before.get("single_claim_atom_count") or 0),
            "clustered_atom_count": int(before.get("clustered_atom_count") or 0),
            "multi_claim_atom_count": int(before.get("multi_claim_atom_count") or 0),
            "weak_atom_count": int(before.get("weak_atom_count") or 0),
            "orphan_claim_count": int(before.get("orphan_claim_count") or 0),
            "orphan_atom_count": int(before.get("orphan_atom_count") or 0),
            "relationship_density": before.get("relationship_density"),
            "synthesis_ready_cluster_count": int(
                before.get("synthesis_ready_cluster_count") or 0
            ),
        },
        "maturity_after": {
            "single_claim_atom_count": int(after.get("single_claim_atom_count") or 0),
            "clustered_atom_count": int(after.get("clustered_atom_count") or 0),
            "multi_claim_atom_count": int(after.get("multi_claim_atom_count") or 0),
            "weak_atom_count": int(after.get("weak_atom_count") or 0),
            "orphan_claim_count": int(after.get("orphan_claim_count") or 0),
            "orphan_atom_count": int(after.get("orphan_atom_count") or 0),
            "relationship_density": after.get("relationship_density"),
            "synthesis_ready_cluster_count": int(
                after.get("synthesis_ready_cluster_count") or 0
            ),
        },
        "maturity_delta": upgrade.get("delta") or {},
        "upgrade_actions": {
            "concept_seed": upgrade.get("concept_seed") or {},
            "cluster_result": upgrade.get("cluster_result") or {},
            "density_result": upgrade.get("density_result") or {},
        },
        "cluster_maturity_explanations": upgrade.get("cluster_explanations") or [],
        "next_recommended_packet": NEXT_RECOMMENDED_PACKET,
    }
    violations = assert_no_private_fields({"artifact": artifact})
    if violations:
        raise ValueError(
            "Graph maturity artifact blocked by private-field policy: "
            + "; ".join(violations[:5])
        )
    return artifact


def sync_graph_maturity_artifact_to_public_site(
    artifact: dict[str, Any],
    *,
    public_path: Path,
) -> dict[str, Any]:
    """Copy validated graph maturity artifact into public-site preview data."""
    if artifact.get("schema_version") != GRAPH_MATURITY_SCHEMA_VERSION:
        raise ValueError(
            f"schema_version must be {GRAPH_MATURITY_SCHEMA_VERSION!r}."
        )
    verdict = str(artifact.get("graph_maturity_verdict") or "")
    if verdict in {"", "PENDING"}:
        raise ValueError("graph_maturity_verdict must be set before public sync.")
    if int(artifact.get("question_count") or 0) < 1:
        raise ValueError("question_count must be >= 1.")
    violations = assert_no_private_fields({"artifact": artifact})
    if violations:
        raise ValueError(
            "Graph maturity artifact failed public-safe validation: "
            + "; ".join(violations[:5])
        )
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return {
        "status": "completed",
        "output_path": str(public_path),
        "graph_maturity_verdict": verdict,
        "question_count": artifact.get("question_count"),
        "total_accepted_claims": artifact.get("total_accepted_claims"),
    }


def run_graph_maturity_evidence_atom_upgrade_smoke(
    conn: sqlite3.Connection,
    *,
    output_dir: Path | None = None,
    domain_pack: str = "creativity",
    profiles: tuple[MultiQuestionLiveAbstractProfile, ...] = MULTI_QUESTION_LIVE_ABSTRACT_PROFILES,
    limit_per_question: int = 3,
    client: Any | None = None,
) -> dict[str, Any]:
    """Operator-gated multi-question ingest + graph maturity upgrade on one DB."""
    env_gates = assert_live_graph_maturity_evidence_atom_upgrade_env()
    os.environ.setdefault("RGE_LLM_MODE", "mock")

    question_rows: list[dict[str, Any]] = []
    all_claim_ids: list[str] = []
    for profile in profiles:
        row = _ingest_profile_into_maturity_db(
            conn,
            profile,
            domain_pack=domain_pack,
            limit=limit_per_question,
            client=client,
        )
        question_rows.append(row)
        all_claim_ids.extend(list(row.get("accepted_claim_ids") or []))

    combined_question = (
        "Graph maturity upgrade across multi-question live abstract evidence"
    )
    before = snapshot_graph_maturity_metrics(
        conn,
        domain_pack=domain_pack,
        question=combined_question,
    )
    concept_seed = seed_deterministic_concepts_for_claims(
        conn,
        domain_pack=domain_pack,
        claim_ids=all_claim_ids or None,
        question=combined_question,
    )
    cluster_result = cluster_compatible_evidence_atoms(
        conn,
        domain=domain_pack,
        claim_ids=all_claim_ids or None,
        question=combined_question,
        enforce_purpose_gate=False,
    )
    density_result: dict[str, Any] = {"status": "skipped", "reason": "no_accepted_claims"}
    if all_claim_ids:
        density_result = ensure_purpose_gated_relationship_density_proof(
            conn,
            domain=domain_pack,
            question=combined_question,
            claim_ids=all_claim_ids,
        )
    after = snapshot_graph_maturity_metrics(
        conn,
        domain_pack=domain_pack,
        question=combined_question,
    )
    metrics = build_graph_connection_metrics(
        conn,
        domain_pack=domain_pack,
        question=combined_question,
    )
    cluster_explanations = [
        explain_cluster_maturity(cluster)
        for cluster in (metrics.get("clusters") or [])
    ]
    delta = {
        "single_claim_atom_delta": int(after.get("single_claim_atom_count") or 0)
        - int(before.get("single_claim_atom_count") or 0),
        "clustered_atom_delta": int(after.get("clustered_atom_count") or 0)
        - int(before.get("clustered_atom_count") or 0),
        "multi_claim_atom_delta": int(after.get("multi_claim_atom_count") or 0)
        - int(before.get("multi_claim_atom_count") or 0),
        "orphan_claim_delta": int(after.get("orphan_claim_count") or 0)
        - int(before.get("orphan_claim_count") or 0),
        "orphan_atom_delta": int(after.get("orphan_atom_count") or 0)
        - int(before.get("orphan_atom_count") or 0),
        "relationship_density_delta": round(
            float(after.get("relationship_density") or 0.0)
            - float(before.get("relationship_density") or 0.0),
            4,
        ),
    }
    upgrade = {
        "before": before,
        "after": after,
        "delta": delta,
        "concept_seed": concept_seed,
        "cluster_result": {
            "clustered_atom_count": int(cluster_result.get("clustered_atom_count") or 0),
            "duplicate_merged_atom_count": int(
                cluster_result.get("duplicate_merged_atom_count") or 0
            ),
            "separate_claim_count": int(cluster_result.get("separate_claim_count") or 0),
        },
        "density_result": {
            "relationship_count": int(density_result.get("relationship_count") or 0),
            "purpose_match_count": int(density_result.get("purpose_match_count") or 0),
        },
        "cluster_explanations": cluster_explanations,
    }
    for row in question_rows:
        row["relationship_count"] = int(density_result.get("relationship_count") or 0)
    verdict, rationale = classify_graph_maturity_verdict(
        upgrade,
        question_ingest_rows=question_rows,
    )
    artifact = build_atlas_safe_graph_maturity_artifact(
        upgrade=upgrade,
        question_ingest_rows=question_rows,
        verdict=verdict,
        rationale=rationale,
        domain_pack=domain_pack,
    )

    report_result = generate_run_report(
        conn,
        run_id=GRAPH_MATURITY_RUN_ID,
        topic=combined_question,
        domain_pack=domain_pack,
        output_dir=output_dir,
    )
    run_report = dict(report_result.get("report") or {})
    source_health_artifact = build_atlas_safe_run_artifact(
        conn,
        question=combined_question,
        domain_pack=domain_pack,
        run_report=run_report,
        question_id="graph_maturity_combined",
    )
    artifact["linked_source_health_artifact"] = {
        "graph_summary": source_health_artifact.get("graph_summary"),
        "trace_summary": {
            "trace_count": int(
                (source_health_artifact.get("trace_summary") or {}).get("trace_count") or 0
            ),
            "atom_count": int(
                (source_health_artifact.get("trace_summary") or {}).get("atom_count") or 0
            ),
        },
    }

    root = repo_root()
    out_dir = output_dir or (root / "data" / "exports" / "graph_maturity_evidence_atom_upgrade")
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = out_dir / GRAPH_MATURITY_ARTIFACT_NAME
    artifact_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    health_path = out_dir / LIVE_SOURCE_HEALTH_ARTIFACT_NAME
    health_path.write_text(json.dumps(source_health_artifact, indent=2), encoding="utf-8")

    try:
        operator_artifact_ref = artifact_path.relative_to(root).as_posix()
    except ValueError:
        operator_artifact_ref = f"{out_dir.name}/{GRAPH_MATURITY_ARTIFACT_NAME}"

    return {
        "packet_id": PACKET_ID,
        "graph_maturity_verdict": verdict,
        "graph_maturity_rationale": rationale,
        "question_count": len(question_rows),
        "total_accepted_claims": artifact.get("total_accepted_claims"),
        "maturity_delta": upgrade.get("delta"),
        "env_gates": env_gates,
        "artifact_path": str(artifact_path),
        "operator_artifact_ref": operator_artifact_ref,
        "atlas_safe_artifact": artifact,
        "next_recommended_packet": NEXT_RECOMMENDED_PACKET,
    }


def run_graph_maturity_with_fresh_db(
    *,
    output_dir: Path | None = None,
    db_path: Path | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Convenience entry: ensure DB, run smoke, close."""
    root = repo_root()
    out_dir = output_dir or (root / "data" / "exports" / "graph_maturity_evidence_atom_upgrade")
    out_dir.mkdir(parents=True, exist_ok=True)
    db = db_path or (out_dir / "graph_maturity.sqlite")
    if db.exists():
        db.unlink()
    conn = ensure_database(db)
    try:
        return run_graph_maturity_evidence_atom_upgrade_smoke(
            conn,
            output_dir=out_dir,
            **kwargs,
        )
    finally:
        conn.close()
