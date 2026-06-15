"""Opt-in live network proof for staged discover + fetch + ingest (ticket-168).

Default pytest collection excludes ``live_network`` tests (see ``pyproject.toml``).

Operator opt-in (real OpenAlex HTTP; no live LLM):

```powershell
$env:RGE_ALLOW_LIVE_STAGED_INGEST = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_ingest_validation.py -m live_network -q
```
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.cli import main
from rge.db.connection import connect
from tests.unit.live_staged_proof_layers import (
    run_live_openalex_discover,
    run_live_source_acquisition,
)

TEST_QUESTION_ID = "rq_live_staged_ingest_validation"


def require_live_staged_ingest_env() -> None:
    """Skip unless operator explicitly opts into live staged ingest proof."""
    allow = os.environ.get("RGE_ALLOW_LIVE_STAGED_INGEST", "0").strip().casefold()
    if allow not in ("1", "true", "yes"):
        pytest.skip("live staged ingest requires RGE_ALLOW_LIVE_STAGED_INGEST=1")
    network = os.environ.get("RGE_ALLOW_SOURCE_NETWORK", "0").strip().casefold()
    if network not in ("1", "true", "yes"):
        pytest.skip("live staged ingest requires RGE_ALLOW_SOURCE_NETWORK=1")
    if not os.environ.get("OPENALEX_MAILTO", "").strip():
        pytest.skip("live staged ingest requires OPENALEX_MAILTO")


def test_require_live_staged_ingest_skips_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_ALLOW_LIVE_STAGED_INGEST", raising=False)
    with pytest.raises(pytest.skip.Exception):
        require_live_staged_ingest_env()


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def live_staged_ingest_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_INGEST", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "live_staged_ingest.sqlite"


@pytest.fixture()
def staging_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "staged"
    directory.mkdir()
    return directory


@pytest.mark.live_network
def test_live_openalex_discover_fetch_ingest_writes_source_and_chunks(
    live_staged_ingest_env: None,
    temp_db: Path,
    staging_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    require_live_staged_ingest_env()

    run_live_openalex_discover(temp_db, TEST_QUESTION_ID)

    conn = connect(temp_db)
    try:
        sources_before = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        chunks_before = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
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
    assert artifacts[0].stat().st_size > 0

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
    assert ingest_payload["status"] == "ingested"
    assert ingest_payload["candidate_id"] == candidate_id
    assert ingest_payload["chunk_count"] >= 1

    conn = connect(temp_db)
    try:
        sources_after = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        chunks_after = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        claims_after = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
        assert sources_after == sources_before + 1
        assert chunks_after > chunks_before
        assert claims_after == claims_before
    finally:
        conn.close()
