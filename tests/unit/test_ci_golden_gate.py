"""Unit tests for CI golden gate and principal audit command evidence."""

from __future__ import annotations

import subprocess
import sys
import tempfile
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
    assert "tests/smoke/" in text
    assert "grep -q live_smoke" not in text
    assert "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24" in text


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
    assert "live_network" in text
    assert "not live_network" in text


def test_default_pytest_deselects_live_smoke() -> None:
    # Redirect nested pytest output to temp files instead of capture_output=True.
    # On Windows, capture_output inside an active pytest session can raise WinError 6
    # when duplicating inherited handles.
    with tempfile.TemporaryDirectory() as tmpdir:
        stdout_path = Path(tmpdir) / "stdout.txt"
        stderr_path = Path(tmpdir) / "stderr.txt"
        with stdout_path.open("w", encoding="utf-8") as stdout_f, stderr_path.open(
            "w", encoding="utf-8"
        ) as stderr_f:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", "-q"],
                cwd=REPO_ROOT,
                stdin=subprocess.DEVNULL,
                stdout=stdout_f,
                stderr=stderr_f,
                check=False,
            )
        combined = stdout_path.read_text(encoding="utf-8") + stderr_path.read_text(
            encoding="utf-8"
        )
    assert result.returncode == pytest.ExitCode.OK
    assert "tests/smoke/" not in combined
    assert (
        "test_live_openalex_discover_and_fetch_writes_staged_artifact" not in combined
    )
    assert (
        "test_live_openalex_discover_fetch_ingest_writes_source_and_chunks"
        not in combined
    )
    assert (
        "test_live_openalex_discover_fetch_ingest_extract_mock_fixture"
        not in combined
    )
    assert (
        "test_live_openalex_discover_through_link_mock_fixture"
        not in combined
    )
    assert (
        "test_live_openalex_discover_through_build_mock_fixture"
        not in combined
    )
    assert (
        "test_live_openalex_discover_through_detect_mock_fixture"
        not in combined
    )
    assert (
        "test_live_openalex_discover_through_reconcile_mock_spine"
        not in combined
    )
