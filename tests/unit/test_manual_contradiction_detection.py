"""Unit tests for contradiction detection on manual_text sources (ticket-091)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rge.modules.manual_source_fixtures import contradiction_fixture_for_manual_source

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNTHNOTE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "manual_synthnote.txt"
SYNTHNOTE_CHECKSUM = "2c53bfdfdf3c68530f89e24f4f6c88e4ba95574f76484aa5664be9b0ff0c04e4"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "manual_contradiction_detection.sqlite"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def _prepare_manual_synthnote_with_relationships(db_path: Path) -> str:
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
                "Synthetic Source Note: AI-Assisted Ideation and Semantic Diversity",
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    from rge.db.connection import connect

    conn = connect(db_path)
    try:
        source_id = conn.execute("SELECT id FROM sources").fetchone()[0]
    finally:
        conn.close()
    assert main(["extract-claims", "--source", source_id, "--db", str(db_path)]) == 0
    assert main(["link-concepts", "--source", source_id, "--db", str(db_path)]) == 0
    assert (
        main(["build-relationships", "--source", source_id, "--db", str(db_path)]) == 0
    )
    return source_id


def test_contradiction_fixture_map_resolves_synthnote_checksum() -> None:
    class _Source:
        source_type = "manual_text"
        raw_text_checksum = SYNTHNOTE_CHECKSUM

    assert (
        contradiction_fixture_for_manual_source(_Source())
        == "contradiction_detection_manual_synthnote.json"
    )


def test_detect_contradictions_on_manual_synthnote_qualifies_edges(
    temp_db: Path,
) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import RelationshipRepository

    source_id = _prepare_manual_synthnote_with_relationships(temp_db)
    assert (
        main(["detect-contradictions", "--source", source_id, "--db", str(temp_db)]) == 0
    )

    conn = connect(temp_db)
    try:
        qualifications = conn.execute(
            """
            SELECT re.stance, re.claim_id, r.domain_metadata_json
            FROM relationship_evidence re
            JOIN relationships r ON r.id = re.relationship_id
            WHERE re.stance = 'qualifies'
            """
        ).fetchall()
        assert len(qualifications) >= 1
        assert qualifications[0]["stance"] == "qualifies"
        metadata = json.loads(qualifications[0]["domain_metadata_json"])
        assert metadata.get("contradiction_classification") == "qualifies"

        active = RelationshipRepository(conn).list_active()
        assert any(rel["predicate"] == "may_reduce" for rel in active)
        assert any(rel["predicate"] == "may_increase" for rel in active)
    finally:
        conn.close()


def test_detect_contradictions_manual_synthnote_is_idempotent(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    source_id = _prepare_manual_synthnote_with_relationships(temp_db)
    args = ["detect-contradictions", "--source", source_id, "--db", str(temp_db)]
    assert main(args) == 0
    assert main(args) == 0

    conn = connect(temp_db)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM relationship_evidence WHERE stance = 'qualifies'"
        ).fetchone()[0]
        assert count == 1
    finally:
        conn.close()


def test_detect_contradictions_cli_json_for_manual_synthnote(
    temp_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    source_id = _prepare_manual_synthnote_with_relationships(temp_db)
    capsys.readouterr()
    assert main(["detect-contradictions", "--source", source_id, "--db", str(temp_db)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["qualification_count"] == 1
    assert len(payload["qualifications"]) == 1


def test_golden_fixture_source_still_uses_diversity_contradiction_fixture(
    temp_db: Path,
) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    base_source = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
    contradiction_source = (
        REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_contradiction.txt"
    )

    assert (
        main(
            [
                "ingest",
                str(base_source),
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
        base_id = conn.execute("SELECT id FROM sources").fetchone()[0]
    finally:
        conn.close()
    assert main(["extract-claims", "--source", base_id, "--db", str(temp_db)]) == 0
    assert main(["link-concepts", "--source", base_id, "--db", str(temp_db)]) == 0
    assert (
        main(["build-relationships", "--source", base_id, "--db", str(temp_db)]) == 0
    )

    assert (
        main(
            [
                "ingest",
                str(contradiction_source),
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
        contra_id = conn.execute(
            "SELECT id FROM sources WHERE title = 'creativity_ai_diversity_contradiction.txt'"
        ).fetchone()[0]
    finally:
        conn.close()
    assert (
        main(
            [
                "extract-claims",
                "--source",
                contra_id,
                "--fixture",
                "claim_extraction_creativity_diversity_contradiction.json",
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
                contra_id,
                "--fixture",
                "relationship_drafting_creativity_diversity_contradiction.json",
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
                contra_id,
                "--fixture",
                "contradiction_detection_creativity_diversity.json",
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM relationship_evidence WHERE stance = 'qualifies'"
        ).fetchone()[0]
        assert count == 1
    finally:
        conn.close()
