---
template_id: implementation_report
status: done
date: 2026-06-15
phase: 2
ticket: ticket-229
---

# ticket-229: Rank-2 Staged Source and Chunk Heuristic for Live LLM Fallthrough Eligibility

## Summary

Added `rge/modules/staged_spine_heuristics.py` with public rank-2 staged OpenAlex
source/chunk helpers (`constraint management` markers aligned with W1234567890 fixture).
Rank-1 pipeline auto-mock routing is unchanged; rank-2 helpers are separate for future
live fallthrough tickets (230+). Seven unit tests prove rank-1/rank-2 disjointness.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-229 |
| Branch | `phase-2/ticket-229-rank-2-staged-spine-heuristics` |
| Date | 2026-06-15 |
| Risk | medium |
| Audit gate | satisfied — `agent_reports/2026-06-15_pre-ticket-228_rank-2-staged-live-llm-audit.md` hardened scope for ticket-229 |
| Main tip before branch | `9fad348` |

## Scope

**In:** New heuristic module; unit tests; rank-1 reference helpers in same module for test parity.

**Out:** Live Ollama fallthrough wiring, env gates, CLI flags, rank-1 heuristic changes, orchestrator changes.

## Changed files

| File | Change |
|------|--------|
| `rge/modules/staged_spine_heuristics.py` | Rank-1/rank-2 public heuristic helpers |
| `tests/unit/test_staged_rank2_spine_heuristics.py` | 7 unit tests |
| `tickets/ticket-229.json` | Status `done` |
| `tickets/ticket-230.json` | Seeded rank-2 live extract |
| `tickets/TICKET_QUEUE.md` | Mark 229 done; seed 230 |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Rank-2 helpers match OpenAlex fixture markers | **PASS** |
| 2 | Rank-1 heuristics unchanged; rank-2 separate public functions | **PASS** |
| 3 | Unit tests positive rank-2 and negative rank-1 | **PASS** (7 tests) |
| 4 | Golden pass; no live Ollama pytest | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_rank2_spine_heuristics.py -q  # 7 passed
python -m pytest tests/golden -q                                       # 142 passed
python -m pytest -q                                                    # 628 passed, 20 deselected
```

Safety audit not required — heuristic module only; no public export or runtime fallthrough.

## Manual CLI verification

Not performed — no CLI changes.

## Spec deviations

Pre-ticket-228 mentioned wiring into fallthrough validators in ticket-229; ticket JSON
non_goals defer wiring to ticket-230+. Heuristic-only delivery matches ticket JSON
`expected_files`.

## Merge to main

Merge commit: `3493fc0` (`Merge branch 'phase-2/ticket-229-rank-2-staged-spine-heuristics'`).
Post-merge pytest: 628 passed, 20 deselected.

## Recommended next ticket

**ticket-230** — Live staged rank-2 extract live LLM opt-in proof (per-step; medium).

## Suggested next prompt

`/rge-run-next-ticket` for **ticket-230**, or pause for rank-1 operator live proofs.
