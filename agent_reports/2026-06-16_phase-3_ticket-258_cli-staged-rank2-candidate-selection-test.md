# Agent Report: ticket-258 — CLI staged spine rank-2 candidate selection unit test

**Date:** 2026-06-16  
**Phase:** 3  
**Ticket:** ticket-258  
**Branch:** `phase-3/ticket-258-cli-staged-rank2-candidate-selection-test`  
**Main tip before branch:** `6172c5aa8e6f132d2edbf370b87ce5caa35ea420`  
**Status:** done

## Summary

Added `tests/unit/test_cli_staged_rank2_candidate_selection.py` to cover
`_staged_rank_candidate_ids` in `rge/cli.py` with synthetic `candidate_sources`
rows. The tests Assert both the default heuristic rank-2 id and the effect of
`RGE_STAGED_RANK2_SCAN_MAX` overrides on the CLI orchestrator path.

## Audit gate

- **Satisfied:** `agent_reports/2026-06-16_principal-audit-post-ticket-257.md`
  (ticket-259); cadence satisfied; `risk_level: low`.

## Scope in / out

**In:**

- CLI helper `_staged_rank_candidate_ids` exercised under temp DB.
- Env-backed scan window override via `RGE_STAGED_RANK2_SCAN_MAX`.
- Unit tests only; no production code changes beyond existing helper.

**Out:**

- Live Ollama proofs.
- Operator loop/autocycle plan changes.
- Public export or site changes.
- Orchestrator live LLM.

## Changed files

| File | Change |
|------|--------|
| `tests/unit/test_cli_staged_rank2_candidate_selection.py` | New unit tests for `_staged_rank_candidate_ids` default + env override |
| `tickets/ticket-258.json`, `TICKET_QUEUE.md` | Status + queue (done) |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Unit test covers `_staged_rank_candidate_ids` rank-2 id with synthetic candidates | **PASS** |
| 2 | Env-backed scan window override is exercised via `RGE_STAGED_RANK2_SCAN_MAX` | **PASS** |
| 3 | Golden + full pytest pass | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_cli_staged_rank2_candidate_selection.py -q  # 2 passed
python -m pytest tests/golden -q                                            # 142 passed
python -m pytest -q                                                         # 687 passed, 30 deselected
```

Safety audit not required — CLI test-only ticket; no surface changes.

## Manual CLI verification

Not performed — behavior is covered by unit tests plus existing staged selection
tests (`test_staged_rank2_candidate_heuristic_scan.py`,
`tests/unit/live_staged_candidates.py`).

## Spec deviations

None.

## Merge to main

- Merge commit: `9a6f0440879f6e8bf3aa4e3ffd5f01fc903f8f66`
- Post-merge pytest: `687 passed, 30 deselected`
- Push: `origin/main` updated

## Recommended next ticket

Cadence window now has one done ticket since checkpoint-257 (ticket-259). Next
implementation ticket should either:

- Extend rank-2 product tests (e.g. staged spine end-to-end CLI smoke on temp DB), or  
- Advance a small product-facing ticket outside staged spine to rebalance value mix.

## Suggested next prompt

```txt
/rge-run-next-ticket
```

