"""Shared operator-loop plan test fixtures (neutral autonomous-loop state)."""

from __future__ import annotations

from pathlib import Path

from rge.modules.operator_loop import WorkingTreeStatus


def seed_public_site_preview_paths(tmp_path: Path, *, include_source_health: bool = True) -> None:
    site = tmp_path / "apps" / "public-site"
    public_data = site / "public" / "data"
    public_data.mkdir(parents=True)
    (site / "package.json").write_text("{}", encoding="utf-8")
    (public_data / "atlas_snapshot_preview.json").write_text("{}", encoding="utf-8")
    (public_data / "atlas_coherence_preview.json").write_text("{}", encoding="utf-8")
    if include_source_health:
        (public_data / "atlas_source_health_run_latest.json").write_text(
            "{}", encoding="utf-8"
        )
    scripts = tmp_path / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "refresh_atlas_preview_from_staged_spine.py").write_text(
        "# refresh staged spine preview\n",
        encoding="utf-8",
    )
    (scripts / "refresh_atlas_source_health_preview.py").write_text(
        "# refresh source health preview\n",
        encoding="utf-8",
    )


def seed_operator_neutral_plan_state(
    tmp_path: Path,
    *,
    queue_markdown: str = "| 40 | ticket-040 | done | prev | | |\n",
    agent_report_name: str = "2026-06-12_pre-phase-2_principal-audit.md",
) -> WorkingTreeStatus:
    """Seed tmp repo root so plan mode reaches autonomous researcher loop."""
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "agent_reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "TICKET_QUEUE.md").write_text(queue_markdown, encoding="utf-8")
    (tmp_path / "agent_reports" / agent_report_name).write_text("# audit", encoding="utf-8")
    seed_public_site_preview_paths(tmp_path, include_source_health=True)
    return WorkingTreeStatus(clean=True, branch="main", dirty_paths=[])


def apply_live_smoke_env_gates(monkeypatch) -> None:
    """Prevent live combined smoke from preempting autonomous-loop plan tests."""
    monkeypatch.setenv("RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_LIVE_QUERY_EXPANSION_SMOKE", "1")
    monkeypatch.setenv("RGE_ALLOW_SOURCE_NETWORK", "1")
    monkeypatch.setenv("OPENALEX_MAILTO", "operator@example.com")
