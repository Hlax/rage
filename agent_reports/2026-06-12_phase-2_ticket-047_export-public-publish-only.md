# Phase 2 Ticket-047 — Export-Public Publish-Only Guard

- Ticket: ticket-047
- Branch: `phase-2/ticket-047-export-public-publish-only`
- Date: 2026-06-12
- Status: done

## Summary

Default mock-mode `export-public` now writes scratch exports to `data/exports/` only. Committed `apps/public-site/public/data/` snapshots update only via `--publish` or fixture-mode runs (deterministic timestamps unchanged).

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_export_publish_gate.py -q   # 4 passed
python -m pytest tests/golden/test_11_public_card_export.py -q  # 4 passed
python -m pytest tests/golden -q                             # 135 passed
python -m pytest -q                                          # 178 passed, 1 deselected
```

## Recommended next ticket

Write pre-ticket-045 audit, then **ticket-045** (improvement draft promotion to ticket-048).
