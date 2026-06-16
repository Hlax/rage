"""Unit tests for research verify operator checklist (ticket-270)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from rge.cli import main
from rge.modules.operator_proof_bundle import COMMAND
from rge.modules.verify_runner import mock_gate_operator_checklist, run_verification


def test_mock_gate_operator_checklist_references_proof_bundle(tmp_path: Path) -> None:
    checklist = mock_gate_operator_checklist(tmp_path)

    assert len(checklist) == 1
    entry = checklist[0]
    assert entry["id"] == "prove_arbitrary_source_bundle"
    assert entry["command"] == COMMAND
    assert entry["automated_in_verify"] is False
    assert "prove-arbitrary-source-bundle" in entry["shell"]


def test_run_verification_includes_operator_checklist(tmp_path: Path) -> None:
    def fake_runner(
        argv: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    result = run_verification(
        root=tmp_path,
        skip_site=True,
        command_runner=fake_runner,
    )

    assert result["skip_site"] is True
    assert "operator_checklist" in result
    assert result["operator_checklist"][0]["command"] == COMMAND
    assert (
        result["arbitrary_source_proof_bundle_status"]["command"] == COMMAND
    )
    assert "prove-arbitrary-source-bundle" in (
        result["operator_checklist"][0]["shell"]
    )


def test_verify_cli_skip_site_stdout_includes_proof_bundle_checklist(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run(*, root, skip_site, command_runner=None):
        assert skip_site is True
        return run_verification(
            root=root,
            skip_site=skip_site,
            command_runner=lambda argv, **kwargs: subprocess.CompletedProcess(
                argv, 0, stdout="ok", stderr=""
            ),
        )

    import rge.cli as cli_module

    monkeypatch.setattr(cli_module, "_REPO_ROOT", Path("."))
    import rge.modules.verify_runner as verify_runner

    monkeypatch.setattr(verify_runner, "run_verification", fake_run)

    exit_code = main(["verify", "--skip-site"])
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["command"] == "verify"
    assert payload["skip_site"] is True
    assert payload["operator_checklist"][0]["command"] == COMMAND
    assert "prove-arbitrary-source-bundle" in payload["operator_checklist"][0]["shell"]
