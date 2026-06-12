"""Unit tests for export snapshot manifest and scratch history."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rge.modules.card_exporter import (
    DEFAULT_SNAPSHOT_RETENTION,
    SNAPSHOT_HISTORY_DIRNAME,
    SNAPSHOT_MANIFEST_FILENAME,
    export_public_cards,
    scratch_exports_dir,
    write_snapshot_history,
)


def _make_scratch_bundle(scratch_dir: Path) -> None:
    scratch_dir.mkdir(parents=True, exist_ok=True)
    cards = [
        {
            "id": "card_test_001",
            "type": "cluster_card",
            "title": "Test card",
            "summary": "Public-safe summary.",
            "confidence": "medium",
            "concepts": ["test"],
            "source_count": 1,
            "public_detail_level": "standard",
            "updated_at": "2026-06-12T12:00:00Z",
        }
    ]
    build_info = {
        "export_schema_version": "0.1.0",
        "generated_at": "2026-06-12T12:00:00Z",
        "phase": "1",
        "card_count": 1,
        "memo_count": 0,
    }
    (scratch_dir / "public_cards.json").write_text(
        json.dumps(cards, indent=2) + "\n", encoding="utf-8"
    )
    (scratch_dir / "public_memos.json").write_text("[]\n", encoding="utf-8")
    (scratch_dir / "build_info.json").write_text(
        json.dumps(build_info, indent=2) + "\n", encoding="utf-8"
    )


def test_write_snapshot_history_creates_manifest_and_bundle(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    scratch = scratch_exports_dir(repo)
    _make_scratch_bundle(scratch)

    entry = write_snapshot_history(
        scratch_dir=scratch,
        repo_root=repo,
        generated_at="2026-06-12T12:00:00Z",
        build_info={
            "export_schema_version": "0.1.0",
            "card_count": 1,
            "memo_count": 0,
        },
        fixture_mode=False,
        publish_public=False,
    )

    manifest_path = scratch / SNAPSHOT_MANIFEST_FILENAME
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(manifest) == 1
    assert manifest[0]["bundle_id"] == entry["bundle_id"]
    history_dir = scratch / SNAPSHOT_HISTORY_DIRNAME / entry["bundle_id"]
    assert (history_dir / "public_cards.json").is_file()
    assert (history_dir / "build_info.json").is_file()


def test_snapshot_history_retention_prunes_oldest(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    scratch = scratch_exports_dir(repo)
    retention = 2

    for hour in ("10", "11", "12"):
        _make_scratch_bundle(scratch)
        write_snapshot_history(
            scratch_dir=scratch,
            repo_root=repo,
            generated_at=f"2026-06-12T{hour}:00:00Z",
            build_info={
                "export_schema_version": "0.1.0",
                "card_count": 1,
                "memo_count": 0,
            },
            fixture_mode=False,
            publish_public=False,
            retention=retention,
        )

    manifest = json.loads(
        (scratch / SNAPSHOT_MANIFEST_FILENAME).read_text(encoding="utf-8")
    )
    assert len(manifest) == retention
    bundle_ids = {entry["bundle_id"] for entry in manifest}
    assert "2026-06-12T10-00-00Z" not in bundle_ids
    assert "2026-06-12T11-00-00Z" in bundle_ids
    assert "2026-06-12T12-00-00Z" in bundle_ids
    assert not (scratch / SNAPSHOT_HISTORY_DIRNAME / "2026-06-12T10-00-00Z").exists()


def test_export_public_skips_history_for_custom_output_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)
    from rge.db.connection import ensure_database
    from rge.db.repositories import PublicCardRepository

    db_path = tmp_path / "test.sqlite"
    export_dir = tmp_path / "custom_export"
    conn = ensure_database(db_path)
    try:
        PublicCardRepository(conn).insert(
            card_id="card_hist_skip",
            card_type="cluster_card",
            title="History skip",
            summary="No history for custom output dir.",
            confidence="low",
            concepts=["test"],
            source_count=1,
            claim_ids=[],
            public_detail_level="standard",
            is_public_safe=True,
        )
        result = export_public_cards(
            conn,
            output_dirs=[export_dir],
            repo_root=tmp_path,
            snapshot_history=True,
        )
    finally:
        conn.close()

    assert result["snapshot_history"] is False
    assert not (export_dir / SNAPSHOT_MANIFEST_FILENAME).exists()


def test_export_public_writes_history_to_scratch_exports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)
    from rge.db.connection import ensure_database
    from rge.db.repositories import PublicCardRepository

    repo = tmp_path / "repo"
    db_path = repo / "data" / "db" / "test.sqlite"
    conn = ensure_database(db_path)
    try:
        PublicCardRepository(conn).insert(
            card_id="card_hist_keep",
            card_type="cluster_card",
            title="History keep",
            summary="Scratch history should be retained.",
            confidence="low",
            concepts=["test"],
            source_count=1,
            claim_ids=[],
            public_detail_level="standard",
            is_public_safe=True,
        )
        result = export_public_cards(
            conn,
            repo_root=repo,
            snapshot_history=True,
            snapshot_retention=DEFAULT_SNAPSHOT_RETENTION,
        )
    finally:
        conn.close()

    scratch = scratch_exports_dir(repo)
    assert result["snapshot_history"] is True
    assert (scratch / SNAPSHOT_MANIFEST_FILENAME).is_file()
    assert (scratch / SNAPSHOT_HISTORY_DIRNAME).is_dir()


def test_cli_no_snapshot_history_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "mock")
    monkeypatch.delenv("RGE_ALLOW_LIVE_LLM", raising=False)
    import rge.modules.card_exporter as card_exporter_module
    from rge.cli import main
    from rge.db.connection import ensure_database
    from rge.db.repositories import PublicCardRepository

    repo = tmp_path / "repo"
    monkeypatch.setattr(card_exporter_module, "_repo_root", lambda: repo)
    db_path = repo / "data" / "db" / "test.sqlite"
    conn = ensure_database(db_path)
    try:
        PublicCardRepository(conn).insert(
            card_id="card_no_hist",
            card_type="cluster_card",
            title="No history",
            summary="CLI opt-out test.",
            confidence="low",
            concepts=["test"],
            source_count=1,
            claim_ids=[],
            public_detail_level="standard",
            is_public_safe=True,
        )
    finally:
        conn.close()

    assert (
        main(
            [
                "export-public",
                "--db",
                str(db_path),
                "--no-snapshot-history",
            ]
        )
        == 0
    )
    scratch = scratch_exports_dir(repo)
    assert (scratch / "public_cards.json").is_file()
    assert not (scratch / SNAPSHOT_MANIFEST_FILENAME).exists()
