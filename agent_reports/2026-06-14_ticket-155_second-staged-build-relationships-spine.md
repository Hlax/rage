---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-155
---

# ticket-155: Build Relationships on Second Staged Source (Mock Spine Step)

## Summary

Added mock relationship fixture and unit tests proving **build-relationships** on OpenAlex
rank #2 after ticket-154 link spine. Uses explicit
`--fixture staged_fetch_second_candidate_build_relationships.json`. No production code changes.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-155 |
| Branch | `phase-2/ticket-155-second-staged-build-relationships-spine` |
| Date | 2026-06-14 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-14_pre-ticket-155_second-staged-build-relationships-audit.md` (GO) |
| Principal audit gate | `agent_reports/2026-06-14_principal-audit-post-ticket-153.md` |
| Main tip before branch | `33bc994` |

## Scope

### In

- `fixtures/llm_outputs/staged_fetch_second_candidate_build_relationships.json`
- `tests/unit/test_staged_second_candidate_build_relationships_spine.py` (2 tests)

### Out

- detect/reconcile/report, live LLM/network, schema, public export/site, relationship_builder refactor

## Changed files

| File | Change |
|------|--------|
| `fixtures/llm_outputs/staged_fetch_second_candidate_build_relationships.json` | constraint → human control edge |
| `tests/unit/test_staged_second_candidate_build_relationships_spine.py` | link → build spine + idempotency |
| `agent_reports/2026-06-14_pre-ticket-155_second-staged-build-relationships-audit.md` | pre-ticket audit (GO) |
| `tickets/ticket-155.json` | status done |
| `tickets/ticket-156.json` | seeded detect-contradictions on second staged source |
| `tickets/TICKET_QUEUE.md` | ticket-155 done |

## Relationship persisted

| Field | Value |
|-------|-------|
| subject | constraint |
| predicate | may_increase |
| object | human control |
| scope | AI-assisted creative team workflows |
| confidence | 0.5 (medium label) |
| evidence | 1 supports row on accepted claim |

Uses concepts from ticket-154 link fixture (constraint, human control).

## Idempotency

Second `build-relationships` run → `already_built`; relationship count unchanged.

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Rank #2 relationship fixture deterministic | **PASS** |
| 2 | Unit test extract → link → build-relationships | **PASS** |
| 3 | ≥1 relationship row persisted | **PASS** |
| 4 | Re-run idempotent | **PASS** |
| 5 | ticket-154 link tests green | **PASS** |
| 6 | Golden pass | **PASS** (142) |
| 7 | Full pytest pass | **PASS** (566) |
| 8 | Safety audit pass | **PASS** |
| 9 | No public export/site | **PASS** |
| 10 | ticket-156 seeded | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/unit/test_staged_second_candidate_link_spine.py -q              # 2 passed
python -m pytest tests/unit/test_staged_second_candidate_build_relationships_spine.py -q # 2 passed
python -m pytest tests/golden -q                                                       # 142 passed
python -m pytest -q                                                                    # 566 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full                                      # pass
```

No live LLM, live network, or public export in this ticket.

## Spec deviations

- No `relationship_builder.py` auto-select heuristic (explicit `--fixture` per pre-ticket audit).

## Merge to main

Placeholder — updated after merge.

## Recommended next ticket

**ticket-156** — Detect contradictions on second staged-ingested source (mock spine step).

Rank #2 spine complete through build-relationships only; not full cross-source synthesis.

## Suggested next prompt

Pre-ticket audit for ticket-156, then:

```text
/rge-run-next-ticket
```
