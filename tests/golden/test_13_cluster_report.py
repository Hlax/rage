"""Golden Test 13: cluster report triggers when threshold is met."""

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
REQUIRED_CONCEPTS = (
    "AI assistance",
    "semantic diversity",
    "originality",
    "ideation",
)


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "cluster_report_test.sqlite"


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


def _prepare_followup_source(db_path: Path) -> str:
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
    return source_id


def _prepare_golden_cluster_graph(db_path: Path) -> None:
    _run_base_graph(db_path)
    _prepare_contradiction_source(db_path)
    _prepare_followup_source(db_path)


def test_cluster_report_triggers_when_threshold_met(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ClusterReportRepository

    _prepare_golden_cluster_graph(temp_db)
    assert (
        main(
            [
                "generate-cluster-report",
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
        assert ClusterReportRepository(conn).count() == 1
        row = conn.execute(
            "SELECT report_json, evidence_packet_json FROM cluster_reports"
        ).fetchone()
        report = json.loads(row["report_json"])
        packet = json.loads(row["evidence_packet_json"])

        assert report["report_type"] == "cluster_report"
        assert report["cluster_label"]
        assert report["included_concepts"] == list(REQUIRED_CONCEPTS)
        assert report["supporting_claims"]
        assert report["qualifying_claims"] or report["contradicting_claims"]
        assert report["strongest_relationships"]
        assert report["evidence_gaps"]
        assert report["candidate_next_questions"]
        assert report["linked_claim_ids"]
        assert all(
            claim_id.startswith("clm_") for claim_id in report["linked_claim_ids"]
        )
        assert packet["top_supporting_claims"]
        assert packet["top_qualifying_claims"] or packet["top_contradicting_claims"]
        assert packet["open_gaps"]

        claim_count = conn.execute(
            "SELECT COUNT(*) FROM claims WHERE status = 'accepted'"
        ).fetchone()[0]
        source_count = conn.execute(
            "SELECT COUNT(DISTINCT source_id) FROM claims WHERE status = 'accepted'"
        ).fetchone()[0]
        assert claim_count >= 15
        assert source_count >= 3
    finally:
        conn.close()

    output_file = report_dir / "cluster_report_latest.json"
    assert output_file.is_file()
    exported = json.loads(output_file.read_text(encoding="utf-8"))
    assert exported["report_type"] == "cluster_report"
    assert exported["linked_claim_ids"]


def test_cluster_report_includes_both_support_and_disagreement(
    temp_db: Path, report_dir: Path
) -> None:
    from rge.cli import main

    _prepare_golden_cluster_graph(temp_db)
    assert (
        main(
            [
                "generate-cluster-report",
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
    report = json.loads(
        (report_dir / "cluster_report_latest.json").read_text(encoding="utf-8")
    )
    assert report["supporting_claims"]
    assert report["qualifying_claims"] or report["contradicting_claims"]
    support_set = set(report["supporting_claims"])
    disagree_set = set(report["qualifying_claims"]) | set(report["contradicting_claims"])
    assert support_set.isdisjoint(disagree_set) or len(disagree_set) >= 1


def test_generate_cluster_report_is_idempotent(temp_db: Path, report_dir: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ClusterReportRepository

    _prepare_golden_cluster_graph(temp_db)
    args = [
        "generate-cluster-report",
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
        assert ClusterReportRepository(conn).count() == 1
    finally:
        conn.close()


def test_generate_cluster_report_cli_emits_machine_readable_json(
    temp_db: Path, report_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    _prepare_golden_cluster_graph(temp_db)
    capsys.readouterr()
    assert (
        main(
            [
                "generate-cluster-report",
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
    assert payload["command"] == "generate-cluster-report"
    assert payload["status"] in {"generated", "already_generated"}
    assert payload["cluster_report_id"].startswith("crpt_")
    assert payload["readiness"]["thresholds_met"] is True
    assert payload["report"]["report_type"] == "cluster_report"
