"""Acquisition quality summary helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.modules.acquisition_quality import (
    acquisition_quality_summary,
    cluster_acquisition_quality_summary,
    failure_modes_from_acquisition_summary,
    summarize_source_metadata_rows,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_FIXTURE = REPO_ROOT / "fixtures" / "sources" / "web_article_creativity_fixture.html"


def test_summarize_source_metadata_rows_counts_parser_backends() -> None:
    rows = [
        {
            "domain_metadata_json": json.dumps(
                {
                    "acquisition_status": "clean_text_ready",
                    "parser_backend": "html_to_text",
                    "source_type": "webpage",
                }
            )
        },
        {
            "domain_metadata_json": json.dumps(
                {
                    "full_text_acquisition_status": "clean_text_ready",
                    "parse": {"parser_backend": "grobid_tei"},
                    "source_type": "selective_fulltext",
                }
            )
        },
    ]
    summary = summarize_source_metadata_rows(rows)
    assert summary["sources_with_metadata"] == 2
    assert summary["parser_backend_counts"]["html_to_text"] == 1
    assert summary["parser_backend_counts"]["grobid_tei"] == 1
    assert summary["acquisition_status_counts"]["clean_text_ready"] == 2


def test_cluster_acquisition_quality_summary_scopes_to_cluster_sources(
    tmp_path: Path,
) -> None:
    from rge.cli import main
    from rge.db.connection import ensure_database

    os.environ["RGE_LLM_MODE"] = "mock"
    db_path = tmp_path / "acq_summary.sqlite"
    staging = tmp_path / "web_staging"
    assert (
        main(
            [
                "ingest-webpage",
                "--html",
                str(WEB_FIXTURE),
                "--domain",
                "creativity",
                "--db",
                str(db_path),
                "--staging-dir",
                str(staging),
            ]
        )
        == 0
    )

    conn = ensure_database(db_path)
    try:
        summary = cluster_acquisition_quality_summary(conn, domain="creativity")
        assert summary["cluster_domain"] == "creativity"
        assert len(summary["cluster_source_ids"]) == 1
        assert summary["sources_with_metadata"] == 1
        assert summary["parser_backend_counts"]["html_to_text"] == 1
        assert summary["acquisition_status_counts"]["clean_text_ready"] == 1
    finally:
        conn.close()


def test_acquisition_quality_summary_empty_scope(tmp_path: Path) -> None:
    from rge.db.connection import ensure_database

    conn = ensure_database(tmp_path / "empty_scope.sqlite")
    try:
        summary = acquisition_quality_summary(conn, source_ids=[])
        assert summary["sources_with_metadata"] == 0
        assert summary["scoped_source_count"] == 0
    finally:
        conn.close()


def test_failure_modes_from_acquisition_summary_dirty_text() -> None:
    summary = {
        "acquisition_status_counts": {"dirty_text": 2, "clean_text_ready": 1},
        "source_type_counts": {"selective_fulltext": 3},
        "parser_backend_counts": {"pymupdf": 2},
    }
    modes = failure_modes_from_acquisition_summary(summary)
    reasons = {mode["reason"] for mode in modes}
    assert "blocked_by_quality_gate" in reasons
    assert "webpage_dirty_text" not in reasons


def test_failure_modes_from_acquisition_summary_webpage_dirty() -> None:
    summary = {
        "acquisition_status_counts": {"dirty_text": 1},
        "source_type_counts": {"webpage": 1},
        "parser_backend_counts": {"html_to_text": 1},
    }
    modes = failure_modes_from_acquisition_summary(summary)
    reasons = {mode["reason"] for mode in modes}
    assert "blocked_by_quality_gate" in reasons
    assert "webpage_dirty_text" in reasons


def test_failure_modes_from_acquisition_summary_pdf_unavailable() -> None:
    summary = {
        "acquisition_status_counts": {"parse_failed": 1},
        "parser_backend_counts": {"pdf_unavailable": 2, "pymupdf": 0},
    }
    modes = failure_modes_from_acquisition_summary(summary)
    reasons = {mode["reason"] for mode in modes}
    assert "parse_failed" in reasons
    assert "pdf_parser_unavailable" in reasons
