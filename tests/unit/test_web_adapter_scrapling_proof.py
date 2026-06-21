"""Unit tests for web adapter / Scrapling proof."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.db.connection import ensure_database
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.scrapling_html_parser import (
    PARSER_HTML_TO_TEXT,
    extract_webpage_clean_text,
)
from rge.modules.web_adapter_scrapling_proof import (
    WebAdapterScraplingProofGateError,
    assert_web_adapter_scrapling_proof_env,
    build_atlas_safe_web_adapter_artifact,
    classify_web_adapter_verdict,
    compare_parser_backends_on_html,
    run_web_adapter_scrapling_proof_smoke,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_FIXTURE = REPO_ROOT / "fixtures" / "sources" / "web_article_creativity_fixture.html"


def test_missing_web_adapter_gate_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RGE_ALLOW_WEB_ADAPTER_SCRAPLING_PROOF", raising=False)
    with pytest.raises(
        WebAdapterScraplingProofGateError,
        match="RGE_ALLOW_WEB_ADAPTER_SCRAPLING_PROOF",
    ):
        assert_web_adapter_scrapling_proof_env()


def test_compare_parser_backends_on_fixture_html() -> None:
    html = WEB_FIXTURE.read_text(encoding="utf-8")
    comparison = compare_parser_backends_on_html(html)
    assert comparison[PARSER_HTML_TO_TEXT]["text_length"] > 0
    assert "scrapling_available" in comparison


def test_extract_webpage_clean_text_html_to_text() -> None:
    html = WEB_FIXTURE.read_text(encoding="utf-8")
    result = extract_webpage_clean_text(html, parser_backend=PARSER_HTML_TO_TEXT)
    assert "semantic diversity" in result["clean_text"].casefold()


def test_run_web_adapter_scrapling_fixture_proof(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_WEB_ADAPTER_SCRAPLING_PROOF", "1")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    conn = ensure_database(tmp_path / "web_adapter.sqlite")
    try:
        result = run_web_adapter_scrapling_proof_smoke(
            conn,
            fixture_path=WEB_FIXTURE,
            output_dir=tmp_path,
        )
    finally:
        conn.close()

    artifact = result["atlas_safe_artifact"]
    spine = artifact["fixture_spine_summary"]

    assert result["web_adapter_verdict"] in {"GO", "PARTIAL"}
    assert spine["accepted_count"] >= 1
    assert spine["quality_gate_passed"] is True
    assert spine["trace_summary"]["trace_count"] >= 1
    assert artifact["parser_comparison"]
    assert assert_no_private_fields({"artifact": artifact}) == []

    loaded = json.loads(Path(result["artifact_path"]).read_text(encoding="utf-8"))
    assert loaded["fixture_ref"].startswith("fixtures/")


def test_build_atlas_safe_web_adapter_artifact_public_safe() -> None:
    artifact = build_atlas_safe_web_adapter_artifact(
        fixture_spine={
            "status": "completed",
            "accepted_count": 2,
            "rejected_count": 0,
            "evidence_atom_count": 2,
            "relationship_count": 1,
            "trace_summary": {"trace_count": 2, "atom_count": 2, "atlas_trace_preview": [{}, {}]},
        },
        parser_comparison={"scrapling_available": False},
        parser_backend_summary={
            "parser_backend": PARSER_HTML_TO_TEXT,
            "acquisition_status": "clean_text_ready",
            "extractable": True,
        },
        live_fetch=None,
        verdict="GO",
        rationale="Fixture proof.",
        fixture_ref="fixtures/sources/web_article_creativity_fixture.html",
    )
    assert artifact["schema_version"].startswith("atlas_web_adapter")
    assert assert_no_private_fields({"artifact": artifact}) == []


def test_sync_web_adapter_artifact_to_public_site(tmp_path: Path) -> None:
    from rge.modules.web_adapter_scrapling_proof import (
        sync_web_adapter_artifact_to_public_site,
    )

    artifact = build_atlas_safe_web_adapter_artifact(
        fixture_spine={
            "status": "completed",
            "accepted_count": 2,
            "rejected_count": 0,
            "evidence_atom_count": 2,
            "relationship_count": 1,
            "trace_summary": {"trace_count": 2, "atom_count": 2},
        },
        parser_comparison={"scrapling_available": False},
        parser_backend_summary={
            "parser_backend": PARSER_HTML_TO_TEXT,
            "acquisition_status": "clean_text_ready",
            "extractable": True,
        },
        live_fetch=None,
        verdict="GO",
        rationale="Fixture proof.",
        fixture_ref="fixtures/sources/web_article_creativity_fixture.html",
    )
    public_path = tmp_path / "atlas_web_adapter_scrapling_proof_latest.json"
    result = sync_web_adapter_artifact_to_public_site(
        artifact,
        public_path=public_path,
    )
    assert result["status"] == "completed"
    loaded = json.loads(public_path.read_text(encoding="utf-8"))
    assert loaded["web_adapter_verdict"] == "GO"


def test_classify_web_adapter_verdict_go() -> None:
    verdict, _ = classify_web_adapter_verdict(
        fixture_spine={
            "status": "completed",
            "accepted_count": 1,
            "trace_summary": {"trace_count": 1},
        },
        parser_comparison={"scrapling_available": False},
        live_fetch=None,
    )
    assert verdict == "GO"
