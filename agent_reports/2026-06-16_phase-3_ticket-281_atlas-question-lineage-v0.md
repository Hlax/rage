# Agent Report: ticket-281 — Atlas snapshot runs question lineage v0

**Date:** 2026-06-16  
**Ticket:** ticket-281  
**Branch:** `phase-3/ticket-281-atlas-question-lineage-v0`  
**Main tip before branch:** `3254ece`  
**Audit gate:** `agent_reports/2026-06-16_pre-ticket-281_atlas-question-lineage-v0-audit.md` (GO)

## Summary

Extended atlas `runs[]` projection with optional research-question lineage fields sourced
from `research_contracts`, `research_queue`, and `cluster_reports`. Root runs expose
`research_question_id` and `parent_question_id: null`; follow-up runs (non-root for the
same contract) add spawn metadata from the prior run's cluster report and queue reason.
Private-field scanner allowlists intentional lineage key names (including
`spawned_from_claim_ids` opaque ID lists).

## Scope

**In:** Builder lineage helpers, contract constants, creativity fixture regeneration,
builder tests, inventory gap downgrade, regenerate script.

**Out:** Schema migrations, public-site UI, live Ollama, review_batch persistence.

## Changed files

| File | Change |
|------|--------|
| `rge/modules/atlas_snapshot_builder.py` | Lineage projection + allowlist |
| `rge/contracts/atlas_snapshot_v0.py` | `ATLAS_RUN_LINEAGE_OPTIONAL_FIELDS` |
| `rge/contracts/__init__.py` | Re-export |
| `fixtures/atlas/atlas_snapshot_v0_creativity_fixture.json` | Root run lineage fields |
| `tests/unit/test_atlas_snapshot_builder.py` | 2 lineage tests (6 total) |
| `scripts/regenerate_atlas_creativity_fixture.py` | Fixture regen helper |
| `rge/modules/atlas_contract_inventory.py` | Lineage gap severity low |

## Acceptance criteria

| Criterion | Status |
|-----------|--------|
| runs[] optional lineage when contract data exists | **PASS** |
| Creativity fixture updated deterministically | **PASS** |
| validate_atlas_snapshot + no private leak | **PASS** |
| Golden + full pytest | **PASS** — 142 golden, 728 full |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_atlas_snapshot_builder.py -q  # 6 passed
python -m pytest tests/golden -q                              # 142 passed
python -m pytest -q                                           # 728 passed, 30 deselected
```

Safety audit not required — private atlas projection only; no public export route changes.

## Manual CLI verification

Regenerated fixture via `python scripts/regenerate_atlas_creativity_fixture.py`.
Root run in fixture includes `research_question_id` and `parent_question_id: null`.

## Spec deviations

- `spawned_from_*` fields omitted on root runs (cluster report is output, not spawn parent).
- Follow-up spawn lineage tested via synthetic second `research_runs` row (not yet in fixture MVP).

## Merge to main

*(pending merge)*

## Recommended next ticket

**ticket-282** — Private atlas snapshot export CLI (operator writes validated snapshot JSON from DB).

## Suggested next prompt

```txt
/rge-run-next-ticket
```
