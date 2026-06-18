"""Autonomous researcher loop staged-spine mock orchestrator proof (ticket-337).

Mock-only pytest: closed loop on staged discover→report spine without live Ollama.
"""

from __future__ import annotations

import io
import json
from itertools import cycle
from pathlib import Path
from unittest.mock import patch

import pytest

from rge.cli import (
    STAGED_FIXTURE_QUESTION_ID,
    STAGED_FIXTURE_RUN_ID,
    GOLDEN_MVP_TOPIC,
    main,
)
from rge.modules.autonomous_researcher_loop import (
    COMMAND,
    LOOP_SCHEMA_VERSION,
    execute_autonomous_researcher_loop,
)
from rge.modules.ticket_writer import improvement_draft_is_actionable

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENALEX_FIXTURE = REPO_ROOT / "fixtures" / "source_providers" / "openalex_works_sample.json"
RANK1_HTML = (
    b"<html><body><p>Human-AI co-creativity supports diverse songwriting outputs.</p></body></html>"
)
RANK2_HTML = (
    b"<html><body><p>Constraint management improves AI-assisted creative team workflows.</p></body></html>"
)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "autonomous_staged_loop.sqlite"


@pytest.fixture()
def artifact_dir(tmp_path: Path) -> Path:
    return tmp_path / "autonomous_staged_loop_artifacts"


@pytest.fixture()
def staging_dir(artifact_dir: Path) -> Path:
    directory = artifact_dir / "staging"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


@pytest.fixture(autouse=True)
def mock_llm_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)


@pytest.fixture(autouse=True)
def _ensure_provider_registry() -> None:
    import rge.modules.source_providers  # noqa: F401


@pytest.fixture(autouse=True)
def mock_network_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    monkeypatch.delenv("RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR", raising=False)


def _staged_network_urlopen(openalex_payload: dict, html_sequence: list[bytes]):
    html_cycle = cycle(html_sequence)

    def _urlopen(request, timeout=30):  # noqa: ARG001
        url = request.full_url if hasattr(request, "full_url") else str(request)
        if "api.openalex.org" in url:
            return io.BytesIO(json.dumps(openalex_payload).encode("utf-8"))

        html = next(html_cycle)

        class _Response(io.BytesIO):
            headers = {"Content-Type": "text/html; charset=utf-8"}

        return _Response(html)

    return _urlopen


@pytest.fixture()
def patched_staged_network():
    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text(encoding="utf-8"))
    urlopen = _staged_network_urlopen(fixture_payload, [RANK1_HTML, RANK2_HTML])
    with patch(
        "rge.modules.source_providers.openalex.urllib.request.urlopen",
        urlopen,
    ), patch(
        "rge.modules.fetcher.urllib.request.urlopen",
        urlopen,
    ):
        yield


def test_autonomous_researcher_loop_staged_spine_proof(
    temp_db: Path,
    artifact_dir: Path,
    staging_dir: Path,
    patched_staged_network: None,
) -> None:
    result = execute_autonomous_researcher_loop(
        topic=GOLDEN_MVP_TOPIC,
        domain="creativity",
        db_path=temp_db,
        artifact_dir=artifact_dir,
        run_id=STAGED_FIXTURE_RUN_ID,
        recommended_ticket_id="ticket-338",
        research_path="staged_spine",
        staging_dir=staging_dir,
        question_id=STAGED_FIXTURE_QUESTION_ID,
    )

    assert result["status"] == "completed"
    assert result["command"] == COMMAND
    assert result["loop_schema_version"] == LOOP_SCHEMA_VERSION
    assert result["research_path"] == "staged_spine"
    assert result["topic"] == GOLDEN_MVP_TOPIC
    assert result["run_summary"]["claims_accepted"] >= 2
    assert result["run_summary"]["relationships_active"] >= 2
    assert result["run_summary"]["rank1_run_id"]
    assert result["run_summary"]["rank2_run_id"]

    atlas_path = Path(result["artifacts"]["atlas_snapshot"])
    coherence_json = Path(result["artifacts"]["coherence_json"])
    coherence_md = Path(result["artifacts"]["coherence_md"])
    loop_report = Path(result["artifacts"]["loop_report"])
    recommended = Path(result["artifacts"]["recommended_improvement_ticket"])
    improvement_path = Path(result["artifacts"]["improvement_tickets"])

    for path in (atlas_path, coherence_json, coherence_md, loop_report, recommended):
        assert path.is_file(), f"missing artifact: {path}"

    coherence = json.loads(coherence_json.read_text(encoding="utf-8"))
    assert coherence["overall_coherence_verdict"] in {"pass", "partial"}
    assert coherence["population"]["runs"] >= 1

    quality = result["research_quality"]
    quality_initial = result["research_quality_initial"]
    assert quality_initial["research_quality_verdict"] in {"PARTIAL", "GO", "NO-GO"}
    assert quality["evaluated_after_ticket_seeding"] is True
    assert quality["research_quality_verdict"] in {"PARTIAL", "GO", "NO-GO"}

    assert result["run_summary"]["quality_driven_ticket_ids"]
    assert result["quality_driven_improvement"]["status"] == "quality_driven_generated"
    assert improvement_path.is_file()

    draft_payload = json.loads(improvement_path.read_text(encoding="utf-8"))
    drafts = draft_payload if isinstance(draft_payload, list) else [draft_payload]
    assert drafts[0]["status"] == "draft"
    assert improvement_draft_is_actionable(drafts[0])

    ticket = json.loads(recommended.read_text(encoding="utf-8"))
    assert ticket["id"] == "ticket-338"
    assert ticket["status"] == "proposed"
    assert ticket["source_weakness"] == quality["weakest_dimension"]


def test_autonomous_researcher_loop_staged_spine_cli(
    temp_db: Path,
    artifact_dir: Path,
    staging_dir: Path,
    patched_staged_network: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    capsys.readouterr()
    exit_code = main(
        [
            "autonomous-researcher-loop",
            "--staged-spine",
            "--topic",
            GOLDEN_MVP_TOPIC,
            "--domain",
            "creativity",
            "--db",
            str(temp_db),
            "--artifact-dir",
            str(artifact_dir),
            "--staging-dir",
            str(staging_dir),
            "--run-id",
            STAGED_FIXTURE_RUN_ID,
            "--question-id",
            STAGED_FIXTURE_QUESTION_ID,
            "--recommended-ticket-id",
            "ticket-338",
        ]
    )
    capsys.readouterr()
    assert exit_code == 0
    loop_report = json.loads(
        (artifact_dir / "autonomous_loop_report.json").read_text(encoding="utf-8")
    )
    assert loop_report["status"] == "completed"
    assert loop_report["research_path"] == "staged_spine"
    assert loop_report["research_quality"]["evaluated_after_ticket_seeding"] is True
    assert loop_report["run_summary"]["quality_driven_ticket_ids"]
