"""Opt-in live network proof for staged discover + fetch (ticket-167).

Default pytest collection excludes ``live_network`` tests (see ``pyproject.toml``).

Operator opt-in (real OpenAlex HTTP; no live LLM):

```powershell
$env:RGE_ALLOW_LIVE_STAGED_FETCH = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_fetch_validation.py -m live_network -q
```
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from rge.db.connection import connect
from tests.unit.live_staged_proof_layers import (
    run_live_openalex_discover,
    run_live_source_acquisition,
)

TEST_QUESTION_ID = "rq_live_staged_fetch_validation"


def require_live_staged_fetch_env() -> None:
    """Skip unless operator explicitly opts into live staged fetch proof."""
    allow = os.environ.get("RGE_ALLOW_LIVE_STAGED_FETCH", "0").strip().casefold()
    if allow not in ("1", "true", "yes"):
        pytest.skip("live staged fetch requires RGE_ALLOW_LIVE_STAGED_FETCH=1")
    network = os.environ.get("RGE_ALLOW_SOURCE_NETWORK", "0").strip().casefold()
    if network not in ("1", "true", "yes"):
        pytest.skip("live staged fetch requires RGE_ALLOW_SOURCE_NETWORK=1")
    if not os.environ.get("OPENALEX_MAILTO", "").strip():
        pytest.skip("live staged fetch requires OPENALEX_MAILTO")


def test_require_live_staged_fetch_skips_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_ALLOW_LIVE_STAGED_FETCH", raising=False)
    with pytest.raises(pytest.skip.Exception):
        require_live_staged_fetch_env()


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def live_staged_fetch_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_FETCH", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "live_staged_fetch.sqlite"


@pytest.fixture()
def staging_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "staged"
    directory.mkdir()
    return directory


@pytest.mark.live_network
def test_live_openalex_discover_and_fetch_writes_staged_artifact(
    live_staged_fetch_env: None,
    temp_db: Path,
    staging_dir: Path,
) -> None:
    require_live_staged_fetch_env()

    run_live_openalex_discover(temp_db, TEST_QUESTION_ID)

    conn = connect(temp_db)
    try:
        queue_count = conn.execute(
            "SELECT COUNT(*) FROM research_queue WHERE research_question_id = ?",
            (TEST_QUESTION_ID,),
        ).fetchone()[0]
        assert queue_count >= 1
        sources_before = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        claims_before = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
        candidate_id, _fetch_payload = run_live_source_acquisition(
            conn,
            research_question_id=TEST_QUESTION_ID,
            staging_dir=staging_dir,
        )
        assert candidate_id.startswith("disc_openalex_")
    finally:
        conn.close()

    artifacts = list(staging_dir.glob(f"{candidate_id}.*"))
    assert artifacts, "fetch-candidate must write a staged artifact file"
    artifact = artifacts[0]
    assert artifact.stat().st_size > 0

    conn = connect(temp_db)
    try:
        sources_after = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        claims_after = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
        assert sources_after == sources_before
        assert claims_after == claims_before
    finally:
        conn.close()
