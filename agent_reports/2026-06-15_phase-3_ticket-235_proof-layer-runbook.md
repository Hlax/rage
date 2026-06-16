# Agent Report: ticket-235 — README proof-layer runbook (unsuitable_live_artifact)

**Date:** 2026-06-15  
**Phase:** 3  
**Ticket:** ticket-235  
**Branch:** `phase-3/ticket-235-proof-layer-runbook`  
**Status:** done (documentation only)

## Summary

Added operator-facing documentation for the three-layer live staged proof model introduced in ticket-234, including how to interpret `unsuitable_live_artifact` pytest skips and when to retry vs treat as expected catalog/fixture drift.

## Changes

| File | Change |
|------|--------|
| `README.md` | New **Live staged proof layers (tickets 233–234)** section under Operator Quickstart: layer table, layer-1 commands, layer-2 CI reference, layer-3 combined commands, skip JSON example, operator interpretation table, helper module pointer |
| `AGENTS.md` | Cross-reference to README proof-layer runbook and one-paragraph layer summary |
| `tickets/TICKET_QUEUE.md` | ticket-235 marked done; queue notes updated; next work ticket-232 |
| `tickets/ticket-235.json` | status → `done` |

No product or test code changes.

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli verify --skip-site
```

**Result:** PASS — golden 142, full pytest **642** passed (26 deselected), safety audit ok.

## Acceptance criteria

- [x] Document layer 1 acquisition, layer 2 fixture mock spine, layer 3 combined live proof
- [x] Document `unsuitable_live_artifact` skip JSON and operator retry guidance
- [x] No product code changes

## Next ticket

**ticket-230** — rank-2 staged extract live LLM opt-in proof (pre-ticket-230 GO).

## Merge note

Merged to `main` @ `65e4efa` (fast-forward).
