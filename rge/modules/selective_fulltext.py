"""Selective full-text acquisition for ranked sources (MVP-P5)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rge.modules.document_parser import (
    CLEAN_TEXT_READY,
    PARSE_FAILED,
    parse_document_bytes,
    parse_document_file,
)
from rge.modules.fetcher import fetch_url_bytes
from rge.modules.research_network import live_selective_fetch_enabled
from rge.modules.source_network import source_network_enabled
from rge.modules.source_resolver.status import apply_acquisition_source_status

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_MANIFEST = REPO_ROOT / "fixtures" / "source_documents" / "manifest.json"
DEFAULT_STAGING_DIR = REPO_ROOT / "data" / "sources" / "selective_fulltext"

FULL_TEXT_NOT_NEEDED = "full_text_not_needed"
FULL_TEXT_REQUESTED = "full_text_requested"
FULL_TEXT_AVAILABLE = "full_text_available"
FULL_TEXT_DOWNLOADED = "full_text_downloaded"
FULL_TEXT_PARSE_FAILED = "full_text_parse_failed"
FULL_TEXT_CLEAN_TEXT_READY = "full_text_clean_text_ready"
FULL_TEXT_EXTRACT_FAILED = "full_text_extract_failed"
FULL_TEXT_EVIDENCE_READY = "full_text_evidence_ready"

ACQUISITION_STATUSES = (
    FULL_TEXT_NOT_NEEDED,
    FULL_TEXT_REQUESTED,
    FULL_TEXT_AVAILABLE,
    FULL_TEXT_DOWNLOADED,
    FULL_TEXT_PARSE_FAILED,
    FULL_TEXT_CLEAN_TEXT_READY,
    FULL_TEXT_EXTRACT_FAILED,
    FULL_TEXT_EVIDENCE_READY,
)


def default_staging_dir() -> Path:
    return DEFAULT_STAGING_DIR


def load_fixture_manifest(path: Path | None = None) -> dict[str, Any]:
    manifest_path = path or FIXTURE_MANIFEST
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def resolve_fulltext_location(record: dict[str, Any]) -> dict[str, Any] | None:
    """Prefer TEI, then OA PDF, then arXiv PDF."""
    if record.get("tei_url"):
        return {"url": record["tei_url"], "kind": "tei", "backend": "tei_xml"}
    if record.get("pdf_url"):
        backend = "arxiv_pdf" if record.get("source_kind") == "arxiv" else "oa_pdf"
        return {"url": record["pdf_url"], "kind": "pdf", "backend": backend}
    if record.get("source_kind") == "arxiv" and record.get("arxiv_id"):
        arxiv_id = str(record["arxiv_id"])
        return {
            "url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
            "kind": "pdf",
            "backend": "arxiv_pdf",
        }
    return None


def should_request_full_text(
    record: dict[str, Any],
    *,
    abstract_card: dict[str, Any] | None = None,
    force: bool = False,
) -> tuple[bool, str]:
    if force:
        return True, "forced_top_n"
    location = resolve_fulltext_location(record)
    if location is None:
        return False, "no_fetchable_location"
    if abstract_card is None:
        return True, "no_abstract_card"
    if abstract_card.get("status") == "skipped":
        return True, "abstract_missing"
    if int(abstract_card.get("accepted_count") or 0) == 0:
        return True, "zero_abstract_claims"
    if abstract_card.get("recommend_full_text"):
        return True, "thin_abstract_evidence"
    return False, "abstract_sufficient"


def _fixture_document_path(source_id: str) -> Path | None:
    manifest = load_fixture_manifest()
    entry = manifest.get(source_id)
    if not entry or not entry.get("path"):
        return None
    return REPO_ROOT / "fixtures" / "source_documents" / str(entry["path"])


def _fixture_entry(source_id: str) -> dict[str, Any] | None:
    manifest = load_fixture_manifest()
    entry = manifest.get(source_id)
    return dict(entry) if isinstance(entry, dict) else None


def acquire_full_text(
    record: dict[str, Any],
    *,
    fixture_mode: bool = False,
    urlopen: Any | None = None,
    staging_dir: Path | None = None,
    force: bool = False,
    abstract_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Acquire and parse full text for one resolved source record."""
    source_id = str(record.get("source_id") or "")
    location = resolve_fulltext_location(record)
    requested, request_reason = should_request_full_text(
        record,
        abstract_card=abstract_card,
        force=force,
    )
    base = {
        "source_id": source_id,
        "title": record.get("title"),
        "requested": requested,
        "request_reason": request_reason,
    }
    if not requested:
        base["acquisition_status"] = FULL_TEXT_NOT_NEEDED
        return base
    if location is None:
        base["acquisition_status"] = FULL_TEXT_NOT_NEEDED
        base["skip_reason"] = "no_fetchable_location"
        return base

    base["acquisition_status"] = FULL_TEXT_REQUESTED
    base["location"] = location

    if fixture_mode:
        entry = _fixture_entry(source_id)
        if entry and entry.get("skip_full_text"):
            base["acquisition_status"] = FULL_TEXT_NOT_NEEDED
            base["skip_reason"] = "fixture_abstract_only"
            return base
        doc_path = _fixture_document_path(source_id)
        if doc_path is None or not doc_path.is_file():
            base["acquisition_status"] = FULL_TEXT_PARSE_FAILED
            base["skip_reason"] = "fixture_document_missing"
            return base
        if entry and entry.get("simulated_pdf_parse"):
            body = doc_path.read_bytes()
            parse_result = parse_document_bytes(
                body,
                content_type="text/plain",
                suffix=".txt",
            )
        else:
            body = doc_path.read_bytes()
            content_type = str(entry.get("content_type") or "") if entry else None
            parse_result = parse_document_bytes(
                body,
                content_type=content_type,
                suffix=doc_path.suffix,
            )
        base["fixture_path"] = str(doc_path)
    else:
        if not live_selective_fetch_enabled():
            base["acquisition_status"] = FULL_TEXT_AVAILABLE
            base["blocked"] = True
            base["blocked_reason"] = (
                "live_selective_fetch_disabled"
                if source_network_enabled()
                else "source_network_disabled"
            )
            return base
        from rge.config import load_config

        cfg = load_config()
        body, content_type = fetch_url_bytes(str(location["url"]), urlopen=urlopen)
        target_dir = staging_dir or default_staging_dir()
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_id = source_id.replace(":", "_")
        suffix = ".xml" if location["kind"] == "tei" else ".pdf"
        artifact_path = target_dir / f"{safe_id}{suffix}"
        artifact_path.write_bytes(body)
        base["artifact_path"] = str(artifact_path.resolve())
        base["acquisition_status"] = FULL_TEXT_DOWNLOADED
        parse_result = parse_document_bytes(
            body,
            content_type=content_type,
            suffix=suffix,
            grobid_url=cfg.grobid_url,
        )

    base["parse"] = parse_result.as_dict()
    if parse_result.source_status == PARSE_FAILED:
        base["acquisition_status"] = FULL_TEXT_PARSE_FAILED
        return base
    if parse_result.source_status == CLEAN_TEXT_READY:
        base["acquisition_status"] = FULL_TEXT_CLEAN_TEXT_READY
        base["clean_text"] = parse_result.clean_text
        return base
    base["acquisition_status"] = FULL_TEXT_PARSE_FAILED
    base["failure_class"] = parse_result.source_status
    return base


def acquire_selective_fulltext(
    records: list[dict[str, Any]],
    *,
    abstract_evidence: dict[str, Any] | None = None,
    top_n: int = 3,
    fixture_mode: bool = False,
    force_top_n: bool = False,
) -> dict[str, Any]:
    """Fetch full text only for selected top sources that need deeper evidence."""
    cards_by_source = {
        str(card.get("source_id") or ""): card
        for card in (abstract_evidence or {}).get("cards") or []
    }
    acquisitions: list[dict[str, Any]] = []
    for index, record in enumerate(records[: max(0, top_n)]):
        card = cards_by_source.get(str(record.get("source_id") or ""))
        acquisitions.append(
            acquire_full_text(
                record,
                fixture_mode=fixture_mode,
                force=force_top_n,
                abstract_card=card,
            )
        )
    status_counts: dict[str, int] = {}
    for item in acquisitions:
        status = str(item.get("acquisition_status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "top_n": top_n,
        "fixture_mode": fixture_mode,
        "acquisition_count": len(acquisitions),
        "status_counts": status_counts,
        "acquisitions": acquisitions,
    }


def apply_parse_to_resolved_record(record: dict[str, Any], acquisition: dict[str, Any]) -> dict[str, Any]:
    """Merge acquisition parse outcome into a resolved source record."""
    merged = dict(record)
    status = str(acquisition.get("acquisition_status") or "")
    parse_failed = status == FULL_TEXT_PARSE_FAILED
    clean_ready = status == FULL_TEXT_CLEAN_TEXT_READY
    download_failed = acquisition.get("blocked") and acquisition.get("blocked_reason")
    apply_acquisition_source_status(
        merged,
        download_failed=bool(download_failed),
        parse_failed=parse_failed,
        clean_text_ready=clean_ready,
        extractable=clean_ready,
    )
    merged["acquisition_status"] = status
    if acquisition.get("clean_text"):
        merged["clean_text"] = acquisition["clean_text"]
    return merged
