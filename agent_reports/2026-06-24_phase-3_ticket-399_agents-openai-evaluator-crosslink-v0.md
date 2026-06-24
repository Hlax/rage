# Ticket-399 — AGENTS.md OpenAI synthesis evaluator runbook cross-link v0

**Date:** 2026-06-24  
**Branch:** `phase-3/ticket-399-agents-openai-evaluator-crosslink`  
**Ticket:** ticket-399  
**Main tip before branch:** `673fd01` (post ticket-398 merge)  
**Audit gate:** satisfied — `agent_reports/2026-06-24_principal-audit-post-ticket-397_openai-evaluator-sequence.md` (GO)

## Summary

Added AGENTS.md Operator Loop cross-link for the live OpenAI synthesis evaluator canary
runbook (tickets 393–397): plan status field, mock-first vs operator live boundary,
autocycle live-canary block, self-improvement spine step, and README/runtime doc pointers.

## Scope

**In:** `AGENTS.md` Operator Loop paragraph only.

**Out:** README edits, engine changes, live HTTP.

## Changed files

| File | Change |
|------|--------|
| `AGENTS.md` | Live OpenAI synthesis evaluator canary cross-link section |
| `tickets/ticket-399.json` | Status `done` |
| `tickets/ticket-400.json` | Proposed optional execute-safe evaluator seed |
| `tickets/TICKET_QUEUE.md` | Row 399 done; active → ticket-400 |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| AGENTS.md cross-links README evaluator runbook and 393–397 spine | **PASS** |
| Documents `openai_synthesis_evaluator_status` and mock-first vs live canary | **PASS** |
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

Merge commit: *(pending merge)*.

## Recommended next ticket

**ticket-400** — Execute-safe mock OpenAI synthesis evaluator seed hook (optional hardening; medium risk — pre-ticket audit recommended).

## Suggested next prompt

```txt
/rge-run-next-ticket
```
