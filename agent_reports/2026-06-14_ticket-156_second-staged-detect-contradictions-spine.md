---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-156
---

# ticket-156: Detect Contradictions on Second Staged Source (Mock Spine Step)

## Summary

Added mock detect-contradictions fixture and unit tests proving **detect-contradictions** on OpenAlex
rank #2 after ticket-155 build spine. Uses explicit
`--fixture staged_fetch_second_candidate_detect_contradictions.json` with GT7-style domain base seed.
No production code changes.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-156 |
| Branch | `phase-2/ticket-156-second-staged-detect-contradictions-spine` |
| Date | 2026-06-14 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-14_pre-ticket-156_second-staged-detect-contradictions-audit.md` (GO) |
| Principal audit gate | Cadence overdue (6 tickets since ticket-150); pre-ticket audit satisfied medium-risk gate |
| Main tip before branch | `ee00f35` |

## Scope

### In

- `fixtures/llm_outputs/staged_fetch_second_candidate_detect_contradictions.json`
- `tests/unit/test_staged_second_candidate_detect_contradictions_spine.py` (2 tests)

### Out

- reconcile/report, live LLM/network, schema, public export/site, contradiction_detector refactor

## Changed files

| File | Change |
|------|--------|
| `fixtures/llm_outputs/staged_fetch_second_candidate_detect_contradictions.json` | cross-edge qualification fixture |
| `tests/unit/test_staged_second_candidate_detect_contradictions_spine.py` | build → detect spine + idempotency |
| `agent_reports/2026-06-14_pre-ticket-156_second-staged-detect-contradictions-audit.md` | pre-ticket audit (GO) |
| `tickets/ticket-156.json` | status done |
| `tickets/ticket-157.json` | seeded reconcile-scores on second staged source |
| `tickets/TICKET_QUEUE.md` | ticket-156 done |

## Qualification persisted

One `qualifies` evidence row on base `AI assistance may_reduce semantic diversity`:

| Field | Value |
|-------|-------|
| Qualifying claim | Constraint management improves AI-assisted creative team workflows. (rank #2) |
| Opposing claim | AI-assisted brainstorming reduced semantic diversity… (domain base) |
| Classification | `apparent_contradiction_metric_or_condition_difference` |
| Base relationship | AI assistance → may_reduce → semantic diversity |
| New relationship | constraint → may_increase → human control |

## Idempotency

Second `detect-contradictions` run → `already_detected`; qualifies evidence count unchanged.

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Rank #2 detect fixture deterministic (domain base seed) | **PASS** |
| 2 | Unit test build → detect-contradictions | **PASS** |
| 3 | No live LLM in default collection | **PASS** |
| 4 | Golden pass | **PASS** (142) |
| 5 | Full pytest pass | **PASS** (568) |
| 6 | Safety audit pass | **PASS** |
| 7 | ticket-155 build tests green | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_second_candidate_detect_contradictions_spine.py -q   # 2 passed
python -m pytest tests/unit/test_staged_second_candidate_build_relationships_spine.py -q     # 2 passed
python -m pytest tests/golden -q                                                              # 142 passed
python -m pytest -q                                                                           # 568 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full                                               # pass
```

## Manual CLI verification

Not required — test-only ticket with mocked network and explicit fixtures.

## Spec deviations

- Test seeds `creativity_ai_diversity_short.txt` base graph before rank #2 spine (GT7 pattern; documented in pre-ticket audit).
- No auto-routing for rank #2 title; explicit `--fixture` only.

## Merge to main

*(placeholder — updated after merge)*

## Recommended next ticket

**ticket-157** — Reconcile scores on second staged-ingested source (mock spine step).

Suggested prompt:

```txt
Write pre-ticket audit for ticket-157, then /rge-run-next-ticket
```
