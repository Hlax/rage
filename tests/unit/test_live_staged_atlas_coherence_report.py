"""Opt-in live network + atlas coherence human-readable report (ticket-289).

Default pytest collection excludes ``live_network`` tests (see ``pyproject.toml``).

Operator opt-in:

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_atlas_coherence_report.py -m live_network -q
```
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.cli import main
from rge.contracts.atlas_snapshot_v0 import ATLAS_SNAPSHOT_SCHEMA_VERSION
from rge.db.connection import connect
from rge.modules.atlas_coherence_report import (
    build_atlas_coherence_report,
    write_atlas_coherence_report,
)
from tests.unit.live_staged_candidates import MOCK_STAGED_ARTIFACT_MARKERS
from tests.unit.live_staged_proof_layers import (
    require_mock_spine_compatible_fetch_or_skip,
    run_live_openalex_discover,
)

TEST_QUESTION_ID = "rq_live_staged_atlas_coherence_report"
STAGED_RUN_ID = "run_live_staged_atlas_coherence_report"
STAGED_TOPIC = "Live Atlas coherence proof v0 operator report"


def require_live_staged_atlas_coherence_report_env() -> None:
    allow = os.environ.get("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", "0").strip().casefold()
    if allow not in ("1", "true", "yes"):
        pytest.skip(
            "live atlas coherence report requires RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=1"
        )
    network = os.environ.get("RGE_ALLOW_SOURCE_NETWORK", "0").strip().casefold()
    if network not in ("1", "true", "yes"):
        pytest.skip("live atlas coherence report requires RGE_ALLOW_SOURCE_NETWORK=1")
    if not os.environ.get("OPENALEX_MAILTO", "").strip():
        pytest.skip("live atlas coherence report requires OPENALEX_MAILTO")


def test_require_live_staged_atlas_coherence_report_skips_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", raising=False)
    with pytest.raises(pytest.skip.Exception):
        require_live_staged_atlas_coherence_report_env()


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def live_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "live_atlas_coherence_report.sqlite"


@pytest.fixture()
def staging_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "staged"
    directory.mkdir()
    return directory


@pytest.fixture()
def report_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "reports"
    directory.mkdir()
    return directory


def _preflight_mock_spine_compatible(probe_db: Path, staging_dir: Path) -> None:
    run_live_openalex_discover(probe_db, TEST_QUESTION_ID)
    conn = connect(probe_db)
    try:
        require_mock_spine_compatible_fetch_or_skip(
            conn,
            research_question_id=TEST_QUESTION_ID,
            staging_dir=staging_dir,
            artifact_text_markers=MOCK_STAGED_ARTIFACT_MARKERS,
        )
    finally:
        conn.close()


@pytest.mark.live_network
def test_live_staged_orchestrator_emits_coherence_report(
    live_env: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    require_live_staged_atlas_coherence_report_env()

    probe_db = tmp_path / "coherence_report_probe.sqlite"
    probe_staging = tmp_path / "probe_staged"
    probe_staging.mkdir()
    _preflight_mock_spine_compatible(probe_db, probe_staging)

    assert (
        main(
            [
                "run",
                "--fixture-mode",
                "--staged-spine",
                "--topic",
                STAGED_TOPIC,
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
                "--staging-dir",
                str(staging_dir),
                "--output-dir",
                str(report_dir),
                "--run-id",
                STAGED_RUN_ID,
                "--question-id",
                TEST_QUESTION_ID,
            ]
        )
        == 0
    )
    capsys.readouterr()

    atlas_path = tmp_path / "atlas_snapshot.json"
    assert (
        main(
            [
                "export-atlas-snapshot",
                "--db",
                str(temp_db),
                "--out",
                str(atlas_path),
                "--topic",
                STAGED_TOPIC,
                "--domain",
                "creativity",
            ]
        )
        == 0
    )
    capsys.readouterr()

    snapshot = json.loads(atlas_path.read_text(encoding="utf-8"))
    assert snapshot["schema_version"] == ATLAS_SNAPSHOT_SCHEMA_VERSION

    coherence_json = tmp_path / "atlas_coherence_report.json"
    coherence_md = tmp_path / "atlas_coherence_report.md"
    write_result = write_atlas_coherence_report(
        snapshot,
        json_path=coherence_json,
        markdown_path=coherence_md,
    )

    assert write_result["status"] == "completed"
    assert coherence_json.is_file()
    assert coherence_md.is_file()

    report = build_atlas_coherence_report(snapshot)
    assert report["safety"]["contract_valid"] is True
    assert report["population"]["cards"] >= 1
    assert report["population"]["nodes"] >= 1
    assert report["population"]["runs"] >= 1
    assert "verdict" in report

    if report["population"]["edges"] < 1:
        pytest.skip(
            json.dumps(
                {
                    "reason": "no_relationship_edges_in_atlas",
                    "coherence_report": write_result,
                },
                indent=2,
            )
        )

    assert report["overall_coherence_verdict"] in {"pass", "partial"}
    assert coherence_md.read_text(encoding="utf-8").startswith("# Research Atlas")
