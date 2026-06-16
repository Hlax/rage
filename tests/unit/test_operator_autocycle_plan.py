"""Unit tests for operator autocycle plan runtime config surfacing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.config import DEFAULT_STAGED_RANK2_SCAN_MAX
from rge.modules.operator_autocycle import run_autocycle
from rge.modules.operator_loop import WorkingTreeStatus


def _seed_minimal_queue(tmp_path: Path) -> None:
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "agent_reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(
        """
| 40 | ticket-040 | done | prev | | |
| 41 | ticket-041 | proposed | Next | | |
""",
        encoding="utf-8",
    )
    (tmp_path / "tickets" / "ticket-041.json").write_text(
        json.dumps(
            {
                "id": "ticket-041",
                "title": "Next",
                "risk_level": "low",
                "status": "proposed",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "agent_reports" / "2026-06-16_principal-audit-post-ticket-254.md").write_text(
        "# audit",
        encoding="utf-8",
    )


def test_autocycle_plan_includes_default_staged_rank2_scan_max(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RGE_STAGED_RANK2_SCAN_MAX", raising=False)
    _seed_minimal_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    monkeypatch.setattr(
        "rge.modules.operator_autocycle.inspect_working_tree",
        lambda root=None: clean_tree,
    )

    payload = run_autocycle(mode="plan", max_cycles=1, root=tmp_path)

    assert payload["staged_rank2_scan_max"] == DEFAULT_STAGED_RANK2_SCAN_MAX
    assert payload["cycles"][0]["staged_rank2_scan_max"] == DEFAULT_STAGED_RANK2_SCAN_MAX


def test_autocycle_plan_honors_staged_rank2_scan_max_env_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_STAGED_RANK2_SCAN_MAX", "20")
    _seed_minimal_queue(tmp_path)
    clean_tree = WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])
    monkeypatch.setattr(
        "rge.modules.operator_autocycle.inspect_working_tree",
        lambda root=None: clean_tree,
    )

    payload = run_autocycle(mode="plan", max_cycles=1, root=tmp_path)

    assert payload["staged_rank2_scan_max"] == 20
    assert payload["cycles"][0]["staged_rank2_scan_max"] == 20
