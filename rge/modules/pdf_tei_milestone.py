"""PDF / TEI milestone: parse → quality gate → quote-backed claim → atom/trace.

Operator-gated proof that TEI/XML and PDF documents flow through document_parser
quality gates, block dirty PDFs before LLM extraction, and produce quote-backed
claims with Atlas-safe trace reporting. GROBID is optional; fixture TEI and
local PDF parsers remain the default CI path.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from rge.db.connection import ensure_database
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.document_parser import (
    CLEAN_TEXT_READY,
    DIRTY_TEXT,
    PARSE_FAILED,
    parse_pdf_bytes,
    parse_tei_xml,
)
from rge.modules.principal_audit_gate import repo_root
from rge.modules.relationship_density_proof import ensure_purpose_gated_relationship_density_proof
from rge.modules.research_spine import wire_selective_fulltext_to_db
from rge.modules.run_evaluator import generate_run_report
from rge.modules.selective_fulltext import (
    FULL_TEXT_CLEAN_TEXT_READY,
    acquire_full_text,
)
from rge.modules.source_resolver import load_manual_fixture_records

PACKET_ID = "pdf-tei-milestone"
PDF_TEI_SCHEMA_VERSION = "atlas_pdf_tei_milestone_v0.1.0"
PDF_TEI_ARTIFACT_NAME = "atlas_pdf_tei_milestone_latest.json"
PDF_TEI_RUN_ID = "run_pdf_tei_milestone"
DOC_FIXTURES = repo_root() / "fixtures" / "source_documents"
TEI_FIXTURE_REL = "fixtures/source_documents/manual_oa_tei.xml"
PDF_FIXTURE_REL = "fixtures/source_documents/manual_oa_minimal.pdf"
DEFAULT_QUESTION = (
    "Does AI assistance improve idea quality while reducing semantic diversity?"
)

NEXT_RECOMMENDED_PACKET = {
    "id": "demo-loop-polish",
    "title": "Demo Loop Polish",
}


class PdfTeiMilestoneGateError(RuntimeError):
    """Raised when operator env gates for PDF / TEI milestone are missing."""


def assert_pdf_tei_milestone_env() -> dict[str, str]:
    """Fail closed unless operator opts into PDF / TEI milestone proof."""
    allow = os.environ.get("RGE_ALLOW_PDF_TEI_MILESTONE", "0").strip().casefold()
    if allow not in {"1", "true", "yes"}:
        raise PdfTeiMilestoneGateError(
            "PDF / TEI milestone requires RGE_ALLOW_PDF_TEI_MILESTONE=1."
        )
    return {"RGE_ALLOW_PDF_TEI_MILESTONE": allow}


def required_env_setup_commands() -> list[str]:
    return [
        '$env:RGE_ALLOW_PDF_TEI_MILESTONE = "1"',
        '$env:RGE_LLM_MODE = "mock"',
        "python scripts/run_pdf_tei_milestone.py --sync-public",
    ]


def _parse_summary(result: Any) -> dict[str, Any]:
    payload = result.as_dict() if hasattr(result, "as_dict") else dict(result)
    return {
        "source_status": payload.get("source_status"),
        "parser_backend": payload.get("parser_backend"),
        "readable_char_ratio": payload.get("readable_char_ratio"),
        "sentence_count": payload.get("sentence_count"),
        "quoteable_span_count": payload.get("quoteable_span_count"),
        "extracted_char_count": payload.get("extracted_char_count"),
        "page_count": payload.get("page_count"),
        "detail": payload.get("detail"),
    }


def compare_pdf_parser_backends(
    pdf_bytes: bytes,
    *,
    grobid_url: str = "",
) -> dict[str, Any]:
    """Compare local PDF parsers vs optional GROBID TEI on the same bytes."""
    local_result = parse_pdf_bytes(pdf_bytes, grobid_url="")
    grobid_result = parse_pdf_bytes(pdf_bytes, grobid_url=grobid_url) if grobid_url else None
    comparison: dict[str, Any] = {
        "local_pdf_parser": _parse_summary(local_result),
        "grobid_enabled": bool(grobid_url),
    }
    if grobid_result is not None:
        comparison["grobid_pdf_parser"] = _parse_summary(grobid_result)
    return comparison


def prove_dirty_pdf_blocked_before_llm(dirty_pdf_bytes: bytes) -> dict[str, Any]:
    """Show unreadable PDF bytes fail quality gates before LLM extraction."""
    result = parse_pdf_bytes(dirty_pdf_bytes)
    blocked = result.source_status in {DIRTY_TEXT, PARSE_FAILED}
    return {
        "source_status": result.source_status,
        "parser_backend": result.parser_backend,
        "quality_gate_passed": result.source_status == CLEAN_TEXT_READY,
        "llm_extraction_blocked": blocked,
        "detail": result.detail,
    }


def _fixture_record_by_id(fixture_id: str) -> dict[str, Any]:
    records = load_manual_fixture_records(domain_pack="creativity")
    for record in records:
        provider_id = str(record.get("provider_id") or "")
        source_id = str(record.get("source_id") or "")
        if provider_id == fixture_id or source_id.endswith(f":{fixture_id}"):
            return dict(record)
    raise ValueError(f"Manual fixture record not found: {fixture_id}")


def run_document_spine_to_trace(
    conn: Any,
    acquisition: dict[str, Any],
    record: dict[str, Any],
    *,
    question: str = DEFAULT_QUESTION,
    domain_pack: str = "creativity",
    client: Any | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Run selective full-text ingest → extract → atom/trace spine."""
    from rge.modules.live_arbitrary_source_health import build_atlas_safe_run_artifact

    source_id = str(record.get("source_id") or acquisition.get("source_id") or "")
    spine = wire_selective_fulltext_to_db(
        conn,
        acquisitions=[acquisition],
        records_by_id={source_id: record},
        domain=domain_pack,
        persist_claims=True,
        client=client,
    )
    if spine.get("status") != "completed":
        return {
            "status": spine.get("status", "error"),
            "spine": spine,
            "accepted_claim_ids": [],
        }

    accepted_ids: list[str] = []
    for row in spine.get("extract_rows") or []:
        accepted_ids.extend(list(row.get("accepted_ids") or row.get("accepted_claim_ids") or []))

    density: dict[str, Any] = {"status": "skipped", "reason": "no_accepted_claims"}
    if accepted_ids:
        density = ensure_purpose_gated_relationship_density_proof(
            conn,
            domain=domain_pack,
            question=question,
            claim_ids=accepted_ids,
        )

    report_result = generate_run_report(
        conn,
        run_id=PDF_TEI_RUN_ID,
        topic=question,
        domain_pack=domain_pack,
        output_dir=output_dir,
    )
    run_report = dict(report_result.get("report") or {})
    atlas_artifact = build_atlas_safe_run_artifact(
        conn,
        question=question,
        domain_pack=domain_pack,
        run_report=run_report,
        question_id="pdf_tei_milestone",
    )
    trace_summary = dict(atlas_artifact.get("trace_summary") or {})

    return {
        "status": "completed",
        "spine": spine,
        "accepted_claim_ids": accepted_ids,
        "accepted_count": int(spine.get("accepted_claims_total") or 0),
        "rejected_count": int(spine.get("rejected_claims_total") or 0),
        "density_proof": density,
        "evidence_atom_count": int(
            (density.get("atom_result") or {}).get("promoted_count")
            or run_report.get("evidence_atoms_created")
            or 0
        ),
        "relationship_count": int(density.get("relationship_count") or 0),
        "trace_summary": trace_summary,
        "run_report": run_report,
        "parser_backend": (acquisition.get("parse") or {}).get("parser_backend"),
        "acquisition_status": acquisition.get("acquisition_status"),
    }


def classify_pdf_tei_verdict(
    *,
    tei_parse: dict[str, Any],
    tei_spine: dict[str, Any],
    pdf_parse: dict[str, Any],
    pdf_spine: dict[str, Any] | None,
    dirty_pdf_gate: dict[str, Any],
) -> tuple[str, str]:
    """Return (verdict, rationale) for PDF / TEI milestone proof."""
    tei_clean = tei_parse.get("source_status") == CLEAN_TEXT_READY
    tei_trace = int((tei_spine.get("trace_summary") or {}).get("trace_count") or 0)
    tei_accepted = int(tei_spine.get("accepted_count") or 0)

    if not tei_clean:
        return "NO-GO", "TEI fixture failed document_parser quality gates."

    if not dirty_pdf_gate.get("llm_extraction_blocked"):
        return (
            "NO-GO",
            "Dirty PDF bytes were not blocked before LLM extraction.",
        )

    if tei_accepted >= 1 and tei_trace >= 1:
        pdf_note = ""
        if pdf_spine and int(pdf_spine.get("accepted_count") or 0) >= 1:
            pdf_note = " PDF fixture also produced quote-backed claims."
        elif pdf_parse.get("source_status") == CLEAN_TEXT_READY:
            pdf_note = " PDF parsed cleanly; claim spine may remain thin on minimal PDF."
        else:
            pdf_note = (
                f" PDF classified as {pdf_parse.get('source_status')} "
                "without unsupported-claim wall."
            )
        return (
            "GO",
            "TEI produced quote-backed claims with trace rows; dirty PDF blocked "
            f"pre-LLM.{pdf_note}",
        )

    if tei_accepted >= 1:
        return (
            "PARTIAL",
            "TEI claims accepted but Atlas trace summary remains thin.",
        )

    return (
        "PARTIAL",
        "TEI parsed cleanly and dirty PDF blocked, but quote-backed extraction is thin.",
    )


def build_atlas_safe_pdf_tei_artifact(
    *,
    tei_parse: dict[str, Any],
    pdf_parse: dict[str, Any],
    parser_comparison: dict[str, Any],
    dirty_pdf_gate: dict[str, Any],
    tei_spine: dict[str, Any],
    pdf_spine: dict[str, Any] | None,
    verdict: str,
    rationale: str,
    tei_fixture_ref: str,
    pdf_fixture_ref: str,
) -> dict[str, Any]:
    """Build public-safe Atlas bundle for PDF / TEI milestone."""
    tei_trace = dict(tei_spine.get("trace_summary") or {})
    pdf_trace = dict((pdf_spine or {}).get("trace_summary") or {})
    artifact: dict[str, Any] = {
        "schema_version": PDF_TEI_SCHEMA_VERSION,
        "status": "completed",
        "packet_id": PACKET_ID,
        "run_id": PDF_TEI_RUN_ID,
        "pdf_tei_verdict": verdict,
        "pdf_tei_rationale": rationale,
        "evaluation_only": False,
        "tei_fixture_ref": tei_fixture_ref,
        "pdf_fixture_ref": pdf_fixture_ref,
        "tei_parse_summary": tei_parse,
        "pdf_parse_summary": pdf_parse,
        "parser_comparison": parser_comparison,
        "dirty_pdf_gate_summary": dirty_pdf_gate,
        "tei_spine_summary": {
            "status": tei_spine.get("status"),
            "accepted_count": int(tei_spine.get("accepted_count") or 0),
            "rejected_count": int(tei_spine.get("rejected_count") or 0),
            "evidence_atom_count": int(tei_spine.get("evidence_atom_count") or 0),
            "relationship_count": int(tei_spine.get("relationship_count") or 0),
            "parser_backend": tei_spine.get("parser_backend"),
            "acquisition_status": tei_spine.get("acquisition_status"),
            "quality_gate_passed": tei_parse.get("source_status") == CLEAN_TEXT_READY,
            "trace_summary": {
                "trace_count": int(tei_trace.get("trace_count") or 0),
                "atom_count": int(tei_trace.get("atom_count") or 0),
                "preview_row_count": len(tei_trace.get("atlas_trace_preview") or []),
            },
        },
        "pdf_spine_summary": {
            "status": (pdf_spine or {}).get("status", "skipped"),
            "accepted_count": int((pdf_spine or {}).get("accepted_count") or 0),
            "rejected_count": int((pdf_spine or {}).get("rejected_count") or 0),
            "evidence_atom_count": int((pdf_spine or {}).get("evidence_atom_count") or 0),
            "relationship_count": int((pdf_spine or {}).get("relationship_count") or 0),
            "parser_backend": (pdf_spine or {}).get("parser_backend")
            or pdf_parse.get("parser_backend"),
            "acquisition_status": (pdf_spine or {}).get("acquisition_status"),
            "quality_gate_passed": pdf_parse.get("source_status") == CLEAN_TEXT_READY,
            "trace_summary": {
                "trace_count": int(pdf_trace.get("trace_count") or 0),
                "atom_count": int(pdf_trace.get("atom_count") or 0),
                "preview_row_count": len(pdf_trace.get("atlas_trace_preview") or []),
            },
        },
        "next_recommended_packet": NEXT_RECOMMENDED_PACKET,
    }
    violations = assert_no_private_fields({"artifact": artifact})
    if violations:
        raise ValueError(
            "PDF / TEI artifact blocked by private-field policy: "
            + "; ".join(violations[:5])
        )
    return artifact


def sync_pdf_tei_artifact_to_public_site(
    artifact: dict[str, Any],
    *,
    public_path: Path,
) -> dict[str, Any]:
    """Copy validated PDF / TEI artifact into public-site preview data."""
    if artifact.get("schema_version") != PDF_TEI_SCHEMA_VERSION:
        raise ValueError(
            f"schema_version must be {PDF_TEI_SCHEMA_VERSION!r}."
        )
    verdict = str(artifact.get("pdf_tei_verdict") or "")
    if verdict in {"", "PENDING"}:
        raise ValueError("pdf_tei_verdict must be set before public sync.")
    tei_spine = artifact.get("tei_spine_summary") or {}
    if str(tei_spine.get("status") or "").casefold() != "completed":
        raise ValueError("tei_spine_summary.status must be completed.")
    dirty_gate = artifact.get("dirty_pdf_gate_summary") or {}
    if not dirty_gate.get("llm_extraction_blocked"):
        raise ValueError("dirty_pdf_gate_summary.llm_extraction_blocked must be true.")
    violations = assert_no_private_fields({"artifact": artifact})
    if violations:
        raise ValueError(
            "PDF / TEI artifact failed public-safe validation: "
            + "; ".join(violations[:5])
        )
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return {
        "status": "completed",
        "output_path": str(public_path),
        "pdf_tei_verdict": verdict,
        "tei_accepted_count": tei_spine.get("accepted_count"),
        "tei_trace_count": (tei_spine.get("trace_summary") or {}).get("trace_count"),
    }


def run_pdf_tei_milestone_smoke(
    conn: Any,
    *,
    domain_pack: str = "creativity",
    question: str = DEFAULT_QUESTION,
    grobid_url: str = "",
    output_dir: Path | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    """Operator-gated fixture PDF / TEI milestone proof."""
    env_gates = assert_pdf_tei_milestone_env()
    os.environ.setdefault("RGE_LLM_MODE", "mock")

    tei_xml = (DOC_FIXTURES / "manual_oa_tei.xml").read_text(encoding="utf-8")
    tei_parse = _parse_summary(parse_tei_xml(tei_xml))

    pdf_bytes = (DOC_FIXTURES / "manual_oa_minimal.pdf").read_bytes()
    pdf_parse = _parse_summary(parse_pdf_bytes(pdf_bytes, grobid_url=grobid_url))
    parser_comparison = compare_pdf_parser_backends(pdf_bytes, grobid_url=grobid_url)

    dirty_pdf_bytes = b"%PDF-1.4\n" + bytes(range(256)) * 20
    dirty_pdf_gate = prove_dirty_pdf_blocked_before_llm(dirty_pdf_bytes)

    tei_record = _fixture_record_by_id("manual_oa_tei")
    tei_acquisition = acquire_full_text(tei_record, fixture_mode=True, force=True)
    tei_spine = run_document_spine_to_trace(
        conn,
        tei_acquisition,
        tei_record,
        question=question,
        domain_pack=domain_pack,
        client=client,
        output_dir=output_dir,
    )

    pdf_spine: dict[str, Any] | None = None
    pdf_record = _fixture_record_by_id("manual_oa_pdf")
    pdf_acquisition = acquire_full_text(pdf_record, fixture_mode=True, force=True)
    if pdf_acquisition.get("acquisition_status") == FULL_TEXT_CLEAN_TEXT_READY:
        pdf_spine = run_document_spine_to_trace(
            conn,
            pdf_acquisition,
            pdf_record,
            question=question,
            domain_pack=domain_pack,
            client=client,
            output_dir=output_dir,
        )

    verdict, rationale = classify_pdf_tei_verdict(
        tei_parse=tei_parse,
        tei_spine=tei_spine,
        pdf_parse=pdf_parse,
        pdf_spine=pdf_spine,
        dirty_pdf_gate=dirty_pdf_gate,
    )

    atlas_artifact = build_atlas_safe_pdf_tei_artifact(
        tei_parse=tei_parse,
        pdf_parse=pdf_parse,
        parser_comparison=parser_comparison,
        dirty_pdf_gate=dirty_pdf_gate,
        tei_spine=tei_spine,
        pdf_spine=pdf_spine,
        verdict=verdict,
        rationale=rationale,
        tei_fixture_ref=TEI_FIXTURE_REL,
        pdf_fixture_ref=PDF_FIXTURE_REL,
    )

    root = repo_root()
    out_dir = output_dir or (root / "data" / "exports" / "pdf_tei_milestone")
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = out_dir / PDF_TEI_ARTIFACT_NAME
    artifact_path.write_text(json.dumps(atlas_artifact, indent=2), encoding="utf-8")

    try:
        operator_artifact_ref = artifact_path.relative_to(root).as_posix()
    except ValueError:
        operator_artifact_ref = f"{out_dir.name}/{PDF_TEI_ARTIFACT_NAME}"

    return {
        "packet_id": PACKET_ID,
        "pdf_tei_verdict": verdict,
        "pdf_tei_rationale": rationale,
        "env_gates": env_gates,
        "artifact_path": str(artifact_path),
        "operator_artifact_ref": operator_artifact_ref,
        "atlas_safe_artifact": atlas_artifact,
        "next_recommended_packet": NEXT_RECOMMENDED_PACKET,
    }


def run_pdf_tei_milestone_with_fresh_db(
    *,
    output_dir: Path | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    root = repo_root()
    out_dir = output_dir or (root / "data" / "exports" / "pdf_tei_milestone")
    out_dir.mkdir(parents=True, exist_ok=True)
    db_path = out_dir / "pdf_tei_milestone.sqlite"
    if db_path.exists():
        db_path.unlink()
    conn = ensure_database(db_path)
    try:
        return run_pdf_tei_milestone_smoke(conn, output_dir=out_dir, **kwargs)
    finally:
        conn.close()
