"""Golden Test 26: full fixture-mode MVP run proves the system is real."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.cli import FIXTURE_RUN_ID, GOLDEN_MVP_TOPIC, execute_fixture_mode_run

REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = REPO_ROOT / "apps" / "public-site"
SITE_OUT_DIR = SITE_DIR / "out"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "full_mvp_run.sqlite"


@pytest.fixture()
def artifact_dirs(tmp_path: Path) -> dict[str, Path]:
    export_dir = tmp_path / "export"
    report_dir = tmp_path / "reports"
    ticket_dir = tmp_path / "tickets"
    for directory in (export_dir, report_dir, ticket_dir):
        directory.mkdir(parents=True, exist_ok=True)
    return {
        "export": export_dir,
        "reports": report_dir,
        "tickets": ticket_dir,
    }


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def _run_fixture_mvp(
    temp_db: Path, artifact_dirs: dict[str, Path], *, run_id: str = FIXTURE_RUN_ID
) -> dict:
    return execute_fixture_mode_run(
        topic=GOLDEN_MVP_TOPIC,
        domain="creativity",
        db_path=temp_db,
        run_id=run_id,
        report_dir=artifact_dirs["reports"],
        ticket_dir=artifact_dirs["tickets"],
        export_dirs=[artifact_dirs["export"]],
    )


def test_fixture_mode_run_produces_required_graph_artifacts(
    temp_db: Path, artifact_dirs: dict[str, Path]
) -> None:
    result = _run_fixture_mvp(temp_db, artifact_dirs)

    assert result["status"] == "completed"
    assert result["mode"] == "fixture"
    assert result["topic"] == GOLDEN_MVP_TOPIC
    assert result["domain"] == "creativity"
    assert result["queue_count"] >= 3
    assert result["sources_ingested"] >= 2
    assert result["claims_accepted"] >= 1
    assert result["claims_rejected"] >= 1
    assert result["relationships_active"] >= 1
    assert result["score_events"] >= 1
    assert result["card_count"] >= 2
    assert result["ticket_ids"]
    assert result["cluster_report_id"]
    assert result["theory_candidate_ids"]
    assert result["safety_audit_status"] == "pass"

    artifacts = result["artifacts"]
    for key in (
        "database",
        "run_report",
        "cluster_report",
        "public_cards_export",
        "public_memos_export",
        "improvement_tickets",
    ):
        assert Path(artifacts[key]).is_file(), f"missing artifact: {key}"

    cards = json.loads(
        Path(artifacts["public_cards_export"]).read_text(encoding="utf-8")
    )
    assert len(cards) >= 2

    run_report = json.loads(
        Path(artifacts["run_report"]).read_text(encoding="utf-8")
    )
    assert run_report["report_type"] == "run_report"
    assert run_report["claims_accepted"] >= 1
    assert run_report["claims_rejected"] >= 1
    assert run_report["top_failure_modes"]

    cluster_report = json.loads(
        Path(artifacts["cluster_report"]).read_text(encoding="utf-8")
    )
    assert cluster_report["report_type"] == "cluster_report"

    tickets = json.loads(
        Path(artifacts["improvement_tickets"]).read_text(encoding="utf-8")
    )
    assert isinstance(tickets, list)
    assert tickets
    assert tickets[0]["title"]
    assert tickets[0]["acceptance_criteria"]


def test_research_run_cli_matches_golden_command(
    temp_db: Path, artifact_dirs: dict[str, Path]
) -> None:
    from rge.cli import main

    exit_code = main(
        [
            "run",
            "--topic",
            GOLDEN_MVP_TOPIC,
            "--domain",
            "creativity",
            "--fixture-mode",
            "--db",
            str(temp_db),
            "--run-id",
            "run_golden_test_26_cli",
            "--output-dir",
            str(artifact_dirs["reports"]),
            "--ticket-dir",
            str(artifact_dirs["tickets"]),
            "--export-dir",
            str(artifact_dirs["export"]),
        ]
    )
    assert exit_code == 0


def test_non_fixture_run_remains_unimplemented() -> None:
    from rge.cli import main

    exit_code = main(
        [
            "run",
            "--topic",
            GOLDEN_MVP_TOPIC,
            "--domain",
            "creativity",
        ]
    )
    assert exit_code != 0


def test_public_site_build_succeeds_after_export() -> None:
    """Requires a prior ``npm run build`` (see ticket-028 test_plan)."""
    if not (SITE_OUT_DIR / "index.html").is_file():
        pytest.skip("Run `cd apps/public-site && npm run build` before this test")

    assert (SITE_OUT_DIR / "index.html").is_file()
    cards = json.loads(
        (REPO_ROOT / "apps/public-site/public/data/public_cards.json").read_text(
            encoding="utf-8"
        )
    )
    for card in cards:
        card_page = SITE_OUT_DIR / "cards" / f"{card['id']}.html"
        assert card_page.is_file(), f"missing static export for card {card['id']}"
