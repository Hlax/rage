"""End-to-end manual synthnote pipeline proof (ticket-092)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNTHNOTE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "manual_synthnote.txt"
SYNTHNOTE_CHECKSUM = "2c53bfdfdf3c68530f89e24f4f6c88e4ba95574f76484aa5664be9b0ff0c04e4"
SYNTHNOTE_TITLE = (
    "Synthetic Source Note: AI-Assisted Ideation and Semantic Diversity"
)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "manual_source_pipeline_e2e.sqlite"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def test_manual_synthnote_pipeline_e2e_through_detect_contradictions(
    temp_db: Path,
) -> None:
    """Run ingest → extract → link → build → detect without explicit --fixture flags."""
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import (
        ClaimRepository,
        RelationshipEvidenceRepository,
        RelationshipRepository,
    )

    assert (
        main(
            [
                "ingest",
                str(SYNTHNOTE_SOURCE),
                "--domain",
                "creativity",
                "--source-type",
                "manual_text",
                "--source-title",
                SYNTHNOTE_TITLE,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        source_row = conn.execute(
            "SELECT id, source_type, raw_text_checksum FROM sources"
        ).fetchone()
        assert source_row is not None
        source_id = source_row["id"]
        assert source_row["source_type"] == "manual_text"
        assert source_row["raw_text_checksum"] == SYNTHNOTE_CHECKSUM
    finally:
        conn.close()

    assert main(["extract-claims", "--source", source_id, "--db", str(temp_db)]) == 0
    assert main(["link-concepts", "--source", source_id, "--db", str(temp_db)]) == 0
    assert (
        main(["build-relationships", "--source", source_id, "--db", str(temp_db)]) == 0
    )
    assert (
        main(["detect-contradictions", "--source", source_id, "--db", str(temp_db)]) == 0
    )

    conn = connect(temp_db)
    try:
        claims = ClaimRepository(conn).list_for_source(source_id, status="accepted")
        assert len(claims) == 2

        links = conn.execute(
            "SELECT COUNT(*) FROM claim_concepts WHERE claim_id IN "
            "(SELECT id FROM claims WHERE source_id = ?)",
            (source_id,),
        ).fetchone()[0]
        assert links == 4

        relationships = RelationshipRepository(conn).list_for_source(source_id)
        assert len(relationships) == 2
        predicates = {rel["predicate"] for rel in relationships}
        assert predicates == {"may_reduce", "may_increase"}

        qualifications = conn.execute(
            """
            SELECT re.stance, r.domain_metadata_json
            FROM relationship_evidence re
            JOIN relationships r ON r.id = re.relationship_id
            WHERE re.stance = 'qualifies'
            """
        ).fetchall()
        assert len(qualifications) == 1
        assert qualifications[0]["stance"] == "qualifies"
        metadata = json.loads(qualifications[0]["domain_metadata_json"])
        assert metadata.get("contradiction_classification") == "qualifies"

        evidence = RelationshipEvidenceRepository(conn).list_for_source(source_id)
        assert any(row["stance"] == "supports" for row in evidence)
    finally:
        conn.close()


def test_manual_synthnote_pipeline_e2e_cli_json_summary(
    temp_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    assert (
        main(
            [
                "ingest",
                str(SYNTHNOTE_SOURCE),
                "--domain",
                "creativity",
                "--source-type",
                "manual_text",
                "--source-title",
                SYNTHNOTE_TITLE,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    from rge.db.connection import connect

    conn = connect(temp_db)
    try:
        source_id = conn.execute("SELECT id FROM sources").fetchone()[0]
    finally:
        conn.close()

    for command in (
        ["extract-claims", "--source", source_id, "--db", str(temp_db)],
        ["link-concepts", "--source", source_id, "--db", str(temp_db)],
        ["build-relationships", "--source", source_id, "--db", str(temp_db)],
    ):
        capsys.readouterr()
        assert main(command) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["status"] == "completed"

    capsys.readouterr()
    assert (
        main(["detect-contradictions", "--source", source_id, "--db", str(temp_db)]) == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["qualification_count"] == 1
