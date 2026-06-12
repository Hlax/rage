"""Unit tests for research verify mock-only suite."""

from __future__ import annotations

import subprocess
from pathlib import Path

from rge.modules.verify_runner import run_verification


def test_run_verification_reports_pass_with_mock_runner(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_runner(
        argv: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    result = run_verification(
        root=tmp_path,
        skip_site=True,
        command_runner=fake_runner,
    )

    assert result["status"] == "pass"
    assert result["command"] == "verify"
    assert result["skip_site"] is True
    assert len(calls) == 3
    assert all(item["passed"] for item in result["checks"])


def test_run_verification_reports_fail_on_nonzero_exit(tmp_path: Path) -> None:
    def fail_pytest(
        argv: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        if "pytest" in argv and "tests/golden" not in argv:
            return subprocess.CompletedProcess(argv, 1, stdout="", stderr="fail")
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    result = run_verification(
        root=tmp_path,
        skip_site=True,
        command_runner=fail_pytest,
    )

    assert result["status"] == "fail"
    assert any(not item["passed"] for item in result["checks"])


def test_research_verify_cli_with_skip_site(monkeypatch) -> None:
    from rge.cli import main

    def fake_run(*, root, skip_site, command_runner=None):
        assert skip_site is True
        return {
            "report_type": "verification_report",
            "command": "verify",
            "status": "pass",
            "mode": "mock",
            "skip_site": True,
            "checks": [],
        }

    import rge.cli as cli_module

    monkeypatch.setattr(cli_module, "_REPO_ROOT", Path("."))
    import rge.modules.verify_runner as verify_runner

    monkeypatch.setattr(verify_runner, "run_verification", fake_run)

    exit_code = main(["verify", "--skip-site"])
    assert exit_code == 0
