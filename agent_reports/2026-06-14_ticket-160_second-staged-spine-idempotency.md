---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-160
---

# ticket-160: Second Staged Candidate Full Spine Idempotency (Mock)

## Summary

Added unit tests proving rank #2 Phase 3 mock spine idempotency: full discover→report
re-run and per-command reruns preserve stable row counts. Mirrors ticket-151 with explicit
rank #2 `--fixture` bindings. No production code changes.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-160 |
| Branch | `phase-2/ticket-160-second-staged-spine-idempotency` |
| Date | 2026-06-14 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-14_pre-ticket-160_second-staged-spine-idempotency-audit.md` (GO) |
| Principal audit gate | `agent_reports/2026-06-14_principal-audit-post-ticket-158.md` (cadence satisfied) |
| Main tip before branch | `05e211d` |

## Scope

### In

- `tests/unit/test_staged_second_candidate_idempotency.py` (2 tests)
- `tickets/ticket-160.json` (seeded this run)
- Principal audit report committed with this merge (post-ticket-158 checkpoint)

### Out

- Dual-candidate combined idempotency, live network, schema, public export/site

## Stable counts (rank #2 staged source)

| Metric | Value |
|--------|-------|
| sources | 2 |
| candidate_sources | 2 |
| research_queue | 2 |
| accepted / rejected claims (staged) | 1 / 1 |
| concept links (staged) | 3 |
| relationships with staged claim evidence | 2 (build supports + detect qualifies) |
| score_events | 1 |
| run_reports | 1 |
| qualifies evidence | 1 |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Full spine twice → stable counts | **PASS** |
| 2 | Per-command reruns idempotent with explicit fixtures | **PASS** |
| 3 | No live LLM/network in default collection | **PASS** |
| 4 | Golden pass | **PASS** (142) |
| 5 | Full pytest pass | **PASS** (577) |
| 6 | Safety audit pass | **PASS** |
| 7 | ticket-158 run-report tests green | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_second_candidate_idempotency.py -q   # 2 passed
python -m pytest tests/unit/test_staged_second_candidate_run_report_spine.py -q # 3 passed
python -m pytest tests/golden -q                                              # 142 passed
python -m pytest -q                                                           # 577 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full                               # pass
```

## Spec deviations

- `relationships_staged` is 2 (not 1) because detect attaches qualifies evidence on the domain-base edge using the rank #2 claim; documented in pre-ticket audit update.

## Merge to main

*(placeholder — updated after merge)*

## Recommended next ticket

**ticket-161** — Dual-candidate staged idempotency on one DB (mock).

Suggested prompt:

```txt
Write pre-ticket audit for ticket-161, then /rge-run-next-ticket
```
