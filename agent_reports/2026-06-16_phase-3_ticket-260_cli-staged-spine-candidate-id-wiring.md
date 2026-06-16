# Agent Report: ticket-260 — Staged spine CLI candidate-id wiring smoke test

**Date:** 2026-06-16  
**Phase:** 3  
**Ticket:** ticket-260  
**Branch:** `phase-3/ticket-260-cli-staged-spine-candidate-id-wiring`  
**Main tip before branch:** `1f389409c106117088660dfc62642a4bcd230d3b`  
**Status:** done

## Summary

Added `tests/unit/test_cli_staged_spine_candidate_id_wiring.py` to smoke-test staged
fixture-mode orchestrator candidate-id wiring on a temp DB. Default path uses hardcoded
fixture candidate IDs; live-orchestrator path calls `_staged_rank_candidate_ids` and
wires heuristic-selected IDs into `fetch-candidate` steps.

## Audit gate

- **Satisfied:** `agent_reports/2026-06-16_principal-audit-post-ticket-258.md`; cadence satisfied; `risk_level: low`

## Scope in / out

**In:** Unit smoke tests recording `fetch-candidate --candidate` argv wiring.

**Out:** Production logic changes, live Ollama, public export/site, schema migrations.

## Changed files

| File | Change |
|------|--------|
| `tests/unit/test_cli_staged_spine_candidate_id_wiring.py` | Default + live-orchestrator wiring smoke tests |
| `tickets/ticket-260.json`, `TICKET_QUEUE.md` | Status + queue |
| `tickets/ticket-261.json` | Follow-on seeded |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Fixture-mode staged spine helper path on temp DB with deterministic candidate-id wiring | **PASS** |
| 2 | No production logic changes | **PASS** |
| 3 | Golden pass | **PASS** |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_cli_staged_spine_candidate_id_wiring.py -q  # 2 passed
python -m pytest tests/golden -q                                            # 142 passed
python -m pytest -q                                                         # 689 passed, 30 deselected
```

Safety audit not required — test-only ticket.

## Manual CLI verification

Not performed — smoke tests exercise `execute_staged_fixture_mode_run` with mocked network.

## Spec deviations

None.

## Merge to main

- Merge commit: `39b85deb9b4b8c82df5680d6be3b54635b125ffe`
- Post-merge pytest: `689 passed, 30 deselected`

## Recommended next ticket

**ticket-261** — Staged fixture run JSON exposes rank candidate ids in result payload.

## Suggested next prompt

```txt
/rge-run-next-ticket
```
