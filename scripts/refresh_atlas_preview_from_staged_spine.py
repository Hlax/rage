"""Regenerate public-site atlas preview JSON from mock staged-spine export (ticket-320).

Operator-only helper; uses temp DB. Requires mock LLM and patched network when run standalone.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from rge.cli import STAGED_FIXTURE_QUESTION_ID, STAGED_FIXTURE_RUN_ID, main as cli_main
from rge.db.connection import connect
from rge.modules.atlas_preview_curator import (
    STAGED_PREVIEW_TOPIC,
    export_staged_spine_preview_to_paths,
)
from tests.unit.test_staged_fixture_mode_run_spine import (
    OPENALEX_FIXTURE,
    RANK1_HTML,
    RANK2_HTML,
    STAGED_TOPIC,
    _staged_network_urlopen,
)

PUBLIC_DATA = REPO_ROOT / "apps" / "public-site" / "public" / "data"


def main() -> None:
    os.environ["RGE_LLM_MODE"] = "mock"
    os.environ["RGE_ALLOW_SOURCE_NETWORK"] = "1"
    os.environ.setdefault("OPENALEX_MAILTO", "operator@example.com")

    fixture_payload = json.loads(OPENALEX_FIXTURE.read_text(encoding="utf-8"))
    urlopen = _staged_network_urlopen(fixture_payload, [RANK1_HTML, RANK2_HTML])

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        db = td_path / "staged_preview.sqlite"
        staging = td_path / "staged"
        staging.mkdir()
        reports = td_path / "reports"
        reports.mkdir()

        with patch(
            "rge.modules.source_providers.openalex.urllib.request.urlopen",
            urlopen,
        ), patch("rge.modules.fetcher.urllib.request.urlopen", urlopen):
            exit_code = cli_main(
                [
                    "run",
                    "--fixture-mode",
                    "--staged-spine",
                    "--topic",
                    STAGED_TOPIC,
                    "--domain",
                    "creativity",
                    "--db",
                    str(db),
                    "--staging-dir",
                    str(staging),
                    "--output-dir",
                    str(reports),
                    "--run-id",
                    STAGED_FIXTURE_RUN_ID,
                    "--question-id",
                    STAGED_FIXTURE_QUESTION_ID,
                ]
            )
            if exit_code != 0:
                raise SystemExit(f"staged orchestrator failed with exit {exit_code}")

        conn = connect(db)
        try:
            result = export_staged_spine_preview_to_paths(
                conn,
                snapshot_path=PUBLIC_DATA / "atlas_snapshot_preview.json",
                coherence_path=PUBLIC_DATA / "atlas_coherence_preview.json",
                topic=STAGED_PREVIEW_TOPIC,
                repo_root=REPO_ROOT,
            )
        finally:
            conn.close()

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
