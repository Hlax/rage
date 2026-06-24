"""Operator plan integration for OpenAI synthesis evaluator status (ticket-396)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.openai_synthesis_evaluator import (
    DEFAULT_ARTIFACT_REL,
    EVALUATOR_SCHEMA_VERSION,
    SYNTHESIS_CANARY_OUTPUT_REL,
    inspect_openai_synthesis_evaluator_plan_status,
    load_evaluator_artifact,
    run_openai_synthesis_evaluator_execute_safe_hook,
    write_evaluator_artifact,
)
from rge.modules.operator_autocycle import evaluate_autocycle_cycle
from rge.modules.operator_loop import WorkingTreeStatus, build_operator_plan
from tests.unit.operator_loop_helpers import (
    seed_operator_neutral_plan_state,
    seed_synthesis_human_review_neutral_artifact,
)


@pytest.fixture(autouse=True)
def _neutralize_live_smoke_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_QUERY_EXPANSION_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")


def _minimal_evaluator_payload(*, verdict: str = "GO", provider: str = "openai") -> dict:
    return {
        "schema_version": EVALUATOR_SCHEMA_VERSION,
        "status": "completed",
        "evaluator_verdict": verdict,
        "governor_verdict": verdict if verdict == "GO" else "NO-GO",
        "grounding_passed": verdict == "GO",
        "provider": provider,
        "packet_id": "syn_packet_grounded_dry_run_fixture",
        "no_accepted_graph_writes": True,
        "live_http_gates_missing": {},
        "input_artifact_path": (
            "data/tmp/openai_synthesis_canary/"
            "synthesis_output_syn_packet_grounded_dry_run_fixture.json"
        ),
    }


def test_inspect_missing_artifact_recommends_evaluator(tmp_path: Path) -> None:
    _seed_evaluator_cli(tmp_path)
    status = inspect_openai_synthesis_evaluator_plan_status(root=tmp_path)
    assert status["status"] == "missing"
    assert status["review_artifact_recommended"] is True
    assert status["live_http_review_gated"] is True
    assert "evaluate_mock" in status["operator_commands"]
    assert "live_canary" in status["operator_commands"]


def test_inspect_available_artifact_surfaces_verdict(tmp_path: Path) -> None:
    _seed_evaluator_cli(tmp_path)
    artifact_path = tmp_path / DEFAULT_ARTIFACT_REL
    write_evaluator_artifact(
        _minimal_evaluator_payload(),
        root=tmp_path,
        artifact_path=artifact_path,
    )
    status = inspect_openai_synthesis_evaluator_plan_status(root=tmp_path)
    assert status["status"] == "available"
    assert status["live_synthesis_verdict"] == "GO"
    assert status["review_artifact_recommended"] is False
    assert load_evaluator_artifact(root=tmp_path) is not None


def test_inspect_status_is_public_safe(tmp_path: Path) -> None:
    _seed_evaluator_cli(tmp_path)
    status = inspect_openai_synthesis_evaluator_plan_status(root=tmp_path)
    violations = assert_no_private_fields({"openai_synthesis_review_status": status})
    assert violations == []


def test_operator_plan_recommends_mock_evaluate_when_artifact_missing(
    tmp_path: Path,
) -> None:
    _seed_evaluator_plan_state(tmp_path)
    plan = build_operator_plan(
        root=tmp_path,
        working_tree=WorkingTreeStatus(clean=True, branch="main", dirty_paths=[]),
    )
    status = plan["openai_synthesis_evaluator_status"]
    assert status["review_artifact_recommended"] is True
    action = plan["next_recommended_action"]
    assert action["action_id"] == "run_openai_synthesis_evaluator"
    assert action["gate"] == "safe_autonomous"
    assert any(
        "run_openai_synthesis_evaluator.py" in cmd.get("shell", "")
        for cmd in action["commands"]
    )


def test_operator_plan_documents_live_canary_in_status(tmp_path: Path) -> None:
    _seed_evaluator_plan_state(tmp_path)
    plan = build_operator_plan(
        root=tmp_path,
        working_tree=WorkingTreeStatus(clean=True, branch="main", dirty_paths=[]),
    )
    commands = plan["openai_synthesis_evaluator_status"]["operator_commands"]
    assert "synthesize --packet" in commands["live_canary"]
    assert plan["openai_synthesis_evaluator_status"]["live_http_review_gated"] is True


def _set_openai_live_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Satisfy all live OpenAI HTTP gates without relying on host shell env."""
    monkeypatch.setenv("RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST", "openai")
    monkeypatch.setenv("RGE_CLOUD_MAX_USD_PER_RUN", "0.50")
    monkeypatch.setenv("RGE_CLOUD_MAX_TOKENS_PER_CALL", "4096")
    monkeypatch.setenv("RGE_ALLOW_OPENAI_SYNTHESIS", "1")
    monkeypatch.setenv("RGE_ALLOW_OPENAI_SYNTHESIS_LIVE_HTTP", "1")
    monkeypatch.setenv("RGE_CLOUD_LLM_ENABLED", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-redacted")


def test_operator_plan_live_canary_review_gated_when_go_and_gates_satisfied(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _seed_evaluator_plan_state(tmp_path)
    _set_openai_live_gates(monkeypatch)
    write_evaluator_artifact(
        _minimal_evaluator_payload(),
        root=tmp_path,
        artifact_path=tmp_path / DEFAULT_ARTIFACT_REL,
    )
    plan = build_operator_plan(
        root=tmp_path,
        working_tree=WorkingTreeStatus(clean=True, branch="main", dirty_paths=[]),
    )
    status = plan["openai_synthesis_evaluator_status"]
    assert status["status"] == "available"
    assert status["live_canary_recommended"] is True
    action = plan["next_recommended_action"]
    assert action["action_id"] == "run_openai_synthesis_live_canary"
    assert action["gate"] == "review_gated"


def test_autocycle_blocks_live_canary_action(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _seed_evaluator_plan_state(tmp_path)
    _set_openai_live_gates(monkeypatch)
    write_evaluator_artifact(
        _minimal_evaluator_payload(),
        root=tmp_path,
        artifact_path=tmp_path / DEFAULT_ARTIFACT_REL,
    )
    autocycle = evaluate_autocycle_cycle(
        root=tmp_path,
        working_tree=WorkingTreeStatus(clean=True, branch="main", dirty_paths=[]),
    )
    assert autocycle["status"] == "stopped"
    assert "run_openai_synthesis_live_canary" in str(autocycle.get("stop_reason") or "")
    assert autocycle.get("recommended_action", {}).get("gate") == "review_gated"


def test_execute_safe_hook_skipped_when_evaluator_artifact_present(tmp_path: Path) -> None:
    _seed_evaluator_plan_state(tmp_path)
    write_evaluator_artifact(
        _minimal_evaluator_payload(),
        root=tmp_path,
        artifact_path=tmp_path / DEFAULT_ARTIFACT_REL,
    )
    result = run_openai_synthesis_evaluator_execute_safe_hook(root=tmp_path, branch="main")
    assert result is None


def test_execute_safe_hook_skipped_when_fixture_missing(tmp_path: Path) -> None:
    _seed_evaluator_plan_state(tmp_path)
    result = run_openai_synthesis_evaluator_execute_safe_hook(root=tmp_path, branch="main")
    assert result == {
        "status": "skipped",
        "detail": "fixture missing: fixtures/synthesis/grounded_evidence_packet_dry_run.json",
    }


def test_execute_safe_hook_mock_synthesizes_and_writes_evaluator(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from tests.unit.test_openai_synthesis_evaluator import REPO_ROOT

    _seed_evaluator_plan_state(tmp_path)
    monkeypatch.setenv("RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST", "openai")
    monkeypatch.setenv("RGE_CLOUD_MAX_USD_PER_RUN", "0.50")
    monkeypatch.setenv("RGE_CLOUD_MAX_TOKENS_PER_CALL", "4096")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    fixture_src = REPO_ROOT / "fixtures/synthesis/grounded_evidence_packet_dry_run.json"
    fixture_dest = tmp_path / "fixtures/synthesis/grounded_evidence_packet_dry_run.json"
    fixture_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(fixture_src, fixture_dest)

    result = run_openai_synthesis_evaluator_execute_safe_hook(root=tmp_path, branch="main")
    assert result is not None
    assert result["status"] == "completed"
    assert result["live_http_used"] is False
    assert result["mock_synthesized"] is True
    assert (tmp_path / SYNTHESIS_CANARY_OUTPUT_REL).is_file()
    assert load_evaluator_artifact(root=tmp_path) is not None


def test_execute_safe_hook_uses_existing_canary_without_mock_synthesize(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from tests.unit.test_openai_synthesis_evaluator import REPO_ROOT

    _seed_evaluator_plan_state(tmp_path)
    monkeypatch.setenv("RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST", "openai")
    monkeypatch.setenv("RGE_CLOUD_MAX_USD_PER_RUN", "0.50")
    monkeypatch.setenv("RGE_CLOUD_MAX_TOKENS_PER_CALL", "4096")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    fixture_src = REPO_ROOT / "fixtures/synthesis/grounded_evidence_packet_dry_run.json"
    fixture_dest = tmp_path / "fixtures/synthesis/grounded_evidence_packet_dry_run.json"
    fixture_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(fixture_src, fixture_dest)
    bootstrap = run_openai_synthesis_evaluator_execute_safe_hook(
        root=tmp_path,
        branch="main",
    )
    assert bootstrap is not None and bootstrap["status"] == "completed"
    (tmp_path / DEFAULT_ARTIFACT_REL).unlink(missing_ok=True)

    def fail_synthesize(**_kwargs: object) -> dict:
        raise AssertionError("run_synthesis_packet should not run when canary exists")

    monkeypatch.setattr(
        "rge.modules.synthesis_packet_runner.run_synthesis_packet",
        fail_synthesize,
    )
    result = run_openai_synthesis_evaluator_execute_safe_hook(root=tmp_path, branch="main")
    assert result is not None
    assert result["status"] == "completed"
    assert result["mock_synthesized"] is False
    assert load_evaluator_artifact(root=tmp_path) is not None


def test_self_improvement_status_includes_review_status(tmp_path: Path) -> None:
    from rge.modules.self_improvement_status import build_self_improvement_status

    seed_operator_neutral_plan_state(tmp_path)
    _seed_evaluator_cli(tmp_path)
    payload = build_self_improvement_status(root=tmp_path)
    review = payload["current_state"]["openai_synthesis_review_status"]
    assert review["cli_wired"] is True
    assert "live_http_gates_missing" in review
    assert "operator_commands" in review


def _seed_evaluator_plan_state(tmp_path: Path) -> None:
    seed_operator_neutral_plan_state(tmp_path)
    seed_synthesis_human_review_neutral_artifact(tmp_path)
    _seed_evaluator_cli(tmp_path)
    health = tmp_path / "apps/public-site/public/data/atlas_source_health_run_latest.json"
    if health.is_file():
        health.touch()


def _seed_evaluator_cli(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    (scripts / "run_openai_synthesis_evaluator.py").write_text("# evaluator\n", encoding="utf-8")
    modules = tmp_path / "rge" / "modules"
    modules.mkdir(parents=True, exist_ok=True)
    (modules / "openai_synthesis_evaluator.py").write_text("# module\n", encoding="utf-8")
