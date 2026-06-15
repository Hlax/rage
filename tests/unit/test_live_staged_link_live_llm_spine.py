"""Opt-in live network + live Ollama staged link spine (ticket-208).

Default pytest collection excludes ``live_network`` and ``live_smoke`` tests.

Operator opt-in (real OpenAlex HTTP through mock extract; live Ollama link only):

```powershell
$env:RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_link_live_llm_spine.py -m "live_network and live_smoke" -q
```
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import main
from rge.db.connection import connect, ensure_database
from rge.llm.schemas import CandidateConceptLinkBatch_v0_1, SCHEMA_VERSION_0_1_0
from rge.modules.live_probe import LiveProbeGateError
from tests.unit.live_staged_candidates import select_rank1_candidate_id

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
TEST_QUESTION_ID = "rq_live_staged_link_live_llm_spine"
CANDIDATE_ID = "disc_openalex_W2741809807"
REFERENCE_YEAR = 2026
STAGED_EXTRACT_FIXTURE = "staged_fetch_extract_claims.json"


class _StubStagedLinkOllamaClient:
    provider = "ollama"
    model = "stub-qwen"

    def link_concepts(self, **kwargs: object) -> CandidateConceptLinkBatch_v0_1:
        claims = kwargs["claims"]
        claim_id = claims[0]["id"]
        return CandidateConceptLinkBatch_v0_1.model_validate(
            {
                "task_name": "concept_linking",
                "schema_version": SCHEMA_VERSION_0_1_0,
                "items": [
                    {
                        "claim_id": claim_id,
                        "concept_label": "co-creation",
                        "role": "subject",
                        "confidence": 0.82,
                        "domain_metadata": {
                            "track": "human-AI",
                            "creative_phase": "execution",
                            "measured_dimension": "semantic diversity",
                        },
                    },
                    {
                        "claim_id": claim_id,
                        "concept_label": "semantic diversity",
                        "role": "object",
                        "confidence": 0.88,
                        "domain_metadata": {
                            "track": "human-AI",
                            "creative_phase": "execution",
                            "measured_dimension": "semantic diversity",
                        },
                    },
                ],
            }
        )


def require_live_staged_link_live_llm_env() -> None:
    """Skip unless operator explicitly opts into live staged Ollama link."""
    allow = os.environ.get("RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM", "0").strip().casefold()
    if allow not in ("1", "true", "yes"):
        pytest.skip("live staged link requires RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM=1")
    live = os.environ.get("RGE_ALLOW_LIVE_LLM", "0").strip().casefold()
    if live not in ("1", "true", "yes"):
        pytest.skip("live staged link requires RGE_ALLOW_LIVE_LLM=1")
    if os.environ.get("RGE_LLM_MODE", "mock") != "ollama":
        pytest.skip("live staged link requires RGE_LLM_MODE=ollama")
    network = os.environ.get("RGE_ALLOW_SOURCE_NETWORK", "0").strip().casefold()
    if network not in ("1", "true", "yes"):
        pytest.skip("live staged link requires RGE_ALLOW_SOURCE_NETWORK=1")
    if not os.environ.get("OPENALEX_MAILTO", "").strip():
        pytest.skip("live staged link requires OPENALEX_MAILTO")


def _assert_ollama_or_skip() -> None:
    from rge.config import load_config
    from rge.modules.live_probe import assert_ollama_health

    try:
        assert_ollama_health(load_config())
    except LiveProbeGateError as exc:
        pytest.skip(str(exc))


def test_require_live_staged_link_live_llm_skips_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM", raising=False)
    with pytest.raises(pytest.skip.Exception):
        require_live_staged_link_live_llm_env()


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "live_staged_link_live.sqlite"


@pytest.fixture()
def staging_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "staged"
    directory.mkdir()
    artifact = directory / f"{CANDIDATE_ID}.html"
    artifact.write_bytes(
        b"<html><body><p>Human-AI co-creativity supports diverse songwriting outputs.</p></body></html>"
    )
    return directory


@pytest.fixture()
def staged_db_with_candidate(temp_db: Path) -> Path:
    from rge.modules.research_queue import (
        enqueue_discovered_candidates,
        rank_discovered_candidates,
    )
    from rge.modules.source_providers.openalex import OpenAlexProvider

    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text(encoding="utf-8"))
    provider = OpenAlexProvider(
        urlopen=lambda request, timeout=30: io.BytesIO(  # noqa: ARG005
            json.dumps(fixture_payload).encode("utf-8")
        )
    )
    candidates = provider.discover("human AI creativity", "creativity", 10)
    ranked = rank_discovered_candidates(
        candidates,
        query="human AI creativity",
        reference_year=REFERENCE_YEAR,
    )
    conn = ensure_database(temp_db)
    try:
        enqueue_discovered_candidates(
            conn,
            ranked,
            provider_id="openalex",
            research_question_id=TEST_QUESTION_ID,
        )
    finally:
        conn.close()
    return temp_db


def _ingest_and_extract(
    temp_db: Path,
    staging_dir: Path,
) -> str:
    conn = connect(temp_db)
    try:
        candidate_id = select_rank1_candidate_id(conn, TEST_QUESTION_ID)
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
    conn = connect(temp_db)
    try:
        row = conn.execute(
            "SELECT id FROM sources ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        assert row is not None
        source_id = str(row["id"])
    finally:
        conn.close()

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
    return source_id


def test_staged_source_without_fallthrough_still_uses_auto_mock_link_fixture(
    temp_db: Path,
    staging_dir: Path,
    staged_db_with_candidate: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    source_id = _ingest_and_extract(temp_db, staging_dir)
    assert main(["link-concepts", "--source", source_id, "--db", str(temp_db)]) == 0

    conn = connect(temp_db)
    try:
        links = conn.execute(
            """
            SELECT COUNT(*) FROM claim_concepts cc
            JOIN claims c ON c.id = cc.claim_id
            WHERE c.source_id = ? AND c.status = 'accepted'
            """,
            (source_id,),
        ).fetchone()[0]
        assert links >= 1
    finally:
        conn.close()


def test_live_staged_link_fallthrough_blocked_without_staged_live_gate(
    temp_db: Path,
    staging_dir: Path,
    staged_db_with_candidate: Path,
) -> None:
    source_id = _ingest_and_extract(temp_db, staging_dir)
    with patch.dict(
        os.environ,
        {"RGE_LLM_MODE": "ollama", "RGE_ALLOW_LIVE_LLM": "1"},
        clear=False,
    ):
        os.environ.pop("RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM", None)
        exit_code = main(
            [
                "link-concepts",
                "--source",
                source_id,
                "--db",
                str(temp_db),
                "--live-staged-link-fallthrough",
            ]
        )
    assert exit_code == 1


def test_live_staged_link_fallthrough_blocked_on_default_graph_db(
    temp_db: Path,
    staging_dir: Path,
    staged_db_with_candidate: Path,
) -> None:
    source_id = _ingest_and_extract(temp_db, staging_dir)
    with patch.dict(
        os.environ,
        {
            "RGE_LLM_MODE": "ollama",
            "RGE_ALLOW_LIVE_LLM": "1",
            "RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM": "1",
        },
        clear=False,
    ):
        exit_code = main(
            [
                "link-concepts",
                "--source",
                source_id,
                "--db",
                "data/db/creative_research.sqlite",
                "--live-staged-link-fallthrough",
            ]
        )
    assert exit_code == 1


def test_mocked_live_staged_link_fallthrough_persists_validated_links(
    temp_db: Path,
    staging_dir: Path,
    staged_db_with_candidate: Path,
) -> None:
    source_id = _ingest_and_extract(temp_db, staging_dir)
    with patch.dict(
        os.environ,
        {
            "RGE_LLM_MODE": "ollama",
            "RGE_ALLOW_LIVE_LLM": "1",
            "RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM": "1",
        },
        clear=False,
    ):
        with patch(
            "rge.modules.live_probe.assert_ollama_health",
            return_value={"model_available": True},
        ):
            with patch(
                "rge.modules.concept_linker.get_model_client",
                return_value=_StubStagedLinkOllamaClient(),
            ):
                exit_code = main(
                    [
                        "link-concepts",
                        "--source",
                        source_id,
                        "--db",
                        str(temp_db),
                        "--live-staged-link-fallthrough",
                    ]
                )
    assert exit_code == 0

    conn = connect(temp_db)
    try:
        links = conn.execute(
            """
            SELECT COUNT(*) FROM claim_concepts cc
            JOIN claims c ON c.id = cc.claim_id
            WHERE c.source_id = ? AND c.status = 'accepted'
            """,
            (source_id,),
        ).fetchone()[0]
        assert links >= 1
    finally:
        conn.close()


@pytest.fixture()
def live_staged_link_live_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)


@pytest.mark.live_network
@pytest.mark.live_smoke
def test_live_openalex_discover_through_live_link(
    live_staged_link_live_env: None,
    temp_db: Path,
    staging_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    require_live_staged_link_live_llm_env()
    _assert_ollama_or_skip()

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
        links_before = conn.execute("SELECT COUNT(*) FROM claim_concepts").fetchone()[0]
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
                "--db",
                str(temp_db),
                "--live-staged-link-fallthrough",
            ]
        )
        == 0
    )

    link_payload = json.loads(capsys.readouterr().out)
    assert link_payload["status"] in ("completed", "already_linked")
    assert link_payload.get("live_staged_link_fallthrough") is True
    assert link_payload["link_count"] >= 1
    assert link_payload.get("provider") == "ollama"

    conn = connect(temp_db)
    try:
        links_after = conn.execute("SELECT COUNT(*) FROM claim_concepts").fetchone()[0]
        source_links = conn.execute(
            """
            SELECT COUNT(*) FROM claim_concepts cc
            JOIN claims c ON c.id = cc.claim_id
            WHERE c.source_id = ? AND c.status = 'accepted'
            """,
            (source_id,),
        ).fetchone()[0]
        assert links_after > links_before
        assert source_links >= 1
    finally:
        conn.close()
