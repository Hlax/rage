# Agent Report: ticket-240 — README rank-2 per-step live Ollama closure checklist

**Date:** 2026-06-16  
**Phase:** 3  
**Ticket:** ticket-240  
**Branch:** `phase-3/ticket-240-readme-rank2-live-closure-checklist`  
**Status:** implemented

## Summary

Added consolidated README operator checklist for rank-2 per-step live Ollama closure
(tickets 230/236/237/238): shared env prerequisites, per-step gate table, pytest commands,
not-in-scope table, and catalog-drift note. Updated maturity tier row and AGENTS cross-reference.

## Audit gate

- Principal audit satisfied: `agent_reports/2026-06-16_ticket-239_principal-audit-post-ticket-238.md` (cadence reset)

## Scope in / out

**In:** README checklist section, maturity tier refresh, AGENTS cross-reference.

**Out:** Product code, new fallthrough flags, runtime config (ticket-241).

## Changed files

| File | Change |
|------|--------|
| `README.md` | **One-time rank-2 per-step live Ollama verification** checklist; maturity tier; orchestrator cross-links |
| `AGENTS.md` | Closure checklist cross-reference |
| `tickets/TICKET_QUEUE.md`, `tickets/ticket-240.json`, `tickets/ticket-241.json` | Queue updates |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Four rank-2 live gates, shared env, per-step pytest | **PASS** |
| 2 | Closure at detect; reconcile/report deterministic | **PASS** |
| 3 | AGENTS cross-reference | **PASS** |
| 4 | Golden pass | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q    # 142 passed
python -m pytest -q                 # 666 passed, 30 deselected
```

Safety audit not required — docs-only ticket.

## Merge to main

Pending merge commit hash (recorded after step 12).

## Recommended next ticket

**ticket-241** — runtime config rank-2 live closure cross-link.

## Suggested next prompt

`/rge-run-next-ticket` for **ticket-241** (runtime config closure summary).
