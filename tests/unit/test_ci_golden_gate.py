"""Unit tests for CI golden gate and principal audit command evidence."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_golden_gate_workflow_exists_with_mock_only_steps() -> None:
    workflow = REPO_ROOT / ".github" / "workflows" / "golden-gate.yml"
    assert workflow.is_file()
    text = workflow.read_text(encoding="utf-8")
    assert "RGE_LLM_MODE: mock" in text
    assert "RGE_ALLOW_LIVE_LLM" in text
    assert "pytest tests/golden" in text
    assert "rge.modules.safety_auditor" in text
    assert "npm run build" in text
    assert "pytest -m live_smoke" not in text
    assert "RGE_LLM_MODE=ollama" not in text
    assert "live_smoke" in text


def test_principal_audit_command_doc_exists() -> None:
    doc = REPO_ROOT / ".cursor" / "commands" / "rge-principal-audit.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "principal audit checkpoint status" in text.lower() or "checkpoint status" in text.lower()
    assert "overdue" in text
    assert "satisfied" in text
    assert "golden-gate.yml" in text
    assert "principal_audit_gate" in text


def test_pyproject_excludes_live_smoke_by_default() -> None:
    pyproject = REPO_ROOT / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    assert "live_smoke" in text
    assert "not live_smoke" in text


def test_default_pytest_deselects_live_smoke() -> None:
    exit_code = pytest.main(["--collect-only", "-q"])
    assert exit_code == pytest.ExitCode.OK
