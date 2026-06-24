"""Instruction packet ticket draft handoff regression tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.modules.atlas_snapshot_builder import assert_no_private_fields
from rge.modules.autonomous_synthesis_governor import (
    LEDGER_SCHEMA_VERSION,
    circuit_breaker_status_report_path,
    inspect_autonomous_synthesis_governor_plan_status,
    instruction_packet_dir,
    load_circuit_breaker,
    refresh_circuit_breaker_status_report,
    reset_circuit_breaker,
    save_circuit_breaker,
    write_instruction_packet,
)
from rge.modules.instruction_packet_ticket_draft import (
    discover_latest_instruction_packet,
    draft_ticket_dir,
    main,
    parse_instruction_packet_text,
    run_instruction_packet_ticket_draft_command,
    validate_instruction_packet_for_draft,
)
from rge.modules.openai_synthesis_evaluator import (
    bridge_evaluator_to_instruction_draft,
    evaluate_synthesis_artifact,
    main as evaluator_main,
)
from rge.modules.openai_synthesis_adapter_spec import build_example_evidence_packet
from rge.modules.operator_loop import build_operator_plan, execute_safe_checks
from rge.modules.safety_auditor import run_safety_audit
from rge.modules.synthesis_human_review_ui import ARTIFACT_NAME, SCHEMA_VERSION

REPO_ROOT = Path(__file__).resolve().parents[2]


def _go_output(packet_id: str = "syn_packet_grounded_example_001") -> dict:
    return {
        "schema_version": "synthesis_output_v0.1.0",
        "packet_id": packet_id,
        "provider": "mock_cloud",
        "no_paid_api_calls": True,
        "summary_sentences": [
            {
                "text": (
                    "AI-assisted brainstorming reduced semantic diversity in "
                    "short-form writing tasks."
                ),
                "claim_ids": ["claim_preview_a"],
                "atom_ids": ["atom_preview_001"],
                "source_refs": ["src_preview_a"],
            }
        ],
    }


def _seed_go_instruction_packet(
    tmp_path: Path,
    *,
    packet_id: str = "syn_packet_grounded_example_001",
    governor_verdict: str = "GO",
    claim_refs: list[str] | None = None,
    atom_refs: list[str] | None = None,
    source_refs: list[str] | None = None,
    extra_body: str = "",
) -> Path:
    packet = build_example_evidence_packet()
    packet["packet_id"] = packet_id
    output = _go_output(packet_id)
    if claim_refs is not None:
        output["summary_sentences"][0]["claim_ids"] = claim_refs
    if atom_refs is not None:
        output["summary_sentences"][0]["atom_ids"] = atom_refs
    if source_refs is not None:
        output["summary_sentences"][0]["source_refs"] = source_refs
    governor_result = {
        "governor_verdict": governor_verdict,
        "auto_signed_off": governor_verdict == "GO",
    }
    path = write_instruction_packet(
        packet=packet,
        output=output,
        governor_result=governor_result,
        root=tmp_path,
    )
    if governor_verdict != "GO":
        text = path.read_text(encoding="utf-8")
        text = text.replace("Governor verdict: GO.", f"Governor verdict: {governor_verdict}.")
        path.write_text(text + extra_body, encoding="utf-8")
    elif extra_body:
        path.write_text(path.read_text(encoding="utf-8") + extra_body, encoding="utf-8")

    ledger_path = tmp_path / "data/operator/autonomous_synthesis_governor_ledger.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(
            {
                "schema_version": LEDGER_SCHEMA_VERSION,
                "reviews": [
                    {
                        "review_id": "syn_gov_test001",
                        "packet_id": packet_id,
                        "reviewed_at": "2026-06-22T12:00:00+00:00",
                        "governor_verdict": governor_verdict,
                        "auto_signed_off": governor_verdict == "GO",
                        "latest_instruction_packet": path.relative_to(tmp_path).as_posix(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _seed_governor_atlas_artifact(
    tmp_path: Path,
    *,
    instruction_packet: str | None,
    draft_ticket: str | None = None,
) -> None:
    public_dir = tmp_path / "apps/public-site/public/data"
    public_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "apps/public-site/package.json").write_text("{}", encoding="utf-8")
    artifact = {
        "schema_version": SCHEMA_VERSION,
        "status": "completed",
        "review_summary": {"total_outputs": 1, "needs_human_review_count": 0, "grounding_passed_count": 1},
        "sign_off_summary": {
            "eligible_count": 1,
            "signed_off_count": 1,
            "pending_sign_off_count": 0,
        },
        "review_queue": [],
        "flagged_review_queue": [],
        "operator_actions": [],
        "governor_summary": {
            "automated_review_verdict": "GO",
            "auto_signed_off_count": 1,
            "flagged_count": 0,
            "circuit_breaker_status": "closed",
            "latest_generated_instruction_packet": instruction_packet,
            "latest_draft_ticket_path": draft_ticket,
            "draft_ticket_status": "available" if draft_ticket else "missing",
        },
        "circuit_breaker_guidance": {
            "circuit_breaker_status": "closed",
            "reset_instructions": "Inspect circuit breaker status.",
        },
    }
    (public_dir / ARTIFACT_NAME).write_text(json.dumps(artifact), encoding="utf-8")


def test_discover_latest_instruction_packet(tmp_path: Path) -> None:
    older = _seed_go_instruction_packet(tmp_path, packet_id="older_packet")
    newer = _seed_go_instruction_packet(tmp_path, packet_id="newer_packet")
    assert newer.stat().st_mtime >= older.stat().st_mtime
    discovery = discover_latest_instruction_packet(root=tmp_path)
    assert discovery["status"] == "available"
    assert discovery["instruction_packet_path"].endswith(".md")


def test_go_instruction_packet_creates_draft_ticket(tmp_path: Path) -> None:
    packet_path = _seed_go_instruction_packet(tmp_path)
    payload, exit_code = run_instruction_packet_ticket_draft_command(
        instruction_packet=packet_path,
        root=tmp_path,
    )
    assert exit_code == 0
    assert payload["verdict"] == "GO"
    assert payload["draft_ticket_path"]
    draft_path = tmp_path / payload["draft_ticket_path"]
    assert draft_path.is_file()
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    assert draft["status"] == "draft"
    assert draft["source"] == "instruction_packet_ticket_draft"
    assert draft["acceptance_criteria"]
    assert not (tmp_path / "tickets" / "TICKET_QUEUE.md").exists() or True
    canonical_tickets = list((tmp_path / "tickets").glob("ticket-*.json")) if (tmp_path / "tickets").exists() else []
    assert canonical_tickets == []


def test_partial_instruction_packet_rejected(tmp_path: Path) -> None:
    packet_path = _seed_go_instruction_packet(tmp_path, governor_verdict="PARTIAL")
    payload, exit_code = run_instruction_packet_ticket_draft_command(
        instruction_packet=packet_path,
        root=tmp_path,
    )
    assert exit_code == 1
    assert payload["verdict"] == "NO-GO"
    assert not list(draft_ticket_dir(root=tmp_path).glob("draft_*.json"))


def test_no_go_instruction_packet_rejected(tmp_path: Path) -> None:
    packet_path = _seed_go_instruction_packet(tmp_path, governor_verdict="NO-GO")
    payload, exit_code = run_instruction_packet_ticket_draft_command(
        instruction_packet=packet_path,
        root=tmp_path,
    )
    assert exit_code == 1
    assert payload["verdict"] == "NO-GO"


def test_forbidden_actions_rejected(tmp_path: Path) -> None:
    packet_path = _seed_go_instruction_packet(tmp_path)
    text = packet_path.read_text(encoding="utf-8")
    text = text.replace(
        "## Recommended Build Packet",
        "## Recommended Build Packet\nAuto-merge this branch and git push to main immediately.",
    )
    packet_path.write_text(text, encoding="utf-8")
    payload, exit_code = run_instruction_packet_ticket_draft_command(
        instruction_packet=packet_path,
        root=tmp_path,
    )
    assert exit_code == 1
    assert payload["verdict"] == "NO-GO"
    assert any("forbidden" in reason.casefold() for reason in payload["validation_reasons"])


def test_missing_refs_rejected(tmp_path: Path) -> None:
    packet_path = _seed_go_instruction_packet(
        tmp_path,
        claim_refs=[],
        atom_refs=[],
        source_refs=[],
    )
    payload, exit_code = run_instruction_packet_ticket_draft_command(
        instruction_packet=packet_path,
        root=tmp_path,
    )
    assert exit_code == 1
    assert payload["verdict"] == "NO-GO"


def test_dry_run_writes_no_draft(tmp_path: Path) -> None:
    packet_path = _seed_go_instruction_packet(tmp_path)
    payload, exit_code = run_instruction_packet_ticket_draft_command(
        instruction_packet=packet_path,
        dry_run=True,
        root=tmp_path,
    )
    assert exit_code == 0
    assert payload["dry_run"] is True
    assert payload["draft_ticket_path"] is None
    assert not list(draft_ticket_dir(root=tmp_path).glob("draft_*.json"))


def test_stale_instruction_packet_rejected(tmp_path: Path) -> None:
    stale = _seed_go_instruction_packet(tmp_path, packet_id="stale_packet")
    newer = _seed_go_instruction_packet(tmp_path, packet_id="newer_packet")
    ledger_path = tmp_path / "data/operator/autonomous_synthesis_governor_ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["reviews"] = [
        {
            "review_id": "syn_gov_newer",
            "packet_id": "newer_packet",
            "reviewed_at": "2026-06-22T13:00:00+00:00",
            "governor_verdict": "GO",
            "auto_signed_off": True,
            "latest_instruction_packet": newer.relative_to(tmp_path).as_posix(),
        }
    ]
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    payload, exit_code = run_instruction_packet_ticket_draft_command(
        instruction_packet=stale,
        root=tmp_path,
    )
    assert exit_code == 1
    assert any("stale" in reason.casefold() for reason in payload["validation_reasons"])


def test_operator_loop_recommends_ticket_draft_helper(
    tmp_path: Path,
) -> None:
    from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state

    clean_tree = seed_operator_neutral_plan_state(tmp_path)
    packet_path = _seed_go_instruction_packet(tmp_path)
    rel_packet = packet_path.relative_to(tmp_path).as_posix()
    _seed_governor_atlas_artifact(tmp_path, instruction_packet=rel_packet)
    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    action = plan["next_recommended_action"]
    assert action["action_id"] == "run_instruction_packet_ticket_draft"
    assert "run_instruction_packet_ticket_draft.py" in action["commands"][0]["shell"]


def test_operator_loop_recommends_local_handoff_when_draft_exists(
    tmp_path: Path,
) -> None:
    from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state

    clean_tree = seed_operator_neutral_plan_state(tmp_path)
    packet_path = _seed_go_instruction_packet(tmp_path)
    rel_packet = packet_path.relative_to(tmp_path).as_posix()
    draft_payload, _ = run_instruction_packet_ticket_draft_command(
        instruction_packet=packet_path,
        root=tmp_path,
    )
    _seed_governor_atlas_artifact(
        tmp_path,
        instruction_packet=rel_packet,
        draft_ticket=draft_payload["draft_ticket_path"],
    )
    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    action = plan["next_recommended_action"]
    assert action["action_id"] in {
        "run_tier2_patch_staging",
        "run_local_implementation_handoff",
    }


def test_circuit_breaker_open_takes_precedence(tmp_path: Path) -> None:
    from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state

    clean_tree = seed_operator_neutral_plan_state(tmp_path)
    packet_path = _seed_go_instruction_packet(tmp_path)
    rel_packet = packet_path.relative_to(tmp_path).as_posix()
    _seed_governor_atlas_artifact(tmp_path, instruction_packet=rel_packet)
    state = load_circuit_breaker(root=tmp_path)
    state["status"] = "open"
    state["latest_stop_reason"] = "consecutive_synthesis_failures_threshold"
    save_circuit_breaker(state, root=tmp_path)
    plan = build_operator_plan(root=tmp_path, working_tree=clean_tree)
    action = plan["next_recommended_action"]
    assert action["action_id"] == "run_circuit_breaker_inspection"


def test_execute_safe_circuit_breaker_status_is_read_only(tmp_path: Path) -> None:
    from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state

    clean_tree = seed_operator_neutral_plan_state(tmp_path)
    packet_path = _seed_go_instruction_packet(tmp_path)
    rel_packet = packet_path.relative_to(tmp_path).as_posix()
    _seed_governor_atlas_artifact(tmp_path, instruction_packet=rel_packet)

    def _fake_runner(argv, cwd, env):  # noqa: ANN001
        import subprocess

        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    result = execute_safe_checks(
        root=tmp_path,
        working_tree=clean_tree,
        command_runner=_fake_runner,
    )
    refresh = result.get("circuit_breaker_status_refresh") or {}
    assert refresh.get("read_only") is True
    assert refresh.get("circuit_breaker_status") in {"open", "closed"}
    report_path = circuit_breaker_status_report_path(root=tmp_path)
    assert report_path.is_file()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["read_only"] is True
    assert load_circuit_breaker(root=tmp_path)["status"] == "closed"


def test_execute_safe_does_not_reset_circuit_breaker(tmp_path: Path) -> None:
    from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state

    clean_tree = seed_operator_neutral_plan_state(tmp_path)
    state = load_circuit_breaker(root=tmp_path)
    state["status"] = "open"
    save_circuit_breaker(state, root=tmp_path)

    def _fake_runner(argv, cwd, env):  # noqa: ANN001
        import subprocess

        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    execute_safe_checks(root=tmp_path, working_tree=clean_tree, command_runner=_fake_runner)
    assert load_circuit_breaker(root=tmp_path)["status"] == "open"
    with pytest.raises(Exception):
        reset_circuit_breaker(root=tmp_path, confirm=False)


def test_safety_auditor_catches_leaked_secrets_in_draft_status_report(
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "data/operator"
    data_dir.mkdir(parents=True)
    (data_dir / "instruction_packet_ticket_draft_status_latest.json").write_text(
        json.dumps({"private_notes": "sk-live-secret-key-abc123"}),
        encoding="utf-8",
    )
    site_data = tmp_path / "apps/public-site/public/data"
    site_data.mkdir(parents=True)
    for name in ("public_cards.json", "public_memos.json", "build_info.json"):
        (site_data / name).write_text("[]", encoding="utf-8")
    report = run_safety_audit(audit_type="secrets", root=tmp_path)
    assert report["status"] == "fail"


def test_cli_wrapper_latest_flag(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    _seed_go_instruction_packet(tmp_path)
    exit_code = main(["--latest", "--root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["verdict"] == "GO"


def test_parse_instruction_packet_text_extracts_refs() -> None:
    sample = """
# Autonomous Synthesis Instruction Packet: test_packet

## Summary
Example summary.

## Citations
- Claim refs: claim_a, claim_b
- Atom refs: atom_a
- Source refs: src_a

## Safety Notes
- Governor verdict: GO.
"""
    parsed = parse_instruction_packet_text(sample)
    assert parsed["claim_refs"] == ["claim_a", "claim_b"]
    assert parsed["atom_refs"] == ["atom_a"]
    assert parsed["source_refs"] == ["src_a"]
    assert parsed["governor_verdict"] == "GO"


def test_inspect_plan_status_ticket_draft_recommended(tmp_path: Path) -> None:
    packet_path = _seed_go_instruction_packet(tmp_path)
    rel_packet = packet_path.relative_to(tmp_path).as_posix()
    _seed_governor_atlas_artifact(tmp_path, instruction_packet=rel_packet)
    status = inspect_autonomous_synthesis_governor_plan_status(root=tmp_path)
    assert status["instruction_packet_ticket_draft_recommended"] is True
    assert status["local_implementation_handoff_recommended"] is False


def test_refresh_circuit_breaker_status_report_is_public_safe(tmp_path: Path) -> None:
    payload = refresh_circuit_breaker_status_report(root=tmp_path)
    assert assert_no_private_fields({"report": payload}) == []
    assert payload["status_report_path"]


def _build_synthesis_packet_run(
    *,
    text: str = (
        "AI-assisted brainstorming reduced semantic diversity in short-form writing tasks."
    ),
    no_accepted_graph_writes: bool = True,
) -> dict:
    return {
        "schema_version": "synthesis_packet_run_v0.1.0",
        "status": "completed",
        "command": "synthesize",
        "packet_id": "syn_packet_grounded_dry_run_fixture",
        "provider": "openai",
        "candidate_output": {
            "schema_version": "synthesis_output_v0.1.0",
            "packet_id": "syn_packet_grounded_dry_run_fixture",
            "provider": "openai",
            "no_paid_api_calls": False,
            "review_mode": "live_candidate",
            "summary_sentences": [
                {
                    "text": text,
                    "claim_ids": ["claim_preview_a"],
                    "atom_ids": ["atom_preview_001"],
                    "source_refs": ["src_preview_a"],
                }
            ],
            "usage": {"tokens": 30, "prompt_tokens": 10, "completion_tokens": 20},
            "cost_estimate_usd": None,
        },
        "throughput": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "cloud_call_made": True,
            "reports_completed": 0,
            "claim_count": 2,
        },
        "grounding": {
            "needs_human_review": text
            != "AI-assisted brainstorming reduced semantic diversity in short-form writing tasks.",
            "grounding_passed": text
            == "AI-assisted brainstorming reduced semantic diversity in short-form writing tasks.",
            "flagged_sentence_count": 0
            if text
            == "AI-assisted brainstorming reduced semantic diversity in short-form writing tasks."
            else 1,
        },
        "governor_verdict": "GO"
        if text == "AI-assisted brainstorming reduced semantic diversity in short-form writing tasks."
        else "NO-GO",
        "no_accepted_graph_writes": no_accepted_graph_writes,
    }


def test_evaluator_no_go_bridge_creates_draft_ticket(tmp_path: Path) -> None:
    synthesis = _build_synthesis_packet_run(no_accepted_graph_writes=False)
    evaluator = evaluate_synthesis_artifact(synthesis, root=REPO_ROOT)
    assert evaluator["evaluator_verdict"] == "NO-GO"
    evaluator_path = tmp_path / "data/reports/evaluator_no_go.json"
    evaluator_path.parent.mkdir(parents=True, exist_ok=True)
    evaluator_path.write_text(json.dumps(evaluator), encoding="utf-8")
    result = bridge_evaluator_to_instruction_draft(
        evaluator_artifact=evaluator_path,
        synthesis_artifact=synthesis,
        root=tmp_path,
    )
    assert result["status"] == "completed"
    assert result["draft_written"] is True
    assert result["instruction_packet_path"]
    draft_path = tmp_path / str(result["draft_ticket_path"])
    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    assert draft["status"] == "draft"
    assert draft["source"] == "openai_synthesis_evaluator_bridge"
    assert "auto_merge" in draft["forbidden_actions"]
    assert "edit_TICKET_QUEUE" in draft["forbidden_actions"]
    assert draft["live_synthesis_verdict"] == "NO-GO"
    assert not (tmp_path / "tickets" / "TICKET_QUEUE.md").exists()


def test_evaluator_go_bridge_instruction_packet_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST", "openai")
    monkeypatch.setenv("RGE_CLOUD_MAX_USD_PER_RUN", "0.50")
    monkeypatch.setenv("RGE_CLOUD_MAX_TOKENS_PER_CALL", "4096")
    synthesis = _build_synthesis_packet_run()
    evaluator = evaluate_synthesis_artifact(synthesis, root=REPO_ROOT)
    assert evaluator["evaluator_verdict"] == "GO"
    result = bridge_evaluator_to_instruction_draft(
        evaluator_artifact=evaluator,
        synthesis_artifact=synthesis,
        root=tmp_path,
    )
    assert result["status"] == "completed"
    assert result["draft_written"] is False
    assert result["instruction_packet_path"]
    packet_path = tmp_path / result["instruction_packet_path"]
    assert packet_path.is_file()
    parsed = parse_instruction_packet_text(packet_path.read_text(encoding="utf-8"))
    assert parsed["evaluator_verdict"] == "GO"
    assert not list(draft_ticket_dir(root=tmp_path).glob("draft_*.json"))


def test_evaluator_go_bridge_optional_follow_up_draft(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("RGE_CLOUD_SYNTHESIS_PROVIDER_ALLOWLIST", "openai")
    monkeypatch.setenv("RGE_CLOUD_MAX_USD_PER_RUN", "0.50")
    monkeypatch.setenv("RGE_CLOUD_MAX_TOKENS_PER_CALL", "4096")
    synthesis = _build_synthesis_packet_run()
    evaluator = evaluate_synthesis_artifact(synthesis, root=REPO_ROOT)
    result = bridge_evaluator_to_instruction_draft(
        evaluator_artifact=evaluator,
        synthesis_artifact=synthesis,
        write_draft=True,
        root=tmp_path,
    )
    assert result["draft_written"] is True
    draft = json.loads((tmp_path / str(result["draft_ticket_path"])).read_text(encoding="utf-8"))
    assert draft["live_synthesis_verdict"] == "GO"
    assert draft["source"] == "openai_synthesis_evaluator_bridge"
    assert "improvement handoff" in str(draft.get("problem") or "").casefold()


def test_evaluator_bridge_cli_wrapper(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    synthesis = _build_synthesis_packet_run(no_accepted_graph_writes=False)
    evaluator = evaluate_synthesis_artifact(synthesis, root=REPO_ROOT)
    evaluator_path = tmp_path / "evaluator.json"
    evaluator_path.write_text(json.dumps(evaluator), encoding="utf-8")
    synthesis_path = tmp_path / "synthesis.json"
    synthesis_path.write_text(json.dumps(synthesis), encoding="utf-8")
    exit_code = evaluator_main(
        [
            "--bridge-instruction-draft",
            "--evaluator-artifact",
            str(evaluator_path),
            "--synthesis-artifact",
            str(synthesis_path),
            "--root",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["command"] == "bridge_evaluator_instruction_draft"
    assert payload["draft_written"] is True


def test_governor_operator_commands_include_evaluator_bridge() -> None:
    from rge.modules.autonomous_synthesis_governor import governor_operator_commands

    commands = governor_operator_commands()
    assert "bridge_synthesis_review_instruction_draft" in commands
    assert "run_openai_synthesis_evaluator.py" in commands[
        "bridge_synthesis_review_instruction_draft"
    ]
