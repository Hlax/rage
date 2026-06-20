"""Staged ingest source-health metadata tests."""

from __future__ import annotations

from pathlib import Path

from rge.modules.acquisition_quality import staged_ingest_health_metadata


def test_staged_ingest_health_metadata_includes_purpose_fit() -> None:
    metadata = staged_ingest_health_metadata(
        candidate={"title": "Human-AI co-creativity", "source_type": "paper"},
        source_type="staged_fetch",
        raw_text="Human-AI co-creativity supports diverse songwriting outputs.",
        domain="creativity",
        artifact_path=Path("sample.html"),
        title="Human-AI co-creativity",
    )
    assert metadata["source_status"] == "clean_text_ready"
    assert metadata["parser_backend"] == "html_parser"
    assert metadata["extractable"] is True
    assert metadata["purpose_fit_status"] in {"match", "mismatch"}
    assert metadata["purpose_gate_decision"]
