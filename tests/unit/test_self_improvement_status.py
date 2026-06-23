from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.modules.autonomous_synthesis_governor import LEDGER_SCHEMA_VERSION
from rge.modules.self_improvement_status import (
    build_self_improvement_status,
    write_self_improvement_status,
)
from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state


def test_self_improvement_status_surfaces_flagged_governor_reviews(tmp_path: Path) -> None:
    seed_operator_neutral_plan_state(tmp_path)
    ledger_path = tmp_path / "data/operator/autonomous_synthesis_governor_ledger.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(
            {
                "schema_version": LEDGER_SCHEMA_VERSION,
                "reviews": [
                    {
                        "review_id": "syn_gov_bad",
                        "governor_verdict": "NO-GO",
                        "failure_reasons": ["budget gate missing"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    payload = build_self_improvement_status(root=tmp_path)

    assert payload["schema_version"] == "self_improvement_status_v0.1.0"
    assert payload["status"] == "NO-GO"
    assert payload["spine_map"][0]["step"] == "research_run_report"
    assert payload["spine_map"][-1]["step"] == "atlas_preview"
    flagged = payload["current_state"]["flagged_synthesis_governor_reviews"]
    assert flagged == [
        {
            "review_id": "syn_gov_bad",
            "governor_verdict": "NO-GO",
            "failure_reasons": ["budget gate missing"],
        }
    ]
    assert "edit_TICKET_QUEUE" in payload["forbidden_actions"]


def test_write_self_improvement_status_uses_private_operator_path(tmp_path: Path) -> None:
    seed_operator_neutral_plan_state(tmp_path)

    path = write_self_improvement_status(root=tmp_path)

    assert path.relative_to(tmp_path).as_posix() == "data/operator/self_improvement_status_latest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "self_improvement_status_v0.1.0"


def _seed_synthesis_cli_wiring(tmp_path: Path) -> None:
    runner_dir = tmp_path / "rge" / "modules"
    runner_dir.mkdir(parents=True, exist_ok=True)
    (runner_dir / "synthesis_packet_runner.py").write_text("# runner\n", encoding="utf-8")
    (tmp_path / "rge" / "cli.py").write_text(
        'subparsers.add_parser("synthesize")\n',
        encoding="utf-8",
    )


def test_self_improvement_status_omits_benchmark_off_synthesis_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed_operator_neutral_plan_state(tmp_path)
    _seed_synthesis_cli_wiring(tmp_path)
    monkeypatch.setattr(
        "rge.modules.self_improvement_status.inspect_working_tree",
        lambda _root: type(
            "Tree",
            (),
            {"clean": True, "branch": "main", "dirty_paths": []},
        )(),
    )

    payload = build_self_improvement_status(root=tmp_path)

    assert "synthesis_packet_benchmark_status" not in payload["current_state"]


def test_self_improvement_status_includes_benchmark_on_synthesis_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rge.modules.synthesis_packet_benchmark import (
        DEFAULT_BENCHMARK_ARTIFACT_REL,
        build_benchmark_summary,
        write_benchmark_artifact,
    )

    seed_operator_neutral_plan_state(tmp_path)
    _seed_synthesis_cli_wiring(tmp_path)
    write_benchmark_artifact(
        build_benchmark_summary(
            runs_completed=25,
            total_elapsed_seconds=0.05,
            counters={"claim_count": 50},
            provider="mock_cloud",
            mode="mock",
            cloud_call_made_any=False,
            estimated_cost_usd_total=0.0,
            local_review={"review_recommended": True},
            openai_big_review={
                "review_recommended": False,
                "openai_live_call_blocked": False,
            },
        ),
        root=tmp_path,
        artifact_path=tmp_path / DEFAULT_BENCHMARK_ARTIFACT_REL,
    )
    monkeypatch.setattr(
        "rge.modules.self_improvement_status.inspect_working_tree",
        lambda _root: type(
            "Tree",
            (),
            {
                "clean": True,
                "branch": "phase-3/cloud-synthesis-packet-cli-throughput",
                "dirty_paths": [],
            },
        )(),
    )

    payload = build_self_improvement_status(root=tmp_path)
    benchmark = payload["current_state"]["synthesis_packet_benchmark_status"]

    assert benchmark["status"] == "available"
    assert benchmark["reports_per_hour_estimate"] == 1800000.0
    assert benchmark["benchmark_recommended"] is False
