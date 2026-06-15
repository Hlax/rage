---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-161
---

# ticket-161: Dual-Candidate Staged Phase 3 Idempotency (Mock)

## Summary

Added unit tests proving rank #1 and rank #2 full mock spines can run sequentially on one DB
and re-run without duplicate row growth. Domain seed and discover happen once; rank #2 uses
explicit `--fixture` bindings. No production code changes.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-161 |
| Branch | `phase-2/ticket-161-dual-candidate-staged-idempotency` |
| Date | 2026-06-14 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-14_pre-ticket-161_dual-candidate-staged-idempotency-audit.md` (GO) |
| Principal audit gate | `agent_reports/2026-06-14_principal-audit-post-ticket-158.md` |
| Main tip before branch | `59b44cd` |

## Scope

### In

- `tests/unit/test_staged_dual_candidate_idempotency.py` (2 tests)

### Out

- Live network, schema, public export/site, `research run` orchestration

## Stable dual counts

| Metric | Value |
|--------|-------|
| sources | 3 |
| candidate_sources / research_queue | 2 each |
| rank #1 accepted / rejected | 1 / 1 |
| rank #2 accepted / rejected | 1 / 1 |
| relationships with staged claim evidence (each rank) | 2 |
| score_events | 2 |
| run_reports | 2 |
| qualifies evidence | 2 |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Dual spine twice → stable counts | **PASS** |
| 2 | Per-command spot-check idempotent | **PASS** |
| 3 | No live LLM/network in default collection | **PASS** |
| 4 | Golden pass | **PASS** (142) |
| 5 | Full pytest pass | **PASS** (579) |
| 6 | Safety audit pass | **PASS** |
| 7 | ticket-151/160 idempotency tests green | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_dual_candidate_idempotency.py -q   # 2 passed
python -m pytest tests/unit/test_staged_second_candidate_idempotency.py -q   # 2 passed
python -m pytest tests/unit/test_staged_ingest_idempotency.py -q             # 2 passed
python -m pytest tests/golden -q                                            # 142 passed
python -m pytest -q                                                           # 579 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full                               # pass
```

## Merge to main

Merged to `main` as `79d0e81f981fd61fa2af9bd91359d2d8aaf475ce` (2026-06-14).
Post-merge pytest: 579 passed, 6 deselected.

## Recommended next ticket

**ticket-162** — Fixture-mode staged `research run` orchestration spine (mock).

Suggested prompt:

```txt
Write pre-ticket audit for ticket-162, then /rge-run-next-ticket
```
