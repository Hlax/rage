# Agent Report: ticket-251 — Rank-2 staged candidate heuristic scan

**Date:** 2026-06-16  
**Phase:** 3  
**Ticket:** ticket-251  
**Branch:** `phase-3/ticket-251-rank-2-candidate-heuristic-scan`  
**Main tip before branch:** `373e5141aba2faddc7abcc145fbb6c4f09394fa2`  
**Status:** implemented

## Summary

Added `rge/modules/staged_candidate_selection.py` with top-N rank-2 title heuristic
scan (`constraint management`) starting after rank-1. Live rank-2 pytest helpers and
live-discover staged orchestrator now share the helper. Pre-fetch skip JSON includes
`scanned_candidates` when no title match exists.

## Audit gate

- **Satisfied:** `agent_reports/2026-06-16_pre-ticket-251_rank-2-staged-candidate-heuristic-scan-audit.md` (medium risk pre-ticket audit GO)

## Scope in / out

**In:** Production selection module, CLI orchestrator rank-2 path, live test helper, unit tests.

**Out:** Live Ollama gates, orchestrator live LLM, reconcile/report live LLM, CI live_network, schema migrations, docs duplication.

## Changed files

| File | Change |
|------|--------|
| `rge/modules/staged_candidate_selection.py` | Rank-1/rank-2 selection + `Rank2StagedCandidateNotFoundError` |
| `rge/cli.py` | `_staged_rank_candidate_ids` uses heuristic scan for rank-2 |
| `tests/unit/live_staged_candidates.py` | `select_rank2_candidate_id` delegates + pytest skip |
| `tests/unit/test_staged_rank2_candidate_heuristic_scan.py` | Unit tests |
| `tickets/ticket-251.json`, `TICKET_QUEUE.md` | Status + queue |
| `tickets/ticket-252.json` | Scratch evidence autocycle follow-on seeded |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `select_rank2_staged_candidate_id` scans top-N after rank-1 for title heuristic | **PASS** |
| 2 | Live rank-2 pytest spines use heuristic scan; skip when no match | **PASS** |
| 3 | Staged orchestrator rank-2 uses same helper on live discover path | **PASS** |
| 4 | Rank-1 OFFSET 0 unchanged; `unsuitable_live_rank2_artifact` preserved | **PASS** |
| 5 | Unit tests: scan success, skip payload, rank-1 isolation | **PASS** |
| 6 | Golden + default pytest mock-only | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_staged_rank2_candidate_heuristic_scan.py -q  # 5 passed
python -m pytest tests/golden -q                                              # 142 passed
python -m pytest -q                                                             # 674 passed, 30 deselected
```

Safety audit not required — staged candidate selection only; no public export surface.

## Manual CLI verification

Not performed — selection logic covered by unit tests; live network proofs remain operator opt-in.

## Spec deviations

None.

## Merge to main

- Merge commit: `bf962db284842f12ed9eb1d35f2983ab2289e1f8`
- Post-merge pytest: **674 passed**, 30 deselected

## Recommended next ticket

**ticket-252** — Scratch evidence review gate in operator autocycle plan (low risk product/operator).

## Suggested next prompt

`/rge-run-next-ticket` for **ticket-252** or operator rank-2 live re-proof out-of-band.
