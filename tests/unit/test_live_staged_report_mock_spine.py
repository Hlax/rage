"""Opt-in live network + deterministic generate-run-report spine (ticket-187).

Default pytest collection excludes ``live_network`` tests (see ``pyproject.toml``).

Operator opt-in (real OpenAlex HTTP through reconcile; deterministic report only):

```powershell
$env:RGE_ALLOW_LIVE_STAGED_REPORT = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_report_mock_spine.py -m live_network -q
```
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.cli import main
from rge.db.connection import connect
from tests.unit.live_staged_candidates import select_rank1_candidate_id
from rge.db.repositories import RunReportRepository
from tests.unit.staged_domain_seed import seed_domain_opposing_context

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_QUESTION_ID = "rq_live_staged_report_mock_spine"
STAGED_RUN_ID = "run_live_staged_report_mock_spine"
STAGED_TOPIC = "Human-AI co-creativity live staged report proof"
STAGED_EXTRACT_FIXTURE = "staged_fetch_extract_claims.json"
STAGED_LINK_FIXTURE = "staged_fetch_link_concepts.json"
STAGED_BUILD_FIXTURE = "staged_fetch_build_relationships.json"
STAGED_DETECT_FIXTURE = "staged_fetch_detect_contradictions.json"


def require_live_staged_report_env() -> None:
    """Skip unless operator explicitly opts into live staged report spine."""
    allow = os.environ.get("RGE_ALLOW_LIVE_STAGED_REPORT", "0").strip().casefold()
    if allow not in ("1", "true", "yes"):
        pytest.skip("live staged report requires RGE_ALLOW_LIVE_STAGED_REPORT=1")
    network = os.environ.get("RGE_ALLOW_SOURCE_NETWORK", "0").strip().casefold()
    if network not in ("1", "true", "yes"):
        pytest.skip("live staged report requires RGE_ALLOW_SOURCE_NETWORK=1")
    if not os.environ.get("OPENALEX_MAILTO", "").strip():
        pytest.skip("live staged report requires OPENALEX_MAILTO")


def test_require_live_staged_report_skips_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_ALLOW_LIVE_STAGED_REPORT", raising=False)
    with pytest.raises(pytest.skip.Exception):
        require_live_staged_report_env()



@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def live_staged_report_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_REPORT", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "live_staged_report_mock.sqlite"


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


@pytest.mark.live_network
def test_live_openalex_discover_through_report_mock_spine(
    live_staged_report_env: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    require_live_staged_report_env()
    seed_domain_opposing_context(temp_db)

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
        candidate_id = select_rank1_candidate_id(conn, TEST_QUESTION_ID)
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

    assert (
        main(
            [
                "generate-run-report",
                "--run-id",
                STAGED_RUN_ID,
                "--topic",
                STAGED_TOPIC,
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
                "--output-dir",
                str(report_dir),
            ]
        )
        == 0
    )

    report_payload = json.loads(capsys.readouterr().out)
    assert report_payload["status"] == "generated"
    assert report_payload["command"] == "generate-run-report"
    assert report_payload["run_id"] == STAGED_RUN_ID
    assert report_payload["report_count"] >= 1

    conn = connect(temp_db)
    try:
        assert RunReportRepository(conn).count() >= 1
        row = conn.execute(
            "SELECT run_id, topic FROM run_reports WHERE run_id = ?",
            (STAGED_RUN_ID,),
        ).fetchone()
        assert row is not None
        assert row["topic"] == STAGED_TOPIC
    finally:
        conn.close()

    assert (report_dir / "run_report_latest.json").is_file()
