# Ticket-396 — Surface OpenAI synthesis evaluator status in operator plan

**Date:** 2026-06-24  
**Branch:** `phase-3/ticket-396-openai-evaluator-operator-status`  
**Ticket:** ticket-396  
**Main tip before branch:** `74f13d9ec1328caf3548faf747dbe50ad22e4a8e`  
**Audit gate:** satisfied — `agent_reports/2026-06-24_pre-ticket-396_openai-evaluator-operator-status-audit.md`

## Summary

Added `inspect_openai_synthesis_evaluator_plan_status()` and wired public-safe evaluator
status into `operator_loop` plan JSON (`openai_synthesis_evaluator_status`),
`operator_autocycle` live-canary blocking, and `self_improvement_status`
(`openai_synthesis_review_status`). Mock evaluate is `safe_autonomous`; live canary remains
`review_gated` and is never auto-executed.

## Scope

**In:** plan status inspector, operator_loop recommendations, autocycle block for live
canary, self-improvement spine step + review status, unit tests.

**Out:** Runbook docs (397), live HTTP automation, draft promotion.

## Changed files

| File | Change |
|------|--------|
| `rge/modules/openai_synthesis_evaluator.py` | `inspect_openai_synthesis_evaluator_plan_status`, `load_evaluator_artifact` |
| `rge/modules/operator_loop.py` | Plan field + mock evaluate / live canary recommendations |
| `rge/modules/operator_autocycle.py` | Block `run_openai_synthesis_live_canary` |
| `rge/modules/self_improvement_status.py` | Spine step + `openai_synthesis_review_status` |
| `tests/unit/test_openai_synthesis_evaluator_operator_plan.py` | Operator plan/autocycle coverage |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| Plan JSON includes artifact path, verdict, gates, missing gates, commands, live HTTP review-gated | **PASS** (`live_synthesis_verdict` field name; see deviations) |
| Autocycle never auto-runs live OpenAI HTTP; blocks live canary | **PASS** |
| self_improvement_status includes synthesis handoff spine without secrets | **PASS** |
| Missing artifact recommends mock evaluate; documents live canary command | **PASS** |
| Tests mirror benchmark plan-status patterns | **PASS** |

## Commands run

| Command | Result |
|---------|--------|
| `pytest tests/unit/test_operator_loop.py tests/unit/test_operator_autocycle.py tests/unit/test_self_improvement_status.py tests/unit/test_openai_synthesis_evaluator.py tests/unit/test_openai_synthesis_evaluator_operator_plan.py -q` | **65 passed** |
| `python -m rge.modules.operator_loop --mode plan` | **ok** |
| `python -m rge.cli verify --skip-site` | **pass** |

## Manual CLI verification

Operator plan on working repo includes `openai_synthesis_evaluator_status` when evaluator CLI is wired.

## Spec deviations

- Status fields use `live_synthesis_verdict` and `review_artifact_recommended` instead of
  keys containing `evaluator` to satisfy `assert_no_private_fields` / export key policy.
- `self_improvement_status` uses `openai_synthesis_review_status` (not
  `openai_synthesis_evaluator_status`) for the same reason; operator_loop plan retains
  `openai_synthesis_evaluator_status` per ticket.

## Merge to main

Merge commit: `beb47ac2846a5d13fce37cd65a8b01dc3e3f6159`.

## Recommended next ticket

**ticket-397** — Document live OpenAI evaluator canary runbook and checkpoint.

## Suggested next prompt

```txt
/rge-run-next-ticket
```

Implement ticket-397 on branch `phase-3/ticket-397-openai-evaluator-runbook`.
