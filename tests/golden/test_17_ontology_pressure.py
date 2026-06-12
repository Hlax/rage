"""Golden Test 17: ontology pressure report proposes but does not auto-activate."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
FOLLOWUP_SOURCE = (
    REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_followup_short.txt"
)
FOLLOWUP_FIXTURE = "claim_extraction_creativity_diversity_followup.json"
CANDIDATE_CONCEPT = "selection burden"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "ontology_pressure_test.sqlite"


@pytest.fixture()
def report_dir(tmp_path: Path) -> Path:
    return tmp_path / "reports"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def _prepare_multi_source_graph(db_path: Path) -> None:
    from rge.cli import main

    assert (
        main(
            [
                "ingest",
                str(BASE_SOURCE),
                "--domain",
                "creativity",
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    from rge.db.connection import connect

    conn = connect(db_path)
    try:
        base_source_id = conn.execute("SELECT id FROM sources").fetchone()[0]
    finally:
        conn.close()
    assert (
        main(["extract-claims", "--source", base_source_id, "--db", str(db_path)]) == 0
    )

    assert (
        main(
            [
                "ingest",
                str(FOLLOWUP_SOURCE),
                "--domain",
                "creativity",
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    conn = connect(db_path)
    try:
        follow_source_id = conn.execute(
            """
            SELECT id FROM sources
            WHERE title = 'creativity_ai_diversity_followup_short.txt'
            """
        ).fetchone()[0]
    finally:
        conn.close()
    assert (
        main(
            [
                "extract-claims",
                "--source",
                follow_source_id,
                "--fixture",
                FOLLOWUP_FIXTURE,
                "--db",
                str(db_path),
            ]
        )
        == 0
    )


def test_ontology_pressure_creates_draft_proposal_with_evidence(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import OntologyProposalRepository

    _prepare_multi_source_graph(temp_db)
    assert (
        main(
            [
                "generate-ontology-pressure",
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

    conn = connect(temp_db)
    try:
        assert OntologyProposalRepository(conn).count() == 1
        row = conn.execute(
            "SELECT status, proposal_json, evidence_claims_json FROM ontology_proposals"
        ).fetchone()
        report = json.loads(row["proposal_json"])
        evidence = json.loads(row["evidence_claims_json"])

        assert row["status"] == "draft"
        assert report["report_type"] == "ontology_pressure_report"
        assert report["proposal_type"] == "promote_concept"
        assert report["candidate_concept"] == CANDIDATE_CONCEPT
        assert report["status"] == "draft"
        assert evidence
        assert all(claim_id.startswith("clm_") for claim_id in evidence)
        assert report["aliases"]
        assert report["reason"]

        active_concept = conn.execute(
            """
            SELECT COUNT(*) FROM concepts
            WHERE lower(label) = ? AND status = 'active'
            """,
            (CANDIDATE_CONCEPT,),
        ).fetchone()[0]
        assert active_concept == 0
    finally:
        conn.close()

    output_file = report_dir / "ontology_pressure_latest.json"
    assert output_file.is_file()


def test_ontology_pressure_does_not_create_duplicate_active_concepts(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    _prepare_multi_source_graph(temp_db)
    assert (
        main(
            [
                "generate-ontology-pressure",
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

    conn = connect(temp_db)
    try:
        proposal_count = conn.execute(
            "SELECT COUNT(*) FROM ontology_proposals"
        ).fetchone()[0]
        concept_count = conn.execute(
            """
            SELECT COUNT(*) FROM concepts
            WHERE lower(label) IN ('selection burden', 'curation load', 'choice overload', 'taste bottleneck')
              AND status = 'active'
            """
        ).fetchone()[0]
        assert proposal_count == 1
        assert concept_count == 0
    finally:
        conn.close()


def test_generate_ontology_pressure_is_idempotent(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import OntologyProposalRepository

    _prepare_multi_source_graph(temp_db)
    args = [
        "generate-ontology-pressure",
        "--domain",
        "creativity",
        "--db",
        str(temp_db),
        "--output-dir",
        str(report_dir),
    ]
    assert main(args) == 0
    assert main(args) == 0

    conn = connect(temp_db)
    try:
        assert OntologyProposalRepository(conn).count() == 1
    finally:
        conn.close()


def test_generate_ontology_pressure_cli_emits_machine_readable_json(
    temp_db: Path, report_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    _prepare_multi_source_graph(temp_db)
    capsys.readouterr()
    assert (
        main(
            [
                "generate-ontology-pressure",
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
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "generate-ontology-pressure"
    assert payload["status"] in {"generated", "already_generated"}
    assert payload["proposal_id"].startswith("ont_")
    assert payload["readiness"]["thresholds_met"] is True
    assert payload["report"]["status"] == "draft"
