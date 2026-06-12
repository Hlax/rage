"""Golden Test 18: domain proposal requires strict thresholds."""

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
PROPOSED_DOMAIN_ID = "creativity.film"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "domain_proposal_test.sqlite"


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


def test_domain_proposal_creates_draft_with_threshold_proof(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import DomainProposalRepository

    _prepare_multi_source_graph(temp_db)
    assert (
        main(
            [
                "generate-domain-proposal",
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
        assert DomainProposalRepository(conn).count() == 1
        row = conn.execute(
            """
            SELECT domain_id, status, threshold_report_json, evidence_claims_json
            FROM domain_proposals
            """
        ).fetchone()
        threshold_report = json.loads(row["threshold_report_json"])
        evidence = json.loads(row["evidence_claims_json"])
        report = DomainProposalRepository(conn).get_latest_for_domain(
            PROPOSED_DOMAIN_ID
        )
        assert report is not None
        payload = json.loads(report.proposal_json)

        assert row["domain_id"] == PROPOSED_DOMAIN_ID
        assert row["status"] == "draft"
        assert payload["report_type"] == "domain_proposal_report"
        assert payload["status"] == "draft"
        assert payload["domain_id"] == PROPOSED_DOMAIN_ID
        assert payload["thresholds"]["accepted_claims"] >= 40
        assert payload["thresholds"]["independent_sources"] >= 8
        assert payload["thresholds"]["recurring_specialized_terms"] >= 15
        assert payload["thresholds"]["mismatch_signals"] >= 3
        assert payload["thresholds"]["parent_underspecified_reason_present"] is True
        assert payload["parent_domains"]
        assert payload["overlap_domains"]
        assert payload["specialized_terms"]
        assert payload["scoring_overlay_proposals"]
        assert payload["reason_parent_domain_is_underspecified"]
        assert payload.get("ontology_rationale")
        assert evidence
        assert all(claim_id.startswith("clm_") for claim_id in evidence)

        active_domain_sources = conn.execute(
            """
            SELECT COUNT(*) FROM sources
            WHERE domain = ?
            """,
            (PROPOSED_DOMAIN_ID,),
        ).fetchone()[0]
        assert active_domain_sources == 0
        assert threshold_report["reason_parent_domain_is_underspecified"]
    finally:
        conn.close()

    output_file = report_dir / "domain_proposal_latest.json"
    assert output_file.is_file()


def test_domain_proposal_does_not_create_duplicate_domains(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    _prepare_multi_source_graph(temp_db)
    assert (
        main(
            [
                "generate-domain-proposal",
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
            "SELECT COUNT(*) FROM domain_proposals"
        ).fetchone()[0]
        domain_ids = {
            row[0]
            for row in conn.execute(
                "SELECT domain_id FROM domain_proposals"
            ).fetchall()
        }
        assert proposal_count == 1
        assert domain_ids == {PROPOSED_DOMAIN_ID}
    finally:
        conn.close()


def test_generate_domain_proposal_is_idempotent(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import DomainProposalRepository

    _prepare_multi_source_graph(temp_db)
    args = [
        "generate-domain-proposal",
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
        assert DomainProposalRepository(conn).count() == 1
    finally:
        conn.close()


def test_generate_domain_proposal_cli_emits_machine_readable_json(
    temp_db: Path, report_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    _prepare_multi_source_graph(temp_db)
    capsys.readouterr()
    assert (
        main(
            [
                "generate-domain-proposal",
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
    assert payload["command"] == "generate-domain-proposal"
    assert payload["status"] in {"generated", "already_generated"}
    assert payload["proposal_id"].startswith("dpr_")
    assert payload["readiness"]["thresholds_met"] is True
    assert payload["report"]["status"] == "draft"
    assert payload["report"]["domain_id"] == PROPOSED_DOMAIN_ID
