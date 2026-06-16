"""Atlas coherence report CLI (ticket-290)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.cli import main

REPO_ROOT = Path(__file__).resolve().parents[2]
CREATIVITY_FIXTURE = REPO_ROOT / "fixtures" / "atlas" / "atlas_snapshot_v0_creativity_fixture.json"


def test_atlas_coherence_report_cli_writes_json_and_markdown(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    json_out = tmp_path / "coherence_report.json"
    md_out = tmp_path / "coherence_report.md"
    exit_code = main(
        [
            "atlas-coherence-report",
            "--snapshot",
            str(CREATIVITY_FIXTURE),
            "--out-json",
            str(json_out),
            "--out-md",
            str(md_out),
        ]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["command"] == "atlas-coherence-report"
    assert payload["overall_coherence_verdict"] in {"pass", "partial", "fail"}
    assert payload["json_path"] == str(json_out)
    assert payload["markdown_path"] == str(md_out)
    assert json_out.is_file()
    assert md_out.is_file()
    report = json.loads(json_out.read_text(encoding="utf-8"))
    assert report["population"]["cards"] >= 2


def test_atlas_coherence_report_cli_json_only(tmp_path: Path) -> None:
    json_out = tmp_path / "coherence_report.json"
    exit_code = main(
        [
            "atlas-coherence-report",
            "--snapshot",
            str(CREATIVITY_FIXTURE),
            "--out-json",
            str(json_out),
        ]
    )
    assert exit_code == 0
    assert json_out.is_file()


def test_atlas_coherence_report_cli_missing_snapshot(tmp_path: Path) -> None:
    json_out = tmp_path / "coherence_report.json"
    exit_code = main(
        [
            "atlas-coherence-report",
            "--snapshot",
            str(tmp_path / "missing_snapshot.json"),
            "--out-json",
            str(json_out),
        ]
    )
    assert exit_code == 1
    assert not json_out.is_file()
