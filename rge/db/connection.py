"""SQLite connection helpers.

Phase 0: path resolution and a connect helper only. No migration harness yet
(that is a later ticket). Nothing in Phase 0 opens a database at import time.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("data") / "db" / "creative_research.sqlite"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_db_path(db_path: Path | None = None) -> Path:
    """Resolve the local private SQLite database path."""
    return db_path if db_path is not None else DEFAULT_DB_PATH


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with foreign keys enabled.

    Callers own the connection lifecycle. Phase 0 code does not call this;
    it exists so later tickets have a single connection boundary.
    """
    path = get_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def read_schema_sql() -> str:
    """Return the schema placeholder SQL text."""
    return SCHEMA_PATH.read_text(encoding="utf-8")
