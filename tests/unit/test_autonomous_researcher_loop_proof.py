"""Autonomous researcher MVP loop proof (ticket-332).

Mock-only pytest: one closed loop from seed question through atlas/coherence
inspection, research quality verdict, and recommended improvement ticket.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.cli import FIXTURE_RUN_ID, GOLDEN_MVP_TOPIC, main
from rge.modules.autonomous_researcher_loop import (
    COMMAND,
    LOOP_SCHEMA_VERSION,
    execute_autonomous_researcher_loop,
)
from rge.modules.ticket_writer import improvement_draft_is_actionable


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "autonomous_loop.sqlite"


@pytest.fixture()
def artifact_dir(tmp_path: Path) -> Path:
    return tmp_path / "autonomous_loop_artifacts"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def test_autonomous_researcher_loop_proof_fixture_mode(
    temp_db: Path,
    artifact_dir: Path,
) -> None:
    result = execute_autonomous_researcher_loop(
        topic=GOLDEN_MVP_TOPIC,
        domain="creativity",
        db_path=temp_db,
        artifact_dir=artifact_dir,
        run_id=FIXTURE_RUN_ID,
        recommended_ticket_id="ticket-333",
    )

    assert result["status"] == "completed"
    assert result["command"] == COMMAND
    assert result["loop_schema_version"] == LOOP_SCHEMA_VERSION
    assert result["topic"] == GOLDEN_MVP_TOPIC

    atlas_path = Path(result["artifacts"]["atlas_snapshot"])
    coherence_json = Path(result["artifacts"]["coherence_json"])
    coherence_md = Path(result["artifacts"]["coherence_md"])
    loop_report = Path(result["artifacts"]["loop_report"])
    recommended = Path(result["artifacts"]["recommended_improvement_ticket"])

    for path in (atlas_path, coherence_json, coherence_md, loop_report, recommended):
        assert path.is_file(), f"missing artifact: {path}"

    coherence = json.loads(coherence_json.read_text(encoding="utf-8"))
    assert coherence["overall_coherence_verdict"] in {"pass", "partial"}
    assert coherence["population"]["cards"] >= 2
    assert coherence["population"]["runs"] >= 1

    quality = result["research_quality"]
    quality_initial = result["research_quality_initial"]
    assert quality["research_quality_verdict"] == "GO"
    assert quality_initial["research_quality_verdict"] == "PARTIAL"
    assert quality_initial["weakest_dimension"] == "weak_ticket_generation"
    assert quality["evaluated_after_ticket_seeding"] is True
    assert quality["dimension_scores"]["weak_ticket_generation"]["score"] >= 80
    assert quality["dimension_scores"]["poor_contradiction_handling"]["score"] >= 80
    assert quality.get("weak_ticket_generation_score_delta", 0) > 0
    assert quality["weakest_dimension"] in {
        "weak_claim_extraction",
        "weak_source_linkage",
        "weak_concept_domain_linkage",
        "missing_hypotheses",
        "missing_follow_up_questions",
        "poor_contradiction_handling",
        "weak_ticket_generation",
        "weak_run_lineage",
    }

    ticket = json.loads(recommended.read_text(encoding="utf-8"))
    assert ticket["id"] == "ticket-333"
    assert ticket["status"] == "proposed"
    assert ticket["title"]
    assert ticket["problem"]
    assert ticket["acceptance_criteria"]
    assert ticket["source_weakness"] == quality["weakest_dimension"]

    assert result["run_summary"]["quality_driven_ticket_ids"]
    assert result["quality_driven_improvement"]["failure_reason"] == "weak_ticket_generation"
    draft_tickets = json.loads(
        Path(result["artifacts"]["improvement_tickets"]).read_text(encoding="utf-8")
    )
    assert len(draft_tickets) >= 1
    assert draft_tickets[0]["failure_reason"] == "weak_ticket_generation"
    assert draft_tickets[0]["status"] == "draft"
    assert improvement_draft_is_actionable(draft_tickets[0])

    assert "frontend contract is parked" in result["drift_note"]


def test_autonomous_researcher_loop_cli(
    temp_db: Path,
    artifact_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    capsys.readouterr()
    exit_code = main(
        [
            "autonomous-researcher-loop",
            "--topic",
            GOLDEN_MVP_TOPIC,
            "--domain",
            "creativity",
            "--db",
            str(temp_db),
            "--artifact-dir",
            str(artifact_dir),
            "--run-id",
            FIXTURE_RUN_ID,
            "--recommended-ticket-id",
            "ticket-333",
        ]
    )
    capsys.readouterr()
    assert exit_code == 0
    loop_report = json.loads(
        (artifact_dir / "autonomous_loop_report.json").read_text(encoding="utf-8")
    )
    assert loop_report["status"] == "completed"
    assert loop_report["research_quality"]["evaluated_after_ticket_seeding"] is True
    assert loop_report["research_quality"]["dimension_scores"]["weak_ticket_generation"][
        "score"
    ] >= 80
    assert loop_report["research_quality"]["research_quality_verdict"] == "GO"
