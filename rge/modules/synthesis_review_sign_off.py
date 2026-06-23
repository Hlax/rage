"""Operator sign-off status for grounding-passed synthesis outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rge.modules.autonomous_synthesis_governor import _safe_rel, utc_now_iso
from rge.modules.principal_audit_gate import repo_root

ARTIFACT_REL = Path("apps/public-site/public/data/atlas_synthesis_human_review_latest.json")
SIGN_OFF_CLI_SCRIPT = "scripts/run_synthesis_review_sign_off.py"


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def inspect_synthesis_sign_off_plan_status(*, root: Path | None = None) -> dict[str, Any]:
    project_root = root or repo_root()
    artifact_path = project_root / ARTIFACT_REL
    payload = _load_json(artifact_path) if artifact_path.is_file() else None
    sign_off = (payload or {}).get("sign_off_summary") or {}
    pending = int(sign_off.get("pending_sign_off_count") or 0)
    eligible = int(sign_off.get("eligible_count") or 0)
    signed_off = int(sign_off.get("signed_off_count") or 0)

    return {
        "status": "available" if payload else "unavailable",
        "artifact_path": _safe_rel(artifact_path, project_root),
        "sign_off_recommended": pending > 0,
        "pending_sign_off_count": pending,
        "eligible_count": eligible,
        "signed_off_count": signed_off,
        "operator_commands": {
            "list_pending": f"python {SIGN_OFF_CLI_SCRIPT} --list-pending",
            "fixture_sign_off": (
                f'$env:RGE_ALLOW_SYNTHESIS_REVIEW_SIGN_OFF = "1"; '
                f"python {SIGN_OFF_CLI_SCRIPT} --fixture-sign-off --sync-public"
            ),
        },
        "updated_at": utc_now_iso(),
    }
