"""Opt-in live network + deterministic reconcile spine (ticket-184).

Default pytest collection excludes ``live_network`` tests (see ``pyproject.toml``).

Operator opt-in (real OpenAlex HTTP through mock detect; deterministic reconcile only):

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

REPO_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_BASE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
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


def _seed_domain_opposing_context(temp_db: Path) -> None:
    """Seed GT7-style base graph so staged qualification has an opposing domain edge."""
    assert (
        main(
            [
                "ingest",
                str(DOMAIN_BASE_SOURCE),
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    conn = connect(temp_db)
    try:
        base_source_id = conn.execute("SELECT id FROM sources").fetchone()["id"]
    finally:
        conn.close()
    assert main(["extract-claims", "--source", base_source_id, "--db", str(temp_db)]) == 0
    assert main(["link-concepts", "--source", base_source_id, "--db", str(temp_db)]) == 0
    assert main(["build-relationships", "--source", base_source_id, "--db", str(temp_db)]) == 0


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
def test_live_openalex_discover_through_reconcile_mock_spine(
    live_staged_reconcile_env: None,
    temp_db: Path,
    staging_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    require_live_staged_reconcile_env()
    _seed_domain_opposing_context(temp_db)

    conn = connect(temp_db)
    try:
        score_events_before = conn.execute("SELECT COUNT(*) FROM score_events").fetchone()[0]
    finally:
        conn.close()

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
            ORDER BY rank ASC
            LIMIT 1
            """,
            (TEST_QUESTION_ID,),
        ).fetchone()
        assert candidate_row is not None
        candidate_id = candidate_row["id"]
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
