"""Opt-in live network + mock-fixture build spine (ticket-178).

Default pytest collection excludes ``live_network`` tests (see ``pyproject.toml``).

Operator opt-in (real OpenAlex HTTP through mock link; mock-fixture build only):

```powershell
$env:RGE_ALLOW_LIVE_STAGED_BUILD = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_build_mock_spine.py -m live_network -q
```
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.cli import main
from rge.db.connection import connect

TEST_QUESTION_ID = "rq_live_staged_build_mock_spine"
STAGED_EXTRACT_FIXTURE = "staged_fetch_extract_claims.json"
STAGED_LINK_FIXTURE = "staged_fetch_link_concepts.json"
STAGED_BUILD_FIXTURE = "staged_fetch_build_relationships.json"


def require_live_staged_build_env() -> None:
    """Skip unless operator explicitly opts into live staged build mock spine."""
    allow = os.environ.get("RGE_ALLOW_LIVE_STAGED_BUILD", "0").strip().casefold()
    if allow not in ("1", "true", "yes"):
        pytest.skip("live staged build requires RGE_ALLOW_LIVE_STAGED_BUILD=1")
    network = os.environ.get("RGE_ALLOW_SOURCE_NETWORK", "0").strip().casefold()
    if network not in ("1", "true", "yes"):
        pytest.skip("live staged build requires RGE_ALLOW_SOURCE_NETWORK=1")
    if not os.environ.get("OPENALEX_MAILTO", "").strip():
        pytest.skip("live staged build requires OPENALEX_MAILTO")


def test_require_live_staged_build_skips_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_ALLOW_LIVE_STAGED_BUILD", raising=False)
    with pytest.raises(pytest.skip.Exception):
        require_live_staged_build_env()


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def live_staged_build_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_BUILD", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "live_staged_build_mock.sqlite"


@pytest.fixture()
def staging_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "staged"
    directory.mkdir()
    return directory


@pytest.mark.live_network
def test_live_openalex_discover_through_build_mock_fixture(
    live_staged_build_env: None,
    temp_db: Path,
    staging_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    require_live_staged_build_env()

    assert (
        main(
            [
                "discover-sources",
                "--provider",
                "openalex",
                "--query",
                "human AI creativity",
                "--rank-only",
                "--enqueue",
                "--question",
                TEST_QUESTION_ID,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        candidate_row = conn.execute(
            """
            SELECT id
            FROM candidate_sources
            WHERE research_question_id = ?
            ORDER BY priority_score DESC
            LIMIT 1
            """,
            (TEST_QUESTION_ID,),
        ).fetchone()
        assert candidate_row is not None
        candidate_id = candidate_row["id"]
        relationships_before = conn.execute(
            "SELECT COUNT(*) FROM relationships"
        ).fetchone()[0]
    finally:
        conn.close()

    assert (
        main(
            [
                "fetch-candidate",
                "--candidate",
                candidate_id,
                "--db",
                str(temp_db),
                "--out",
                str(staging_dir),
            ]
        )
        == 0
    )

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

    build_payload = json.loads(capsys.readouterr().out)
    assert build_payload["status"] == "completed"
    assert build_payload["relationship_count"] >= 1

    conn = connect(temp_db)
    try:
        relationships_after = conn.execute(
            "SELECT COUNT(*) FROM relationships"
        ).fetchone()[0]
        source_relationships = conn.execute(
            """
            SELECT COUNT(*) FROM relationships
            WHERE source_id = ?
            """,
            (source_id,),
        ).fetchone()[0]
        assert relationships_after > relationships_before
        assert source_relationships >= 1
    finally:
        conn.close()
