# Agent Report: ticket-265 — README documents staged run rank candidate id output fields

**Date:** 2026-06-16  
**Phase:** 3  
**Ticket:** ticket-265  
**Branch:** `phase-3/ticket-265-readme-staged-run-candidate-ids`  
**Main tip before branch:** `98fcbe8d97b98abb86ba903a8e298e36ef6c7d32`  
**Status:** done

## Summary

Documented `rank1_candidate_id` and `rank2_candidate_id` in README Operator Quickstart
staged spine section: field meanings, default fixture ids, live-orchestrator heuristic
selection, and idempotency note. Updated live orchestrator checklist step to mention
candidate id fields in stdout JSON.

## Audit gate

- **Satisfied:** `agent_reports/2026-06-16_principal-audit-post-ticket-262.md`; cadence satisfied; `risk_level: low`

## Scope in / out

**In:** README operator documentation only.

**Out:** Production code, public site, export surface, live Ollama.

## Changed files

| File | Change |
|------|--------|
| `README.md` | Staged spine stdout candidate-id fields + orchestrator checklist |
| `tickets/ticket-265.json`, `TICKET_QUEUE.md` | Status + queue |
| `tickets/ticket-266.json` | Principal audit follow-on seeded |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | README documents rank candidate ids in staged run stdout JSON | **PASS** |
| 2 | No code or export surface changes | **PASS** |
| 3 | Golden pass | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q  # 142 passed
python -m pytest -q               # 689 passed, 30 deselected
```

Safety audit not required — README-only ticket.

## Manual CLI verification

Not performed — documentation aligns with ticket-261–264 implementation and tests.

## Spec deviations

None.

## Merge to main

- Merge commit: `f715e9ed2aa4fa7d8d400649cdf22b124829cd58`
- Post-merge pytest: `689 passed, 30 deselected`

## Recommended next ticket

**ticket-266** — Principal audit post-ticket-265 (cadence: three done tickets 263–265 since audit post-ticket-262).

## Suggested next prompt

```txt
/rge-principal-audit
```
