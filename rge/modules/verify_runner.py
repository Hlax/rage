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

from rge.modules.operator_loop import (
    inspect_arbitrary_source_proof_bundle_status,
    safe_verification_commands,
)
from rge.modules.researcher_product_proof import (
    inspect_researcher_product_proof_plan_status,
)
from rge.subprocess_capture import run_captured

_MOCK_ENV = {
    "RGE_LLM_MODE": "mock",
    "RGE_ALLOW_LIVE_LLM": "0",
    "RGE_TEST_LLM_MODE": "mock",
}


def mock_gate_operator_checklist(root: Path) -> list[dict[str, Any]]:
    """Optional operator commands surfaced by verify (not run automatically)."""
    proof_bundle_status = inspect_arbitrary_source_proof_bundle_status(root=root)
    product_proof_status = inspect_researcher_product_proof_plan_status(root=root)
    return [
        {
            "id": "prove_arbitrary_source_bundle",
            "command": proof_bundle_status["command"],
            "pipeline_mode": proof_bundle_status["pipeline_mode"],
            "shell": proof_bundle_status["operator_commands"]["proof_bundle"],
            "automated_in_verify": False,
            "notes": (
                "Optional mock arbitrary-source maturity proof on a temp or scratch "
                "database; inspect operator_proof_bundle.json after run."
            ),
        },
        {
            "id": "prove_researcher_product",
            "command": product_proof_status["command"],
            "shell": product_proof_status["operator_commands"]["product_proof"],
            "automated_in_verify": False,
            "notes": (
                "Optional mock end-to-end researcher product proof on a scratch work "
                "dir; inspect researcher_product_proof_latest.json after run."
            ),
        },
    ]


def run_verification(
    *,
    root: Path | None = None,
    skip_site: bool = False,
    command_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> dict[str, Any]:
    """Run mock-only verification commands and return a JSON-serializable report."""
    project_root = root or Path(__file__).resolve().parents[2]
    runner = command_runner or run_captured
    commands = safe_verification_commands(project_root)
    if skip_site:
        commands = [cmd for cmd in commands if cmd["name"] != "public_site_build"]

    results: list[dict[str, Any]] = []
    all_passed = True
    for command in commands:
        env = os.environ.copy()
        env.update(_MOCK_ENV)
        env.update(command.get("env", {}))
        print(
            f"[verify] running {command['name']}...",
            file=sys.stderr,
            flush=True,
        )
        completed = runner(
            command["argv"],
            cwd=command["cwd"],
            env=env,
        )
        passed = completed.returncode == 0
        all_passed = all_passed and passed
        print(
            f"[verify] {command['name']}: "
            f"{'ok' if passed else 'FAIL'} (exit {completed.returncode})",
            file=sys.stderr,
            flush=True,
        )
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
        "operator_checklist": mock_gate_operator_checklist(project_root),
        "arbitrary_source_proof_bundle_status": inspect_arbitrary_source_proof_bundle_status(
            root=project_root
        ),
        "researcher_product_proof_status": inspect_researcher_product_proof_plan_status(
            root=project_root
        ),
    }
