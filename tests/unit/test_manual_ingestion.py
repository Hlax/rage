"""Unit tests for real manual source ingestion (ticket-086)."""

from __future__ import annotations

import inspect
import json
import sqlite3
from pathlib import Path

import pytest

from rge.modules.card_exporter import GOLDEN_PRIVATE_FIELDS

REPO_ROOT = Path(__file__).resolve().parents[2]
MANUAL_SOURCE_DIR = REPO_ROOT / "data" / "sources" / "manual" / "creativity"


@pytest.fixture()
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "manual_ingestion.sqlite"


@pytest.fixture()
def manual_md_source(tmp_path: Path) -> Path:
    path = tmp_path / "operator_note.md"
    path.write_text(
        "# Creativity note\n\n"
        "Manual ingestion test: AI may improve output volume while reducing diversity.\n",
        encoding="utf-8",
    )
    return path


def _ingest(
    source_path: Path,
    temp_db: Path,
    *,
    source_type: str = "manual_text",
    source_title: str | None = None,
    extra_args: list[str] | None = None,
) -> dict:
    from rge.cli import main

    args = [
        "ingest",
        str(source_path),
        "--domain",
        "creativity",
        "--source-type",
        source_type,
        "--db",
        str(temp_db),
    ]
    if source_title is not None:
        args.extend(["--source-title", source_title])
    if extra_args:
        args.extend(extra_args)
    assert main(args) == 0
    return args


def _ingest_json(
    source_path: Path,
    temp_db: Path,
    capsys: pytest.CaptureFixture[str],
    **kwargs,
) -> dict:
    _ingest(source_path, temp_db, **kwargs)
    captured = capsys.readouterr()
    return json.loads(captured.out)


def test_manual_md_ingest_persists_manual_text_source_type(
    temp_db: Path, manual_md_source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = _ingest_json(
        manual_md_source,
        temp_db,
        capsys,
        source_title="Operator creativity note",
    )
    assert payload["status"] == "ingested"
    assert payload["source"]["source_type"] == "manual_text"
    assert payload["source"]["title"] == "Operator creativity note"
    assert payload["source"]["domain"] == "creativity"
    assert payload["source"]["status"] == "ingested"
    assert payload["chunk_count"] >= 1
    assert "local_path" not in payload["source"]

    conn = sqlite3.connect(temp_db)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM sources").fetchone()
        assert row is not None
        assert row["source_type"] == "manual_text"
        assert row["title"] == "Operator creativity note"
        assert row["raw_text_checksum"]
        assert row["local_path"]
    finally:
        conn.close()


def test_ingest_without_source_type_defaults_to_fixture(
    temp_db: Path, manual_md_source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from rge.cli import main

    assert (
        main(
            [
                "ingest",
                str(manual_md_source),
                "--domain",
                "creativity",
                "--db",
                str(temp_db),
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["source"]["source_type"] == "fixture"


def test_reingest_is_idempotent_with_stable_chunk_ids(
    temp_db: Path, manual_md_source: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    first = _ingest_json(manual_md_source, temp_db, capsys)
    second = _ingest_json(manual_md_source, temp_db, capsys)

    assert first["status"] == "ingested"
    assert second["status"] == "already_ingested"
    assert first["chunk_ids"] == second["chunk_ids"]

    conn = sqlite3.connect(temp_db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == 1
    finally:
        conn.close()


def test_ingest_writes_no_claims_concepts_or_relationships(
    temp_db: Path, manual_md_source: Path
) -> None:
    _ingest(manual_md_source, temp_db)

    conn = sqlite3.connect(temp_db)
    try:
        for table in ("claims", "concepts", "relationships"):
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            assert count == 0, f"expected no rows in {table}"
    finally:
        conn.close()


def test_ingest_unchanged_regardless_of_llm_mode(
    temp_db: Path,
    manual_md_source: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RGE_LLM_MODE", "ollama")
    monkeypatch.setenv("RGE_ALLOW_LIVE_LLM", "1")
    _ingest(manual_md_source, temp_db)

    conn = sqlite3.connect(temp_db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 0
        source = conn.execute("SELECT source_type FROM sources").fetchone()
        assert source is not None
        assert source[0] == "manual_text"
    finally:
        conn.close()


def test_source_record_to_public_dict_omits_private_fields(
    temp_db: Path, manual_md_source: Path
) -> None:
    from rge.db.connection import connect
    from rge.db.repositories import SourceRepository, source_record_to_public_dict

    _ingest(manual_md_source, temp_db, source_title="Public-safe title")

    conn = connect(temp_db)
    try:
        rows = conn.execute("SELECT id FROM sources").fetchall()
        assert len(rows) == 1
        source = SourceRepository(conn).get_by_id(rows[0][0])
        assert source is not None
        public = source_record_to_public_dict(source)
        assert "local_path" not in public
        assert "raw_text" not in public
        assert "chunk_text" not in public
        assert public["title"] == "Public-safe title"
    finally:
        conn.close()


def test_local_path_remains_golden_private_field() -> None:
    assert "local_path" in GOLDEN_PRIVATE_FIELDS


def test_ingest_path_imports_no_llm_client() -> None:
    import rge.cli as cli_module

    source = inspect.getsource(cli_module._cmd_ingest)
    assert "llm" not in source.lower()
    assert "ollama" not in source.lower()
    assert "openai" not in source.lower()


def test_manual_source_directory_is_under_gitignored_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Operator convention: data/sources/manual/<domain>/ lives under gitignored data/."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".gitignore").write_text("data/\n", encoding="utf-8")
    manual_dir = repo / "data" / "sources" / "manual" / "creativity"
    manual_dir.mkdir(parents=True)
    sample = manual_dir / "note.md"
    sample.write_text("Private operator source.\n", encoding="utf-8")

    db_path = repo / "data" / "db" / "test.sqlite"
    db_path.parent.mkdir(parents=True)
    _ingest(sample, db_path)

    gitignore = (repo / ".gitignore").read_text(encoding="utf-8")
    assert "data/" in gitignore
    assert sample.is_file()


def test_ingest_does_not_write_export_artifacts(
    temp_db: Path, manual_md_source: Path, tmp_path: Path
) -> None:
    exports_dir = tmp_path / "data" / "exports"
    public_dir = tmp_path / "apps" / "public-site" / "public" / "data"
    exports_dir.mkdir(parents=True)
    public_dir.mkdir(parents=True)

    _ingest(manual_md_source, temp_db)

    assert list(exports_dir.iterdir()) == []
    assert list(public_dir.iterdir()) == []
