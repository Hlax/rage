"""Unit tests for PDF / TEI milestone proof."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.db.connection import ensure_database
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.document_parser import CLEAN_TEXT_READY, parse_pdf_bytes
from rge.modules.pdf_tei_milestone import (
    PdfTeiMilestoneGateError,
    assert_pdf_tei_milestone_env,
    build_atlas_safe_pdf_tei_artifact,
    classify_pdf_tei_verdict,
    compare_pdf_parser_backends,
    prove_dirty_pdf_blocked_before_llm,
    run_pdf_tei_milestone_smoke,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_FIXTURES = REPO_ROOT / "fixtures" / "source_documents"


def test_missing_pdf_tei_gate_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RGE_ALLOW_PDF_TEI_MILESTONE", raising=False)
    with pytest.raises(PdfTeiMilestoneGateError, match="RGE_ALLOW_PDF_TEI_MILESTONE"):
        assert_pdf_tei_milestone_env()


def test_prove_dirty_pdf_blocked_before_llm() -> None:
    dirty_pdf_bytes = b"%PDF-1.4\n" + bytes(range(256)) * 20
    gate = prove_dirty_pdf_blocked_before_llm(dirty_pdf_bytes)

    assert gate["llm_extraction_blocked"] is True
    assert gate["quality_gate_passed"] is False


def test_compare_pdf_parser_backends_on_fixture_pdf() -> None:
    pdf_bytes = (DOC_FIXTURES / "manual_oa_minimal.pdf").read_bytes()
    comparison = compare_pdf_parser_backends(pdf_bytes)

    assert comparison["local_pdf_parser"]["source_status"] in {
        CLEAN_TEXT_READY,
        "dirty_text",
        "parse_failed",
    }


def test_compare_pdf_parser_backends_grobid_fixture() -> None:
    pdf_bytes = (DOC_FIXTURES / "manual_oa_minimal.pdf").read_bytes()
    tei_bytes = (DOC_FIXTURES / "grobid_response_tei.xml").read_bytes()

    class _FakeResponse:
        def read(self) -> bytes:
            return tei_bytes

        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    with patch("urllib.request.urlopen", return_value=_FakeResponse()):
        comparison = compare_pdf_parser_backends(
            pdf_bytes,
            grobid_url="http://grobid-fixture.local",
        )

    assert comparison["grobid_enabled"] is True
    assert comparison["grobid_pdf_parser"]["parser_backend"] == "grobid_tei"
    assert comparison["grobid_pdf_parser"]["source_status"] == CLEAN_TEXT_READY


def test_run_pdf_tei_milestone_fixture_proof(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_PDF_TEI_MILESTONE", "1")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    conn = ensure_database(tmp_path / "pdf_tei.sqlite")
    try:
        result = run_pdf_tei_milestone_smoke(
            conn,
            output_dir=tmp_path,
        )
    finally:
        conn.close()

    artifact = result["atlas_safe_artifact"]
    tei_spine = artifact["tei_spine_summary"]

    assert result["pdf_tei_verdict"] in {"GO", "PARTIAL"}
    assert artifact["tei_parse_summary"]["source_status"] == CLEAN_TEXT_READY
    assert artifact["dirty_pdf_gate_summary"]["llm_extraction_blocked"] is True
    assert tei_spine["accepted_count"] >= 1
    assert tei_spine["trace_summary"]["trace_count"] >= 1
    assert assert_no_private_fields({"artifact": artifact}) == []

    loaded = json.loads(Path(result["artifact_path"]).read_text(encoding="utf-8"))
    assert loaded["tei_fixture_ref"].startswith("fixtures/")


def test_build_atlas_safe_pdf_tei_artifact_public_safe() -> None:
    artifact = build_atlas_safe_pdf_tei_artifact(
        tei_parse={"source_status": CLEAN_TEXT_READY, "parser_backend": "tei_xml"},
        pdf_parse={"source_status": CLEAN_TEXT_READY, "parser_backend": "pymupdf"},
        parser_comparison={"local_pdf_parser": {}},
        dirty_pdf_gate={"llm_extraction_blocked": True, "quality_gate_passed": False},
        tei_spine={
            "status": "completed",
            "accepted_count": 1,
            "trace_summary": {"trace_count": 1, "atom_count": 1, "atlas_trace_preview": [{}]},
        },
        pdf_spine=None,
        verdict="GO",
        rationale="Fixture proof.",
        tei_fixture_ref="fixtures/source_documents/manual_oa_tei.xml",
        pdf_fixture_ref="fixtures/source_documents/manual_oa_minimal.pdf",
    )
    assert artifact["schema_version"].startswith("atlas_pdf_tei")
    assert assert_no_private_fields({"artifact": artifact}) == []


def test_sync_pdf_tei_artifact_to_public_site(tmp_path: Path) -> None:
    from rge.modules.pdf_tei_milestone import sync_pdf_tei_artifact_to_public_site

    artifact = build_atlas_safe_pdf_tei_artifact(
        tei_parse={"source_status": CLEAN_TEXT_READY, "parser_backend": "tei_xml"},
        pdf_parse={"source_status": CLEAN_TEXT_READY, "parser_backend": "pymupdf"},
        parser_comparison={"local_pdf_parser": {}},
        dirty_pdf_gate={"llm_extraction_blocked": True, "quality_gate_passed": False},
        tei_spine={
            "status": "completed",
            "accepted_count": 1,
            "trace_summary": {"trace_count": 1, "atom_count": 1},
        },
        pdf_spine=None,
        verdict="GO",
        rationale="Fixture proof.",
        tei_fixture_ref="fixtures/source_documents/manual_oa_tei.xml",
        pdf_fixture_ref="fixtures/source_documents/manual_oa_minimal.pdf",
    )
    public_path = tmp_path / "atlas_pdf_tei_milestone_latest.json"
    result = sync_pdf_tei_artifact_to_public_site(
        artifact,
        public_path=public_path,
    )
    assert result["status"] == "completed"
    loaded = json.loads(public_path.read_text(encoding="utf-8"))
    assert loaded["pdf_tei_verdict"] == "GO"


def test_classify_pdf_tei_verdict_go() -> None:
    verdict, _ = classify_pdf_tei_verdict(
        tei_parse={"source_status": CLEAN_TEXT_READY},
        tei_spine={
            "status": "completed",
            "accepted_count": 1,
            "trace_summary": {"trace_count": 1},
        },
        pdf_parse={"source_status": CLEAN_TEXT_READY},
        pdf_spine=None,
        dirty_pdf_gate={"llm_extraction_blocked": True},
    )
    assert verdict == "GO"
