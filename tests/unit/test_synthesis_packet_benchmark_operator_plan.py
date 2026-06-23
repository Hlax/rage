"""Operator plan integration for synthesis packet benchmark artifact."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.modules.operator_loop import WorkingTreeStatus, build_operator_plan
from rge.modules.synthesis_packet_benchmark import (
    DEFAULT_BENCHMARK_ARTIFACT_REL,
    build_benchmark_summary,
    inspect_synthesis_packet_benchmark_plan_status,
    is_synthesis_packet_cli_branch,
    load_benchmark_artifact,
    write_benchmark_artifact,
)
from tests.unit.operator_loop_helpers import (
    apply_live_smoke_env_gates,
    seed_operator_neutral_plan_state,
)


@pytest.fixture(autouse=True)
def _live_smoke_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    apply_live_smoke_env_gates(monkeypatch)


def _synthesis_branch_tree(tmp_path: Path) -> WorkingTreeStatus:
    seed_operator_neutral_plan_state(tmp_path)
    _seed_cli_and_runner(tmp_path)
    (tmp_path / "fixtures" / "synthesis").mkdir(parents=True, exist_ok=True)
    (tmp_path / "fixtures" / "synthesis" / "grounded_evidence_packet_dry_run.json").write_text(
        "{}",
        encoding="utf-8",
    )
    return WorkingTreeStatus(
        clean=True,
        branch="phase-3/cloud-synthesis-packet-cli-throughput",
        dirty_paths=[],
    )


def test_action_from_state_recommends_benchmark_when_artifact_missing(
    tmp_path: Path,
) -> None:
    plan = build_operator_plan(root=tmp_path, working_tree=_synthesis_branch_tree(tmp_path))
    action = plan["next_recommended_action"]
    assert action["action_id"] == "run_synthesis_packet_benchmark"
    assert action["gate"] == "safe_autonomous"
    assert any(
        "run_synthesis_packet_benchmark.py" in cmd.get("shell", "")
        for cmd in action["commands"]
    )


def test_action_prefers_benchmark_over_autonomous_loop_on_synthesis_branch(
    tmp_path: Path,
) -> None:
    plan = build_operator_plan(root=tmp_path, working_tree=_synthesis_branch_tree(tmp_path))
    assert plan["next_recommended_action"]["action_id"] == "run_synthesis_packet_benchmark"
    assert plan["synthesis_packet_benchmark_status"]["benchmark_recommended"] is True


def test_action_falls_back_when_benchmark_artifact_present(tmp_path: Path) -> None:
    tree = _synthesis_branch_tree(tmp_path)
    write_benchmark_artifact(
        _minimal_summary(),
        root=tmp_path,
        artifact_path=tmp_path / DEFAULT_BENCHMARK_ARTIFACT_REL,
    )
    plan = build_operator_plan(root=tmp_path, working_tree=tree)
    assert plan["next_recommended_action"]["action_id"] == "run_autonomous_researcher_loop"


def test_execute_safe_hook_writes_benchmark_artifact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from rge.modules.synthesis_packet_benchmark import run_synthesis_packet_benchmark_execute_safe_hook

    tree = _synthesis_branch_tree(tmp_path)
    calls: list[int] = []

    def fake_benchmark(**kwargs: object) -> dict:
        calls.append(int(kwargs.get("runs") or 0))
        summary = _minimal_summary()
        write_benchmark_artifact(
            summary,
            root=tmp_path,
            artifact_path=tmp_path / DEFAULT_BENCHMARK_ARTIFACT_REL,
        )
        return summary

    monkeypatch.setattr(
        "rge.modules.synthesis_packet_benchmark.run_synthesis_packet_benchmark",
        fake_benchmark,
    )
    result = run_synthesis_packet_benchmark_execute_safe_hook(
        root=tmp_path,
        branch=tree.branch,
    )
    assert result is not None
    assert result["status"] == "completed"
    assert result["reports_per_hour_estimate"] == 1800000.0
    assert calls == [25]
    assert load_benchmark_artifact(root=tmp_path) is not None


def _minimal_summary() -> dict:
    return build_benchmark_summary(
        runs_completed=25,
        total_elapsed_seconds=0.05,
        counters={"claim_count": 50},
        provider="mock_cloud",
        mode="mock",
        cloud_call_made_any=False,
        estimated_cost_usd_total=0.0,
        local_review={"review_recommended": True},
        openai_big_review={"review_recommended": False, "openai_live_call_blocked": False},
    )


def test_is_synthesis_packet_cli_branch_matches_feature_branch() -> None:
    assert is_synthesis_packet_cli_branch("phase-3/cloud-synthesis-packet-cli-throughput")
    assert not is_synthesis_packet_cli_branch("main")


def test_write_and_load_benchmark_artifact(tmp_path: Path) -> None:
    artifact_path = tmp_path / DEFAULT_BENCHMARK_ARTIFACT_REL
    write_benchmark_artifact(_minimal_summary(), root=tmp_path, artifact_path=artifact_path)
    loaded = load_benchmark_artifact(root=tmp_path, artifact_path=artifact_path)
    assert loaded is not None
    assert loaded["reports_per_hour_estimate"] == 1800000.0
    assert loaded.get("artifact_written_at")


def test_inspect_surfaces_reports_per_hour_on_synthesis_branch(tmp_path: Path) -> None:
    _seed_cli_and_runner(tmp_path)
    artifact_path = tmp_path / DEFAULT_BENCHMARK_ARTIFACT_REL
    write_benchmark_artifact(_minimal_summary(), root=tmp_path, artifact_path=artifact_path)

    status = inspect_synthesis_packet_benchmark_plan_status(
        root=tmp_path,
        branch="phase-3/cloud-synthesis-packet-cli-throughput",
    )
    assert status["status"] == "available"
    assert status["reports_per_hour_estimate"] == 1800000.0
    assert status["runs_completed"] == 25


def test_inspect_not_applicable_off_synthesis_branch(tmp_path: Path) -> None:
    _seed_cli_and_runner(tmp_path)
    artifact_path = tmp_path / DEFAULT_BENCHMARK_ARTIFACT_REL
    write_benchmark_artifact(_minimal_summary(), root=tmp_path, artifact_path=artifact_path)

    status = inspect_synthesis_packet_benchmark_plan_status(
        root=tmp_path,
        branch="main",
    )
    assert status["status"] == "not_applicable"
    assert status["reports_per_hour_estimate"] is None


def test_inspect_missing_artifact_recommends_benchmark(tmp_path: Path) -> None:
    _seed_cli_and_runner(tmp_path)
    status = inspect_synthesis_packet_benchmark_plan_status(
        root=tmp_path,
        branch="phase-3/cloud-synthesis-packet-cli-throughput",
    )
    assert status["status"] == "missing"
    assert status["benchmark_recommended"] is True
    assert "run_synthesis_packet_benchmark.py" in status["operator_commands"]["benchmark"]


def test_operator_plan_includes_benchmark_status_on_synthesis_branch(tmp_path: Path) -> None:
    seed_operator_neutral_plan_state(tmp_path)
    _seed_cli_and_runner(tmp_path)
    write_benchmark_artifact(
        _minimal_summary(),
        root=tmp_path,
        artifact_path=tmp_path / DEFAULT_BENCHMARK_ARTIFACT_REL,
    )

    plan = build_operator_plan(
        root=tmp_path,
        working_tree=WorkingTreeStatus(
            clean=True,
            branch="phase-3/cloud-synthesis-packet-cli-throughput",
            dirty_paths=[],
        ),
    )
    status = plan["synthesis_packet_benchmark_status"]
    assert status["status"] == "available"
    assert status["reports_per_hour_estimate"] == 1800000.0


def test_artifact_json_contains_no_secrets(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-should-not-appear")
    artifact_path = tmp_path / DEFAULT_BENCHMARK_ARTIFACT_REL
    write_benchmark_artifact(_minimal_summary(), root=tmp_path, artifact_path=artifact_path)
    blob = artifact_path.read_text(encoding="utf-8")
    assert "sk-secret-should-not-appear" not in blob
    assert ".env.local" not in blob


def _seed_cli_and_runner(tmp_path: Path) -> None:
    runner_dir = tmp_path / "rge" / "modules"
    runner_dir.mkdir(parents=True, exist_ok=True)
    (runner_dir / "synthesis_packet_runner.py").write_text("# runner\n", encoding="utf-8")
    (tmp_path / "rge" / "cli.py").write_text(
        'subparsers.add_parser("synthesize")\n',
        encoding="utf-8",
    )
