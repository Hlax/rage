"""Opt-in live network + mock-fixture extract spine (ticket-172).

Default pytest collection excludes ``live_network`` tests (see ``pyproject.toml``).

Operator opt-in (real OpenAlex HTTP through ingest; mock-fixture extract only):

```powershell
$env:RGE_ALLOW_LIVE_STAGED_EXTRACT = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_extract_mock_spine.py -m live_network -q
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

TEST_QUESTION_ID = "rq_live_staged_extract_mock_spine"
STAGED_EXTRACT_FIXTURE = "staged_fetch_extract_claims.json"


def require_live_staged_extract_env() -> None:
    """Skip unless operator explicitly opts into live staged extract mock spine."""
    allow = os.environ.get("RGE_ALLOW_LIVE_STAGED_EXTRACT", "0").strip().casefold()
    if allow not in ("1", "true", "yes"):
        pytest.skip("live staged extract requires RGE_ALLOW_LIVE_STAGED_EXTRACT=1")
    network = os.environ.get("RGE_ALLOW_SOURCE_NETWORK", "0").strip().casefold()
    if network not in ("1", "true", "yes"):
        pytest.skip("live staged extract requires RGE_ALLOW_SOURCE_NETWORK=1")
    if not os.environ.get("OPENALEX_MAILTO", "").strip():
        pytest.skip("live staged extract requires OPENALEX_MAILTO")


def test_require_live_staged_extract_skips_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_ALLOW_LIVE_STAGED_EXTRACT", raising=False)
    with pytest.raises(pytest.skip.Exception):
        require_live_staged_extract_env()


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def live_staged_extract_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_EXTRACT", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "live_staged_extract_mock.sqlite"


@pytest.fixture()
def staging_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "staged"
    directory.mkdir()
    return directory


@pytest.mark.live_network
def test_live_openalex_source_acquisition_for_extract_spine(
    live_staged_extract_env: None,
    temp_db: Path,
    staging_dir: Path,
) -> None:
    """Layer 1: live discover + top-N fetch without mock-spine phrase coupling."""
    require_live_staged_extract_env()
    run_live_openalex_discover(temp_db, TEST_QUESTION_ID)

    conn = connect(temp_db)
    try:
        candidate_id, fetch_payload = run_live_source_acquisition(
            conn,
            research_question_id=TEST_QUESTION_ID,
            staging_dir=staging_dir,
        )
        assert candidate_id.startswith("disc_openalex_")
        assert Path(str(fetch_payload["artifact_path"])).stat().st_size > 0
    finally:
        conn.close()


@pytest.mark.live_network
def test_live_openalex_combined_extract_mock_fixture(
    live_staged_extract_env: None,
    temp_db: Path,
    staging_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Layer 3: live extract spine when artifact satisfies mock preconditions."""
    require_live_staged_extract_env()

    run_live_openalex_discover(temp_db, TEST_QUESTION_ID)
    capsys.readouterr()

    conn = connect(temp_db)
    try:
        claims_before = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
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

    extract_payload = json.loads(capsys.readouterr().out)
    assert extract_payload["status"] == "completed"
    assert extract_payload["accepted_count"] >= 1

    conn = connect(temp_db)
    try:
        claims_after = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
        accepted = conn.execute(
            """
            SELECT COUNT(*) FROM claims
            WHERE source_id = ? AND status = 'accepted'
            """,
            (source_id,),
        ).fetchone()[0]
        assert claims_after > claims_before
        assert accepted >= 1
    finally:
        conn.close()
