# Phase 2 Ticket-055 — Export Snapshot History

- Ticket: ticket-055
- Branch: `phase-2/ticket-055-export-snapshot-history`
- Date: 2026-06-12
- Status: done
- Pre-ticket audit: `agent_reports/2026-06-12_pre-ticket-055_export-snapshot-versioning-readiness-audit.md` (GO)

## Summary

Added scratch export snapshot history for operator review. Default mock `export-public` still writes the latest trio to `data/exports/` and now also appends `snapshot_manifest.json` plus a copy under `data/exports/history/<bundle_id>/`. Retention cap (10) prunes oldest bundles. `--no-snapshot-history` opt-out preserves test/CI determinism. Ticket-047 publish-only semantics unchanged.

## Changes

| File | Update |
| ---- | ------ |
| `rge/modules/card_exporter.py` | Manifest + history write, retention prune, helpers |
| `rge/cli.py` | `--no-snapshot-history`; accurate export-public help |
| `rge/modules/safety_auditor.py` | Audit history bundle triplets + manifest |
| `tests/unit/test_export_snapshot_history.py` | 5 unit tests |
| `tests/golden/test_23_safety_audit_gate.py` | +1 history bundle audit test |
| `docs/deployment/public-site-static-hosting.md` | History review + `export_schema_version` bump checklist |

## Commands run (mock only)

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/unit/test_export_snapshot_history.py -q   # 5 passed
python -m pytest tests/golden -q                                 # 140 passed
python -m pytest -q                                            # 196 passed, 1 deselected
python -m rge.modules.safety_auditor --audit full               # pass
python -m rge.cli verify --skip-site                             # pass
```

## Non-goals honored

- No auto-publish; no new public JSON fields
- No npm/execute-safe Windows fix
- No live Ollama / live smoke

## Merge

- Commit: `0c12d31` on `phase-2/ticket-055-export-snapshot-history`
- Merged to `main` via fast-forward from `b620fe3`
- Pushed to `origin/main`

## Recommended next ticket

Windows npm subprocess fix for `operator_loop --mode execute-safe` (low-risk, separate), or next Post-Phase-2 roadmap item per human review.
