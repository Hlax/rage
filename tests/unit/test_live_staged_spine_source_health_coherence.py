"""Staged-spine source-health artifact coherence with atlas snapshot preview.

Mock staged orchestrator proof (default pytest) plus opt-in live_network layer.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import STAGED_FIXTURE_QUESTION_ID, STAGED_FIXTURE_RUN_ID, main
from rge.contracts.atlas_snapshot_v0 import validate_atlas_snapshot
from rge.db.connection import connect
from rge.modules.atlas_preview_curator import export_staged_spine_source_health_artifact
from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from tests.unit.test_staged_fixture_mode_run_spine import (
    OPENALEX_FIXTURE,
    RANK1_HTML,
    RANK2_HTML,
    STAGED_TOPIC,
    _staged_network_urlopen,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL_SAFE_ATLAS_ARTIFACT_SCHEMA = "atlas_source_health_run_v0.1.0"


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


def _assert_source_health_coherence(
    *,
    snapshot_health: dict,
    artifact: dict,
) -> None:
    artifact_summary = artifact.get("source_health_summary") or {}
    assert int(artifact_summary.get("sources_with_metadata") or 0) >= 1
    assert int(snapshot_health.get("sources_with_metadata") or 0) >= 1
    assert (
        artifact_summary.get("sources_with_metadata")
        == snapshot_health.get("sources_with_metadata")
    )
    assert artifact_summary.get("source_status_counts") == snapshot_health.get(
        "source_status_counts"
    )
    assert artifact.get("schema_version") == LOCAL_SAFE_ATLAS_ARTIFACT_SCHEMA
    assert artifact.get("purpose", {}).get("research_intent")
    assert artifact.get("purpose_fit_summary")
    assert isinstance(artifact.get("readiness_warnings"), list)
    assert assert_no_private_fields({"artifact": artifact}) == []
    joined = json.dumps(artifact)
    for forbidden in ("source_id", "local_path", "prompt", "claim_id"):
        assert forbidden not in joined.casefold()


def test_mock_staged_spine_source_health_coherence() -> None:
    """Mock staged orchestrator temp export matches atlas source-health artifact thresholds."""
    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text(encoding="utf-8"))
    urlopen = _staged_network_urlopen(fixture_payload, [RANK1_HTML, RANK2_HTML])

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        db = td_path / "staged_source_health_coherence.sqlite"
        staging = td_path / "staged"
        staging.mkdir()
        reports = td_path / "reports"
        reports.mkdir()
        atlas_path = td_path / "atlas_snapshot.json"
        artifact_path = td_path / "atlas_source_health_run_latest.json"

        with patch(
            "rge.modules.source_providers.openalex.urllib.request.urlopen",
            urlopen,
        ), patch("rge.modules.fetcher.urllib.request.urlopen", urlopen):
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
                    str(db),
                    "--staging-dir",
                    str(staging),
                    "--output-dir",
                    str(reports),
                    "--run-id",
                    STAGED_FIXTURE_RUN_ID,
                    "--question-id",
                    STAGED_FIXTURE_QUESTION_ID,
                ]
            )
            assert exit_code == 0

            export_exit = main(
                [
                    "export-atlas-snapshot",
                    "--db",
                    str(db),
                    "--out",
                    str(atlas_path),
                    "--topic",
                    STAGED_TOPIC,
                    "--domain",
                    "creativity",
                ]
            )
            assert export_exit == 0

            conn = connect(db)
            try:
                export_staged_spine_source_health_artifact(
                    conn,
                    run_id=STAGED_FIXTURE_RUN_ID,
                    question=STAGED_TOPIC,
                    domain_pack="creativity",
                    output_path=artifact_path,
                    question_id=STAGED_FIXTURE_QUESTION_ID,
                )
            finally:
                conn.close()

        snapshot = json.loads(atlas_path.read_text(encoding="utf-8"))
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        validate_atlas_snapshot(snapshot)
        _assert_source_health_coherence(
            snapshot_health=snapshot.get("source_health_preview") or {},
            artifact=artifact,
        )


def require_live_staged_source_health_coherence_env() -> None:
    allow = os.environ.get("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", "0").strip().casefold()
    if allow not in ("1", "true", "yes"):
        pytest.skip(
            "live staged source-health coherence requires "
            "RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR=1"
        )
    network = os.environ.get("RGE_ALLOW_SOURCE_NETWORK", "0").strip().casefold()
    if network not in ("1", "true", "yes"):
        pytest.skip("live staged source-health coherence requires RGE_ALLOW_SOURCE_NETWORK=1")
    if not os.environ.get("OPENALEX_MAILTO", "").strip():
        pytest.skip("live staged source-health coherence requires OPENALEX_MAILTO")


@pytest.fixture()
def live_staged_spine_source_health_coherence_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)


@pytest.mark.live_network
def test_live_staged_spine_source_health_coherence(
    live_staged_spine_source_health_coherence_env: None,
    tmp_path: Path,
) -> None:
    """Live staged orchestrator temp export coheres with source-health artifact."""
    from tests.unit.test_live_staged_atlas_snapshot_coherence import (
        STAGED_RUN_ID,
        STAGED_TOPIC,
        TEST_QUESTION_ID,
        _preflight_mock_spine_compatible,
    )

    require_live_staged_source_health_coherence_env()

    temp_db = tmp_path / "live_staged_source_health.sqlite"
    staging_dir = tmp_path / "staged"
    staging_dir.mkdir()
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    atlas_path = tmp_path / "atlas_snapshot.json"
    artifact_path = tmp_path / "atlas_source_health_run_latest.json"

    probe_db = tmp_path / "probe.sqlite"
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

    conn = connect(temp_db)
    try:
        export_staged_spine_source_health_artifact(
            conn,
            run_id=STAGED_RUN_ID,
            question=STAGED_TOPIC,
            domain_pack="creativity",
            output_path=artifact_path,
            question_id=TEST_QUESTION_ID,
        )
    finally:
        conn.close()

    snapshot = json.loads(atlas_path.read_text(encoding="utf-8"))
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    _assert_source_health_coherence(
        snapshot_health=snapshot.get("source_health_preview") or {},
        artifact=artifact,
    )
