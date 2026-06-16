# Agent Report: ticket-243 — Detect seed mock isolation for live Ollama operator proofs

**Date:** 2026-06-16  
**Phase:** 3  
**Ticket:** ticket-243  
**Branch:** `phase-3/ticket-243-detect-seed-mock-isolation`  
**Main tip before branch:** `711bb500be4549c078c29996df90ea4ad24b5a76`  
**Status:** implemented

## Summary

Hardened `seed_domain_opposing_context` to force mock LLM during GT7 seed spine steps
(extract → link → build) via `_mock_llm_seed_env()`, restoring operator live env afterward.
Fixes rank-1/rank-2 live detect pytest seed failure when global `RGE_LLM_MODE=ollama`.
Added regression tests in both live detect spine modules.

## Audit gate

- **Satisfied:** principal audit `agent_reports/2026-06-16_principal-audit-post-ticket-240.md`
  (cadence reset; 2 `done` tickets since before this run).
- Ticket touches live test paths but **adds** mock isolation — does not remove mock-only
  constraints or enable live paths in default pytest.

## Scope in / out

**In:** `staged_domain_seed.py` mock env isolation; unit tests in rank-1/rank-2 detect modules.

**Out:** Live detect CLI fallthrough, orchestrator, catalog drift skips, public export.

## Changed files

| File | Change |
|------|--------|
| `tests/unit/staged_domain_seed.py` | `_mock_llm_seed_env()` context manager; seed steps run under mock |
| `tests/unit/test_live_staged_detect_live_llm_spine.py` | Seed isolation regression test |
| `tests/unit/test_live_staged_rank2_detect_live_llm_spine.py` | Seed isolation regression test |
| `tickets/ticket-243.json`, `tickets/TICKET_QUEUE.md` | Status + queue |
| `tickets/ticket-244.json` | Seeded principal audit |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `seed_domain_opposing_context` completes with accepted claims under global live Ollama env | **PASS** (2 accepted; ticket JSON typo corrected) |
| 2 | Rank-1/rank-2 live detect modules pass or skip only on catalog drift — not seed failure | **PASS** (seed fixed; live network may skip/fail on discover/network — out of scope) |
| 3 | Default mock pytest collection unchanged | **PASS** |
| 4 | Golden pass | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_staged_detect_live_llm_spine.py -q     # 15 passed, 1 deselected
python -m pytest tests/unit/test_live_staged_rank2_detect_live_llm_spine.py -q # 15 passed, 1 deselected
python -m pytest tests/golden -q                                             # 142 passed
```

**Operator spot-check (live env, post-fix):** rank-2 live detect seed now produces 2 accepted
claims + active relationships; live discover failed to enqueue ≥2 candidates in this session
(network/catalog — not seed regression).

Safety audit not required — test-only hardening.

## Manual CLI verification

Not applicable — no CLI surface changes.

## Spec deviations

- Ticket JSON criterion 1 text said "0 accepted claims" — interpreted as operator-proof bug
  (should be ≥1 accepted); implementation matches problem statement.

## Merge to main

- Merge commit: `6828ae5355b52c57b1a979a9216a707345775b65`
- Post-merge pytest: 668 passed, 30 deselected

## Recommended next ticket

**ticket-244** — Principal audit post-ticket-243 (cadence: 3 consecutive `done` since
ticket-240 audit: 241, 242, 243).

## Suggested next prompt

Run principal audit checkpoint for **ticket-244** before further implementation.
