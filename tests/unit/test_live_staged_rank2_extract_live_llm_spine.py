"""Opt-in live network + live Ollama rank-2 staged extract spine (ticket-230).

Default pytest collection excludes ``live_network`` and ``live_smoke`` tests.

Operator opt-in (real OpenAlex HTTP through rank-2 ingest; live Ollama extract only):

```powershell
$env:RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_STAGED_RANK2 = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_rank2_extract_live_llm_spine.py -m "live_network and live_smoke" -q
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
from rge.llm.schemas import CandidateClaimBatch_v0_1, SCHEMA_VERSION_0_1_0
from rge.modules.live_probe import LiveProbeGateError
from rge.modules.staged_spine_heuristics import is_staged_rank2_fetch_spine_chunk
from tests.unit.live_staged_candidates import select_rank2_candidate_id
from tests.unit.live_staged_proof_layers import run_live_openalex_discover

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
TEST_QUESTION_ID = "rq_live_staged_rank2_extract_live_llm_spine"
RANK2_CANDIDATE_ID = "disc_openalex_W1234567890"
REFERENCE_YEAR = 2026
RANK2_CHUNK_QUOTE = (
    "Constraint management improves AI-assisted creative team workflows."
)
RANK2_HTML = (
    b"<html><body><p>Constraint management improves AI-assisted creative team "
    b"workflows.</p></body></html>"
)


class _StubRank2StagedOllamaClient:
    provider = "ollama"
    model = "stub-qwen"

    def extract_claims(self, **kwargs: object) -> CandidateClaimBatch_v0_1:
        return CandidateClaimBatch_v0_1.model_validate(
            {
                "task_name": "claim_extraction",
                "schema_version": SCHEMA_VERSION_0_1_0,
                "items": [
                    {
                        "claim_text": RANK2_CHUNK_QUOTE,
                        "quote_span": RANK2_CHUNK_QUOTE,
                        "scope": "AI-assisted creative team workflows",
                        "subject": "Constraint management",
                        "predicate": "improves",
                        "object": "AI-assisted creative team workflows",
                        "evidence_type": "empirical",
                        "confidence": 0.85,
                        "limitations": [],
                        "domain": "creativity",
                        "domain_metadata": {},
                    },
                    {
                        "claim_text": (
                            "Constraint management always increases creative output."
                        ),
                        "quote_span": None,
                        "scope": "all creative teams",
                        "subject": "Constraint management",
                        "predicate": "increases",
                        "object": "creative output",
                        "evidence_type": "empirical",
                        "confidence": 0.9,
                        "limitations": [],
                        "domain": "creativity",
                        "domain_metadata": {},
                    },
                ],
            }
        )


def require_live_staged_rank2_extract_live_llm_env() -> None:
    """Skip unless operator explicitly opts into rank-2 staged Ollama extract."""
    allow = os.environ.get(
        "RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM", "0"
    ).strip().casefold()
    if allow not in ("1", "true", "yes"):
        pytest.skip(
            "live staged rank-2 extract requires "
            "RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM=1"
        )
    rank2 = os.environ.get("RGE_ALLOW_LIVE_STAGED_RANK2", "0").strip().casefold()
    if rank2 not in ("1", "true", "yes"):
        pytest.skip("live staged rank-2 extract requires RGE_ALLOW_LIVE_STAGED_RANK2=1")
    live = os.environ.get("RGE_ALLOW_LIVE_LLM", "0").strip().casefold()
    if live not in ("1", "true", "yes"):
        pytest.skip("live staged rank-2 extract requires RGE_ALLOW_LIVE_LLM=1")
    if os.environ.get("RGE_LLM_MODE", "mock") != "ollama":
        pytest.skip("live staged rank-2 extract requires RGE_LLM_MODE=ollama")
    network = os.environ.get("RGE_ALLOW_SOURCE_NETWORK", "0").strip().casefold()
    if network not in ("1", "true", "yes"):
        pytest.skip("live staged rank-2 extract requires RGE_ALLOW_SOURCE_NETWORK=1")
    if not os.environ.get("OPENALEX_MAILTO", "").strip():
        pytest.skip("live staged rank-2 extract requires OPENALEX_MAILTO")


def _assert_ollama_or_skip() -> None:
    from rge.config import load_config
    from rge.modules.live_probe import assert_ollama_health

    try:
        assert_ollama_health(load_config())
    except LiveProbeGateError as exc:
        pytest.skip(str(exc))


def test_require_live_staged_rank2_extract_live_llm_skips_without_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM", raising=False)
    with pytest.raises(pytest.skip.Exception):
        require_live_staged_rank2_extract_live_llm_env()


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "live_staged_rank2_extract_live.sqlite"


@pytest.fixture()
def staging_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "staged"
    directory.mkdir()
    artifact = directory / f"{RANK2_CANDIDATE_ID}.html"
    artifact.write_bytes(RANK2_HTML)
    return directory


@pytest.fixture()
def staged_db_with_candidates(temp_db: Path) -> Path:
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


def _ingest_rank2_staged_source(
    temp_db: Path,
    staging_dir: Path,
    *,
    candidate_id: str | None = None,
    capsys: pytest.CaptureFixture[str] | None = None,
) -> str:
    if candidate_id is None:
        conn = connect(temp_db)
        try:
            candidate_id = select_rank2_candidate_id(conn, TEST_QUESTION_ID)
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
    if capsys is not None:
        ingest_payload = json.loads(capsys.readouterr().out)
        return str(ingest_payload["source_id"])
    conn = connect(temp_db)
    try:
        row = conn.execute(
            "SELECT id FROM sources ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        assert row is not None
        return str(row["id"])
    finally:
        conn.close()


def test_rank2_staged_source_without_fallthrough_uses_explicit_fixture(
    temp_db: Path,
    staging_dir: Path,
    staged_db_with_candidates: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    source_id = _ingest_rank2_staged_source(temp_db, staging_dir)
    assert (
        main(
            [
                "extract-claims",
                "--source",
                source_id,
                "--db",
                str(temp_db),
                "--fixture",
                "staged_fetch_second_candidate_extract_claims.json",
            ]
        )
        == 0
    )
    conn = connect(temp_db)
    try:
        accepted = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ? AND status = 'accepted'",
            (source_id,),
        ).fetchone()[0]
        assert accepted >= 1
    finally:
        conn.close()


def test_live_staged_rank2_fallthrough_blocked_without_staged_live_gate(
    temp_db: Path,
    staging_dir: Path,
    staged_db_with_candidates: Path,
) -> None:
    source_id = _ingest_rank2_staged_source(temp_db, staging_dir)
    with patch.dict(
        os.environ,
        {"RGE_LLM_MODE": "ollama", "RGE_ALLOW_LIVE_LLM": "1"},
        clear=False,
    ):
        os.environ.pop("RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM", None)
        exit_code = main(
            [
                "extract-claims",
                "--source",
                source_id,
                "--db",
                str(temp_db),
                "--live-staged-rank2-extract-fallthrough",
            ]
        )
    assert exit_code == 1


def test_live_staged_rank2_fallthrough_blocked_on_default_graph_db(
    temp_db: Path,
    staging_dir: Path,
    staged_db_with_candidates: Path,
) -> None:
    source_id = _ingest_rank2_staged_source(temp_db, staging_dir)
    with patch.dict(
        os.environ,
        {
            "RGE_LLM_MODE": "ollama",
            "RGE_ALLOW_LIVE_LLM": "1",
            "RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM": "1",
        },
        clear=False,
    ):
        exit_code = main(
            [
                "extract-claims",
                "--source",
                source_id,
                "--db",
                "data/db/creative_research.sqlite",
                "--live-staged-rank2-extract-fallthrough",
            ]
        )
    assert exit_code == 1


def test_rank1_fallthrough_rejects_rank2_chunk(
    temp_db: Path,
    staging_dir: Path,
    staged_db_with_candidates: Path,
) -> None:
    source_id = _ingest_rank2_staged_source(temp_db, staging_dir)
    with patch.dict(
        os.environ,
        {
            "RGE_LLM_MODE": "ollama",
            "RGE_ALLOW_LIVE_LLM": "1",
            "RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM": "1",
        },
        clear=False,
    ):
        exit_code = main(
            [
                "extract-claims",
                "--source",
                source_id,
                "--db",
                str(temp_db),
                "--live-staged-fallthrough",
            ]
        )
    assert exit_code == 1


def test_mocked_live_staged_rank2_fallthrough_persists_validated_claims(
    temp_db: Path,
    staging_dir: Path,
    staged_db_with_candidates: Path,
) -> None:
    source_id = _ingest_rank2_staged_source(temp_db, staging_dir)
    with patch.dict(
        os.environ,
        {
            "RGE_LLM_MODE": "ollama",
            "RGE_ALLOW_LIVE_LLM": "1",
            "RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM": "1",
        },
        clear=False,
    ):
        with patch(
            "rge.modules.live_extraction_write.assert_ollama_health",
            return_value={"model_available": True},
        ):
            with patch(
                "rge.modules.live_extraction_write.get_model_client",
                return_value=_StubRank2StagedOllamaClient(),
            ):
                exit_code = main(
                    [
                        "extract-claims",
                        "--source",
                        source_id,
                        "--db",
                        str(temp_db),
                        "--live-staged-rank2-extract-fallthrough",
                    ]
                )
    assert exit_code == 0

    conn = connect(temp_db)
    try:
        accepted = conn.execute(
            "SELECT claim_text FROM claims WHERE source_id = ? AND status = 'accepted'",
            (source_id,),
        ).fetchall()
        rejected = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE source_id = ? AND status = 'rejected'",
            (source_id,),
        ).fetchone()[0]
        assert len(accepted) >= 1
        assert rejected >= 1
    finally:
        conn.close()


@pytest.fixture()
def live_staged_rank2_extract_live_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_STAGED_RANK2", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)


def _require_rank2_chunk_or_skip(staging_dir: Path, candidate_id: str) -> None:
    artifact_path = staging_dir / f"{candidate_id}.html"
    if not artifact_path.is_file():
        pytest.skip(f"rank-2 artifact missing after fetch: {artifact_path}")
    text = artifact_path.read_text(encoding="utf-8", errors="replace")
    if not is_staged_rank2_fetch_spine_chunk(text):
        pytest.skip(
            json.dumps(
                {
                    "reason": "unsuitable_live_rank2_artifact",
                    "detail": (
                        "Live rank-2 fetch succeeded but artifact text lacks "
                        "constraint management marker required for rank-2 live extract."
                    ),
                    "candidate_id": candidate_id,
                },
                indent=2,
            )
        )


@pytest.mark.live_network
@pytest.mark.live_smoke
def test_live_openalex_rank2_discover_fetch_ingest_live_extract(
    live_staged_rank2_extract_live_env: None,
    temp_db: Path,
    staging_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    require_live_staged_rank2_extract_live_llm_env()
    _assert_ollama_or_skip()

    run_live_openalex_discover(temp_db, TEST_QUESTION_ID, query="human AI creativity")
    capsys.readouterr()

    conn = connect(temp_db)
    try:
        claims_before = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
        candidate_id = select_rank2_candidate_id(conn, TEST_QUESTION_ID)
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
    capsys.readouterr()
    _require_rank2_chunk_or_skip(staging_dir, candidate_id)

    source_id = _ingest_rank2_staged_source(
        temp_db,
        staging_dir,
        candidate_id=candidate_id,
        capsys=capsys,
    )
    assert (
        main(
            [
                "extract-claims",
                "--source",
                source_id,
                "--db",
                str(temp_db),
                "--live-staged-rank2-extract-fallthrough",
            ]
        )
        == 0
    )

    extract_payload = json.loads(capsys.readouterr().out)
    assert extract_payload["status"] in ("completed", "already_extracted")
    assert extract_payload.get("live_staged_rank2_fallthrough") is True
    assert extract_payload["accepted_count"] >= 1
    assert extract_payload.get("provider") == "ollama"

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
