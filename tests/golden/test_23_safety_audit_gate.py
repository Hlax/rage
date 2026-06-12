"""Golden Test 23: safety audit blocks dangerous or leaky changes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.modules.safety_auditor import (
    run_safety_audit,
    scan_model_module_for_violations,
    scan_public_site_source_for_violations,
)

REQUIRED_AUDIT_FIELDS = (
    "status",
    "blocked_reasons",
    "checked_routes",
    "checked_exports",
    "checked_secrets",
)


def test_full_audit_returns_machine_readable_json_with_required_fields() -> None:
    report = run_safety_audit("full")
    assert report["report_type"] == "safety_audit_report"
    assert report["audit_type"] == "full"
    for field in REQUIRED_AUDIT_FIELDS:
        assert field in report
        assert isinstance(report[field], (str, list))
    assert report["status"] in {"pass", "fail"}
    assert isinstance(report["blocked_reasons"], list)
    assert isinstance(report["checked_routes"], list)
    assert isinstance(report["checked_exports"], list)
    assert isinstance(report["checked_secrets"], list)
    assert report["created_at"]


def test_full_audit_passes_on_clean_repo() -> None:
    report = run_safety_audit("full")
    assert report["status"] == "pass", report["blocked_reasons"]
    assert report["blocked_reasons"] == []


def test_audit_fails_closed_on_forbidden_public_write_route_pattern() -> None:
    violations = scan_public_site_source_for_violations(
        "export async function POST() { return Response.json({ ok: true }); }",
        "apps/public-site/app/api/ingest/route.ts",
    )
    assert violations
    assert any("forbidden public route pattern" in item for item in violations)


def test_audit_fails_closed_on_model_shell_execution_pattern() -> None:
    violations = scan_model_module_for_violations(
        "import subprocess\nsubprocess.run(['git', 'push'], shell=True)",
        "rge/llm/evil_client.py",
    )
    assert violations
    assert any("forbidden model tool pattern" in item for item in violations)


def test_safety_auditor_cli_emits_json_not_prose(capsys: pytest.CaptureFixture[str]) -> None:
    from rge.modules.safety_auditor import main

    exit_code = main(["--audit", "full"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "pass"
    for field in REQUIRED_AUDIT_FIELDS:
        assert field in payload
    assert "detail" not in payload
