# Ticket-407 — README researcher product proof drift clearance quickstep v0

**Date:** 2026-06-24  
**Branch:** `phase-3/ticket-407-readme-product-proof-drift-quickstep`  
**Ticket:** ticket-407  
**Main tip before branch:** `33fe150e66fc902cbc13c0fc4d884af7862cdc96`  
**Audit gate:** satisfied — `agent_reports/2026-06-24_principal-audit-post-ticket-405_execute-safe-docs-trilogy.md` (GO)

## Summary

Added a **Product-risk drift clearance quickstep** subsection to README **Operator Quickstart**
(*Researcher product proof*) documenting the five-step operator flow when plan JSON shows
`product_proof_recommended: true`, including mock-only `prove-researcher-product` and replan
expectations. Documentation-only; no code changes.

## Scope

**In:** README quickstep table and autocycle/execute-safe boundary note.

**Out:** Engine changes, live network or live LLM.

## Changed files

| File | Change |
|------|--------|
| `README.md` | Product-risk drift clearance quickstep subsection |
| `tickets/ticket-407.json` | Status `done` |
| `tickets/ticket-408.json` | Proposed AGENTS cross-link |
| `tickets/TICKET_QUEUE.md` | Row 407 done; active → ticket-408 |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| README documents when `product_proof_recommended` appears and mock-only prove command | **PASS** |
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

Merge commit: `292b47cdd8d7ae0dde6f16d38967a579c9911c66`.

Post-merge full pytest: **1380 passed, 1 failed** — flaky
`test_export_atlas_snapshot_fixture_mode_second_run_byte_identical` (passes in isolation;
unrelated to README-only change).

## Recommended next ticket

**ticket-408** — AGENTS.md researcher product proof drift clearance quickstep cross-link v0.

## Suggested next prompt

```txt
/rge-run-next-ticket
```
