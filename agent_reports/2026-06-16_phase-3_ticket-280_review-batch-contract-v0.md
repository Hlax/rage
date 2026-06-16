# Agent Report: ticket-280 — Agent Lab review_batch contract v0 schema and fixture

**Date:** 2026-06-16  
**Ticket:** ticket-280  
**Branch:** `phase-3/ticket-280-review-batch-contract-v0`  
**Main tip before branch:** `e29780b5b50f6181a378bd74bb2125d7f32ee2cf`  
**Audit gate:** `agent_reports/2026-06-16_pre-ticket-280_review-batch-contract-v0-audit.md` (GO)

## Summary

Added `review_batch_v0.1.0` private contract for Agent Lab principal review passes,
including reporting-spec `model_runtime` metadata, fail-closed validation, and a
minimal fixture. Inventory notes now classify `review_batch.json` as
`agent_lab_private` and downgrade the review_batch gap to shape-defined / persistence deferred.

## Scope

**In:** Contract module, fixture, unit tests, inventory note updates, pre-ticket audit.

**Out:** DB persistence, live Ollama, public atlas export, public-site UI.

## Changed files

| File | Change |
|------|--------|
| `rge/contracts/review_batch_v0.py` | Contract + validator |
| `fixtures/agent_lab/review_batch_v0_minimal.json` | Minimal fixture |
| `tests/unit/test_review_batch_contract.py` | 5 unit tests |
| `rge/modules/atlas_contract_inventory.py` | review_batch export shape + gap/safety notes |
| `rge/contracts/__init__.py` | Re-exports |
| `docs/contracts/research_atlas_export_contract_inventory_v0.{md,json}` | Regenerated |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| review_batch_v0.1.0 with model_runtime envelope | **PASS** |
| Minimal fixture validates; agent_lab_private in inventory | **PASS** |
| Fail-closed unit tests | **PASS** — 5 |
| Golden pass | **PASS** — 142 |
| Full pytest pass | **PASS** — 726 |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_review_batch_contract.py -q  # 5 passed
python -m pytest tests/golden -q                              # 142 passed
python -m pytest -q                                           # 726 passed, 30 deselected
```

Safety audit not required — private contract shape only; no export route changes.

## Manual CLI verification

Not performed — contract validation covered by unit tests.

## Spec deviations

None.

## Merge to main

Merge commit: `6848091798c2268a750564180e8c55be6161036d`

## Recommended next ticket

**ticket-281** — Research question lineage fields on atlas snapshot `runs` projection v0.

## Suggested next prompt

```txt
/rge-run-next-ticket
```
