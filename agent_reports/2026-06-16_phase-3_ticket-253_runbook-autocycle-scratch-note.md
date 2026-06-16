# Agent Report: ticket-253 — Runbook autocycle scratch evidence operator note

**Date:** 2026-06-16  
**Phase:** 3  
**Ticket:** ticket-253  
**Branch:** `phase-3/ticket-253-runbook-autocycle-scratch-note`  
**Main tip before branch:** `bdce3987bfed7a02d67ba49bacfeb4e7666d60ac`  
**Status:** implemented

## Summary

Documented operator autocycle scratch evidence gate in
`docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md`: JSON fields
(`scratch_evidence_review_recommended`, `scratch_evidence_status`), drift carve-out,
and priority relative to open queue tickets. Docs-only.

## Audit gate

- **Satisfied:** cadence satisfied (1 done since checkpoint-251 before this ticket); `risk_level: low`

## Scope in / out

**In:** Runbook section + checklist step 5 cross-link.

**Out:** Product code, live Ollama, README/AGENTS duplication.

## Changed files

| File | Change |
|------|--------|
| `docs/agents/14_LIVE_PROBE_OPERATOR_RUNBOOK.md` | Autocycle scratch gate section |
| `tickets/ticket-253.json`, `TICKET_QUEUE.md` | Status + queue |
| `tickets/ticket-254.json` | Product follow-on seeded |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Runbook documents autocycle fields and drift carve-out | **PASS** |
| 2 | Golden pass | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q    # 142 passed
```

Safety audit not required — docs-only.

## Manual CLI verification

Not applicable.

## Spec deviations

None.

## Merge to main

- Merge commit: _(pending)_
- Post-merge pytest: _(pending)_

## Recommended next ticket

**ticket-254** — Configurable rank-2 staged candidate scan window env (product hardening).

## Suggested next prompt

`/rge-run-next-ticket` for **ticket-254** (product) or `/rge-principal-audit` after third consecutive done ticket.
