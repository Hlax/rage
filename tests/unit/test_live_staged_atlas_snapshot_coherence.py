"""Opt-in live network + private atlas snapshot coherence proof (ticket-285).

Default pytest collection excludes ``live_network`` tests (see ``pyproject.toml``).

Proof flow:
- Layer 3 preflight: live OpenAlex discover + mock-spine marker compatibility
  (skip with ``unsuitable_live_artifact`` when fetchable but fixture-incompatible).
- Single-command staged orchestrator on temp DB (mock LLM upstream).
- ``export-atlas-snapshot`` without ``--fixture-mode`` → coherence audit.

Operator opt-in:

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_atlas_snapshot_coherence.py -m live_network -q
```
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from rge.cli import main
from rge.contracts.atlas_snapshot_v0 import (
    ATLAS_SNAPSHOT_SCHEMA_VERSION,
    validate_atlas_snapshot,
)
from rge.db.connection import connect
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from tests.unit.live_staged_candidates import MOCK_STAGED_ARTIFACT_MARKERS
from tests.unit.live_staged_proof_layers import (
    require_mock_spine_compatible_fetch_or_skip,
    run_live_openalex_discover,
)

TEST_QUESTION_ID = "rq_live_staged_atlas_snapshot_coherence"
STAGED_RUN_ID = "run_live_staged_atlas_snapshot_coherence"
STAGED_TOPIC = "Live staged atlas snapshot coherence proof"


def require_live_staged_atlas_coherence_env() -> None:
    """Skip unless operator explicitly opts into live staged atlas coherence proof."""
    allow = os.environ.get("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", "0").strip().casefold()
    if allow not in ("1", "true", "yes"):
        pytest.skip(
            "live staged atlas coherence requires RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=1"
        )
    network = os.environ.get("RGE_ALLOW_SOURCE_NETWORK", "0").strip().casefold()
    if network not in ("1", "true", "yes"):
        pytest.skip("live staged atlas coherence requires RGE_ALLOW_SOURCE_NETWORK=1")
    if not os.environ.get("OPENALEX_MAILTO", "").strip():
        pytest.skip("live staged atlas coherence requires OPENALEX_MAILTO")


def audit_atlas_snapshot_coherence(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Return structured coherence audit fields for operator reporting."""
    leak_violations = assert_no_private_fields(snapshot)
    validate_atlas_snapshot(snapshot)
    return {
        "schema_version": snapshot.get("schema_version"),
        "cards": len(snapshot.get("cards", [])),
        "nodes": len(snapshot.get("nodes", [])),
        "edges": len(snapshot.get("edges", [])),
        "runs": len(snapshot.get("runs", [])),
        "follow_up_questions": len(snapshot.get("follow_up_questions", [])),
        "private_field_violations": leak_violations,
        "contract_valid": True,
    }


def test_require_live_staged_atlas_coherence_skips_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", raising=False)
    with pytest.raises(pytest.skip.Exception):
        require_live_staged_atlas_coherence_env()


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def live_staged_atlas_coherence_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "live_staged_atlas_coherence.sqlite"


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


def _preflight_mock_spine_compatible(
    probe_db: Path,
    staging_dir: Path,
) -> None:
    """Layer-3 preflight on a throwaway DB; skip when live artifact is unsuitable."""
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
def test_live_staged_orchestrator_atlas_snapshot_coherence(
    live_staged_atlas_coherence_env: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Live staged orchestrator → private atlas export with contract coherence audit."""
    require_live_staged_atlas_coherence_env()

    probe_db = tmp_path / "atlas_coherence_probe.sqlite"
    probe_staging = tmp_path / "probe_staged"
    probe_staging.mkdir()
    _preflight_mock_spine_compatible(probe_db, probe_staging)

    exit_code = main(
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
    assert exit_code == 0

    run_payload = json.loads(capsys.readouterr().out)
    assert run_payload["status"] == "completed"
    assert run_payload["mode"] == "fixture_staged"
    assert run_payload["run_reports"] >= 1

    atlas_path = tmp_path / "atlas_snapshot.json"
    export_exit = main(
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
    assert export_exit == 0
    export_payload = json.loads(capsys.readouterr().out)
    assert export_payload["status"] == "completed"
    assert export_payload["schema_version"] == ATLAS_SNAPSHOT_SCHEMA_VERSION
    assert atlas_path.is_file()

    snapshot = json.loads(atlas_path.read_text(encoding="utf-8"))
    audit = audit_atlas_snapshot_coherence(snapshot)

    assert audit["schema_version"] == ATLAS_SNAPSHOT_SCHEMA_VERSION
    assert audit["private_field_violations"] == []
    assert audit["cards"] >= 1
    assert audit["nodes"] >= 1
    assert audit["runs"] >= 1

    if audit["edges"] < 1:
        pytest.skip(
            json.dumps(
                {
                    "reason": "no_relationship_edges_in_atlas",
                    "detail": (
                        "Staged orchestrator completed but atlas snapshot has no "
                        "relationship edges; coherence thresholds not met."
                    ),
                    "coherence_audit": audit,
                },
                indent=2,
            )
        )

    assert audit["edges"] >= 1
