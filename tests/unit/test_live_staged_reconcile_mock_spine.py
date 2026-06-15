"""Opt-in live network + deterministic reconcile spine (ticket-184; layers ticket-234).

Default pytest collection excludes ``live_network`` tests (see ``pyproject.toml``).

Proof layers:
- Layer 1 (``test_live_openalex_source_acquisition_for_reconcile_spine``): discover + top-N fetch.
- Layer 2: fixture-backed ``tests/unit/test_staged_ingest_reconcile_spine.py`` (network-free).
- Layer 3 (``test_live_openalex_combined_reconcile_mock_spine``): full live spine when artifact
  matches mock markers; otherwise skips with ``unsuitable_live_artifact``.

Operator opt-in:

```powershell
$env:RGE_ALLOW_LIVE_STAGED_RECONCILE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_reconcile_mock_spine.py -m live_network -q
```
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.cli import main
from rge.db.connection import connect
from tests.unit.live_staged_candidates import MOCK_STAGED_ARTIFACT_MARKERS
from tests.unit.live_staged_proof_layers import (
    require_mock_spine_compatible_fetch_or_skip,
    run_live_openalex_discover,
    run_live_source_acquisition,
)
from tests.unit.staged_domain_seed import seed_domain_opposing_context

TEST_QUESTION_ID = "rq_live_staged_reconcile_mock_spine"
STAGED_EXTRACT_FIXTURE = "staged_fetch_extract_claims.json"
STAGED_LINK_FIXTURE = "staged_fetch_link_concepts.json"
STAGED_BUILD_FIXTURE = "staged_fetch_build_relationships.json"
STAGED_DETECT_FIXTURE = "staged_fetch_detect_contradictions.json"


def require_live_staged_reconcile_env() -> None:
    """Skip unless operator explicitly opts into live staged reconcile spine."""
    allow = os.environ.get("RGE_ALLOW_LIVE_STAGED_RECONCILE", "0").strip().casefold()
    if allow not in ("1", "true", "yes"):
        pytest.skip("live staged reconcile requires RGE_ALLOW_LIVE_STAGED_RECONCILE=1")
    network = os.environ.get("RGE_ALLOW_SOURCE_NETWORK", "0").strip().casefold()
    if network not in ("1", "true", "yes"):
        pytest.skip("live staged reconcile requires RGE_ALLOW_SOURCE_NETWORK=1")
    if not os.environ.get("OPENALEX_MAILTO", "").strip():
        pytest.skip("live staged reconcile requires OPENALEX_MAILTO")


def test_require_live_staged_reconcile_skips_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_ALLOW_LIVE_STAGED_RECONCILE", raising=False)
    with pytest.raises(pytest.skip.Exception):
        require_live_staged_reconcile_env()


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def live_staged_reconcile_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_RECONCILE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "live_staged_reconcile_mock.sqlite"


@pytest.fixture()
def staging_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "staged"
    directory.mkdir()
    return directory


@pytest.mark.live_network
def test_live_openalex_source_acquisition_for_reconcile_spine(
    live_staged_reconcile_env: None,
    temp_db: Path,
    staging_dir: Path,
) -> None:
    """Layer 1: live discover + top-N fetch without mock-spine phrase coupling."""
    require_live_staged_reconcile_env()
    run_live_openalex_discover(temp_db, TEST_QUESTION_ID)

    conn = connect(temp_db)
    try:
        queue_count = conn.execute(
            "SELECT COUNT(*) FROM research_queue WHERE research_question_id = ?",
            (TEST_QUESTION_ID,),
        ).fetchone()[0]
        assert queue_count >= 1
        candidate_id, fetch_payload = run_live_source_acquisition(
            conn,
            research_question_id=TEST_QUESTION_ID,
            staging_dir=staging_dir,
        )
        assert candidate_id.startswith("disc_openalex_")
        assert fetch_payload.get("selected_url_kind")
        artifact = Path(str(fetch_payload["artifact_path"]))
        assert artifact.is_file()
        assert artifact.stat().st_size > 0
    finally:
        conn.close()


@pytest.mark.live_network
def test_live_openalex_combined_reconcile_mock_spine(
    live_staged_reconcile_env: None,
    temp_db: Path,
    staging_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Layer 3: full live reconcile spine when artifact satisfies mock preconditions."""
    require_live_staged_reconcile_env()
    seed_domain_opposing_context(temp_db)

    conn = connect(temp_db)
    try:
        score_events_before = conn.execute("SELECT COUNT(*) FROM score_events").fetchone()[0]
    finally:
        conn.close()

    run_live_openalex_discover(temp_db, TEST_QUESTION_ID)
    capsys.readouterr()

    conn = connect(temp_db)
    try:
        candidate_id, _fetch_payload = require_mock_spine_compatible_fetch_or_skip(
            conn,
            research_question_id=TEST_QUESTION_ID,
            staging_dir=staging_dir,
            artifact_text_markers=MOCK_STAGED_ARTIFACT_MARKERS,
        )
    finally:
        conn.close()

    assert (
        main(
            [
                "ingest-staged",
                "--domain",
                "creativity",
                "--candidate",
                candidate_id,
                "--staging-dir",
                str(staging_dir),
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )

    ingest_payload = json.loads(capsys.readouterr().out)
    source_id = ingest_payload["source_id"]
    assert ingest_payload["status"] == "ingested"

    assert (
        main(
            [
                "extract-claims",
                "--source",
                source_id,
                "--fixture",
                STAGED_EXTRACT_FIXTURE,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )

    assert (
        main(
            [
                "link-concepts",
                "--source",
                source_id,
                "--fixture",
                STAGED_LINK_FIXTURE,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )

    assert (
        main(
            [
                "build-relationships",
                "--source",
                source_id,
                "--fixture",
                STAGED_BUILD_FIXTURE,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )

    assert (
        main(
            [
                "detect-contradictions",
                "--source",
                source_id,
                "--fixture",
                STAGED_DETECT_FIXTURE,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )

    assert (
        main(
            [
                "reconcile-scores",
                "--source",
                source_id,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )

    reconcile_payload = json.loads(capsys.readouterr().out)
    assert reconcile_payload["status"] == "completed"
    assert reconcile_payload["score_events_created"] >= 1
    assert reconcile_payload["relationships_updated"] >= 1

    conn = connect(temp_db)
    try:
        score_events_after = conn.execute("SELECT COUNT(*) FROM score_events").fetchone()[0]
        assert score_events_after > score_events_before
        assert score_events_after >= 1
    finally:
        conn.close()
