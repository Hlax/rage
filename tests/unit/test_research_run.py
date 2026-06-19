"""Unit tests for single-command research demo loop (MVP-P7)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.cli import main
from rge.modules.research_run import run_research_demo


def test_research_demo_fixture_mode_produces_full_bundle() -> None:
    payload = run_research_demo(
        topic="AI assisted creativity and idea diversity",
        fixture_mode=True,
        top_sources=3,
        full_text_top_n=2,
    )

    assert payload["status"] == "ok"
    assert payload["abstract_evidence"]["accepted_claims_total"] >= 1
    assert payload["field_map_report"]["report_type"] == "field_map"
    assert payload["improvement_recommendation"]["recommended_packet"].startswith("MVP-P")
    assert payload["selective_fulltext"] is not None
    assert payload["source_status_table"]


def test_research_run_cli_fixture_mode_writes_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "research-run",
            "--fixture-mode",
            "--topic",
            "AI creativity diversity",
            "--out",
            str(tmp_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert Path(payload["output_path"]).is_file()
    saved = json.loads(Path(payload["output_path"]).read_text(encoding="utf-8"))
    assert saved["command"] == "research-run"
