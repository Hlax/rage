"""Atlas connection traces and graph health metrics.

Private traces keep durable IDs for operator debugging. Atlas-safe previews keep
only non-private counts and labels for frontend planning.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

ATLAS_TRACE_SCHEMA_VERSION = "atlas_trace_v0.1.0"
GRAPH_CONNECTION_METRICS_SCHEMA_VERSION = "graph_connection_metrics_v0.1.0"


def _json_list(raw: str | None) -> list[Any]:
    try:
        value = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


def _first_question_id(conn: sqlite3.Connection) -> str:
    row = conn.execute(
        """
        SELECT research_question_id
        FROM research_queue
        WHERE research_question_id IS NOT NULL AND research_question_id != ''
        ORDER BY created_at, id
        LIMIT 1
        """
    ).fetchone()
    if row and row["research_question_id"]:
        return str(row["research_question_id"])
    return "question_unassigned"


def _cluster_claim_map(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute(
        """
        SELECT id, report_json, evidence_packet_json
        FROM cluster_reports
        ORDER BY created_at, id
        """
    ).fetchall()
    mapping: dict[str, str] = {}
    for row in rows:
        cluster_id = str(row["id"])
        report = {}
        packet = {}
        try:
            report = json.loads(row["report_json"] or "{}")
        except json.JSONDecodeError:
            report = {}
        try:
            packet = json.loads(row["evidence_packet_json"] or "{}")
        except json.JSONDecodeError:
            packet = {}
        explicit_cluster_id = str(
            report.get("cluster_id") or packet.get("cluster_id") or cluster_id
        )
        claim_ids = set(str(item) for item in report.get("linked_claim_ids") or [])
        for key in (
            "supporting_claims",
            "contradicting_claims",
            "qualifying_claims",
        ):
            claim_ids.update(str(item) for item in report.get(key) or [])
        for key in (
            "top_supporting_claims",
            "top_contradicting_claims",
            "top_qualifying_claims",
            "newest_claims",
        ):
            claim_ids.update(str(item) for item in packet.get(key) or [])
        for claim_id in claim_ids:
            mapping.setdefault(claim_id, explicit_cluster_id)
    return mapping


def _atom_for_claim(conn: sqlite3.Connection, claim_id: str) -> dict[str, Any] | None:
    rows = conn.execute(
        """
        SELECT id, source_claim_ids_json, evidence_maturity
        FROM evidence_atoms
        ORDER BY updated_at DESC, id
        """
    ).fetchall()
    for row in rows:
        if claim_id in {str(item) for item in _json_list(row["source_claim_ids_json"])}:
            return {
                "atom_id": str(row["id"]),
                "maturity": str(row["evidence_maturity"] or "seed"),
            }
    return None


def _concept_ids_for_claim(conn: sqlite3.Connection, claim_id: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT concept_id
        FROM claim_concepts
        WHERE claim_id = ?
        ORDER BY concept_id
        """,
        (claim_id,),
    ).fetchall()
    return [str(row["concept_id"]) for row in rows]


def _relationship_ids_for_claim(conn: sqlite3.Connection, claim_id: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT DISTINCT relationship_id
        FROM relationship_evidence
        WHERE claim_id = ?
        ORDER BY relationship_id
        """,
        (claim_id,),
    ).fetchall()
    return [str(row["relationship_id"]) for row in rows]


def build_atlas_trace_export(
    conn: sqlite3.Connection,
    *,
    domain_pack: str,
    question_id: str | None = None,
    visibility: str = "private",
) -> list[dict[str, Any]]:
    """Build private source -> quote -> claim -> atom -> concept -> cluster traces."""
    resolved_question_id = question_id or _first_question_id(conn)
    cluster_map = _cluster_claim_map(conn)
    rows = conn.execute(
        """
        SELECT c.id AS claim_id, c.source_id, q.id AS quote_id
        FROM claims c
        JOIN claim_quotes q ON q.claim_id = c.id
        WHERE c.domain = ? AND c.status = 'accepted'
        ORDER BY c.id, q.is_primary DESC, q.created_at
        """,
        (domain_pack,),
    ).fetchall()
    traces: list[dict[str, Any]] = []
    for row in rows:
        claim_id = str(row["claim_id"])
        atom = _atom_for_claim(conn, claim_id) or {}
        concept_ids = _concept_ids_for_claim(conn, claim_id)
        relationship_ids = _relationship_ids_for_claim(conn, claim_id)
        cluster_id = cluster_map.get(claim_id, "cluster_unassigned")
        connection_type = "source_quote_claim_atom_concept_cluster"
        if not atom:
            connection_type = "source_quote_claim_concept_cluster"
        traces.append(
            {
                "question_id": resolved_question_id,
                "cluster_id": cluster_id,
                "atom_id": atom.get("atom_id"),
                "claim_id": claim_id,
                "quote_id": str(row["quote_id"]),
                "source_id": str(row["source_id"]),
                "concept_ids": concept_ids,
                "relationship_ids": relationship_ids,
                "connection_type": connection_type,
                "maturity": atom.get("maturity", "seed"),
                "visibility": visibility,
                "why_connected": (
                    "Accepted quote-backed claim links source provenance to "
                    f"{len(concept_ids)} concept(s), {len(relationship_ids)} relationship(s), "
                    f"and cluster {cluster_id}."
                ),
            }
        )
    return traces


def build_atlas_trace_preview(traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Strip private IDs from trace rows for Atlas/public preview surfaces."""
    previews: list[dict[str, Any]] = []
    for index, trace in enumerate(traces):
        previews.append(
            {
                "trace_ref": f"trace_{index + 1:03d}",
                "connection_type": str(trace.get("connection_type") or ""),
                "maturity": str(trace.get("maturity") or "seed"),
                "visibility": "public_safe",
                "has_quote": bool(trace.get("quote_id")),
                "concept_count": len(trace.get("concept_ids") or []),
                "relationship_count": len(trace.get("relationship_ids") or []),
                "why_connected": str(trace.get("why_connected") or ""),
            }
        )
    return previews


def _cluster_definitions(conn: sqlite3.Connection, domain_pack: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, report_json, evidence_packet_json
        FROM cluster_reports
        ORDER BY created_at, id
        """
    ).fetchall()
    clusters: list[dict[str, Any]] = []
    for row in rows:
        report: dict[str, Any] = {}
        packet: dict[str, Any] = {}
        try:
            report = json.loads(row["report_json"] or "{}")
        except json.JSONDecodeError:
            report = {}
        try:
            packet = json.loads(row["evidence_packet_json"] or "{}")
        except json.JSONDecodeError:
            packet = {}
        claim_ids = set(str(item) for item in report.get("linked_claim_ids") or [])
        for key in (
            "supporting_claims",
            "contradicting_claims",
            "qualifying_claims",
        ):
            claim_ids.update(str(item) for item in report.get(key) or [])
        for key in (
            "top_supporting_claims",
            "top_contradicting_claims",
            "top_qualifying_claims",
            "newest_claims",
        ):
            claim_ids.update(str(item) for item in packet.get(key) or [])
        if claim_ids:
            clusters.append(
                {
                    "cluster_id": str(report.get("cluster_id") or packet.get("cluster_id") or row["id"]),
                    "claim_ids": sorted(claim_ids),
                }
            )
    if clusters:
        return clusters
    claim_rows = conn.execute(
        """
        SELECT id FROM claims
        WHERE domain = ? AND status = 'accepted'
        ORDER BY id
        """,
        (domain_pack,),
    ).fetchall()
    claim_ids = [str(row["id"]) for row in claim_rows]
    return [{"cluster_id": "cluster_unassigned", "claim_ids": claim_ids}] if claim_ids else []


def _atom_ids_for_claims(conn: sqlite3.Connection, claim_ids: set[str]) -> set[str]:
    rows = conn.execute(
        "SELECT id, source_claim_ids_json FROM evidence_atoms ORDER BY id"
    ).fetchall()
    atom_ids: set[str] = set()
    for row in rows:
        atom_claims = {str(item) for item in _json_list(row["source_claim_ids_json"])}
        if atom_claims & claim_ids:
            atom_ids.add(str(row["id"]))
    return atom_ids


def build_graph_connection_metrics(
    conn: sqlite3.Connection,
    *,
    domain_pack: str,
) -> dict[str, Any]:
    """Return graph/Atlas connection metrics per cluster and in aggregate."""
    clusters = _cluster_definitions(conn, domain_pack)
    cluster_metrics: list[dict[str, Any]] = []
    for cluster in clusters:
        claim_ids = set(cluster["claim_ids"])
        placeholders = ",".join("?" for _ in claim_ids)
        rel_rows = conn.execute(
            f"""
            SELECT relationship_id, claim_id, stance
            FROM relationship_evidence
            WHERE claim_id IN ({placeholders})
            """,
            tuple(claim_ids),
        ).fetchall() if claim_ids else []
        relationship_ids = {str(row["relationship_id"]) for row in rel_rows}
        claims_with_relationships = {str(row["claim_id"]) for row in rel_rows}
        contradiction_edges = sum(1 for row in rel_rows if row["stance"] == "contradicts")
        qualification_edges = sum(1 for row in rel_rows if row["stance"] == "qualifies")
        source_rows = conn.execute(
            f"""
            SELECT DISTINCT source_id
            FROM claims
            WHERE id IN ({placeholders})
            """,
            tuple(claim_ids),
        ).fetchall() if claim_ids else []
        atom_ids = _atom_ids_for_claims(conn, claim_ids)
        orphan_claims = sorted(claim_ids - claims_with_relationships)
        orphan_atoms = 0
        for atom_id in atom_ids:
            atom_row = conn.execute(
                "SELECT source_claim_ids_json FROM evidence_atoms WHERE id = ?",
                (atom_id,),
            ).fetchone()
            atom_claims = {str(item) for item in _json_list(atom_row["source_claim_ids_json"])} if atom_row else set()
            if not (atom_claims & claims_with_relationships):
                orphan_atoms += 1
        claims_per_cluster = len(claim_ids)
        relationships_per_cluster = len(relationship_ids)
        density = relationships_per_cluster / claims_per_cluster if claims_per_cluster else 0.0
        cluster_metrics.append(
            {
                "cluster_id": cluster["cluster_id"],
                "claims_per_cluster": claims_per_cluster,
                "atoms_per_cluster": len(atom_ids),
                "relationships_per_cluster": relationships_per_cluster,
                "sources_per_cluster": len(source_rows),
                "contradiction_edges": contradiction_edges,
                "qualification_edges": qualification_edges,
                "orphan_claims": len(orphan_claims),
                "orphan_atoms": orphan_atoms,
                "relationship_density": round(density, 4),
                "low_relationship_density": claims_per_cluster > 0 and density < 0.5,
            }
        )
    return {
        "schema_version": GRAPH_CONNECTION_METRICS_SCHEMA_VERSION,
        "clusters": cluster_metrics,
        "totals": {
            "claims": sum(item["claims_per_cluster"] for item in cluster_metrics),
            "atoms": sum(item["atoms_per_cluster"] for item in cluster_metrics),
            "relationships": sum(item["relationships_per_cluster"] for item in cluster_metrics),
            "sources": sum(item["sources_per_cluster"] for item in cluster_metrics),
            "orphan_claims": sum(item["orphan_claims"] for item in cluster_metrics),
            "orphan_atoms": sum(item["orphan_atoms"] for item in cluster_metrics),
        },
    }
