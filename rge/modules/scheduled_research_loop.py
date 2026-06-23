"""Local-safe scheduled research loop for Windows Task Scheduler.

Default profile ``local_mock_daily`` runs mock-only research, safety audit,
and compact status JSON. Live network, live LLM, paid APIs, merge, push,
ticket promotion, and public publish are blocked.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rge.modules.one_button_research_run import (
    DEFAULT_ARTIFACT_DIR_REL,
    DEFAULT_DB_REL,
    execute_one_button_research_run,
)
from rge.modules.principal_audit_gate import repo_root

SCHEMA_VERSION = "scheduled_research_loop_v0.1.0"
DEFAULT_TOPIC = "Does AI improve creative output while reducing diversity?"

PROFILES: dict[str, dict[str, Any]] = {
    "local_mock_daily": {
        "llm_mode": "mock",
        "live_network": False,
        "live_llm": False,
        "paid_apis": False,
        "export_atlas": True,
        "run_safety_audit": True,
        "run_one_button_research": True,
        "sync_atlas_public": False,
        "skip_site_build": True,
    },
}


class ScheduledResearchLoopBlockedError(RuntimeError):
    """Raised when scheduled mode detects forbidden operator actions."""


def _truthy(name: str) -> bool:
    return os.environ.get(name, "0").strip().casefold() in {"1", "true", "yes"}


def assert_scheduled_mock_profile(*, profile: str) -> dict[str, str]:
    """Enforce mock-only scheduled profile gates."""
    if profile not in PROFILES:
        raise ScheduledResearchLoopBlockedError(
            f"Unknown scheduled profile: {profile}. "
            f"Available: {', '.join(sorted(PROFILES))}"
        )
    spec = PROFILES[profile]
    if spec.get("llm_mode") != "mock":
        raise ScheduledResearchLoopBlockedError(
            "Scheduled mode only supports mock LLM profiles."
        )

    os.environ["RGE_LLM_MODE"] = "mock"
    enforced = {"RGE_LLM_MODE": "mock", "profile": profile}

    blocked_env = {
        "RGE_ALLOW_SOURCE_NETWORK": "live network",
        "RGE_ALLOW_LIVE_LLM": "live LLM",
        "RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR": "live staged orchestrator",
        "RGE_ALLOW_OPENAI": "paid OpenAI API",
        "RGE_ALLOW_CLOUD_LLM": "cloud LLM",
    }
    active_blocks = [
        f"{name} ({label})"
        for name, label in blocked_env.items()
        if _truthy(name)
    ]
    if active_blocks:
        raise ScheduledResearchLoopBlockedError(
            "Scheduled mock profile refuses active live/paid gates: "
            + ", ".join(active_blocks)
        )

    forbidden_actions = {
        "RGE_SCHEDULED_ALLOW_MERGE": "merge",
        "RGE_SCHEDULED_ALLOW_PUSH": "push",
        "RGE_SCHEDULED_ALLOW_PROMOTE": "ticket promotion",
        "RGE_SCHEDULED_ALLOW_PUBLIC_PUBLISH": "public publish",
    }
    for name, label in forbidden_actions.items():
        if _truthy(name):
            raise ScheduledResearchLoopBlockedError(
                f"Scheduled mode blocks {label} even when {name} is set."
            )
    return enforced


def run_safety_audit(*, root: Path) -> dict[str, Any]:
    """Run full safety audit subprocess."""
    # On Windows, nested capture_output=True inside pytest can fail while
    # duplicating inherited handles. File-backed capture keeps the gate strict.
    with tempfile.TemporaryDirectory() as tmpdir:
        stdout_path = Path(tmpdir) / "stdout.txt"
        stderr_path = Path(tmpdir) / "stderr.txt"
        with stdout_path.open("w", encoding="utf-8") as stdout_f, stderr_path.open(
            "w", encoding="utf-8"
        ) as stderr_f:
            result = subprocess.run(
                [sys.executable, "-m", "rge.modules.safety_auditor", "--audit", "full"],
                cwd=root,
                stdin=subprocess.DEVNULL,
                stdout=stdout_f,
                stderr=stderr_f,
                check=False,
            )
        stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
        stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
    return {
        "exit_code": result.returncode,
        "passed": result.returncode == 0,
        "stdout_tail": stdout[-2000:],
        "stderr_tail": stderr[-1000:],
    }


def write_scheduled_reports(
    *,
    payload: dict[str, Any],
    root: Path,
    report_dir: Path,
) -> dict[str, str]:
    """Write timestamped markdown + latest JSON under agent_reports/."""
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = "scheduled-research-loop"
    agent_reports = root / "agent_reports"
    agent_reports.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    json_latest = agent_reports / f"{stamp}_{slug}-latest.json"
    json_latest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    md_path = agent_reports / f"{stamp}_{slug}.md"
    lines = [
        f"# Scheduled Research Loop — {stamp}",
        "",
        f"- **Profile:** `{payload.get('profile')}`",
        f"- **Overall verdict:** {payload.get('overall_verdict')}",
        f"- **LLM mode:** {payload.get('llm_mode')}",
        "",
        "## Steps",
        "",
    ]
    for step, status in (payload.get("step_status") or {}).items():
        lines.append(f"- {step}: **{status}**")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            f"- Safety audit: **{'PASS' if payload.get('safety_audit_passed') else 'FAIL'}**",
            f"- Live network blocked: **{payload.get('live_network_blocked')}**",
            f"- Live LLM blocked: **{payload.get('live_llm_blocked')}**",
            "",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    status_json = report_dir / "scheduled_status_latest.json"
    status_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    return {
        "markdown": str(md_path),
        "json_latest": str(json_latest),
        "status_json": str(status_json),
    }


def execute_scheduled_research_loop(
    *,
    profile: str = "local_mock_daily",
    topic: str = DEFAULT_TOPIC,
    domain: str = "creativity",
    root: Path | None = None,
    report_dir: Path | None = None,
    refresh_atlas: bool = True,
) -> dict[str, Any]:
    """Execute local-safe scheduled research loop."""
    project_root = root or repo_root()
    audit_root = repo_root()
    resolved_report_dir = report_dir or (
        project_root / "data/reports/scheduled_research"
    )
    if not resolved_report_dir.is_absolute():
        resolved_report_dir = project_root / resolved_report_dir

    enforced = assert_scheduled_mock_profile(profile=profile)
    spec = PROFILES[profile]
    step_status: dict[str, str] = {}
    research_result: dict[str, Any] | None = None
    safety_result: dict[str, Any] | None = None

    if spec.get("run_one_button_research"):
        db_path = project_root / DEFAULT_DB_REL
        artifact_dir = project_root / DEFAULT_ARTIFACT_DIR_REL
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_artifact = resolved_report_dir / stamp
        research_result = execute_one_button_research_run(
            topic=topic,
            domain=domain,
            db_path=db_path,
            artifact_dir=run_artifact,
            export_atlas=refresh_atlas and bool(spec.get("export_atlas")),
            live_network=False,
            live_llm_extract=False,
            sync_atlas_public=False,
            root=project_root,
        )
        step_status["one_button_research_run"] = research_result.get("status", "failed")

    if spec.get("run_safety_audit"):
        safety_result = run_safety_audit(root=audit_root)
        step_status["safety_audit"] = "completed" if safety_result["passed"] else "failed"

    research_ok = (research_result or {}).get("status") == "completed"
    safety_ok = (safety_result or {}).get("passed", True)
    overall = "GO" if research_ok and safety_ok else "PARTIAL" if research_ok else "NO-GO"

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "profile": profile,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_verdict": overall,
        "llm_mode": enforced.get("RGE_LLM_MODE", "mock"),
        "topic": topic,
        "domain": domain,
        "live_network_blocked": True,
        "live_llm_blocked": True,
        "paid_apis_blocked": True,
        "no_merge": True,
        "no_push": True,
        "no_ticket_promotion": True,
        "no_public_publish": True,
        "step_status": step_status,
        "research_result_summary": {
            "status": (research_result or {}).get("status"),
            "research_quality_verdict": (research_result or {}).get(
                "research_quality_verdict"
            ),
            "artifact_dir": (research_result or {}).get("artifact_dir"),
        },
        "safety_audit_passed": safety_ok,
        "safety_audit_exit_code": (safety_result or {}).get("exit_code"),
        "next_recommended_packet": {
            "id": "live-ollama-abstract-extract-gate",
            "title": "Live Ollama Abstract Extract Gate (operator opt-in)",
        },
    }
    paths = write_scheduled_reports(
        payload=payload,
        root=project_root,
        report_dir=resolved_report_dir,
    )
    payload["report_paths"] = paths
    return payload
