"""Golden Test 34: conservative asset export candidates (Packet 8)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_SOURCE = REPO_ROOT / "fixtures" / "sources" / "creativity_ai_diversity_short.txt"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "asset_export_golden.sqlite"


@pytest.fixture()
def export_dir(tmp_path: Path) -> Path:
    return tmp_path / "asset_exports"


@pytest.fixture(autouse=True)
def mock_llm_mode() -> None:
    prior = os.environ.get("RGE_LLM_MODE")
    os.environ["RGE_LLM_MODE"] = "mock"
    yield
    if prior is None:
        os.environ.pop("RGE_LLM_MODE", None)
    else:
        os.environ["RGE_LLM_MODE"] = prior


def test_export_asset_candidates_cli_emits_clustered_qa_eval_only(
    temp_db: Path,
    export_dir: Path,
) -> None:
    from rge.cli import main
    from rge.db.connection import connect

    assert (
        main(
            [
                "ingest",
                str(BASE_SOURCE),
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
        source_id = conn.execute("SELECT id FROM sources").fetchone()[0]
    finally:
        conn.close()

    assert main(["extract-claims", "--source", source_id, "--db", str(temp_db)]) == 0
    assert main(["promote-evidence-atoms", "--domain", "creativity", "--db", str(temp_db)]) == 0

    out_path = export_dir / "creativity_asset_candidates.json"
    assert (
        main(
            [
                "export-asset-candidates",
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
                "--output",
                str(out_path),
            ]
        )
        == 0
    )

    bundle = json.loads(out_path.read_text(encoding="utf-8"))
    assert bundle["schema_version"] == "asset_export_candidates_v0.1.0"
    assert bundle["atom_count"] >= 1
    for candidate in bundle["candidates"]:
        assert "quote" not in candidate
        if candidate["export_category"] == "qa_eval_candidate":
            assert candidate["evidence_maturity"] == "clustered"
            assert candidate["human_review_required"] is True
            assert candidate["review_status"] == "pending"
        if candidate["evidence_maturity"] == "promising":
            assert candidate["export_category"] == "do_not_export"
