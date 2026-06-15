---
template_id: implementation_report
status: done
date: 2026-06-15
phase: 2
ticket: ticket-197
---

# ticket-197: Shared Staged Domain Opposing-Context Seed Test Helper

## Summary

Added `tests/unit/staged_domain_seed.py` with `seed_domain_opposing_context` and refactored
fourteen staged mock/idempotency and live staged tests to import the shared helper,
eliminating duplicated GT7-style base-graph seed logic.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-197 |
| Branch | `phase-2/ticket-197-staged-domain-seed-helper` |
| Date | 2026-06-15 |
| Risk | low |
| Principal audit gate | `agent_reports/2026-06-15_principal-audit-post-ticket-194.md` (cadence satisfied; tickets 195–196 done since) |
| Main tip before branch | `ad24464` |

## Scope

**In:** Test-only DRY helper; refactor fourteen staged tests listed in ticket JSON.

**Out:** Production code, schema, CI live network, public export/site.

## Changed files

| File | Change |
|------|--------|
| `tests/unit/staged_domain_seed.py` | New: `DOMAIN_BASE_SOURCE`, `seed_domain_opposing_context` |
| `tests/unit/test_live_staged_report_mock_spine.py` | Import shared helper |
| `tests/unit/test_live_staged_detect_mock_spine.py` | Import shared helper |
| `tests/unit/test_live_staged_reconcile_mock_spine.py` | Import shared helper |
| `tests/unit/test_live_staged_rank2_report_mock_spine.py` | Import shared helper |
| `tests/unit/test_staged_ingest_idempotency.py` | Import shared helper |
| `tests/unit/test_staged_ingest_reconcile_spine.py` | Import shared helper |
| `tests/unit/test_staged_ingest_contradiction_spine.py` | Import shared helper |
| `tests/unit/test_staged_ingest_run_report_spine.py` | Import shared helper |
| `tests/unit/test_staged_second_candidate_idempotency.py` | Import shared helper |
| `tests/unit/test_staged_second_candidate_detect_contradictions_spine.py` | Import shared helper |
| `tests/unit/test_staged_second_candidate_reconcile_spine.py` | Import shared helper |
| `tests/unit/test_staged_second_candidate_run_report_spine.py` | Import shared helper |
| `tests/unit/test_staged_dual_candidate_idempotency.py` | Import shared helper |
| `tickets/ticket-197.json` | Status `done` |
| `tickets/TICKET_QUEUE.md` | Mark done; seed ticket-198 |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Shared helper seeds opposing domain context identically | **PASS** |
| 2 | All listed staged tests import shared helper | **PASS** (14 files) |
| 3 | Golden pass | **PASS** (142) |
| 4 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q   # 142 passed
python -m pytest -q                # 599 passed, 16 deselected
python -m rge.modules.safety_auditor --audit full  # pass
```

No live network pytest run (test-only refactor).

## Manual CLI verification

Not required (no CLI or production code changes).

## Spec deviations

None.

## Merge to main

Pending merge in this run.

## Recommended next ticket

**ticket-198** — Principal audit post-ticket-197 (cadence overdue: three hygiene tickets since post-ticket-194 audit).

## Suggested next prompt

`/rge-principal-audit` or `/rge-run-next-ticket` for ticket-198 audit checkpoint.
