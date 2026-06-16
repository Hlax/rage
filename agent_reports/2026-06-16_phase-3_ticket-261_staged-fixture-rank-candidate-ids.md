# Agent Report: ticket-261 — Staged fixture run JSON exposes rank candidate ids

**Date:** 2026-06-16  
**Phase:** 3  
**Ticket:** ticket-261  
**Branch:** `phase-3/ticket-261-staged-fixture-rank-candidate-ids-json`  
**Main tip before branch:** `5fc72ac90d9d92500d256a54fefec7a6ff8d807a`  
**Status:** done

## Summary

Extended `execute_staged_fixture_mode_run` result JSON with `rank1_candidate_id` and
`rank2_candidate_id`, derived from the same `candidate_pairs` used for fetch wiring.
Updated staged spine candidate-id wiring tests to assert both default and live-orchestrator
paths populate the new fields.

## Audit gate

- **Satisfied:** `agent_reports/2026-06-16_principal-audit-post-ticket-258.md`; cadence satisfied (2 done since checkpoint-258); `risk_level: low`

## Scope in / out

**In:** Result payload fields + unit test assertions.

**Out:** Live Ollama, public export/site, selection heuristics changes.

## Changed files

| File | Change |
|------|--------|
| `rge/cli.py` | Expose `rank1_candidate_id` / `rank2_candidate_id` in staged fixture run result |
| `tests/unit/test_cli_staged_spine_candidate_id_wiring.py` | Assert result fields on default + live-orchestrator paths |
| `tickets/ticket-261.json`, `TICKET_QUEUE.md` | Status + queue |
| `tickets/ticket-262.json` | Follow-on seeded |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Result includes `rank1_candidate_id` and `rank2_candidate_id` | **PASS** |
| 2 | Unit test asserts both paths populate fields | **PASS** |
| 3 | Golden pass | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_cli_staged_spine_candidate_id_wiring.py -q  # 2 passed
python -m pytest tests/golden -q                                            # 142 passed
python -m pytest -q                                                         # 689 passed, 30 deselected
```

Safety audit not required — CLI result JSON only; no public export or site changes.

## Manual CLI verification

Not performed — unit tests exercise `execute_staged_fixture_mode_run` with mocked network.

## Spec deviations

None.

## Merge to main

- Merge commit: `3e9e895902e85ffc29e7eae1f5de6de3fe9f280b`
- Post-merge pytest: `689 passed, 30 deselected`

## Recommended next ticket

**ticket-262** — Staged fixture spine idempotency test asserts rank candidate ids in result.

## Suggested next prompt

```txt
/rge-run-next-ticket
```
