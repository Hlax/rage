"""Golden Test 15: theory generator creates candidate theories, not facts."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"
CONTRADICTION_SOURCE = (
    REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_contradiction.txt"
)
FOLLOWUP_SOURCE = (
    REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_followup_short.txt"
)
CLAIM_FIXTURE = "claim_extraction_creativity_diversity_contradiction.json"
LINK_FIXTURE = "concept_linking_creativity_diversity_contradiction.json"
RELATIONSHIP_FIXTURE = "relationship_drafting_creativity_diversity_contradiction.json"
CONTRADICTION_FIXTURE = "contradiction_detection_creativity_diversity.json"
FOLLOWUP_FIXTURE = "claim_extraction_creativity_diversity_followup.json"
THEORY_FIXTURE = "theory_generation_creativity_diversity.json"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "theory_generator_test.sqlite"


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


def _run_base_graph(db_path: Path) -> str:
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
        source_id = conn.execute("SELECT id FROM sources").fetchone()[0]
    finally:
        conn.close()
    assert main(["extract-claims", "--source", source_id, "--db", str(db_path)]) == 0
    assert main(["link-concepts", "--source", source_id, "--db", str(db_path)]) == 0
    assert (
        main(["build-relationships", "--source", source_id, "--db", str(db_path)]) == 0
    )
    return source_id


def _prepare_contradiction_source(db_path: Path) -> str:
    from rge.cli import main

    assert (
        main(
            [
                "ingest",
                str(CONTRADICTION_SOURCE),
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
        row = conn.execute(
            """
            SELECT id FROM sources
            WHERE title = 'creativity_ai_diversity_contradiction.txt'
            """
        ).fetchone()
        assert row is not None
        source_id = row[0]
    finally:
        conn.close()
    assert (
        main(
            [
                "extract-claims",
                "--source",
                source_id,
                "--fixture",
                CLAIM_FIXTURE,
                "--db",
                str(db_path),
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
                "--fixture",
                LINK_FIXTURE,
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "build-relationships",
                "--source",
                source_id,
                "--fixture",
                RELATIONSHIP_FIXTURE,
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "detect-contradictions",
                "--source",
                source_id,
                "--fixture",
                CONTRADICTION_FIXTURE,
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    return source_id


def _prepare_followup_source(db_path: Path) -> None:
    from rge.cli import main

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
    from rge.db.connection import connect

    conn = connect(db_path)
    try:
        row = conn.execute(
            """
            SELECT id FROM sources
            WHERE title = 'creativity_ai_diversity_followup_short.txt'
            """
        ).fetchone()
        assert row is not None
        source_id = row[0]
    finally:
        conn.close()
    assert (
        main(
            [
                "extract-claims",
                "--source",
                source_id,
                "--fixture",
                FOLLOWUP_FIXTURE,
                "--db",
                str(db_path),
            ]
        )
        == 0
    )
    assert main(["reconcile-scores", "--source", source_id, "--db", str(db_path)]) == 0


def _prepare_cluster_report(db_path: Path, report_dir: Path) -> None:
    _run_base_graph(db_path)
    _prepare_contradiction_source(db_path)
    _prepare_followup_source(db_path)
    from rge.cli import main

    assert (
        main(
            [
                "generate-cluster-report",
                "--domain",
                "creativity",
                "--db",
                str(db_path),
                "--output-dir",
                str(report_dir),
            ]
        )
        == 0
    )


def test_theory_generator_creates_candidate_with_caveats(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import TheoryCandidateRepository

    _prepare_cluster_report(temp_db, report_dir)
    assert (
        main(
            [
                "generate-theory-candidates",
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
                "--fixture",
                THEORY_FIXTURE,
                "--output-dir",
                str(report_dir),
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        assert TheoryCandidateRepository(conn).count() == 1
        row = conn.execute(
            """
            SELECT status, report_json, supporting_claims_json,
                   contradicting_or_qualifying_claims_json,
                   boundary_conditions_json, weakening_evidence_json,
                   next_questions_json
            FROM theory_candidates
            """
        ).fetchone()
        report = json.loads(row["report_json"])
        supporting = json.loads(row["supporting_claims_json"])
        contradicting = json.loads(row["contradicting_or_qualifying_claims_json"])
        boundaries = json.loads(row["boundary_conditions_json"])
        weakening = json.loads(row["weakening_evidence_json"])
        next_questions = json.loads(row["next_questions_json"])

        assert row["status"] == "candidate"
        assert report["report_type"] == "theory_candidate_report"
        assert report["type"] == "candidate_theory"
        assert report["status"] == "candidate"
        assert report["theory_text"]
        assert report["confidence"] == "medium"
        assert report["graph_pattern"] == "contradiction_by_metric"
        assert supporting
        assert all(claim_id.startswith("clm_") for claim_id in supporting)
        assert contradicting
        assert boundaries
        assert weakening
        assert next_questions
        assert supporting != contradicting
    finally:
        conn.close()

    output_file = report_dir / "theory_candidate_latest.json"
    assert output_file.is_file()
    exported = json.loads(output_file.read_text(encoding="utf-8"))
    assert exported["type"] == "candidate_theory"
    assert exported["status"] == "candidate"


def test_theory_candidates_are_not_stored_as_facts(temp_db: Path, report_dir: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    _prepare_cluster_report(temp_db, report_dir)
    assert (
        main(
            [
                "generate-theory-candidates",
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
                "--fixture",
                THEORY_FIXTURE,
                "--output-dir",
                str(report_dir),
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        accepted_theory_rows = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE status = 'accepted' AND claim_text LIKE '%theory%'"
        ).fetchone()[0]
        assert accepted_theory_rows == 0
        statuses = {
            row[0]
            for row in conn.execute("SELECT status FROM theory_candidates").fetchall()
        }
        assert statuses == {"candidate"}
    finally:
        conn.close()


def test_generate_theory_candidates_is_idempotent(temp_db: Path, report_dir: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import TheoryCandidateRepository

    _prepare_cluster_report(temp_db, report_dir)
    args = [
        "generate-theory-candidates",
        "--domain",
        "creativity",
        "--db",
        str(temp_db),
        "--fixture",
        THEORY_FIXTURE,
        "--output-dir",
        str(report_dir),
    ]
    assert main(args) == 0
    assert main(args) == 0

    conn = connect(temp_db)
    try:
        assert TheoryCandidateRepository(conn).count() == 1
    finally:
        conn.close()


def test_generate_theory_candidates_cli_emits_machine_readable_json(
    temp_db: Path, report_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    _prepare_cluster_report(temp_db, report_dir)
    capsys.readouterr()
    assert (
        main(
            [
                "generate-theory-candidates",
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
                "--fixture",
                THEORY_FIXTURE,
                "--output-dir",
                str(report_dir),
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "generate-theory-candidates"
    assert payload["status"] in {"generated", "already_generated"}
    assert payload["theory_candidate_ids"][0].startswith("thc_")
    assert payload["report"]["type"] == "candidate_theory"
    assert payload["report"]["supporting_claims"]
    assert payload["report"]["contradicting_or_qualifying_claims"]
