from __future__ import annotations

import json
from pathlib import Path

from rge.modules.autonomous_synthesis_governor import LEDGER_SCHEMA_VERSION
from rge.modules.self_improvement_status import (
    build_self_improvement_status,
    write_self_improvement_status,
)
from tests.unit.operator_loop_helpers import seed_operator_neutral_plan_state


def test_self_improvement_status_surfaces_flagged_governor_reviews(tmp_path: Path) -> None:
    seed_operator_neutral_plan_state(tmp_path)
    ledger_path = tmp_path / "data/operator/autonomous_synthesis_governor_ledger.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(
            {
                "schema_version": LEDGER_SCHEMA_VERSION,
                "reviews": [
                    {
                        "review_id": "syn_gov_bad",
                        "governor_verdict": "NO-GO",
                        "failure_reasons": ["budget gate missing"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    payload = build_self_improvement_status(root=tmp_path)

    assert payload["schema_version"] == "self_improvement_status_v0.1.0"
    assert payload["status"] == "NO-GO"
    assert payload["spine_map"][0]["step"] == "research_run_report"
    assert payload["spine_map"][-1]["step"] == "atlas_preview"
    flagged = payload["current_state"]["flagged_synthesis_governor_reviews"]
    assert flagged == [
        {
            "review_id": "syn_gov_bad",
            "governor_verdict": "NO-GO",
            "failure_reasons": ["budget gate missing"],
        }
    ]
    assert "edit_TICKET_QUEUE" in payload["forbidden_actions"]


def test_write_self_improvement_status_uses_private_operator_path(tmp_path: Path) -> None:
    seed_operator_neutral_plan_state(tmp_path)

    path = write_self_improvement_status(root=tmp_path)

    assert path.relative_to(tmp_path).as_posix() == "data/operator/self_improvement_status_latest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "self_improvement_status_v0.1.0"
