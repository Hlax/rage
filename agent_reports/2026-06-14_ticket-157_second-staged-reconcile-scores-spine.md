---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-157
---

# ticket-157: Reconcile Scores on Second Staged Source (Mock Spine Step)

## Summary

Added rank #2 reconcile contract fixture, staged edge matcher in `score_reconciler`, raised rank #2
extract claim confidence to meet pack threshold, and unit tests proving **reconcile-scores** on OpenAlex
rank #2 after ticket-156 detect spine.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-157 |
| Branch | `phase-2/ticket-157-second-staged-reconcile-scores-spine` |
| Date | 2026-06-14 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-14_pre-ticket-157_second-staged-reconcile-scores-audit.md` (GO) |
| Principal audit gate | Cadence overdue (7 tickets since ticket-150); pre-ticket audit satisfied medium-risk gate |
| Main tip before branch | `7ae609a` |

## Scope

### In

- `fixtures/llm_outputs/staged_fetch_second_candidate_reconcile_scores.json`
- `fixtures/llm_outputs/staged_fetch_second_candidate_extract_claims.json` (confidence 0.85)
- `score_reconciler._matches_staged_second_candidate_may_increase_human_control()`
- `tests/unit/test_staged_second_candidate_reconcile_spine.py` (4 tests)

### Out

- run report, live LLM/network, schema, public export/site

## Changed files

| File | Change |
|------|--------|
| `fixtures/llm_outputs/staged_fetch_second_candidate_reconcile_scores.json` | reconcile contract |
| `fixtures/llm_outputs/staged_fetch_second_candidate_extract_claims.json` | confidence 0.7 → 0.85 |
| `rge/modules/score_reconciler.py` | rank #2 constraint/human-control matcher |
| `tests/unit/test_staged_second_candidate_reconcile_spine.py` | detect → reconcile spine |
| `agent_reports/2026-06-14_pre-ticket-157_second-staged-reconcile-scores-audit.md` | pre-ticket audit (GO) |
| `tickets/ticket-157.json` | status done |
| `tickets/ticket-158.json` | seeded run-report on second staged source |
| `tickets/TICKET_QUEUE.md` | ticket-157 done |

## Score event persisted

| Field | Value |
|-------|-------|
| Relationship | constraint → may_increase → human control |
| Scope | AI-assisted creative team workflows |
| Old confidence | 0.5 |
| New confidence | 0.62 (+0.12 boost) |
| Formula | golden_v0.1.0 |
| Reason | New supporting empirical claim from higher-credibility source. |

One append-only `score_events` row; idempotent re-run produces no duplicate.

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | reconcile-scores persists score_events / confidence update | **PASS** |
| 2 | Unit test extends ticket-156 spine through reconcile-scores | **PASS** |
| 3 | No live LLM in default collection | **PASS** |
| 4 | Golden pass | **PASS** (142) |
| 5 | Full pytest pass | **PASS** (572) |
| 6 | Safety audit pass | **PASS** |
| 7 | ticket-156 detect tests green | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_second_candidate_reconcile_spine.py -q   # 4 passed
python -m pytest tests/unit/test_staged_second_candidate_detect_contradictions_spine.py -q # 2 passed
python -m pytest tests/golden -q                                              # 142 passed
python -m pytest -q                                                           # 572 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full                               # pass
```

## Spec deviations

- Ticket JSON listed `affected_modules: []`; minimal `score_reconciler` matcher required (same precedent as ticket-148).
- Extract fixture confidence bump required to meet pack threshold 0.8.

## Merge to main

*(placeholder — updated after merge)*

## Recommended next ticket

**ticket-158** — Generate run report on second staged-ingested source (mock spine step).

Suggested prompt:

```txt
Write pre-ticket audit for ticket-158, then /rge-run-next-ticket
```
