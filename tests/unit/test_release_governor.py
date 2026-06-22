"""Release governor and autonomy tier policy regression tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.modules.autonomy_tier_policy import (
    action_allowed,
    configured_autonomy_tier,
    effective_autonomy_tier,
    summarize_tier_policy,
)
from rge.modules.autonomous_synthesis_governor import (
    GovernorOperatorSurfaceError,
    LEDGER_SCHEMA_VERSION,
    load_circuit_breaker,
    load_governor_ledger,
    load_governor_remediations,
    resolve_historical_no_go_review,
    save_circuit_breaker,
)
from rge.modules.operator_loop import build_operator_plan, execute_safe_checks
from rge.modules.release_governor import (
    build_safe_fixture_batch,
    evaluate_release_governor,
    inspect_release_governor_plan_status,
    load_release_batch,
    main,
    promote_draft_tickets_to_candidates,
    release_batch_dir,
    run_release_governor_command,
    validate_batch_schema,
    write_release_report,
)
from rge.modules.safety_auditor import run_safety_audit


def _write_batch(tmp_path: Path, batch: dict, name: str = "batch_fixture_safe_001.json") -> Path:
    batch_dir = release_batch_dir(root=tmp_path)
    batch_dir.mkdir(parents=True, exist_ok=True)
    path = batch_dir / name
    path.write_text(json.dumps(batch), encoding="utf-8")
    return path


def _seed_safe_batch(tmp_path: Path, **overrides: object) -> Path:
    batch = build_safe_fixture_batch()
    batch.update(overrides)
    reports_dir = tmp_path / "agent_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "2026-06-22_autonomous-release-governor-batch-promotion.md").write_text(
        "# report", encoding="utf-8"
    )
    (reports_dir / "2026-06-22_autonomous-release-governor-batch-promotion-latest.json").write_text(
        "{}", encoding="utf-8"
    )
    return _write_batch(tmp_path, batch)


def test_tier_policy_blocks_forbidden_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RGE_ALLOW_FEATURE_BRANCH_PUSH", raising=False)
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "1")
    assert action_allowed("generate_draft_ticket")[0] is True
    assert action_allowed("push_feature_branch")[0] is False
    assert action_allowed("merge_batch")[0] is False
    assert action_allowed("publish_public_export")[0] is False


def test_tier_three_allows_push_with_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "3")
    monkeypatch.setenv("RGE_ALLOW_FEATURE_BRANCH_PUSH", "1")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    assert effective_autonomy_tier() == 3
    assert action_allowed("push_feature_branch")[0] is True
    assert action_allowed("merge_batch")[0] is False


def test_release_governor_dry_run_go_on_safe_fixture(tmp_path: Path) -> None:
    batch_path = _seed_safe_batch(tmp_path)
    batch = load_release_batch(batch_path, root=tmp_path)
    evaluation = evaluate_release_governor(
        batch,
        root=tmp_path,
        run_verify=False,
        run_safety=False,
    )
    assert evaluation["governor_verdict"] == "GO"


def test_missing_safety_audit_blocks(tmp_path: Path) -> None:
    batch_path = _seed_safe_batch(tmp_path, safety_results={"status": "fail"})
    batch = load_release_batch(batch_path, root=tmp_path)
    evaluation = evaluate_release_governor(
        batch,
        root=tmp_path,
        run_verify=False,
        run_safety=False,
    )
    assert evaluation["governor_verdict"] != "GO"
    assert any("safety_results" in reason for reason in evaluation["failure_reasons"])


def test_verify_failure_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    batch_path = _seed_safe_batch(tmp_path, test_results={"passed": False})
    batch = load_release_batch(batch_path, root=tmp_path)

    def _fail_verify(**kwargs):  # noqa: ANN003
        return {"status": "fail", "results": [{"name": "full_pytest", "passed": False}]}

    monkeypatch.setattr("rge.modules.release_governor.run_verification", _fail_verify)
    evaluation = evaluate_release_governor(batch, root=tmp_path, run_safety=False)
    assert evaluation["governor_verdict"] != "GO"


def test_open_circuit_breaker_blocks(tmp_path: Path) -> None:
    batch_path = _seed_safe_batch(tmp_path)
    batch = load_release_batch(batch_path, root=tmp_path)
    state = load_circuit_breaker(root=tmp_path)
    state["status"] = "open"
    save_circuit_breaker(state, root=tmp_path)
    evaluation = evaluate_release_governor(
        batch,
        root=tmp_path,
        run_verify=False,
        run_safety=False,
    )
    assert evaluation["governor_verdict"] == "NO-GO"
    assert any("circuit breaker" in reason for reason in evaluation["failure_reasons"])


def test_partial_synthesis_output_blocks(tmp_path: Path) -> None:
    batch_path = _seed_safe_batch(tmp_path)
    ledger_path = tmp_path / "data/operator/autonomous_synthesis_governor_ledger.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(
            {
                "schema_version": LEDGER_SCHEMA_VERSION,
                "reviews": [
                    {
                        "review_id": "bad",
                        "governor_verdict": "PARTIAL",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    batch = load_release_batch(batch_path, root=tmp_path)
    evaluation = evaluate_release_governor(
        batch,
        root=tmp_path,
        run_verify=False,
        run_safety=False,
    )
    assert any("PARTIAL" in reason for reason in evaluation["failure_reasons"])


def test_historical_no_go_resolution_preserves_review_and_unblocks_release_governor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    batch_path = _seed_safe_batch(tmp_path)
    ledger_path = tmp_path / "data/operator/autonomous_synthesis_governor_ledger.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(
            {
                "schema_version": LEDGER_SCHEMA_VERSION,
                "reviews": [
                    {
                        "review_id": "syn_gov_budget",
                        "governor_verdict": "NO-GO",
                        "failure_reasons": [
                            "provider 'openai' not in explicit allowlist",
                            "RGE_CLOUD_MAX_USD_PER_RUN is required",
                        ],
                        "metrics": {
                            "budget_gate": {
                                "passed": False,
                                "provider_id": "openai",
                            }
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    batch = load_release_batch(batch_path, root=tmp_path)
    blocked = evaluate_release_governor(
        batch,
        root=tmp_path,
        run_verify=False,
        run_safety=False,
    )
    assert any("syn_gov_budget" in reason for reason in blocked["failure_reasons"])

    with pytest.raises(GovernorOperatorSurfaceError, match="requires --confirm"):
        resolve_historical_no_go_review(
            "syn_gov_budget",
            root=tmp_path,
            operator_label="release-readiness-test",
            confirm=False,
        )
    with pytest.raises(GovernorOperatorSurfaceError, match="provider/budget"):
        resolve_historical_no_go_review(
            "syn_gov_budget",
            root=tmp_path,
            operator_label="release-readiness-test",
            confirm=True,
        )

    monkeypatch.setenv("RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST", "openai")
    monkeypatch.setenv("RGE_CLOUD_MAX_USD_PER_RUN", "0.25")
    monkeypatch.setenv("RGE_CLOUD_MAX_TOKENS_PER_CALL", "2048")

    result = resolve_historical_no_go_review(
        "syn_gov_budget",
        root=tmp_path,
        operator_label="release-readiness-test",
        confirm=True,
    )

    assert result["status"] == "completed"
    assert load_governor_ledger(root=tmp_path)["reviews"][0]["governor_verdict"] == "NO-GO"
    resolutions = load_governor_remediations(root=tmp_path)["resolutions"]
    assert resolutions[0]["review_id"] == "syn_gov_budget"
    assert resolutions[0]["status"] == "resolved"
    assert (tmp_path / result["audit_record_path"]).is_file()

    unblocked = evaluate_release_governor(
        batch,
        root=tmp_path,
        run_verify=False,
        run_safety=False,
    )
    assert unblocked["governor_verdict"] == "GO"


def test_batch_size_limit_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RGE_RELEASE_BATCH_MAX_ITEMS", "1")
    batch_path = _seed_safe_batch(
        tmp_path,
        draft_ticket_ids=["a", "b"],
        branch_names=["b1", "b2"],
    )
    batch = load_release_batch(batch_path, root=tmp_path)
    evaluation = evaluate_release_governor(
        batch,
        root=tmp_path,
        run_verify=False,
        run_safety=False,
    )
    assert any("batch size" in reason for reason in evaluation["failure_reasons"])


def test_rollback_plan_missing_blocks() -> None:
    batch = build_safe_fixture_batch()
    batch["rollback_plan"] = ""
    assert any("rollback" in reason for reason in validate_batch_schema(batch))


def test_changed_file_allowlist_blocks(tmp_path: Path) -> None:
    batch_path = _seed_safe_batch(tmp_path, changed_files=["../secrets/private.key"])
    batch = load_release_batch(batch_path, root=tmp_path)
    evaluation = evaluate_release_governor(
        batch,
        root=tmp_path,
        run_verify=False,
        run_safety=False,
    )
    assert any("allowlist" in reason or "blocked" in reason for reason in evaluation["failure_reasons"])


def test_canonical_ticket_promotion_blocked_until_governor_go(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "4")
    monkeypatch.setenv("RGE_ALLOW_BATCH_MERGE", "1")
    batch_path = _seed_safe_batch(tmp_path, test_results={"passed": False})
    batch = load_release_batch(batch_path, root=tmp_path)
    evaluation = evaluate_release_governor(batch, root=tmp_path, run_safety=False, run_verify=False)
    payload, exit_code = run_release_governor_command(
        candidate=batch_path,
        promote_tickets=True,
        confirm=True,
        dry_run=False,
        root=tmp_path,
    )
    assert evaluation["governor_verdict"] != "GO"
    assert exit_code == 1
    assert payload["actions"][0]["status"] == "blocked"


def test_feature_branch_push_blocked_unless_tier_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    batch_path = _seed_safe_batch(tmp_path)
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "1")
    payload, _ = run_release_governor_command(
        candidate=batch_path,
        push_branches=True,
        confirm=True,
        dry_run=False,
        root=tmp_path,
    )
    push_action = next(row for row in payload["actions"] if row["action"] == "push_branches")
    assert push_action["status"] == "blocked"


def test_merge_publish_blocked_unless_higher_tier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    batch_path = _seed_safe_batch(tmp_path)
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "3")
    monkeypatch.setenv("RGE_ALLOW_FEATURE_BRANCH_PUSH", "1")
    monkeypatch.setenv("RGE_ALLOW_BRANCH_AUTONOMY", "1")
    payload, _ = run_release_governor_command(
        candidate=batch_path,
        merge_batch=True,
        publish=True,
        confirm=True,
        dry_run=False,
        root=tmp_path,
    )
    merge_action = next(row for row in payload["actions"] if row["action"] == "merge_batch")
    publish_action = next(row for row in payload["actions"] if row["action"] == "publish")
    assert merge_action["status"] == "blocked"
    assert publish_action["status"] == "blocked"


def test_promote_tickets_writes_candidates_not_canonical_queue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_AUTONOMY_TIER", "4")
    monkeypatch.setenv("RGE_ALLOW_BATCH_MERGE", "1")
    draft_dir = tmp_path / "data/operator/draft_tickets"
    draft_dir.mkdir(parents=True)
    draft = {
        "id": "draft-from-syn-packet-fixture",
        "status": "draft",
        "title": "Fixture draft",
    }
    (draft_dir / "draft_fixture.json").write_text(json.dumps(draft), encoding="utf-8")
    batch_path = _seed_safe_batch(tmp_path)
    batch = load_release_batch(batch_path, root=tmp_path)
    result = promote_draft_tickets_to_candidates(batch, root=tmp_path, dry_run=False)
    assert result["promoted"]
    assert not (tmp_path / "tickets" / "TICKET_QUEUE.md").exists()
    assert (tmp_path / "data/operator/canonical_ticket_candidates").is_dir()


def test_operator_loop_recommends_release_dry_run(tmp_path: Path) -> None:
    from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state

    clean_tree = seed_operator_neutral_plan_state(tmp_path)
    draft_dir = tmp_path / "data/operator/draft_tickets"
    draft_dir.mkdir(parents=True)
    draft = {"id": "draft-from-syn-packet-fixture", "status": "draft", "title": "Fixture"}
    (draft_dir / "draft_fixture.json").write_text(json.dumps(draft), encoding="utf-8")
    _seed_safe_batch(tmp_path)
    status = inspect_release_governor_plan_status(root=tmp_path)
    assert status["release_governor_dry_run_recommended"] is True
    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    assert plan["next_recommended_action"]["action_id"] == "run_release_governor_dry_run"
    assert plan["release_governor_status"]["release_governor_dry_run_recommended"] is True


def test_execute_safe_can_dry_run_but_not_push(tmp_path: Path) -> None:
    from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state

    clean_tree = seed_operator_neutral_plan_state(tmp_path)
    _seed_safe_batch(tmp_path)

    def _fake_runner(argv, cwd, env):  # noqa: ANN001
        import subprocess

        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    result = execute_safe_checks(
        root=tmp_path,
        working_tree=clean_tree,
        command_runner=_fake_runner,
    )
    assert result.get("release_governor_status_refresh")
    shells = " ".join(row.get("shell", "") for row in result.get("execution_results") or [])
    assert "git push" not in shells
    assert result.get("execution_status") == "pass"


def test_safety_auditor_catches_leaked_secrets_in_release_report(tmp_path: Path) -> None:
    report_path = tmp_path / "data/operator/release_governor_report_latest.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({"private_notes": "sk-secret"}), encoding="utf-8")
    site_data = tmp_path / "apps/public-site/public/data"
    site_data.mkdir(parents=True)
    for name in ("public_cards.json", "public_memos.json", "build_info.json"):
        (site_data / name).write_text("[]", encoding="utf-8")
    report = run_safety_audit(audit_type="secrets", root=tmp_path)
    assert report["status"] == "fail"


def test_cli_inspect_mode(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    exit_code = main(["--inspect", "--root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["status"] == "completed"
    assert "autonomy_tier" in payload


def test_forbidden_synthesis_instructions_block(tmp_path: Path) -> None:
    packet_dir = tmp_path / "data/operator/instruction_packets"
    packet_dir.mkdir(parents=True)
    bad_packet = packet_dir / "bad.md"
    bad_packet.write_text(
        "## Recommended Build Packet\nAuto-merge and git push immediately.\n",
        encoding="utf-8",
    )
    batch_path = _seed_safe_batch(
        tmp_path,
        instruction_packet_refs=[bad_packet.relative_to(tmp_path).as_posix()],
    )
    batch = load_release_batch(batch_path, root=tmp_path)
    evaluation = evaluate_release_governor(
        batch,
        root=tmp_path,
        run_verify=False,
        run_safety=False,
    )
    assert any("forbidden" in reason for reason in evaluation["failure_reasons"])


def test_write_release_report_blocks_private_fields(tmp_path: Path) -> None:
    with pytest.raises(Exception, match="blocked"):
        write_release_report({"private_notes": "secret"}, root=tmp_path)


def test_summarize_tier_policy_default() -> None:
    summary = summarize_tier_policy()
    assert summary["default_tier"] == 1
    assert summary["effective_tier"] >= 0
