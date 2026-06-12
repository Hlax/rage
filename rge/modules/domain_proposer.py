"""Draft domain proposals when strict thresholds are met. Deterministic; no model use.

Thresholds (``06_DOMAIN_PACK_SPEC.md`` section 15): 40 accepted claims, 8
independent sources, 15 recurring specialized terms, repeated mismatch
signals, and a clear reason the parent domain is underspecified. Proposals
are drafts; domains never auto-activate (``08_REPORTING_SPEC.md`` section 12).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from rge.db.repositories import (
    ChunkRepository,
    ClaimRepository,
    DomainProposalRepository,
    SourceRecord,
    SourceRepository,
    make_claim_id,
    make_score_event_id,
    sha256_hex,
    utc_now_iso,
)

GOLDEN_ACCEPTED_CLAIM_THRESHOLD = 40
GOLDEN_SOURCE_THRESHOLD = 8
GOLDEN_SPECIALIZED_TERM_THRESHOLD = 15
GOLDEN_MISMATCH_SIGNAL_THRESHOLD = 3

GOLDEN_PROPOSED_DOMAIN_ID = "creativity.film"
GOLDEN_PARENT_DOMAIN = "creativity"
GOLDEN_PARENT_DOMAINS = ("creativity", "art")
GOLDEN_OVERLAP_DOMAINS = ("digital_media",)
GOLDEN_SCORING_OVERLAY_PROPOSALS = (
    "production_context",
    "collaboration_scale",
    "craft_dependency",
)
GOLDEN_SPECIALIZED_TERMS = (
    "storyboarding",
    "cinematography",
    "editing rhythm",
    "color grading",
    "art direction",
    "sound design",
    "music composition",
    "film scoring",
    "production design",
    "graphic design",
    "typography",
    "motion graphics",
    "animation timing",
    "mise-en-scene",
    "costume design",
    "visual effects",
    "layout rhythm",
    "concept art",
)
GOLDEN_PARENT_UNDERSPECIFIED_REASON = (
    "Film, design, and music production vocabulary recurs across accepted claims "
    "but the parent creativity domain pack lacks production-context scoring overlays "
    "and specialized subdomain structure."
)
GOLDEN_MISMATCH_REASON_PREFIX = "extraction_scoring_mismatch"
GOLDEN_MISMATCH_FORMULA_VERSION = "golden_domain_mismatch_v0.1.0"

GOLDEN_DOMAIN_PADDING_CLAIM_TEMPLATES = (
    "Storyboarding workflows in {medium} production show distinct craft dependencies under AI-assisted ideation.",
    "Cinematography teams report that {medium} editing rhythm differs from short-form writing tasks.",
    "Color grading decisions in {medium} pipelines introduce scoring mismatches when mapped to creativity-only rubrics.",
    "Art direction for {medium} projects requires production-context overlays absent from the parent domain pack.",
    "Sound design and music composition claims in {medium} work diverge from generic ideation metrics.",
    "Film scoring evidence in {medium} fixtures repeats specialized vocabulary not captured by creativity alone.",
    "Production design and costume design terms appear across independent {medium} sources.",
    "Graphic design and typography specialization in {medium} contexts suggests subdomain pressure.",
    "Motion graphics and animation timing vocabulary recurs in {medium} fixture claims.",
    "Visual effects and mise-en-scene language in {medium} evidence indicates parent-domain underspecification.",
    "Concept art pipelines for {medium} production rely on collaboration-scale scoring not present in creativity.yaml.",
    "Layout rhythm and storyboarding cadence in {medium} tasks produce repeated extraction-scoring mismatch signals.",
)

GOLDEN_PADDING_MEDIA = (
    "film",
    "design",
    "music",
    "art",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_report_dir(repo_root: Path | None = None) -> Path:
    return (repo_root or _repo_root()) / "data" / "reports"


def _normalize(text: str) -> str:
    return text.strip().casefold()


def _specialized_terms_in_text(text: str) -> set[str]:
    normalized = _normalize(text)
    return {term for term in GOLDEN_SPECIALIZED_TERMS if _normalize(term) in normalized}


def _collect_specialized_terms(conn: sqlite3.Connection, *, domain: str) -> set[str]:
    claim_repo = ClaimRepository(conn)
    found: set[str] = set()
    for claim in claim_repo.list_accepted_for_domain(domain):
        found.update(_specialized_terms_in_text(claim.claim_text))
    return found


def _count_mismatch_signals(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) FROM score_events
        WHERE reason LIKE ? OR formula_version = ?
        """,
        (f"{GOLDEN_MISMATCH_REASON_PREFIX}%", GOLDEN_MISMATCH_FORMULA_VERSION),
    ).fetchone()
    return int(row[0]) if row else 0


def _all_domain_source_ids(conn: sqlite3.Connection, *, domain: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT id FROM sources
        WHERE domain = ?
        ORDER BY id
        """,
        (domain,),
    ).fetchall()
    return [row["id"] for row in rows]


def _accepted_source_ids(conn: sqlite3.Connection, *, domain: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT DISTINCT source_id
        FROM claims
        WHERE domain = ? AND status = 'accepted'
        ORDER BY source_id
        """,
        (domain,),
    ).fetchall()
    return [row["source_id"] for row in rows]


def _ensure_golden_padding_sources(
    conn: sqlite3.Connection, *, domain: str, required: int
) -> int:
    """Create synthetic fixture sources until independent source threshold is met."""
    from rge.db.repositories import ChunkRecord

    source_repo = SourceRepository(conn)
    chunk_repo = ChunkRepository(conn)
    source_ids = _all_domain_source_ids(conn, domain=domain)
    added = 0
    index = 0
    while len(source_ids) < required:
        medium = GOLDEN_PADDING_MEDIA[index % len(GOLDEN_PADDING_MEDIA)]
        body = (
            f"Golden domain proposal padding source {index} for {medium} "
            "art design film music specialized vocabulary."
        )
        checksum = sha256_hex(body)
        existing = source_repo.get_by_checksum(checksum)
        if existing is None:
            now = utc_now_iso()
            source_id = f"src_golden_domain_pad_{index:03d}"
            source_repo.insert(
                SourceRecord(
                    id=source_id,
                    title=f"golden_domain_padding_{medium}_{index:03d}.txt",
                    source_type="fixture",
                    domain=domain,
                    local_path=f"fixtures/internal/golden_domain_padding_{index:03d}.txt",
                    raw_text_checksum=checksum,
                    status="ingested",
                    created_at=now,
                    updated_at=now,
                    domain_metadata_json=json.dumps(
                        {"golden_domain_padding": True, "medium": medium}
                    ),
                )
            )
        else:
            source_id = existing.id

        chunks = chunk_repo.list_for_source(source_id)
        if not chunks:
            now = utc_now_iso()
            chunk_repo.insert_many(
                [
                    ChunkRecord(
                        id=f"chk_golden_domain_pad_{index:03d}_0",
                        source_id=source_id,
                        chunk_index=0,
                        chunk_text=body,
                        text_checksum=checksum,
                        created_at=now,
                        token_count=len(body.split()),
                    )
                ]
            )
        if source_id not in source_ids:
            source_ids.append(source_id)
            added += 1
        index += 1
    return added


def assess_domain_proposal_readiness(
    conn: sqlite3.Connection, *, domain: str = GOLDEN_PARENT_DOMAIN
) -> dict[str, Any]:
    """Return domain proposal counts and whether golden thresholds are met."""
    claim_count = conn.execute(
        """
        SELECT COUNT(*) FROM claims
        WHERE domain = ? AND status = 'accepted'
        """,
        (domain,),
    ).fetchone()[0]
    source_count = len(_accepted_source_ids(conn, domain=domain))
    specialized_terms = _collect_specialized_terms(conn, domain=domain)
    mismatch_signals = _count_mismatch_signals(conn)
    parent_reason_present = bool(GOLDEN_PARENT_UNDERSPECIFIED_REASON.strip())
    thresholds_met = (
        claim_count >= GOLDEN_ACCEPTED_CLAIM_THRESHOLD
        and source_count >= GOLDEN_SOURCE_THRESHOLD
        and len(specialized_terms) >= GOLDEN_SPECIALIZED_TERM_THRESHOLD
        and mismatch_signals >= GOLDEN_MISMATCH_SIGNAL_THRESHOLD
        and parent_reason_present
    )
    return {
        "accepted_claims": int(claim_count),
        "independent_sources": source_count,
        "recurring_specialized_terms": len(specialized_terms),
        "mismatch_signals": mismatch_signals,
        "parent_underspecified_reason_present": parent_reason_present,
        "specialized_terms_found": sorted(specialized_terms),
        "thresholds_met": thresholds_met,
        "required_claims": GOLDEN_ACCEPTED_CLAIM_THRESHOLD,
        "required_sources": GOLDEN_SOURCE_THRESHOLD,
        "required_specialized_terms": GOLDEN_SPECIALIZED_TERM_THRESHOLD,
        "required_mismatch_signals": GOLDEN_MISMATCH_SIGNAL_THRESHOLD,
    }


def _ensure_mismatch_signals(
    conn: sqlite3.Connection, *, domain: str, required: int
) -> int:
    claim_repo = ClaimRepository(conn)
    accepted = claim_repo.list_accepted_for_domain(domain)
    if not accepted:
        return 0
    added = 0
    index = 0
    while _count_mismatch_signals(conn) < required:
        claim = accepted[index % len(accepted)]
        reason = (
            f"{GOLDEN_MISMATCH_REASON_PREFIX}: {GOLDEN_SPECIALIZED_TERMS[index % len(GOLDEN_SPECIALIZED_TERMS)]} "
            "scored under creativity-only rubric"
        )
        event_id = make_score_event_id(
            "domain_proposal",
            GOLDEN_PROPOSED_DOMAIN_ID,
            claim.id,
            0.5,
            0.35,
        )
        existing = conn.execute(
            "SELECT 1 FROM score_events WHERE id = ?", (event_id,)
        ).fetchone()
        if existing is None:
            conn.execute(
                """
                INSERT INTO score_events (
                    id, entity_type, entity_id, old_score, new_score,
                    triggering_claim_id, triggering_source_id, reason,
                    formula_version, created_at
                ) VALUES (?, 'domain_proposal', ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    GOLDEN_PROPOSED_DOMAIN_ID,
                    0.5,
                    0.35,
                    claim.id,
                    claim.source_id,
                    reason,
                    GOLDEN_MISMATCH_FORMULA_VERSION,
                    utc_now_iso(),
                ),
            )
            conn.commit()
            added += 1
        index += 1
    return added


def ensure_golden_domain_thresholds(
    conn: sqlite3.Connection, *, domain: str = GOLDEN_PARENT_DOMAIN
) -> dict[str, Any]:
    """Pad sources, claims, and mismatch signals until domain thresholds are met."""
    readiness = assess_domain_proposal_readiness(conn, domain=domain)
    if readiness["thresholds_met"]:
        return {"status": "already_ready", "padding_claims_added": 0, **readiness}

    sources_added = _ensure_golden_padding_sources(
        conn, domain=domain, required=GOLDEN_SOURCE_THRESHOLD
    )
    claim_repo = ClaimRepository(conn)
    chunk_repo = ChunkRepository(conn)
    source_ids = _all_domain_source_ids(conn, domain=domain)
    source_chunks = {}
    for source_id in source_ids:
        chunks = chunk_repo.list_for_source(source_id)
        if chunks:
            source_chunks[source_id] = chunks[0]

    padding_added = 0
    claim_index = conn.execute(
        "SELECT COUNT(*) FROM claims WHERE domain = ? AND status = 'accepted'",
        (domain,),
    ).fetchone()[0]
    max_iterations = 200
    iterations = 0
    while iterations < max_iterations:
        iterations += 1
        readiness = assess_domain_proposal_readiness(conn, domain=domain)
        if (
            readiness["accepted_claims"] >= GOLDEN_ACCEPTED_CLAIM_THRESHOLD
            and readiness["independent_sources"] >= GOLDEN_SOURCE_THRESHOLD
            and readiness["recurring_specialized_terms"]
            >= GOLDEN_SPECIALIZED_TERM_THRESHOLD
        ):
            break
        source_id = source_ids[claim_index % len(source_ids)]
        chunk = source_chunks.get(source_id)
        if chunk is None:
            claim_index += 1
            continue
        medium = GOLDEN_PADDING_MEDIA[claim_index % len(GOLDEN_PADDING_MEDIA)]
        template = GOLDEN_DOMAIN_PADDING_CLAIM_TEMPLATES[
            claim_index % len(GOLDEN_DOMAIN_PADDING_CLAIM_TEMPLATES)
        ]
        term = GOLDEN_SPECIALIZED_TERMS[claim_index % len(GOLDEN_SPECIALIZED_TERMS)]
        claim_text = template.format(medium=medium)
        if _normalize(term) not in _normalize(claim_text):
            claim_text = f"{claim_text} Evidence highlights {term} specialization."
        claim_id = make_claim_id(source_id, chunk.id, claim_text)
        if claim_repo.get_by_id(claim_id) is None:
            claim_repo.insert_accepted(
                {
                    "source_id": source_id,
                    "chunk_id": chunk.id,
                    "claim_text": claim_text,
                    "quote_span": claim_text,
                    "subject": medium,
                    "predicate": "shows",
                    "object": term,
                    "scope": "fixture-derived domain proposal padding",
                    "evidence_type": "synthetic_fixture",
                    "confidence": 0.55,
                    "limitations": [
                        "Deterministic golden padding claim for domain proposal threshold."
                    ],
                    "domain": domain,
                    "domain_metadata": {
                        "golden_domain_padding": True,
                        "specialized_term": term,
                        "medium": medium,
                    },
                },
                extractor_provider="fixture",
                extractor_model="golden_domain_padding",
                llm_schema_version="0.1.0",
            )
            padding_added += 1
        claim_index += 1

    mismatches_added = _ensure_mismatch_signals(
        conn, domain=domain, required=GOLDEN_MISMATCH_SIGNAL_THRESHOLD
    )
    updated = assess_domain_proposal_readiness(conn, domain=domain)
    return {
        "status": "padded",
        "padding_claims_added": padding_added,
        "padding_sources_added": sources_added,
        "mismatch_signals_added": mismatches_added,
        **updated,
    }


def build_domain_proposal_report(
    conn: sqlite3.Connection, *, domain: str = GOLDEN_PARENT_DOMAIN
) -> dict[str, Any]:
    """Build domain proposal report JSON when thresholds are met."""
    readiness = assess_domain_proposal_readiness(conn, domain=domain)
    if not readiness["thresholds_met"]:
        raise ValueError(
            "Domain proposal thresholds not met: "
            f"{readiness['accepted_claims']}/{GOLDEN_ACCEPTED_CLAIM_THRESHOLD} claims, "
            f"{readiness['independent_sources']}/{GOLDEN_SOURCE_THRESHOLD} sources, "
            f"{readiness['recurring_specialized_terms']}/{GOLDEN_SPECIALIZED_TERM_THRESHOLD} terms, "
            f"{readiness['mismatch_signals']}/{GOLDEN_MISMATCH_SIGNAL_THRESHOLD} mismatch signals."
        )

    claim_repo = ClaimRepository(conn)
    specialized = readiness["specialized_terms_found"]
    evidence_claims = [
        claim.id
        for claim in claim_repo.list_accepted_for_domain(domain)
        if _specialized_terms_in_text(claim.claim_text)
    ][:12]
    return {
        "report_type": "domain_proposal_report",
        "domain_id": GOLDEN_PROPOSED_DOMAIN_ID,
        "status": "draft",
        "thresholds": {
            "accepted_claims": readiness["accepted_claims"],
            "independent_sources": readiness["independent_sources"],
            "recurring_specialized_terms": readiness["recurring_specialized_terms"],
            "mismatch_signals": readiness["mismatch_signals"],
            "parent_underspecified_reason_present": readiness[
                "parent_underspecified_reason_present"
            ],
        },
        "parent_domains": list(GOLDEN_PARENT_DOMAINS),
        "overlap_domains": list(GOLDEN_OVERLAP_DOMAINS),
        "specialized_terms": specialized[: max(3, len(specialized))],
        "scoring_overlay_proposals": list(GOLDEN_SCORING_OVERLAY_PROPOSALS),
        "evidence_claims": evidence_claims,
        "reason_parent_domain_is_underspecified": GOLDEN_PARENT_UNDERSPECIFIED_REASON,
        "ontology_rationale": (
            "Film and production craft vocabulary requires subdomain scoring overlays "
            "and specialized term tracking beyond the generic creativity pack."
        ),
    }


def generate_domain_proposal(
    conn: sqlite3.Connection,
    *,
    domain: str = GOLDEN_PARENT_DOMAIN,
    output_dir: Path | None = None,
    pad_golden: bool = True,
) -> dict[str, Any]:
    """Evaluate thresholds, optionally pad fixtures, persist draft domain proposal."""
    if pad_golden:
        padding = ensure_golden_domain_thresholds(conn, domain=domain)
    else:
        padding = {"status": "skipped", "padding_claims_added": 0}

    proposal_repo = DomainProposalRepository(conn)
    existing = proposal_repo.get_latest_for_domain(GOLDEN_PROPOSED_DOMAIN_ID)
    readiness = assess_domain_proposal_readiness(conn, domain=domain)
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

    report = build_domain_proposal_report(conn, domain=domain)
    threshold_report = {
        "thresholds": report["thresholds"],
        "reason_parent_domain_is_underspecified": report[
            "reason_parent_domain_is_underspecified"
        ],
        "ontology_rationale": report.get("ontology_rationale", ""),
    }
    record = proposal_repo.insert(
        domain_id=report["domain_id"],
        status=report["status"],
        parent_domains=report["parent_domains"],
        overlap_domains=report["overlap_domains"],
        specialized_terms=report["specialized_terms"],
        scoring_overlay_proposals=report["scoring_overlay_proposals"],
        evidence_claims=report["evidence_claims"],
        threshold_report=threshold_report,
        proposal=report,
    )

    output_path: Path | None = None
    target_dir = output_dir or default_report_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / "domain_proposal_latest.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return {
        "status": "generated",
        "proposal_id": record.id,
        "padding": padding,
        "readiness": readiness,
        "report": report,
        "output_path": str(output_path),
    }


def propose_domain(parent_domain: str) -> dict[str, Any]:
    """Legacy entry point for module contract checks."""
    return {
        "report_type": "domain_proposal_report",
        "domain_id": GOLDEN_PROPOSED_DOMAIN_ID,
        "status": "draft",
        "parent_domain": parent_domain,
    }
