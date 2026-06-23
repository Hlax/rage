# Ticket-387 — AGENTS.md operator loop researcher product proof cross-link v0

**Date:** 2026-06-23  
**Branch:** `phase-3/ticket-387-agents-researcher-product-proof-crosslink`  
**Ticket:** ticket-387

## Summary

Added AGENTS.md Operator Loop cross-link for `researcher_product_proof_status`,
`product_verdict`, and `prove-researcher-product`, mirroring the synthesis benchmark and
arbitrary-source proof bundle patterns. Points to README Operator Quickstart and post-launch
orchestrator checklist (ticket-389).

## Changed files

| File | Change |
|------|--------|
| `AGENTS.md` | Researcher product proof operator loop paragraph |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| AGENTS.md cross-links README researcher product proof quickstart | **PASS** |
| Mentions `researcher_product_proof_status` / `product_verdict` without full JSON | **PASS** |
| No code changes | **PASS** |

## Commands run

| Command | Result |
|---------|--------|
| `python -m pytest tests/golden -q` | **165 passed** |

## Merge to main

Placeholder — updated after merge.

## Recommended next ticket

Principal audit checkpoint (cadence overdue after tickets 386–389) or operator live
orchestrator retry on network-unrestricted machine per ticket-389 report.
