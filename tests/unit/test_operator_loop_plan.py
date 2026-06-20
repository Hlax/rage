"""Unit tests for operator loop plan runtime config surfacing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.config import DEFAULT_STAGED_RANK2_SCAN_MAX
from rge.modules.operator_loop import WorkingTreeStatus, build_operator_plan
from rge.modules.operator_proof_bundle import COMMAND, PIPELINE_MODE


def _seed_minimal_queue(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "agent_reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        """
| 40 | ticket-040 | done | prev | | |
| 41 | ticket-041 | proposed | Next | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "tickets" / "ticket-041.json").write_text(
        json.dumps(
            {
                "id": "ticket-041",
                "title": "Next",
                "risk_level": "low",
                "status": "proposed",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "agent_reports" / "2026-06-16_principal-audit-post-ticket-254.md").write_text(
        "# audit",
        encoding="utf-8",
    )


def _seed_done_only_queue(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "agent_reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        """
| 40 | ticket-040 | done | prev | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "tickets" / "ticket-040.json").write_text(
        json.dumps(
            {
                "id": "ticket-040",
                "title": "Done",
                "risk_level": "low",
                "status": "done",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "agent_reports" / "2026-06-16_principal-audit-post-ticket-254.md").write_text(
        "# audit",
        encoding="utf-8",
    )


def test_plan_includes_default_staged_rank2_scan_max(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_STAGED_RANK2_SCAN_MAX", raising=False)
    _seed_minimal_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)

    assert plan["staged_rank2_scan_max"] == DEFAULT_STAGED_RANK2_SCAN_MAX


def test_plan_honors_staged_rank2_scan_max_env_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_STAGED_RANK2_SCAN_MAX", "20")
    _seed_minimal_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)

    assert plan["staged_rank2_scan_max"] == 20


def test_plan_includes_arbitrary_source_proof_bundle_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_STAGED_RANK2_SCAN_MAX", raising=False)
    _seed_minimal_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    status = plan["arbitrary_source_proof_bundle_status"]

    assert status["command"] == COMMAND
    assert status["pipeline_mode"] == PIPELINE_MODE
    assert status["mock_llm_only"] is True
    assert status["requires_temp_db"] is True
    assert "prove-arbitrary-source-bundle" in status["operator_commands"]["proof_bundle"]
    assert status["proof_artifact"] == "operator_proof_bundle.json"


def test_proof_bundle_recommended_action_when_product_drift_and_no_open_ticket(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_done_only_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    monkeypatch.setattr(
        "rge.modules.operator_loop.checkpoint_status",
        lambda **kwargs: {
            "cadence_status": "satisfied",
            "implementation_gate": "satisfied",
            "drift_warning": [
                "No product-risk or live-research proof advanced in the last 3 completed tickets."
            ],
        },
    )

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    action = plan["next_recommended_action"]

    assert plan["arbitrary_source_proof_bundle_status"]["proof_bundle_recommended"] is True
    assert action["action_id"] == "run_arbitrary_source_proof_bundle"
    assert "prove-arbitrary-source-bundle" in action["commands"][0]["shell"]


def test_proof_bundle_action_deferred_when_open_ticket_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_minimal_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    monkeypatch.setattr(
        "rge.modules.operator_loop.checkpoint_status",
        lambda **kwargs: {
            "cadence_status": "satisfied",
            "implementation_gate": "satisfied",
            "drift_warning": [
                "No product-risk or live-research proof advanced in the last 3 completed tickets."
            ],
        },
    )

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)

    assert plan["arbitrary_source_proof_bundle_status"]["proof_bundle_recommended"] is True
    assert plan["next_recommended_action"]["action_id"] == "begin_ticket_implementation"


def _seed_public_site_preview_paths(tmp_path: Path, *, include_source_health: bool) -> None:
    site = tmp_path / "apps" / "public-site"
    public_data = site / "public" / "data"
    public_data.mkdir(parents=True)
    (site / "package.json").write_text("{}", encoding="utf-8")
    (public_data / "atlas_snapshot_preview.json").write_text("{}", encoding="utf-8")
    (public_data / "atlas_coherence_preview.json").write_text("{}", encoding="utf-8")
    if include_source_health:
        (public_data / "atlas_source_health_run_latest.json").write_text(
            "{}", encoding="utf-8"
        )
    scripts = tmp_path / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "refresh_atlas_preview_from_staged_spine.py").write_text(
        "# refresh staged spine preview\n",
        encoding="utf-8",
    )
    (scripts / "refresh_atlas_source_health_preview.py").write_text(
        "# refresh source health preview\n",
        encoding="utf-8",
    )


def test_plan_includes_atlas_preview_refresh_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_STAGED_RANK2_SCAN_MAX", raising=False)
    _seed_done_only_queue(tmp_path)
    _seed_public_site_preview_paths(tmp_path, include_source_health=False)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    status = plan["atlas_preview_refresh_status"]

    assert status["status"] == "available"
    assert status["refresh_recommended"] is True
    assert status["single_refresh_recommended"] is True
    assert "atlas_source_health_run_latest" in status["missing_outputs"]
    assert "refresh_atlas_preview_from_staged_spine.py" in status["operator_commands"][
        "staged_spine_refresh"
    ]
    assert "refresh_atlas_source_health_preview.py" in status["operator_commands"][
        "source_health_refresh"
    ]


def test_atlas_refresh_recommended_action_when_missing_source_health_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_done_only_queue(tmp_path)
    _seed_public_site_preview_paths(tmp_path, include_source_health=False)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    action = plan["next_recommended_action"]

    assert plan["atlas_preview_refresh_status"]["refresh_recommended"] is True
    assert plan["atlas_preview_refresh_status"]["single_refresh_recommended"] is True
    assert action["action_id"] == "refresh_atlas_public_previews"
    assert len(action["commands"]) == 2
    assert "refresh_atlas_preview_from_staged_spine.py" in action["commands"][0]["shell"]
    assert "npm run build" in action["commands"][1]["shell"]


def test_plan_includes_live_combined_source_health_smoke_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_done_only_queue(tmp_path)
    _seed_public_site_preview_paths(tmp_path, include_source_health=True)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    status = plan["live_combined_source_health_smoke_status"]

    assert status["status"] == "available"
    assert status["source_health_work_detected"] is True
    assert status["live_smoke_recommended"] is True
    assert "combined_source_health_smoke" in status["operator_commands"]["combined_smoke"]


def test_live_combined_smoke_recommended_action_when_gates_unset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_done_only_queue(tmp_path)
    _seed_public_site_preview_paths(tmp_path, include_source_health=True)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    monkeypatch.delenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", raising=False)
    monkeypatch.delenv("RGE_ALLOW_LIVE_QUERY_EXPANSION_SMOKE", raising=False)
    monkeypatch.delenv("RGE_ALLOW_SOURCE_NETWORK", raising=False)
    monkeypatch.delenv("OPENALEX_MAILTO", raising=False)

    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    action = plan["next_recommended_action"]

    assert plan["live_combined_source_health_smoke_status"]["live_smoke_recommended"] is True
    assert action["action_id"] == "run_live_combined_source_health_smoke"
    assert "combined_source_health_smoke" in action["commands"][-1]["shell"]
