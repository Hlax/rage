# Ticket-402 — AGENTS.md execute-safe OpenAI evaluator seed hook cross-link v0

**Date:** 2026-06-24  
**Branch:** `phase-3/ticket-402-agents-execute-safe-evaluator-seed`  
**Ticket:** ticket-402  
**Main tip before branch:** `1641bd03e56a83cd22ffd215018f0f57e1189210`  
**Audit gate:** not required — docs-only, `risk_level: low`; cadence satisfied

## Summary

Extended AGENTS.md Operator Loop Live OpenAI synthesis evaluator bullet with ticket-400
execute-safe seed hook cross-link to README (*Execute-safe evaluator seed hook* subsection).

## Scope

**In:** AGENTS.md paragraph only.

**Out:** README edits, engine changes.

## Changed files

| File | Change |
|------|--------|
| `AGENTS.md` | Execute-safe evaluator seed cross-link (ticket-400) |
| `tickets/ticket-402.json` | Status `done` |
| `tickets/ticket-403.json` | Proposed principal audit post 399–402 |
| `tickets/TICKET_QUEUE.md` | Row 402 done; active → ticket-403 |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| AGENTS.md cross-links README execute-safe evaluator seed hook (ticket-400) | **PASS** |
| No code changes | **PASS** |

## Commands run

| Command | Result |
|---------|--------|
| `RGE_LLM_MODE=mock python -m pytest tests/golden -q` | **165 passed** |

## Manual CLI verification

Not required — documentation-only ticket.

## Spec deviations

None.

## Merge to main

Merge commit: `49eadfc79cd7374f2f808316af3d0717e0879d88`.

## Recommended next ticket

**ticket-403** — Principal audit post OpenAI evaluator docs sequence (399–402).

## Suggested next prompt

```txt
/rge-principal-audit for ticket-403, then /rge-run-next-ticket when audit is GO.
```
