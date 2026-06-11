"""Run deterministic safety checks. Deterministic; no model use.

Future audit types (10_SAFETY_MODEL.md section 13): prompt_injection,
public_export, route_permissions, secrets, raw_html, model_tool_permissions,
full. Deterministic checks decide pass/fail; model commentary never does.

Phase 0: the audit logic is not implemented. Running this module reports
``NOT AVAILABLE IN THIS PHASE`` as machine-readable JSON and exits non-zero
so nothing can mistake it for a passing audit.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

AUDIT_TYPES = (
    "prompt_injection",
    "public_export",
    "route_permissions",
    "secrets",
    "raw_html",
    "model_tool_permissions",
    "full",
)

_NOT_AVAILABLE_EXIT_CODE = 3


def run_safety_audit(audit_type: str = "full") -> dict[str, Any]:
    """Run a deterministic safety audit. Not implemented in Phase 0."""
    raise NotImplementedError(
        "safety_auditor.run_safety_audit arrives with Phase 4/5."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m rge.modules.safety_auditor",
        description="Deterministic safety auditor (NOT AVAILABLE IN THIS PHASE).",
    )
    parser.add_argument("--audit", default="full", choices=AUDIT_TYPES)
    args = parser.parse_args(argv)

    payload = {
        "report_type": "safety_audit_report",
        "audit_type": args.audit,
        "status": "NOT AVAILABLE IN THIS PHASE",
        "phase": "0",
        "detail": (
            "The deterministic safety auditor is not implemented in the Phase 0 "
            "scaffold. This is an honest non-result, not a pass."
        ),
    }
    print(json.dumps(payload, indent=2))
    return _NOT_AVAILABLE_EXIT_CODE


if __name__ == "__main__":
    sys.exit(main())
