"""Build Research Atlas snapshot v0.1.0 from an existing research DB (ticket-279).

Read-only projection: maps public-safe cards, concept nodes, and relationship edges
into the atlas contract without writing public export files or mutating graph state.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from rge.contracts.atlas_snapshot_v0 import (
    ATLAS_RUN_LINEAGE_OPTIONAL_FIELDS,
    ATLAS_SNAPSHOT_SCHEMA_VERSION,
    AtlasSnapshot_v0_1,
    validate_atlas_snapshot,
)
from rge.db.repositories import (
    ConceptRepository,
    PublicCardRepository,
    public_card_record_to_export_dict,
    utc_now_iso,
)
from rge.modules.card_exporter import (
    FIXTURE_EXPORT_TIMESTAMP,
    GOLDEN_CARD_EXTRAS,
    GOLDEN_FIXTURE_SOURCE_COUNT,
    ensure_golden_public_cards,
    order_public_card_fields,
)
from rge.modules.domain_pack_loader import load_domain_pack
from rge.modules.research_planner import DEFAULT_RESEARCH_QUESTION_ID
from rge.safety.public_export_policy import (
    FORBIDDEN_KEY_SUBSTRINGS,
    curated_public_card,
    validate_public_card,
)

ATLAS_FIXTURE_SNAPSHOT_ID = "snap_creativity_fixture_v0_001"
ATLAS_FIXTURE_GENERATED_AT = "2026-06-16T00:00:00Z"
ATLAS_FIXTURE_SAFETY_AUDIT_ID = "audit_atlas_fixture_v0_001"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _dominant_evidence_type(conn: sqlite3.Connection, claim_ids: list[str]) -> str | None:
    if not claim_ids:
        return None
    placeholders = ",".join("?" * len(claim_ids))
    rows = conn.execute(
        f"""
        SELECT evidence_type FROM claims
        WHERE id IN ({placeholders}) AND status = 'accepted'
        """,
        claim_ids,
    ).fetchall()
    types = [row[0] for row in rows if row[0]]
    if not types:
        return None
    return max(set(types), key=types.count)


def _build_curated_cards(
    conn: sqlite3.Connection,
    *,
    fixture_mode: bool,
    repo_root: Path,
) -> list[dict[str, Any]]:
    ensure_golden_public_cards(conn)
    pack = load_domain_pack("creativity", root=repo_root)
    repo = PublicCardRepository(conn)
    cards: list[dict[str, Any]] = []
    for record in repo.list_public_safe(limit=100):
        extras = dict(GOLDEN_CARD_EXTRAS.get(record.id) or {})
        claim_ids = json.loads(record.claim_ids_json or "[]")
        if "evidence_type" not in extras:
            evidence_type = _dominant_evidence_type(conn, claim_ids)
            if evidence_type:
                extras["evidence_type"] = evidence_type
        if "public_run_timestamp" not in extras:
            extras["public_run_timestamp"] = record.created_at
        card = curated_public_card(
            public_card_record_to_export_dict(record, extras=extras)
        )
        if fixture_mode:
            card["source_count"] = GOLDEN_FIXTURE_SOURCE_COUNT
            stable_ts = FIXTURE_EXPORT_TIMESTAMP
            card["updated_at"] = stable_ts
            if "public_run_timestamp" not in extras:
                card["public_run_timestamp"] = stable_ts
        violations = validate_public_card(
            card,
            template_required_fields=pack.card_templates.required_fields_by_type.get(
                str(card.get("type", "")).strip().casefold(),
                (),
            ),
        )
        if violations:
            raise ValueError(
                "Atlas card projection blocked by safety policy: "
                + "; ".join(violations[:3])
            )
        cards.append(order_public_card_fields(card))
    cards.sort(key=lambda item: item["id"])
    return cards


def _build_concept_nodes(conn: sqlite3.Connection, domain_pack: str) -> list[dict[str, Any]]:
    concepts = ConceptRepository(conn).list_for_domain(domain_pack)
    nodes: list[dict[str, Any]] = []
    for concept in concepts:
        if concept.status not in {"candidate", "active", "accepted"}:
            continue
        nodes.append(
            {
                "id": concept.id,
                "node_type": "concept",
                "label": concept.label,
                "domain_pack": domain_pack,
            }
        )
    nodes.sort(key=lambda item: item["id"])
    return nodes


def _build_relationship_edges(conn: sqlite3.Connection, domain_pack: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT r.id, r.predicate, r.scope, r.confidence, r.status,
               sub.id AS subject_id, sub.label AS subject_label,
               obj.id AS object_id, obj.label AS object_label
        FROM relationships r
        JOIN concepts sub ON sub.id = r.subject_concept_id
        JOIN concepts obj ON obj.id = r.object_concept_id
        WHERE r.status = 'active' AND r.domain = ?
        ORDER BY r.id
        """,
        (domain_pack,),
    ).fetchall()
    edges: list[dict[str, Any]] = []
    for row in rows:
        edges.append(
            {
                "id": row["id"],
                "edge_type": "relationship",
                "predicate": row["predicate"],
                "source_node_id": row["subject_id"],
                "target_node_id": row["object_id"],
                "source_label": row["subject_label"],
                "target_label": row["object_label"],
                "scope": row["scope"],
                "confidence": row["confidence"],
            }
        )
    return edges


def _build_domains(domain_pack: str) -> list[dict[str, Any]]:
    return [
        {
            "id": domain_pack,
            "label": domain_pack,
            "role": "primary",
        }
    ]


_LINEAGE_KEY_ALLOWLIST = frozenset(ATLAS_RUN_LINEAGE_OPTIONAL_FIELDS)


def _contract_question_lineage(
    conn: sqlite3.Connection,
    contract_id: str | None,
) -> dict[str, Any]:
    if not contract_id:
        return {}
    contract = conn.execute(
        "SELECT id FROM research_contracts WHERE id = ?",
        (contract_id,),
    ).fetchone()
    if contract is None:
        return {}
    queue_row = conn.execute(
        """
        SELECT research_question_id FROM research_queue
        WHERE contract_id = ? AND item_type = 'question'
        ORDER BY priority_score DESC, created_at
        LIMIT 1
        """,
        (contract_id,),
    ).fetchone()
    question_id = (
        str(queue_row["research_question_id"]).strip()
        if queue_row and queue_row["research_question_id"]
        else DEFAULT_RESEARCH_QUESTION_ID
    )
    return {"research_question_id": question_id}


def _is_root_run_for_contract(
    conn: sqlite3.Connection,
    run_id: str,
    contract_id: str,
) -> bool:
    first = conn.execute(
        """
        SELECT id FROM research_runs
        WHERE contract_id = ?
        ORDER BY started_at, id
        LIMIT 1
        """,
        (contract_id,),
    ).fetchone()
    return first is not None and first["id"] == run_id


def _cluster_report_row_for_prior_run(
    conn: sqlite3.Connection,
    prior_run_id: str,
) -> sqlite3.Row | None:
    row = conn.execute(
        """
        SELECT id, report_json FROM cluster_reports
        WHERE run_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (prior_run_id,),
    ).fetchone()
    if row is not None:
        return row
    return conn.execute(
        """
        SELECT id, report_json FROM cluster_reports
        WHERE run_id IS NULL
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """
    ).fetchone()


def _spawn_lineage_for_run(
    conn: sqlite3.Connection,
    *,
    run_id: str,
    contract_id: str,
) -> dict[str, Any]:
    if _is_root_run_for_contract(conn, run_id, contract_id):
        return {"parent_question_id": None}

    prior_run = conn.execute(
        """
        SELECT id FROM research_runs
        WHERE contract_id = ? AND id != ?
        ORDER BY started_at, id
        LIMIT 1
        """,
        (contract_id, run_id),
    ).fetchone()
    if prior_run is None:
        return {"parent_question_id": DEFAULT_RESEARCH_QUESTION_ID}

    cluster_row = _cluster_report_row_for_prior_run(conn, str(prior_run["id"]))
    if cluster_row is None:
        return {"parent_question_id": DEFAULT_RESEARCH_QUESTION_ID}

    report = json.loads(cluster_row["report_json"] or "{}")
    claim_ids = sorted(str(claim_id) for claim_id in (report.get("linked_claim_ids") or []))
    reason_row = conn.execute(
        """
        SELECT reason FROM research_queue
        WHERE contract_id = ? AND item_type = 'question' AND status = 'queued'
        ORDER BY priority_score DESC, created_at
        LIMIT 1
        """,
        (contract_id,),
    ).fetchone()
    lineage: dict[str, Any] = {
        "parent_question_id": DEFAULT_RESEARCH_QUESTION_ID,
        "spawned_from_report_id": cluster_row["id"],
    }
    if claim_ids:
        lineage["spawned_from_claim_ids"] = claim_ids
    if reason_row and reason_row["reason"]:
        lineage["spawn_reason"] = str(reason_row["reason"])
    return lineage


def _build_runs(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, topic, domain_pack, mode, status, contract_id
        FROM research_runs
        ORDER BY started_at, id
        """
    ).fetchall()
    runs: list[dict[str, Any]] = []
    for row in rows:
        entry: dict[str, Any] = {
            "run_id": row["id"],
            "topic": row["topic"],
            "domain_pack": row["domain_pack"],
            "mode": row["mode"],
            "status": row["status"],
        }
        contract_id = row["contract_id"]
        lineage = _contract_question_lineage(conn, contract_id)
        if lineage and contract_id:
            lineage.update(
                _spawn_lineage_for_run(conn, run_id=row["id"], contract_id=contract_id)
            )
            entry.update(lineage)
        runs.append(entry)
    return runs


def _build_report_summaries(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT run_id, report_json
        FROM run_reports
        ORDER BY created_at, id
        """
    ).fetchall()
    summaries: list[dict[str, Any]] = []
    for row in rows:
        report = json.loads(row["report_json"])
        summaries.append(
            {
                "report_type": report.get("report_type", "run_report"),
                "schema_version": report.get("schema_version", "0.1.0"),
                "run_id": report.get("run_id", row["run_id"]),
                "status": report.get("status", "informational"),
            }
        )
    return summaries


def _build_cluster_summaries(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, run_id, cluster_label
        FROM cluster_reports
        ORDER BY created_at, id
        """
    ).fetchall()
    return [
        {
            "cluster_id": row["id"],
            "cluster_label": row["cluster_label"],
            "run_id": row["run_id"],
        }
        for row in rows
    ]


def _iter_keys(value: object, prefix: str = "") -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            keys.append(path)
            keys.extend(_iter_keys(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            keys.extend(_iter_keys(item, f"{prefix}[{index}]"))
    return keys


def assert_no_private_fields(snapshot: dict[str, Any]) -> list[str]:
    """Return violations when forbidden export key fragments appear in snapshot keys."""
    violations: list[str] = []
    for key_path in _iter_keys(snapshot):
        leaf = key_path.rsplit(".", 1)[-1]
        leaf = leaf.split("[", 1)[0]
        if leaf in _LINEAGE_KEY_ALLOWLIST:
            continue
        lowered = leaf.casefold()
        if any(fragment in lowered for fragment in FORBIDDEN_KEY_SUBSTRINGS):
            violations.append(f"forbidden snapshot key: {key_path}")
    return violations


def build_atlas_snapshot_from_db(
    conn: sqlite3.Connection,
    *,
    topic: str,
    primary_question: str | None = None,
    domain_pack: str = "creativity",
    snapshot_id: str | None = None,
    generated_at: str | None = None,
    safety_audit_id: str | None = None,
    fixture_mode: bool = False,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Project a validated atlas snapshot dict from the current DB state."""
    root = repo_root or _repo_root()
    resolved_question = primary_question or topic
    cards = _build_curated_cards(conn, fixture_mode=fixture_mode, repo_root=root)
    nodes = _build_concept_nodes(conn, domain_pack)
    edges = _build_relationship_edges(conn, domain_pack)

    if fixture_mode:
        resolved_generated_at = generated_at or ATLAS_FIXTURE_GENERATED_AT
        resolved_snapshot_id = snapshot_id or ATLAS_FIXTURE_SNAPSHOT_ID
        resolved_audit_id = safety_audit_id or ATLAS_FIXTURE_SAFETY_AUDIT_ID
    else:
        resolved_generated_at = generated_at or utc_now_iso()
        resolved_snapshot_id = snapshot_id or f"snap_{resolved_generated_at.replace(':', '').replace('-', '')}"
        resolved_audit_id = safety_audit_id or "audit_atlas_projection_pending"

    snapshot_dict: dict[str, Any] = {
        "schema_version": ATLAS_SNAPSHOT_SCHEMA_VERSION,
        "generated_at": resolved_generated_at,
        "snapshot_id": resolved_snapshot_id,
        "root": {
            "topic": topic,
            "primary_question": resolved_question,
            "domain_pack": domain_pack,
        },
        "domains": _build_domains(domain_pack),
        "runs": _build_runs(conn),
        "nodes": nodes,
        "edges": edges,
        "clusters": _build_cluster_summaries(conn),
        "reports": _build_report_summaries(conn),
        "cards": cards,
        "safety": {
            "public_safe": True,
            "safety_audit_id": resolved_audit_id,
        },
    }

    leak_violations = assert_no_private_fields(snapshot_dict)
    if leak_violations:
        raise ValueError(
            "Atlas snapshot projection blocked by private-field policy: "
            + "; ".join(leak_violations[:5])
        )

    validate_atlas_snapshot(snapshot_dict)
    return snapshot_dict


def export_atlas_snapshot_to_path(
    conn: sqlite3.Connection,
    output_path: Path,
    *,
    topic: str,
    primary_question: str | None = None,
    domain_pack: str = "creativity",
    snapshot_id: str | None = None,
    generated_at: str | None = None,
    safety_audit_id: str | None = None,
    fixture_mode: bool = False,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build, validate, and write an atlas snapshot JSON file (operator-private)."""
    snapshot = build_atlas_snapshot_from_db(
        conn,
        topic=topic,
        primary_question=primary_question,
        domain_pack=domain_pack,
        snapshot_id=snapshot_id,
        generated_at=generated_at,
        safety_audit_id=safety_audit_id,
        fixture_mode=fixture_mode,
        repo_root=repo_root,
    )
    leak_violations = assert_no_private_fields(snapshot)
    if leak_violations:
        raise ValueError(
            "Atlas snapshot export blocked by private-field policy: "
            + "; ".join(leak_violations[:5])
        )
    validate_atlas_snapshot(snapshot)
    payload = json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(payload, encoding="utf-8")
    return {
        "status": "completed",
        "command": "export-atlas-snapshot",
        "output_path": str(output_path),
        "snapshot_id": snapshot["snapshot_id"],
        "schema_version": snapshot["schema_version"],
        "byte_length": len(payload.encode("utf-8")),
    }


def build_atlas_snapshot_model(
    conn: sqlite3.Connection,
    **kwargs: Any,
) -> AtlasSnapshot_v0_1:
    return validate_atlas_snapshot(build_atlas_snapshot_from_db(conn, **kwargs))
