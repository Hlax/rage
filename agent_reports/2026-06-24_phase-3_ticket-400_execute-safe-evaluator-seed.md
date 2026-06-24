# Ticket-400 — Execute-safe mock OpenAI synthesis evaluator seed hook

**Date:** 2026-06-24  
**Branch:** `phase-3/ticket-400-execute-safe-evaluator-seed`  
**Ticket:** ticket-400  
**Main tip before branch:** `1efcb067d2be7d0a91f5bb6080089cb5bc7ab9d6`  
**Audit gate:** satisfied — `agent_reports/2026-06-24_pre-ticket-400_execute-safe-evaluator-seed-audit.md` (GO)

## Summary

Added `run_openai_synthesis_evaluator_execute_safe_hook()` mirroring the synthesis
packet benchmark execute-safe pattern. After verification passes when the recommended
action is `run_openai_synthesis_evaluator`, execute-safe seeds the gitignored evaluator
artifact from an existing canary JSON or mock-cloud synthesis of the grounded fixture.

## Scope

**In:** execute-safe hook, operator_loop wiring, unit tests, pre-ticket audit.

**Out:** Live HTTP, autocycle auto-execution, draft bridge, graph writes.

## Changed files

| File | Change |
|------|--------|
| `rge/modules/openai_synthesis_evaluator.py` | `run_openai_synthesis_evaluator_execute_safe_hook` |
| `rge/modules/operator_loop.py` | Post-verify hook when `action_id == run_openai_synthesis_evaluator` |
| `tests/unit/test_openai_synthesis_evaluator_operator_plan.py` | Seed/skip path tests |
| `agent_reports/2026-06-24_pre-ticket-400_execute-safe-evaluator-seed-audit.md` | Pre-ticket audit GO |
| `tickets/ticket-400.json` | Status `done` |
| `tickets/ticket-401.json` | Proposed README cross-link |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Execute-safe mock evaluate when `review_artifact_recommended` and canary/fixture available | **PASS** |
| Never live HTTP; never accepted graph writes | **PASS** (`mock_cloud` only; `live_http_used: false`) |
| Autocycle/verify unchanged when hook skipped | **PASS** |
| Unit tests cover seed/skip without host `OPENAI_API_KEY` | **PASS** |

## Commands run

| Command | Result |
|---------|--------|
| `pytest tests/unit/test_openai_synthesis_evaluator_operator_plan.py tests/unit/test_operator_loop.py -q` | **52 passed** |
| `python -m rge.cli verify --skip-site` | **pass** |

## Manual CLI verification

Not run — unit tests cover hook orchestration; execute-safe remains mock-only.

## Spec deviations

None.

## Merge to main

Merge commit: *(pending merge)*.

## Recommended next ticket

**ticket-401** — README execute-safe OpenAI evaluator seed hook cross-link v0.

## Suggested next prompt

```txt
/rge-run-next-ticket
```
