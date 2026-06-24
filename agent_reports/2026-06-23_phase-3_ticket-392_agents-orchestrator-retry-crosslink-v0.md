# Ticket-392 — AGENTS.md live orchestrator retry runbook cross-link v0

**Date:** 2026-06-23  
**Branch:** `phase-3/ticket-392-agents-orchestrator-retry-crosslink`  
**Ticket:** ticket-392  
**Main tip before branch:** `fb833bc6911a46d5671f3bbbe68b3bd7280f2901`  
**Audit gate:** not required — docs-only, `risk_level: low`; no public export, schema, or live Ollama changes.

## Summary

Added AGENTS.md Operator Loop cross-links for live staged orchestrator retry guidance when
OpenAlex catalogs lack mock-spine marker phrases. Mirrors README **Interpreting
`unsuitable_live_artifact`** and points to the ticket-391 retry runbook agent report.

No code changes.

## Scope

**In:** AGENTS.md orchestrator checklist and proof-layer paragraphs; ticket queue update.

**Out:** README edits; engine changes; live network pytest in CI.

## Changed files

| File | Change |
|------|--------|
| `AGENTS.md` | Orchestrator retry runbook (ticket-391) cross-link after one-time checklist |
| `tickets/ticket-392.json` | Status `done` |
| `tickets/TICKET_QUEUE.md` | Row 392 done; active ticket → ticket-393 |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| AGENTS.md cross-links README `unsuitable_live_artifact` and ticket-391 retry runbook | **PASS** |
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

Merge commit: `df4e0b25ba41b2b0d5e38de2efa1dc887f3eb2ad`.

## Recommended next ticket

**ticket-393** — Hydrate live OpenAI synthesis grounding input (live OpenAI evaluator path;
`risk_level: medium` — principal audit may be required before implementation).

## Suggested next prompt

```txt
/rge-run-next-ticket
```

Implement ticket-393 on branch `phase-3/ticket-393-live-openai-grounding-input`.
