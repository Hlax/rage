# Agent Report: ticket-272 — Operator proof bundle idempotency unit test

**Date:** 2026-06-16  
**Ticket:** ticket-272  
**Branch:** `phase-3/ticket-272-operator-proof-bundle-idempotency`  
**Main tip before branch:** `728660fd1b33c113e4f43e13148041a145ce9b06`  
**Audit gate:** `agent_reports/2026-06-16_principal-audit-post-ticket-270.md` (GO, cadence satisfied)

## Summary

Added `test_proof_bundle_second_run_is_idempotent_on_same_temp_paths` proving a second
`execute_arbitrary_source_proof_bundle` call on the same temp DB/paths yields stable
counts, reconcile snapshot, `usable_output`, and `source_id`.

## Scope

**In:** Idempotency unit test + stable snapshot helper in `test_operator_proof_bundle.py`.

**Out:** Production code changes, README/AGENTS.md, live LLM, public site.

## Changed files

| File | Change |
|------|--------|
| `tests/unit/test_operator_proof_bundle.py` | Idempotency test + `_stable_bundle_snapshot` |
| `tickets/ticket-272.json`, `TICKET_QUEUE.md` | Status + queue |
| `tickets/ticket-273.json` | Follow-on seeded |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Twice on same temp paths with patched network | **PASS** |
| Second bundle matches stable counts and usable_output | **PASS** |
| Mock LLM only; no live_network | **PASS** |
| Golden pass | **PASS** — 142 |
| Full pytest pass | **PASS** — 706 |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_operator_proof_bundle.py -q  # 9 passed
python -m pytest tests/golden -q                              # 142 passed
python -m pytest -q                                           # 706 passed, 30 deselected
```

Safety audit not required — test-only change.

## Manual CLI verification

Not performed — module-level idempotency covered; staged orchestrator idempotency proven separately in ticket-162.

## Spec deviations

None.

## Merge to main

Merge commit: `fac6bc123b6f5541f1d6d75d2537c86bf9ac2210`

## Recommended next ticket

**ticket-273** — CLI prove-arbitrary-source-bundle second-run idempotency test via `main()`.

## Suggested next prompt

```txt
/rge-run-next-ticket
```
