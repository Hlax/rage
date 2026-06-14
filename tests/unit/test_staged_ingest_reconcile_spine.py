"""Phase 3 spine through reconcile-scores on staged-ingested source (ticket-148)."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.db.connection import connect
from rge.modules.score_reconciler import (
    FORMULA_VERSION,
    STRONGER_SOURCE_BOOST,
    STRONGER_SOURCE_REASON,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
DOMAIN_BASE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
RECONCILE_CONTRACT = (
    REPO_ROOT / "fixtures" / "llm_outputs" / "staged_fetch_reconcile_scores.json"
)
TEST_QUESTION_ID = "rq_staged_reconcile_spine"
CANDIDATE_ID = "disc_openalex_W2741809807"
STAGED_CHUNK_TEXT = "Human-AI co-creativity supports diverse songwriting outputs."
SAMPLE_HTML = (
    f"<html><body><p>{STAGED_CHUNK_TEXT}</p></body></html>"
).encode("utf-8")


@pytest.fixture(autouse=True)
def mock_llm_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def mock_network_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "staged_reconcile_spine.sqlite"


@pytest.fixture()
def staging_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "staged"
    directory.mkdir()
    return directory


@pytest.fixture()
def reconcile_contract() -> dict:
    payload = json.loads(RECONCILE_CONTRACT.read_text(encoding="utf-8"))
    return payload["items"][0]


def _mock_urlopen_factory(payload: dict):
    body = json.dumps(payload).encode("utf-8")

    def _urlopen(request, timeout=30):  # noqa: ARG001
        return io.BytesIO(body)

    return _urlopen


def _mock_html_urlopen(html: bytes, content_type: str = "text/html; charset=utf-8"):
    class _Response(io.BytesIO):
        headers = {"Content-Type": content_type}

    def _urlopen(request, timeout=30):  # noqa: ARG001
        return _Response(html)

    return _urlopen


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


def _run_spine_through_detect_contradictions(temp_db: Path, staging_dir: Path) -> str:
    _seed_domain_opposing_context(temp_db)

    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text())
    discover_args = [
        "discover-sources",
        "--provider",
        "openalex",
        "--query",
        "human AI creativity",
        "--rank-only",
        "--enqueue",
        "--db",
        str(temp_db),
        "--question",
        TEST_QUESTION_ID,
    ]
    with patch(
        "rge.modules.source_providers.openalex.urllib.request.urlopen",
        _mock_urlopen_factory(fixture_payload),
    ):
        assert main(discover_args) == 0

    with patch("rge.modules.fetcher.urllib.request.urlopen", _mock_html_urlopen(SAMPLE_HTML)):
        assert main(
            [
                "fetch-candidate",
                "--candidate",
                CANDIDATE_ID,
                "--db",
                str(temp_db),
                "--out",
                str(staging_dir),
            ]
        ) == 0

    assert main(
        [
            "ingest-staged",
            "--domain",
            "creativity",
            "--candidate",
            CANDIDATE_ID,
            "--staging-dir",
            str(staging_dir),
            "--db",
            str(temp_db),
        ]
    ) == 0

    conn = connect(temp_db)
    try:
        source_id = conn.execute(
            """
            SELECT id FROM sources
            WHERE title LIKE '%songwriting%'
            ORDER BY rowid DESC
            LIMIT 1
            """
        ).fetchone()["id"]
    finally:
        conn.close()

    assert main(["extract-claims", "--source", source_id, "--db", str(temp_db)]) == 0
    assert main(["link-concepts", "--source", source_id, "--db", str(temp_db)]) == 0
    assert main(["build-relationships", "--source", source_id, "--db", str(temp_db)]) == 0
    assert main(["detect-contradictions", "--source", source_id, "--db", str(temp_db)]) == 0
    return source_id


def test_staged_reconcile_contract_fixture(reconcile_contract: dict) -> None:
    assert reconcile_contract["predicate"] == "may_increase"
    assert reconcile_contract["expected_confidence"] == pytest.approx(
        reconcile_contract["initial_confidence"] + reconcile_contract["expected_boost"]
    )


def test_staged_spine_through_reconcile_scores(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
    reconcile_contract: dict,
) -> None:
    source_id = _run_spine_through_detect_contradictions(temp_db, staging_dir)
    assert main(["reconcile-scores", "--source", source_id, "--db", str(temp_db)]) == 0

    conn = connect(temp_db)
    try:
        relationship = conn.execute(
            """
            SELECT r.id, r.confidence, r.scope
            FROM relationships r
            JOIN concepts sub ON sub.id = r.subject_concept_id
            JOIN concepts obj ON obj.id = r.object_concept_id
            WHERE sub.label = ?
              AND obj.label = ?
              AND r.predicate = ?
            """,
            (
                reconcile_contract["subject_concept"],
                reconcile_contract["object_concept"],
                reconcile_contract["predicate"],
            ),
        ).fetchone()
        assert relationship is not None
        assert relationship["scope"] == reconcile_contract["scope"]
        assert float(relationship["confidence"]) == reconcile_contract["expected_confidence"]

        event = conn.execute(
            """
            SELECT old_score, new_score, reason, formula_version
            FROM score_events
            WHERE entity_type = 'relationship' AND entity_id = ?
            """,
            (relationship["id"],),
        ).fetchone()
        assert event is not None
        assert float(event["old_score"]) == reconcile_contract["initial_confidence"]
        assert float(event["new_score"]) == reconcile_contract["expected_confidence"]
        assert event["reason"] == STRONGER_SOURCE_REASON
        assert event["formula_version"] == FORMULA_VERSION
    finally:
        conn.close()


def test_reconcile_scores_staged_spine_is_idempotent(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
) -> None:
    source_id = _run_spine_through_detect_contradictions(temp_db, staging_dir)
    args = ["reconcile-scores", "--source", source_id, "--db", str(temp_db)]
    assert main(args) == 0
    assert main(args) == 0

    conn = connect(temp_db)
    try:
        count = conn.execute("SELECT COUNT(*) FROM score_events").fetchone()[0]
        assert count == 1
    finally:
        conn.close()


def test_reconcile_scores_cli_json_for_staged_spine(
    mock_network_env: None,
    temp_db: Path,
    staging_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_id = _run_spine_through_detect_contradictions(temp_db, staging_dir)
    capsys.readouterr()
    assert main(["reconcile-scores", "--source", source_id, "--db", str(temp_db)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["score_events_created"] == 1
    assert payload["relationships_updated"] == 1
