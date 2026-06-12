# Phase 2 Ticket-050 — CI Node 24 Actions Opt-In

- Ticket: ticket-050
- Branch: `phase-2/ticket-050-ci-node24-actions`
- Date: 2026-06-12
- Status: done

## Summary

Added `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` to Golden Gate workflow job env to silence GitHub Actions Node 20 deprecation warnings ahead of the June 2026 runner default change.

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_ci_golden_gate.py -q   # 5 passed
```
