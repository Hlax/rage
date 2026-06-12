"""Unit tests for UTF-8-safe subprocess capture."""

from __future__ import annotations

import subprocess
import sys

from rge.modules.operator_loop import WorkingTreeStatus, execute_safe_checks
from rge.modules.verify_runner import run_verification
from rge.subprocess_capture import run_captured


def test_run_captured_replaces_invalid_utf8_bytes() -> None:
    script = (
        "import sys; sys.stdout.buffer.write(b'prefix \\x8f \\xe2\\x9c\\x93 suffix\\n')"
    )
    completed = run_captured([sys.executable, "-c", script])
    assert completed.returncode == 0
    assert "prefix" in completed.stdout
    assert "suffix" in completed.stdout
    assert "\ufffd" in completed.stdout


def test_run_captured_preserves_nonzero_exit_code() -> None:
    completed = run_captured([sys.executable, "-c", "import sys; sys.exit(7)"])
    assert completed.returncode == 7


def test_execute_safe_checks_survives_binary_mixed_stdout(tmp_path, monkeypatch) -> None:
    site = tmp_path / "apps" / "public-site"
    site.mkdir(parents=True)
    (site / "package.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "rge.modules.operator_loop.resolve_npm_executable",
        lambda: sys.executable,
    )

    script = (
        "import sys; sys.stdout.buffer.write(b'build \\x8f ok\\n'); sys.exit(0)"
    )

    def runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if argv[:3] == [sys.executable, "-m", "pytest"]:
            return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")
        if len(argv) >= 2 and argv[-2:] == ["run", "build"]:
            return run_captured([sys.executable, "-c", script])
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    result = execute_safe_checks(
        root=tmp_path,
        working_tree=WorkingTreeStatus(clean=True, branch="main", dirty_paths=[]),
        command_runner=runner,
    )
    site_build = [
        item for item in result["execution_results"] if item["name"] == "public_site_build"
    ]
    assert site_build
    assert site_build[0]["passed"] is True
    assert "build" in site_build[0]["stdout_tail"]
    assert result["execution_status"] == "pass"


def test_execute_safe_checks_fails_on_nonzero_subprocess_exit(tmp_path) -> None:
    def runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "tests/golden" in argv:
            return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")
        if "tests/golden" not in argv and "pytest" in argv:
            return subprocess.CompletedProcess(argv, 1, stdout="", stderr="pytest failed")
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    result = execute_safe_checks(
        root=tmp_path,
        working_tree=WorkingTreeStatus(clean=True, branch="main", dirty_paths=[]),
        command_runner=runner,
    )
    assert result["execution_status"] == "fail"
    failed = [item for item in result["execution_results"] if not item["passed"]]
    assert failed
    assert failed[0]["exit_code"] == 1


def test_run_verification_survives_binary_mixed_stdout(tmp_path, monkeypatch) -> None:
    site = tmp_path / "apps" / "public-site"
    site.mkdir(parents=True)
    (site / "package.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "rge.modules.operator_loop.resolve_npm_executable",
        lambda: sys.executable,
    )
    script = "import sys; sys.stderr.buffer.write(b'warn \\x8f tail\\n')"

    def runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if len(argv) >= 2 and argv[-2:] == ["run", "build"]:
            return run_captured([sys.executable, "-c", script])
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    result = run_verification(
        root=tmp_path,
        skip_site=False,
        command_runner=runner,
    )
    site_build = [item for item in result["checks"] if item["name"] == "public_site_build"]
    assert site_build
    assert site_build[0]["passed"] is True
    assert "warn" in site_build[0]["stderr_tail"]
    assert result["status"] == "pass"
