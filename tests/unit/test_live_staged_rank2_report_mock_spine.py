"""Opt-in live network + rank-2 second-candidate mock spine (ticket-190).

Default pytest collection excludes ``live_network`` tests (see ``pyproject.toml``).

Operator opt-in (real OpenAlex HTTP for rank-2 candidate; second-candidate fixtures):

```powershell
$env:RGE_ALLOW_LIVE_STAGED_RANK2 = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_rank2_report_mock_spine.py -m live_network -q
```
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.cli import main
from rge.db.connection import connect
from rge.db.repositories import RunReportRepository

REPO_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_BASE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
TEST_QUESTION_ID = "rq_live_staged_rank2_report_mock_spine"
STAGED_RUN_ID = "run_live_staged_rank2_report_mock_spine"
STAGED_TOPIC = "Constraint management in AI-assisted creative teams (live rank-2 proof)"
EXTRACT_FIXTURE = "staged_fetch_second_candidate_extract_claims.json"
LINK_FIXTURE = "staged_fetch_second_candidate_link_concepts.json"
BUILD_FIXTURE = "staged_fetch_second_candidate_build_relationships.json"
DETECT_FIXTURE = "staged_fetch_second_candidate_detect_contradictions.json"


def require_live_staged_rank2_env() -> None:
    """Skip unless operator explicitly opts into live staged rank-2 mock spine."""
    allow = os.environ.get("RGE_ALLOW_LIVE_STAGED_RANK2", "0").strip().casefold()
    if allow not in ("1", "true", "yes"):
        pytest.skip("live staged rank2 requires RGE_ALLOW_LIVE_STAGED_RANK2=1")
    network = os.environ.get("RGE_ALLOW_SOURCE_NETWORK", "0").strip().casefold()
    if network not in ("1", "true", "yes"):
        pytest.skip("live staged rank2 requires RGE_ALLOW_SOURCE_NETWORK=1")
    if not os.environ.get("OPENALEX_MAILTO", "").strip():
        pytest.skip("live staged rank2 requires OPENALEX_MAILTO")


def test_require_live_staged_rank2_skips_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_ALLOW_LIVE_STAGED_RANK2", raising=False)
    with pytest.raises(pytest.skip.Exception):
        require_live_staged_rank2_env()


def _seed_domain_opposing_context(temp_db: Path) -> None:
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
def live_staged_rank2_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_RANK2", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "live_staged_rank2_report_mock.sqlite"


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
def test_live_openalex_rank2_through_report_mock_spine(
    live_staged_rank2_env: None,
    temp_db: Path,
    staging_dir: Path,
    report_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    require_live_staged_rank2_env()
    _seed_domain_opposing_context(temp_db)

    assert (
        main(
            [
                "discover-sources",
                "--provider",
                "openalex",
                "--query",
                "human AI creativity constraint",
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
        candidate_count = conn.execute(
            """
            SELECT COUNT(*) FROM candidate_sources
            WHERE research_question_id = ?
            """,
            (TEST_QUESTION_ID,),
        ).fetchone()[0]
        assert candidate_count >= 2, "live discover must enqueue at least 2 candidates"
        candidate_row = conn.execute(
            """
            SELECT id
            FROM candidate_sources
            WHERE research_question_id = ?
            ORDER BY priority_score DESC
            LIMIT 1 OFFSET 1
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
                EXTRACT_FIXTURE,
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
                LINK_FIXTURE,
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
                BUILD_FIXTURE,
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
                DETECT_FIXTURE,
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
    assert report_payload["run_id"] == STAGED_RUN_ID
    assert report_payload["report_count"] >= 1

    conn = connect(temp_db)
    try:
        assert RunReportRepository(conn).count() >= 1
        rank2_sources = conn.execute(
            """
            SELECT COUNT(*) FROM sources
            WHERE id = ?
            """,
            (source_id,),
        ).fetchone()[0]
        assert rank2_sources == 1
    finally:
        conn.close()

    assert (report_dir / "run_report_latest.json").is_file()
