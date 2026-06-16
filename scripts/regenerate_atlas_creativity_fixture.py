"""Regenerate atlas creativity fixture (ticket-279/281)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from rge.cli import FIXTURE_RUN_ID, GOLDEN_MVP_TOPIC, execute_fixture_mode_run
from rge.db.connection import connect
from rge.modules.atlas_snapshot_builder import build_atlas_snapshot_from_db

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "fixtures" / "atlas" / "atlas_snapshot_v0_creativity_fixture.json"


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db_path = base / "atlas.sqlite"
        export_dir = base / "export"
        report_dir = base / "reports"
        ticket_dir = base / "tickets"
        for directory in (export_dir, report_dir, ticket_dir):
            directory.mkdir(parents=True)
        execute_fixture_mode_run(
            topic=GOLDEN_MVP_TOPIC,
            domain="creativity",
            db_path=db_path,
            run_id=FIXTURE_RUN_ID,
            report_dir=report_dir,
            ticket_dir=ticket_dir,
            export_dirs=[export_dir],
        )
        conn = connect(db_path)
        try:
            snapshot = build_atlas_snapshot_from_db(
                conn,
                topic=GOLDEN_MVP_TOPIC,
                domain_pack="creativity",
                fixture_mode=True,
                repo_root=REPO_ROOT,
            )
        finally:
            conn.close()
    FIXTURE_PATH.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {FIXTURE_PATH}")


if __name__ == "__main__":
    main()
