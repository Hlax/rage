"""Web adapter / Scrapling proof: webpage → clean text → claim → atom → trace.

Operator-gated proof that public HTML (fixture-first; optional live fetch) flows
through quality gates, quote-first extraction, and Atlas-safe trace reporting.
Scrapling is optional; html_to_text remains the default CI path.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from rge.db.connection import ensure_database
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.principal_audit_gate import repo_root
from rge.modules.relationship_density_proof import ensure_purpose_gated_relationship_density_proof
from rge.modules.run_evaluator import generate_run_report
from rge.modules.scrapling_html_parser import (
    PARSER_HTML_TO_TEXT,
    PARSER_SCRAPLING,
    extract_webpage_clean_text,
    scrapling_parser_available,
)
from rge.modules.web_source_adapter import (
    acquire_webpage_from_path,
    acquire_webpage_from_url,
    run_ingest_webpage_pipeline,
)

PACKET_ID = "web-adapter-scrapling-proof"
WEB_ADAPTER_SCHEMA_VERSION = "atlas_web_adapter_scrapling_proof_v0.1.0"
WEB_ADAPTER_ARTIFACT_NAME = "atlas_web_adapter_scrapling_proof_latest.json"
WEB_ADAPTER_RUN_ID = "run_web_adapter_scrapling_proof"
DEFAULT_WEB_FIXTURE = repo_root() / "fixtures" / "sources" / "web_article_creativity_fixture.html"
DEFAULT_LIVE_WEB_URL = "https://example.com/"
DEFAULT_QUESTION = (
    "Does AI assistance improve idea quality while reducing semantic diversity?"
)

NEXT_RECOMMENDED_PACKET = {
    "id": "pdf-tei-milestone",
    "title": "PDF / TEI Milestone",
}


class WebAdapterScraplingProofGateError(RuntimeError):
    """Raised when operator env gates for web adapter proof are missing."""


def assert_web_adapter_scrapling_proof_env(*, require_live_fetch: bool = False) -> dict[str, str]:
    """Fail closed unless operator opts into web adapter / Scrapling proof."""
    allow = os.environ.get("RGE_ALLOW_WEB_ADAPTER_SCRAPLING_PROOF", "0").strip().casefold()
    if allow not in {"1", "true", "yes"}:
        raise WebAdapterScraplingProofGateError(
            "Web adapter Scrapling proof requires RGE_ALLOW_WEB_ADAPTER_SCRAPLING_PROOF=1."
        )
    combined = {"RGE_ALLOW_WEB_ADAPTER_SCRAPLING_PROOF": allow}
    if require_live_fetch:
        from rge.modules.source_network import assert_source_network_enabled

        combined.update(assert_source_network_enabled(command="web-adapter-scrapling-live-fetch"))
        live = os.environ.get("RGE_ALLOW_WEB_ADAPTER_SCRAPLING_LIVE_FETCH", "0").strip().casefold()
        if live not in {"1", "true", "yes"}:
            raise WebAdapterScraplingProofGateError(
                "Live webpage fetch proof requires RGE_ALLOW_WEB_ADAPTER_SCRAPLING_LIVE_FETCH=1."
            )
        combined["RGE_ALLOW_WEB_ADAPTER_SCRAPLING_LIVE_FETCH"] = live
    return combined


def required_env_setup_commands() -> list[str]:
    return [
        '$env:RGE_ALLOW_WEB_ADAPTER_SCRAPLING_PROOF = "1"',
        '$env:RGE_LLM_MODE = "mock"',
        "python scripts/run_web_adapter_scrapling_proof.py --sync-public",
        "# Optional live fetch:",
        '$env:RGE_ALLOW_SOURCE_NETWORK = "1"',
        '$env:RGE_ALLOW_WEB_ADAPTER_SCRAPLING_LIVE_FETCH = "1"',
        "python scripts/run_web_adapter_scrapling_proof.py --live-fetch --sync-public",
    ]


def compare_parser_backends_on_html(html: str) -> dict[str, Any]:
    """Compare html_to_text vs Scrapling extraction on the same HTML."""
    html_result = extract_webpage_clean_text(html, parser_backend=PARSER_HTML_TO_TEXT)
    scrapling_result = extract_webpage_clean_text(html, parser_backend=PARSER_SCRAPLING)
    return {
        "scrapling_available": scrapling_parser_available(),
        PARSER_HTML_TO_TEXT: {
            "text_length": len(str(html_result.get("clean_text") or "")),
            "parser_backend": html_result.get("parser_backend"),
        },
        PARSER_SCRAPLING: {
            "text_length": len(str(scrapling_result.get("clean_text") or "")),
            "parser_backend": scrapling_result.get("parser_backend"),
            "fallback_reason": scrapling_result.get("fallback_reason"),
            "scrapling_used": scrapling_result.get("scrapling_used"),
        },
    }


def build_parser_backend_summary(artifact: dict[str, Any]) -> dict[str, Any]:
    metrics = dict(artifact.get("quality_metrics") or {})
    return {
        "parser_backend": artifact.get("parser_backend"),
        "acquisition_status": artifact.get("acquisition_status"),
        "extractable": metrics.get("extractable"),
        "quoteable_span_count": metrics.get("quoteable_span_count"),
        "text_length": metrics.get("text_length"),
        "parser_request": artifact.get("parser_request") or {},
    }


def run_webpage_spine_to_trace(
    conn: Any,
    artifact: dict[str, Any],
    *,
    question: str = DEFAULT_QUESTION,
    domain_pack: str = "creativity",
    fixture_name: str | None = None,
    client: Any | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Run webpage ingest → extract → atom/trace spine on one artifact."""
    from rge.modules.live_arbitrary_source_health import build_atlas_safe_run_artifact

    pipeline = run_ingest_webpage_pipeline(
        conn,
        artifact,
        domain=domain_pack,
        persist_claims=True,
        fixture_name=fixture_name,
        client=client,
    )
    if pipeline.get("status") != "completed":
        return {
            "status": pipeline.get("status", "error"),
            "pipeline": pipeline,
            "accepted_claim_ids": [],
        }

    extract_row = dict(pipeline.get("extract") or {})
    accepted_ids = list(extract_row.get("accepted_claim_ids") or [])
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
        run_id=WEB_ADAPTER_RUN_ID,
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
        question_id="web_adapter_scrapling_proof",
    )
    trace_summary = dict(atlas_artifact.get("trace_summary") or {})

    return {
        "status": "completed",
        "pipeline": pipeline,
        "accepted_claim_ids": accepted_ids,
        "accepted_count": int(extract_row.get("accepted_count") or 0),
        "rejected_count": int(extract_row.get("rejected_count") or 0),
        "density_proof": density,
        "evidence_atom_count": int(
            (density.get("atom_result") or {}).get("promoted_count")
            or run_report.get("evidence_atoms_created")
            or 0
        ),
        "relationship_count": int(density.get("relationship_count") or 0),
        "trace_summary": trace_summary,
        "run_report": run_report,
        "atlas_safe_run_artifact": atlas_artifact,
    }


def classify_web_adapter_verdict(
    *,
    fixture_spine: dict[str, Any],
    parser_comparison: dict[str, Any],
    live_fetch: dict[str, Any] | None,
) -> tuple[str, str]:
    """Return (verdict, rationale) for web adapter proof."""
    if fixture_spine.get("status") != "completed":
        return "NO-GO", "Fixture webpage pipeline did not complete ingest/extract."

    accepted = int(fixture_spine.get("accepted_count") or 0)
    trace_count = int((fixture_spine.get("trace_summary") or {}).get("trace_count") or 0)
    if accepted >= 1 and trace_count >= 1:
        scrapling_note = (
            "Scrapling parser available and compared."
            if parser_comparison.get("scrapling_available")
            else "Scrapling not installed; html_to_text baseline used."
        )
        if live_fetch and live_fetch.get("status") == "completed":
            return (
                "GO",
                "Fixture webpage produced quote-backed claims with trace rows; "
                f"live fetch succeeded. {scrapling_note}",
            )
        return (
            "GO",
            "Fixture webpage produced quote-backed claims with trace rows. "
            f"{scrapling_note}",
        )

    if accepted >= 1:
        return (
            "PARTIAL",
            "Webpage claims were accepted but Atlas trace summary remains thin.",
        )

    if fixture_spine.get("status") == "completed":
        return (
            "PARTIAL",
            "Webpage ingest succeeded but quote-backed claim extraction is thin.",
        )

    return "NO-GO", "Web adapter proof did not produce usable webpage evidence."


def build_atlas_safe_web_adapter_artifact(
    *,
    fixture_spine: dict[str, Any],
    parser_comparison: dict[str, Any],
    parser_backend_summary: dict[str, Any],
    live_fetch: dict[str, Any] | None,
    verdict: str,
    rationale: str,
    fixture_ref: str,
) -> dict[str, Any]:
    """Build public-safe Atlas bundle for web adapter / Scrapling proof."""
    trace = dict(fixture_spine.get("trace_summary") or {})
    artifact: dict[str, Any] = {
        "schema_version": WEB_ADAPTER_SCHEMA_VERSION,
        "status": "completed",
        "packet_id": PACKET_ID,
        "run_id": WEB_ADAPTER_RUN_ID,
        "web_adapter_verdict": verdict,
        "web_adapter_rationale": rationale,
        "evaluation_only": False,
        "fixture_ref": fixture_ref,
        "parser_comparison": parser_comparison,
        "parser_backend_summary": parser_backend_summary,
        "fixture_spine_summary": {
            "status": fixture_spine.get("status"),
            "accepted_count": int(fixture_spine.get("accepted_count") or 0),
            "rejected_count": int(fixture_spine.get("rejected_count") or 0),
            "evidence_atom_count": int(fixture_spine.get("evidence_atom_count") or 0),
            "relationship_count": int(fixture_spine.get("relationship_count") or 0),
            "acquisition_status": parser_backend_summary.get("acquisition_status"),
            "quality_gate_passed": parser_backend_summary.get("extractable") is True,
            "trace_summary": {
                "trace_count": int(trace.get("trace_count") or 0),
                "atom_count": int(trace.get("atom_count") or 0),
                "preview_row_count": len(trace.get("atlas_trace_preview") or []),
            },
        },
        "live_fetch_summary": live_fetch or {"status": "skipped", "reason": "not_requested"},
        "next_recommended_packet": NEXT_RECOMMENDED_PACKET,
    }
    violations = assert_no_private_fields({"artifact": artifact})
    if violations:
        raise ValueError(
            "Web adapter artifact blocked by private-field policy: "
            + "; ".join(violations[:5])
        )
    return artifact


def sync_web_adapter_artifact_to_public_site(
    artifact: dict[str, Any],
    *,
    public_path: Path,
) -> dict[str, Any]:
    """Copy validated web adapter artifact into public-site preview data."""
    if artifact.get("schema_version") != WEB_ADAPTER_SCHEMA_VERSION:
        raise ValueError(
            f"schema_version must be {WEB_ADAPTER_SCHEMA_VERSION!r}."
        )
    verdict = str(artifact.get("web_adapter_verdict") or "")
    if verdict in {"", "PENDING"}:
        raise ValueError("web_adapter_verdict must be set before public sync.")
    spine = artifact.get("fixture_spine_summary") or {}
    if str(spine.get("status") or "").casefold() != "completed":
        raise ValueError("fixture_spine_summary.status must be completed.")
    violations = assert_no_private_fields({"artifact": artifact})
    if violations:
        raise ValueError(
            "Web adapter artifact failed public-safe validation: "
            + "; ".join(violations[:5])
        )
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return {
        "status": "completed",
        "output_path": str(public_path),
        "web_adapter_verdict": verdict,
        "accepted_count": spine.get("accepted_count"),
        "trace_count": (spine.get("trace_summary") or {}).get("trace_count"),
    }


def run_web_adapter_scrapling_proof_smoke(
    conn: Any,
    *,
    fixture_path: Path | None = None,
    domain_pack: str = "creativity",
    question: str = DEFAULT_QUESTION,
    parser_backend: str = PARSER_HTML_TO_TEXT,
    live_fetch: bool = False,
    live_url: str = DEFAULT_LIVE_WEB_URL,
    output_dir: Path | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    """Operator-gated fixture (and optional live) web adapter proof."""
    env_gates = assert_web_adapter_scrapling_proof_env(require_live_fetch=live_fetch)
    os.environ.setdefault("RGE_LLM_MODE", "mock")

    fixture = fixture_path or DEFAULT_WEB_FIXTURE
    html = fixture.read_text(encoding="utf-8")
    parser_comparison = compare_parser_backends_on_html(html)
    artifact = acquire_webpage_from_path(
        fixture,
        parser_backend=parser_backend,
    )
    parser_backend_summary = build_parser_backend_summary(artifact)

    fixture_spine = run_webpage_spine_to_trace(
        conn,
        artifact,
        question=question,
        domain_pack=domain_pack,
        client=client,
        output_dir=output_dir,
    )

    live_fetch_summary: dict[str, Any] | None = None
    if live_fetch:
        try:
            live_artifact = acquire_webpage_from_url(live_url, parser_backend=parser_backend)
            live_fetch_summary = {
                "status": "completed",
                "url_ref": "live_public_webpage",
                "parser_backend": live_artifact.get("parser_backend"),
                "acquisition_status": live_artifact.get("acquisition_status"),
                "text_length": (live_artifact.get("quality_metrics") or {}).get("text_length"),
                "extractable": (live_artifact.get("quality_metrics") or {}).get("extractable"),
            }
        except Exception as exc:
            live_fetch_summary = {
                "status": "failed",
                "url_ref": "live_public_webpage",
                "reason": str(exc)[:200],
            }

    verdict, rationale = classify_web_adapter_verdict(
        fixture_spine=fixture_spine,
        parser_comparison=parser_comparison,
        live_fetch=live_fetch_summary,
    )
    try:
        fixture_ref = fixture.relative_to(repo_root()).as_posix()
    except ValueError:
        fixture_ref = fixture.name

    atlas_artifact = build_atlas_safe_web_adapter_artifact(
        fixture_spine=fixture_spine,
        parser_comparison=parser_comparison,
        parser_backend_summary=parser_backend_summary,
        live_fetch=live_fetch_summary,
        verdict=verdict,
        rationale=rationale,
        fixture_ref=fixture_ref,
    )

    root = repo_root()
    out_dir = output_dir or (root / "data" / "exports" / "web_adapter_scrapling_proof")
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = out_dir / WEB_ADAPTER_ARTIFACT_NAME
    artifact_path.write_text(json.dumps(atlas_artifact, indent=2), encoding="utf-8")

    try:
        operator_artifact_ref = artifact_path.relative_to(root).as_posix()
    except ValueError:
        operator_artifact_ref = f"{out_dir.name}/{WEB_ADAPTER_ARTIFACT_NAME}"

    return {
        "packet_id": PACKET_ID,
        "web_adapter_verdict": verdict,
        "web_adapter_rationale": rationale,
        "parser_backend": artifact.get("parser_backend"),
        "scrapling_available": scrapling_parser_available(),
        "env_gates": env_gates,
        "artifact_path": str(artifact_path),
        "operator_artifact_ref": operator_artifact_ref,
        "atlas_safe_artifact": atlas_artifact,
        "next_recommended_packet": NEXT_RECOMMENDED_PACKET,
    }


def run_web_adapter_scrapling_with_fresh_db(
    *,
    output_dir: Path | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    root = repo_root()
    out_dir = output_dir or (root / "data" / "exports" / "web_adapter_scrapling_proof")
    out_dir.mkdir(parents=True, exist_ok=True)
    db_path = out_dir / "web_adapter_scrapling.sqlite"
    if db_path.exists():
        db_path.unlink()
    conn = ensure_database(db_path)
    try:
        return run_web_adapter_scrapling_proof_smoke(conn, output_dir=out_dir, **kwargs)
    finally:
        conn.close()


# Public-safe fixture reference for docs/tests (no absolute paths in artifacts).
WEB_FIXTURE_RELATIVE = "fixtures/sources/web_article_creativity_fixture.html"
