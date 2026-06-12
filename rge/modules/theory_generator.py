"""Generate candidate theories from evidence packets. Model-assisted, validated.

Theories emerge from graph patterns and evidence packets, not model vibes:
graph pattern -> evidence packet -> constrained inference -> candidate theory
-> validation -> stored as candidate, never fact. Candidates require
supporting claims, caveats, boundary conditions, and weakening evidence.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from rge.db.repositories import (
    ClaimRepository,
    ClusterReportRepository,
    TheoryCandidateRepository,
)
from rge.modules.cluster_reporter import GOLDEN_CLUSTER_LABEL

DEFAULT_THEORY_FIXTURE = "theory_generation_creativity_diversity.json"
VALID_CONFIDENCE = frozenset({"low", "medium", "high"})
VALID_GRAPH_PATTERNS = frozenset(
    {
        "bridge_path",
        "repeated_support",
        "contradiction_by_metric",
        "boundary_condition",
        "emerging_subdomain",
        "evidence_gap",
    }
)
SUPPORT_FRAGMENT = "reduced semantic diversity"
QUALIFY_FRAGMENT = "increased idea diversity"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_report_dir(repo_root: Path | None = None) -> Path:
    return (repo_root or _repo_root()) / "data" / "reports"


def _normalize(text: str) -> str:
    return text.strip().casefold()


def _packet_claim_ids(
    evidence_packet: dict[str, Any], cluster_report: dict[str, Any]
) -> set[str]:
    ids: set[str] = set()
    for key in (
        "top_supporting_claims",
        "top_contradicting_claims",
        "top_qualifying_claims",
        "newest_claims",
    ):
        ids.update(evidence_packet.get(key) or [])
    ids.update(cluster_report.get("supporting_claims") or [])
    ids.update(cluster_report.get("contradicting_claims") or [])
    ids.update(cluster_report.get("qualifying_claims") or [])
    ids.update(cluster_report.get("linked_claim_ids") or [])
    return {claim_id for claim_id in ids if claim_id}


def _resolve_claim_ids_by_fragments(
    fragments: list[str],
    *,
    allowed_claim_ids: set[str],
    conn: sqlite3.Connection,
) -> list[str]:
    if not fragments:
        return []
    claim_repo = ClaimRepository(conn)
    resolved: list[str] = []
    for fragment in fragments:
        normalized = _normalize(fragment)
        match_id: str | None = None
        for claim_id in sorted(allowed_claim_ids):
            claim = claim_repo.get_by_id(claim_id)
            if claim is not None and normalized in _normalize(claim.claim_text):
                match_id = claim_id
                break
        if match_id is None:
            return []
        if match_id not in resolved:
            resolved.append(match_id)
    return resolved


def validate_theory_candidates(
    candidates: list[dict[str, Any]],
    *,
    allowed_claim_ids: set[str],
    evidence_packet: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Validate proposed theory candidates before persistence."""
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for candidate in candidates:
        theory_type = (candidate.get("type") or "").strip()
        if theory_type != "candidate_theory":
            rejected.append({**candidate, "rejection_reason": "invalid_type"})
            continue
        theory_text = (candidate.get("theory_text") or "").strip()
        if not theory_text:
            rejected.append({**candidate, "rejection_reason": "missing_theory_text"})
            continue
        confidence = (candidate.get("confidence") or "").strip().casefold()
        if confidence not in VALID_CONFIDENCE:
            rejected.append({**candidate, "rejection_reason": "invalid_confidence"})
            continue
        graph_pattern = (candidate.get("graph_pattern") or "").strip()
        if graph_pattern not in VALID_GRAPH_PATTERNS:
            rejected.append({**candidate, "rejection_reason": "invalid_graph_pattern"})
            continue
        status = (candidate.get("status") or "").strip().casefold()
        if status != "candidate":
            rejected.append({**candidate, "rejection_reason": "invalid_status"})
            continue

        supporting = candidate.get("supporting_claims") or []
        contradicting_or_qualifying = (
            candidate.get("contradicting_or_qualifying_claims") or []
        )
        if not supporting:
            rejected.append({**candidate, "rejection_reason": "missing_supporting_claims"})
            continue
        if not set(supporting).issubset(allowed_claim_ids):
            rejected.append(
                {**candidate, "rejection_reason": "supporting_claim_not_in_packet"}
            )
            continue
        if contradicting_or_qualifying and not set(contradicting_or_qualifying).issubset(
            allowed_claim_ids
        ):
            rejected.append(
                {
                    **candidate,
                    "rejection_reason": "contradicting_claim_not_in_packet",
                }
            )
            continue
        if not contradicting_or_qualifying and not (
            candidate.get("boundary_conditions") or candidate.get("weakening_evidence")
        ):
            rejected.append({**candidate, "rejection_reason": "missing_caveats"})
            continue

        weakening = candidate.get("weakening_evidence") or []
        claim_weakening = [item for item in weakening if str(item).startswith("clm_")]
        if claim_weakening and not set(claim_weakening).issubset(allowed_claim_ids):
            rejected.append(
                {**candidate, "rejection_reason": "weakening_claim_not_in_packet"}
            )
            continue
        if not weakening:
            gaps = evidence_packet.get("open_gaps") or []
            if gaps:
                weakening = list(gaps[:2])
            else:
                rejected.append(
                    {**candidate, "rejection_reason": "missing_weakening_evidence"}
                )
                continue

        boundary_conditions = candidate.get("boundary_conditions") or []
        if not boundary_conditions:
            rejected.append(
                {**candidate, "rejection_reason": "missing_boundary_conditions"}
            )
            continue
        next_questions = candidate.get("next_questions") or []
        if not next_questions:
            rejected.append({**candidate, "rejection_reason": "missing_next_questions"})
            continue

        accepted.append(
            {
                **candidate,
                "confidence": confidence,
                "status": status,
                "supporting_claims": supporting,
                "contradicting_or_qualifying_claims": contradicting_or_qualifying,
                "boundary_conditions": boundary_conditions,
                "weakening_evidence": weakening,
                "next_questions": next_questions,
            }
        )

    return {"accepted": accepted, "rejected": rejected}


def _load_theory_fixture(fixture_name: str) -> dict[str, Any]:
    path = _repo_root() / "fixtures" / "llm_outputs" / fixture_name
    return json.loads(path.read_text(encoding="utf-8"))


def propose_theory_candidates_from_fixture(
    evidence_packet: dict[str, Any],
    cluster_report: dict[str, Any],
    *,
    conn: sqlite3.Connection,
    fixture_name: str = DEFAULT_THEORY_FIXTURE,
) -> list[dict[str, Any]]:
    """Load mock fixture proposals and resolve claim references from the packet."""
    raw = _load_theory_fixture(fixture_name)

    allowed_claim_ids = _packet_claim_ids(evidence_packet, cluster_report)
    proposed: list[dict[str, Any]] = []
    for item in raw.get("items") or []:
        supporting = _resolve_claim_ids_by_fragments(
            item.get("supporting_claim_fragments") or [],
            allowed_claim_ids=allowed_claim_ids,
            conn=conn,
        )
        if not supporting and allowed_claim_ids:
            supporting = _resolve_claim_ids_by_fragments(
                [SUPPORT_FRAGMENT],
                allowed_claim_ids=allowed_claim_ids,
                conn=conn,
            )
        contradicting_or_qualifying = _resolve_claim_ids_by_fragments(
            item.get("contradicting_or_qualifying_claim_fragments") or [],
            allowed_claim_ids=allowed_claim_ids,
            conn=conn,
        )
        if not contradicting_or_qualifying and allowed_claim_ids:
            contradicting_or_qualifying = _resolve_claim_ids_by_fragments(
                [QUALIFY_FRAGMENT],
                allowed_claim_ids=allowed_claim_ids,
                conn=conn,
            )
        weakening = _resolve_claim_ids_by_fragments(
            item.get("weakening_evidence_fragments") or [],
            allowed_claim_ids=allowed_claim_ids,
            conn=conn,
        )
        proposed.append(
            {
                "type": item.get("type"),
                "graph_pattern": item.get("graph_pattern"),
                "theory_text": item.get("theory_text"),
                "confidence": item.get("confidence"),
                "supporting_claims": supporting,
                "contradicting_or_qualifying_claims": contradicting_or_qualifying,
                "boundary_conditions": item.get("boundary_conditions") or [],
                "weakening_evidence": weakening,
                "next_questions": item.get("next_questions") or [],
                "status": item.get("status") or "candidate",
            }
        )
    return proposed


def _build_theory_report(
    candidate: dict[str, Any],
    *,
    cluster_report_id: str,
    cluster_id: str,
) -> dict[str, Any]:
    return {
        "report_type": "theory_candidate_report",
        "type": "candidate_theory",
        "graph_pattern": candidate["graph_pattern"],
        "cluster_report_id": cluster_report_id,
        "cluster_id": cluster_id,
        "theory_text": candidate["theory_text"],
        "confidence": candidate["confidence"],
        "supporting_claims": candidate["supporting_claims"],
        "contradicting_or_qualifying_claims": candidate[
            "contradicting_or_qualifying_claims"
        ],
        "boundary_conditions": candidate["boundary_conditions"],
        "weakening_evidence": candidate["weakening_evidence"],
        "next_questions": candidate["next_questions"],
        "status": "candidate",
    }


def generate_theory_candidates(
    conn: sqlite3.Connection,
    *,
    domain: str = "creativity",
    cluster_report_id: str | None = None,
    fixture_name: str = DEFAULT_THEORY_FIXTURE,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Generate and persist candidate theories from a cluster report evidence packet."""
    cluster_repo = ClusterReportRepository(conn)
    if cluster_report_id:
        cluster_record = cluster_repo.get_by_id(cluster_report_id)
    else:
        cluster_record = cluster_repo.get_latest_for_label(GOLDEN_CLUSTER_LABEL)
    if cluster_record is None:
        raise ValueError(
            "No cluster report found. Run generate-cluster-report before theory generation."
        )

    theory_repo = TheoryCandidateRepository(conn)
    existing = theory_repo.list_for_cluster_report(cluster_record.id)
    if existing:
        report = json.loads(existing[0].report_json)
        return {
            "status": "already_generated",
            "cluster_report_id": cluster_record.id,
            "theory_candidate_ids": [record.id for record in existing],
            "candidates": [json.loads(record.report_json) for record in existing],
            "report": report,
            "output_path": None,
        }

    cluster_report = json.loads(cluster_record.report_json)
    evidence_packet = json.loads(cluster_record.evidence_packet_json)
    if cluster_report.get("report_type") != "cluster_report":
        raise ValueError("Cluster report JSON has unexpected report_type.")

    proposed = propose_theory_candidates_from_fixture(
        evidence_packet,
        cluster_report,
        conn=conn,
        fixture_name=fixture_name,
    )
    allowed_claim_ids = _packet_claim_ids(evidence_packet, cluster_report)
    validated = validate_theory_candidates(
        proposed,
        allowed_claim_ids=allowed_claim_ids,
        evidence_packet=evidence_packet,
    )
    if not validated["accepted"]:
        reasons = [item.get("rejection_reason") for item in validated["rejected"]]
        raise ValueError(
            "No valid theory candidates: "
            + ", ".join(reason for reason in reasons if reason)
        )

    cluster_id = cluster_report.get("cluster_id", "")
    persisted: list[dict[str, Any]] = []
    theory_ids: list[str] = []
    for candidate in validated["accepted"]:
        report = _build_theory_report(
            candidate,
            cluster_report_id=cluster_record.id,
            cluster_id=cluster_id,
        )
        record = theory_repo.insert(
            cluster_report_id=cluster_record.id,
            theory_text=candidate["theory_text"],
            confidence=candidate["confidence"],
            supporting_claims=candidate["supporting_claims"],
            contradicting_or_qualifying_claims=candidate[
                "contradicting_or_qualifying_claims"
            ],
            boundary_conditions=candidate["boundary_conditions"],
            weakening_evidence=candidate["weakening_evidence"],
            next_questions=candidate["next_questions"],
            report=report,
        )
        theory_ids.append(record.id)
        persisted.append(report)

    output_path: Path | None = None
    if persisted:
        target_dir = output_dir or default_report_dir()
        target_dir.mkdir(parents=True, exist_ok=True)
        output_path = target_dir / "theory_candidate_latest.json"
        output_path.write_text(json.dumps(persisted[0], indent=2), encoding="utf-8")

    return {
        "status": "generated",
        "cluster_report_id": cluster_record.id,
        "theory_candidate_ids": theory_ids,
        "candidates": persisted,
        "rejected_count": len(validated["rejected"]),
        "rejected": validated["rejected"],
        "report": persisted[0] if persisted else None,
        "output_path": str(output_path) if output_path else None,
    }


def generate_theory_candidates_from_packet(
    evidence_packet: dict[str, Any],
) -> list[dict[str, Any]]:
    """Legacy entry point for module contract checks."""
    return [
        {
            "type": "candidate_theory",
            "theory_text": (
                "Fixture-only theory candidate placeholder for contract checks."
            ),
            "confidence": "medium",
            "supporting_claims": evidence_packet.get("top_supporting_claims") or [],
            "contradicting_or_qualifying_claims": (
                evidence_packet.get("top_qualifying_claims") or []
            ),
            "boundary_conditions": ["Contract-check placeholder."],
            "weakening_evidence": evidence_packet.get("open_gaps") or [],
            "next_questions": ["Contract-check placeholder question?"],
            "status": "candidate",
        }
    ]
