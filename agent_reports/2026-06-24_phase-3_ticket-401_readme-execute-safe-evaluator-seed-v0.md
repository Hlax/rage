# Ticket-401 — README execute-safe OpenAI evaluator seed hook cross-link v0

**Date:** 2026-06-24  
**Branch:** `phase-3/ticket-401-readme-execute-safe-evaluator-seed`  
**Ticket:** ticket-401  
**Main tip before branch:** `c30cc1b69d30cfc352c1b8b101c29af01890b585`  
**Audit gate:** not required — docs-only, `risk_level: low`; cadence satisfied per `principal_audit_gate`

## Summary

Documented the ticket-400 execute-safe evaluator seed hook in README Operator Quickstart
under the Live OpenAI synthesis evaluator canary runbook: trigger conditions
(`review_artifact_recommended` + `run_openai_synthesis_evaluator`), input resolution,
payload keys, and mock-only boundary.

## Scope

**In:** README execute-safe evaluator seed subsection only.

**Out:** Engine changes, AGENTS.md (ticket-402), live HTTP.

## Changed files

| File | Change |
|------|--------|
| `README.md` | Execute-safe evaluator seed hook table + command |
| `tickets/ticket-401.json` | Status `done` |
| `tickets/ticket-402.json` | Proposed AGENTS cross-link |
| `tickets/TICKET_QUEUE.md` | Row 401 done; active → ticket-402 |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| README documents execute-safe seed trigger and mock evaluate action | **PASS** |
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

**ticket-402** — AGENTS.md execute-safe OpenAI evaluator seed hook cross-link v0.

## Suggested next prompt

```txt
/rge-run-next-ticket
```
