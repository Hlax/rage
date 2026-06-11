"""Golden Test 7: contradiction detection preserves disagreement."""

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
CLAIM_FIXTURE = "claim_extraction_creativity_diversity_contradiction.json"
LINK_FIXTURE = "concept_linking_creativity_diversity_contradiction.json"
RELATIONSHIP_FIXTURE = "relationship_drafting_creativity_diversity_contradiction.json"
CONTRADICTION_FIXTURE = "contradiction_detection_creativity_diversity.json"
REDUCE_FRAGMENT = "reduced semantic diversity"
INCREASE_FRAGMENT = "increased idea diversity"
CLASSIFICATION = "apparent_contradiction_metric_or_condition_difference"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "contradiction_detection_test.sqlite"


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


def _ingest_contradiction_source(db_path: Path) -> str:
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
        return row[0]
    finally:
        conn.close()


def _prepare_contradiction_source(db_path: Path) -> str:
    from rge.cli import main

    source_id = _ingest_contradiction_source(db_path)
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
    return source_id


def test_contradiction_detection_preserves_both_edges(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect
    from rge.db.repositories import ClaimRepository, RelationshipRepository

    _run_base_graph(temp_db)
    contradiction_source_id = _prepare_contradiction_source(temp_db)
    assert (
        main(
            [
                "detect-contradictions",
                "--source",
                contradiction_source_id,
                "--fixture",
                CONTRADICTION_FIXTURE,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )

    conn = connect(temp_db)
    try:
        claim_repo = ClaimRepository(conn)
        all_claims = claim_repo.list_accepted_for_domain("creativity")
        reduce_claims = [
            claim for claim in all_claims if REDUCE_FRAGMENT in claim.claim_text
        ]
        increase_claims = [
            claim for claim in all_claims if INCREASE_FRAGMENT in claim.claim_text
        ]
        assert len(reduce_claims) == 1
        assert len(increase_claims) == 1
        assert reduce_claims[0].id != increase_claims[0].id
        assert "mixed effects" not in " ".join(
            claim.claim_text.casefold() for claim in all_claims
        )

        rel_repo = RelationshipRepository(conn)
        active = rel_repo.list_active()
        reduce_edge = next(
            rel
            for rel in active
            if rel["predicate"] == "may_reduce"
            and rel["object_concept"] == "semantic diversity"
        )
        increase_edge = next(
            rel
            for rel in active
            if rel["predicate"] == "may_increase" and rel["object_concept"] == "diversity"
        )
        assert reduce_edge["status"] == "active"
        assert increase_edge["status"] == "active"
        assert "divergent prompting" in increase_edge["scope"].casefold()

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
        assert metadata.get("contradiction_classification") == CLASSIFICATION
    finally:
        conn.close()


def test_detect_contradictions_is_idempotent(temp_db: Path) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    _run_base_graph(temp_db)
    contradiction_source_id = _prepare_contradiction_source(temp_db)
    args = [
        "detect-contradictions",
        "--source",
        contradiction_source_id,
        "--fixture",
        CONTRADICTION_FIXTURE,
        "--db",
        str(temp_db),
    ]
    assert main(args) == 0
    assert main(args) == 0

    conn = connect(temp_db)
    try:
        count = conn.execute(
            """
            SELECT COUNT(*) FROM relationship_evidence WHERE stance = 'qualifies'
            """
        ).fetchone()[0]
        assert count == 1
    finally:
        conn.close()


def test_detect_contradictions_cli_emits_machine_readable_json(
    temp_db: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    _run_base_graph(temp_db)
    contradiction_source_id = _prepare_contradiction_source(temp_db)
    capsys.readouterr()
    assert (
        main(
            [
                "detect-contradictions",
                "--source",
                contradiction_source_id,
                "--fixture",
                CONTRADICTION_FIXTURE,
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "detect-contradictions"
    assert payload["status"] == "completed"
    assert payload["qualification_count"] == 1
    assert len(payload["qualifications"]) == 1
    assert payload["qualifications"][0]["stance"] == "qualifies"
    assert len(payload["active_relationships"]) == 2
