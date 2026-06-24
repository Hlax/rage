# Ticket-408 — AGENTS.md researcher product proof drift clearance quickstep cross-link v0

**Date:** 2026-06-24  
**Branch:** `phase-3/ticket-408-agents-product-proof-drift-quickstep`  
**Ticket:** ticket-408  
**Main tip before branch:** `059b7352cf67e2fd00028bdc0fcbe7309347faf2`  
**Audit gate:** satisfied — cadence below threshold (2 done since ticket-405 audit); `risk_level: low`

## Summary

Extended AGENTS.md **Researcher product proof** paragraph with a cross-link to README
**Operator Quickstart** (*Researcher product proof* — *Product-risk drift clearance
quickstep*) for when plan JSON shows `product_proof_recommended: true` (ticket-407).

## Scope

**In:** AGENTS.md paragraph only.

**Out:** README edits, engine changes, live network or live LLM.

## Changed files

| File | Change |
|------|--------|
| `AGENTS.md` | Product-risk drift clearance quickstep cross-link (ticket-407) |
| `tickets/ticket-408.json` | Status `done` |
| `tickets/ticket-409.json` | Proposed principal audit post 406–408 |
| `tickets/TICKET_QUEUE.md` | Row 408 done; active → ticket-409 |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| AGENTS.md cross-links README product-risk drift clearance quickstep | **PASS** |
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

Merge commit: `86eb058620643153f7d0d973271be92edf5a9c24`.

Post-merge full pytest: **1381 passed**, 49 deselected.

## Recommended next ticket

**ticket-409** — Principal audit post product proof docs sequence (406–408).

## Suggested next prompt

```txt
/rge-principal-audit for ticket-409 sequence, then /rge-run-next-ticket
```
