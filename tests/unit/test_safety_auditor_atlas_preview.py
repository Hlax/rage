"""Safety auditor coverage for atlas preview public data (ticket-302)."""

from __future__ import annotations

import json
from pathlib import Path

from rge.modules.safety_auditor import (
    ATLAS_PREVIEW_PUBLIC_DATA_FILES,
    run_safety_audit,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DATA = REPO_ROOT / "apps" / "public-site" / "public" / "data"


def _copy_public_site_data(site_data: Path) -> None:
    site_data.mkdir(parents=True)
    for name in (
        "public_cards.json",
        "public_memos.json",
        "build_info.json",
        *ATLAS_PREVIEW_PUBLIC_DATA_FILES,
    ):
        (site_data / name).write_text(
            (PUBLIC_DATA / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )


def test_secrets_audit_scans_atlas_preview_public_data_files() -> None:
    report = run_safety_audit("secrets")
    assert report["status"] == "pass", report["blocked_reasons"]
    checked = report["checked_secrets"]
    for name in ATLAS_PREVIEW_PUBLIC_DATA_FILES:
        assert any(name in item for item in checked), (
            f"secrets audit must scan {name}"
        )


def test_full_audit_includes_atlas_preview_in_checked_secrets() -> None:
    report = run_safety_audit("full")
    assert report["status"] == "pass", report["blocked_reasons"]
    checked = report["checked_secrets"]
    assert any("atlas_snapshot_preview.json" in item for item in checked)
    assert any("atlas_coherence_preview.json" in item for item in checked)


def test_atlas_preview_audit_fails_closed_on_forbidden_path(tmp_path: Path) -> None:
    site_data = tmp_path / "apps" / "public-site" / "public" / "data"
    _copy_public_site_data(site_data)
    snapshot_path = site_data / "atlas_snapshot_preview.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    snapshot["root"]["topic"] = "Leaked path C:\\Users\\private\\atlas.sqlite"
    snapshot_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")

    report = run_safety_audit("secrets", root=tmp_path)
    assert report["status"] == "fail"
    assert any("atlas_snapshot_preview.json" in item for item in report["blocked_reasons"])


def test_atlas_preview_audit_fails_closed_on_secret_like_content(tmp_path: Path) -> None:
    site_data = tmp_path / "apps" / "public-site" / "public" / "data"
    _copy_public_site_data(site_data)
    coherence_path = site_data / "atlas_coherence_preview.json"
    coherence = json.loads(coherence_path.read_text(encoding="utf-8"))
    coherence["preview_label"] = "sk-abcdefghijklmnopqrstuvwxyz123456"
    coherence_path.write_text(json.dumps(coherence, indent=2) + "\n", encoding="utf-8")

    report = run_safety_audit("secrets", root=tmp_path)
    assert report["status"] == "fail"
    assert any("atlas_coherence_preview.json" in item for item in report["blocked_reasons"])
