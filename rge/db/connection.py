"""SQLite connection helpers and migration harness."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("data") / "db" / "creative_research.sqlite"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
_MIGRATION_FILE_PATTERN = re.compile(r"^(\d{4})_.+\.sql$")


def get_db_path(db_path: Path | None = None) -> Path:
    """Resolve the local private SQLite database path."""
    return db_path if db_path is not None else DEFAULT_DB_PATH


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with foreign keys enabled."""
    path = get_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def read_schema_sql() -> str:
    """Return the schema reference SQL text."""
    return SCHEMA_PATH.read_text(encoding="utf-8")


def _list_migration_files() -> list[Path]:
    if not MIGRATIONS_DIR.is_dir():
        return []
    files = [
        path
        for path in MIGRATIONS_DIR.iterdir()
        if path.is_file() and _MIGRATION_FILE_PATTERN.match(path.name)
    ]
    return sorted(files, key=lambda path: path.name)


def _ensure_schema_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )


def _applied_migration_versions(conn: sqlite3.Connection) -> set[str]:
    _ensure_schema_migrations_table(conn)
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row[0] for row in rows}


def apply_migrations(conn: sqlite3.Connection) -> list[str]:
    """Apply pending versioned SQL migrations. Returns newly applied versions."""
    applied_now: list[str] = []
    already_applied = _applied_migration_versions(conn)

    for migration_path in _list_migration_files():
        version = migration_path.stem
        if version in already_applied:
            continue
        sql = migration_path.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (?, datetime('now'))",
            (version,),
        )
        applied_now.append(version)

    conn.commit()
    return applied_now


def ensure_database(db_path: Path | None = None) -> sqlite3.Connection:
    """Open the database and apply any pending migrations."""
    conn = connect(db_path)
    apply_migrations(conn)
    return conn
