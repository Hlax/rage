---
template_id: implementation_report
status: done
date: 2026-06-15
phase: 2
ticket: ticket-196
---

# ticket-196: Shared Live Staged Candidate Query Test Helper

## Summary

Added `tests/unit/live_staged_candidates.py` with shared rank-1/rank-2 candidate
selection helpers (`ORDER BY priority_score DESC`) and refactored all nine
`live_network` staged tests to use them, eliminating duplicated SQL and reducing
drift risk after ticket-195.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-196 |
| Branch | `phase-2/ticket-196-live-staged-candidate-helper` |
| Date | 2026-06-15 |
| Risk | low |
| Principal audit gate | `agent_reports/2026-06-15_principal-audit-post-ticket-194.md` (cadence satisfied; only ticket-195 done since) |
| Main tip before branch | `d7c397b` |

## Scope

**In:** Test-only DRY helper; refactor nine live staged tests.

**Out:** Production code, schema, CI live network, public export/site.

## Changed files

| File | Change |
|------|--------|
| `tests/unit/live_staged_candidates.py` | New: `count_staged_candidates`, `select_staged_candidate_row`, `select_rank1_candidate_id`, `select_rank2_candidate_id` |
| `tests/unit/test_live_staged_fetch_validation.py` | Use `select_rank1_candidate_id` |
| `tests/unit/test_live_staged_ingest_validation.py` | Use `select_rank1_candidate_id` |
| `tests/unit/test_live_staged_extract_mock_spine.py` | Use `select_rank1_candidate_id` |
| `tests/unit/test_live_staged_link_mock_spine.py` | Use `select_rank1_candidate_id` |
| `tests/unit/test_live_staged_build_mock_spine.py` | Use `select_rank1_candidate_id` |
| `tests/unit/test_live_staged_detect_mock_spine.py` | Use `select_rank1_candidate_id` |
| `tests/unit/test_live_staged_reconcile_mock_spine.py` | Use `select_rank1_candidate_id` |
| `tests/unit/test_live_staged_report_mock_spine.py` | Use `select_rank1_candidate_id` |
| `tests/unit/test_live_staged_rank2_report_mock_spine.py` | Use `select_rank2_candidate_id` |
| `tickets/ticket-196.json` | Status `done` |
| `tickets/TICKET_QUEUE.md` | Mark done; seed ticket-197 |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Shared helper selects rank-1 and rank-2 by `priority_score DESC` | **PASS** |
| 2 | All live staged tests use the helper | **PASS** (9 files) |
| 3 | Golden pass | **PASS** (142) |
| 4 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q   # 142 passed
python -m pytest -q                # 599 passed, 16 deselected
python -m rge.modules.safety_auditor --audit full  # pass
```

No live network pytest run (test-only refactor; operator opt-in unchanged).

## Manual CLI verification

Not required (no CLI or production code changes).

## Spec deviations

None.

## Merge to main

Pending merge in this run.

## Recommended next ticket

**ticket-197** — Shared staged domain opposing-context seed test helper (DRY across staged mock/idempotency tests).

## Suggested next prompt

`/rge-run-next-ticket`
