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


def _write_clean_scratch_export(exports_dir: Path) -> None:
    exports_dir.mkdir(parents=True, exist_ok=True)
    cards = [
        {
            "id": "card_scratch_001",
            "type": "cluster_card",
            "title": "Scratch export card",
            "summary": "Public-safe scratch export for safety audit coverage.",
            "confidence": "medium",
            "concepts": ["semantic diversity"],
            "source_count": 1,
            "public_detail_level": "standard",
            "updated_at": "2026-06-12T00:00:00Z",
        }
    ]
    build_info = {
        "export_schema_version": "0.1.0",
        "generated_at": "2026-06-12T00:00:00Z",
        "phase": "1",
        "card_count": 1,
        "memo_count": 0,
    }
    (exports_dir / "public_cards.json").write_text(
        json.dumps(cards, indent=2) + "\n", encoding="utf-8"
    )
    (exports_dir / "public_memos.json").write_text("[]\n", encoding="utf-8")
    (exports_dir / "build_info.json").write_text(
        json.dumps(build_info, indent=2) + "\n", encoding="utf-8"
    )


def test_data_exports_audit_skipped_when_directory_missing(tmp_path: Path) -> None:
    report = run_safety_audit("public_export", root=tmp_path)
    assert report["status"] == "fail"
    assert any("missing public export file" in item for item in report["blocked_reasons"])
    assert report["checked_exports"] == []


def test_data_exports_audit_passes_on_clean_scratch_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    public_data = repo_root / "apps" / "public-site" / "public" / "data"
    site_data = tmp_path / "apps" / "public-site" / "public" / "data"
    site_data.mkdir(parents=True)
    for name in ("public_cards.json", "public_memos.json", "build_info.json"):
        (site_data / name).write_text(
            (public_data / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    _write_clean_scratch_export(tmp_path / "data" / "exports")

    report = run_safety_audit("public_export", root=tmp_path)
    assert report["status"] == "pass", report["blocked_reasons"]
    assert "data\\exports\\public_cards.json" in report["checked_exports"] or (
        "data/exports/public_cards.json" in report["checked_exports"]
    )


def test_data_exports_audit_passes_on_history_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    public_data = repo_root / "apps" / "public-site" / "public" / "data"
    site_data = tmp_path / "apps" / "public-site" / "public" / "data"
    site_data.mkdir(parents=True)
    for name in ("public_cards.json", "public_memos.json", "build_info.json"):
        (site_data / name).write_text(
            (public_data / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    exports_dir = tmp_path / "data" / "exports"
    _write_clean_scratch_export(exports_dir)
    history_bundle = exports_dir / "history" / "2026-06-12T00-00-00Z"
    history_bundle.mkdir(parents=True)
    for name in ("public_cards.json", "public_memos.json", "build_info.json"):
        (history_bundle / name).write_text(
            (exports_dir / name).read_text(encoding="utf-8"), encoding="utf-8"
        )

    report = run_safety_audit("public_export", root=tmp_path)
    assert report["status"] == "pass", report["blocked_reasons"]
    checked = report["checked_exports"]
    assert any("history" in item for item in checked)


def test_data_exports_audit_fails_closed_on_leaky_scratch_export(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    public_data = repo_root / "apps" / "public-site" / "public" / "data"
    site_data = tmp_path / "apps" / "public-site" / "public" / "data"
    site_data.mkdir(parents=True)
    for name in ("public_cards.json", "public_memos.json", "build_info.json"):
        (site_data / name).write_text(
            (public_data / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    exports_dir = tmp_path / "data" / "exports"
    _write_clean_scratch_export(exports_dir)
    cards_path = exports_dir / "public_cards.json"
    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    cards[0]["summary"] = "Leaked path C:\\Users\\private\\notes.txt in export."
    cards_path.write_text(json.dumps(cards, indent=2) + "\n", encoding="utf-8")

    report = run_safety_audit("public_export", root=tmp_path)
    assert report["status"] == "fail"
    assert any("data/exports" in item or "data\\exports" in item for item in report["blocked_reasons"])
