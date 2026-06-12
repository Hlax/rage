"""Mock-only verification suite for `research verify`.

Runs the same deterministic checks as operator loop execute-safe without
git working-tree or queue preconditions.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from rge.modules.operator_loop import safe_verification_commands

_MOCK_ENV = {
    "RGE_LLM_MODE": "mock",
    "RGE_ALLOW_LIVE_LLM": "0",
    "RGE_TEST_LLM_MODE": "mock",
}


def run_verification(
    *,
    root: Path | None = None,
    skip_site: bool = False,
    command_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> dict[str, Any]:
    """Run mock-only verification commands and return a JSON-serializable report."""
    project_root = root or Path(__file__).resolve().parents[2]
    runner = command_runner or subprocess.run
    commands = safe_verification_commands(project_root)
    if skip_site:
        commands = [cmd for cmd in commands if cmd["name"] != "public_site_build"]

    results: list[dict[str, Any]] = []
    all_passed = True
    for command in commands:
        env = os.environ.copy()
        env.update(_MOCK_ENV)
        env.update(command.get("env", {}))
        completed = runner(
            command["argv"],
            cwd=command["cwd"],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        passed = completed.returncode == 0
        all_passed = all_passed and passed
        results.append(
            {
                "name": command["name"],
                "shell": command["shell"],
                "exit_code": completed.returncode,
                "passed": passed,
                "stdout_tail": completed.stdout[-500:] if completed.stdout else "",
                "stderr_tail": completed.stderr[-500:] if completed.stderr else "",
            }
        )

    return {
        "report_type": "verification_report",
        "command": "verify",
        "status": "pass" if all_passed else "fail",
        "mode": "mock",
        "skip_site": skip_site,
        "python": sys.version.split()[0],
        "checks": results,
    }
