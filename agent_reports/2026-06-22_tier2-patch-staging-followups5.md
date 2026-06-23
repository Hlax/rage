# Tier 2 patch staging follow-ups batch 5

**Date:** 2026-06-22  
**Scope:** Execute-safe hook chain, draft status revalidation row, golden fixture shape  
**Verdict:** GO

## Summary

1. **Execute-safe hook chain** — `run_execute_safe_tier2_hook_chain()` runs backfill first; when the tree transitions from clean to controlled-dirty, patch staging hook runs in the same pass. `execute_safe_checks` and autocycle surface `execute_safe_tier2_hook_chain` plus legacy `backfill` / `patch_staging` keys.

2. **Draft status inspect row** — `inspect_instruction_packet_ticket_draft_status()` and operator plan JSON now include `last_patch_revalidation` and `expected_files_backfilled_at` from the latest draft ticket.

3. **Golden fixture shape** — committed `atlas_tier2_patch_staging_latest.json` includes optional `patch_revalidation_summary: null`; golden test validates field presence and shape.

## Files changed

| Area | File |
|------|------|
| Hook chain | `rge/modules/instruction_packet_ticket_draft.py` |
| Plan + execute-safe | `rge/modules/operator_loop.py` |
| Autocycle | `rge/modules/operator_autocycle.py` |
| Committed fixture | `apps/public-site/public/data/atlas_tier2_patch_staging_latest.json` |
| Golden test | `tests/golden/test_12_public_site_static_render.py` |
| Unit tests | `tests/unit/test_tier2_patch_staging_followups5.py` |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_tier2_patch_staging_followups5.py tests/golden/test_12_public_site_static_render.py -q
python -m rge.modules.safety_auditor --audit full
cd apps/public-site && npm run build
```

## Operator notes

- Enable both hooks: `RGE_EXECUTE_SAFE_DRAFT_BACKFILL=1` and `RGE_EXECUTE_SAFE_PATCH_STAGING=1`
- Chain fires only when backfill completes and post-backfill tree is controlled-dirty (typically `data/operator/draft_tickets/` writes)
- Plan mode: `instruction_packet_ticket_draft_status.last_patch_revalidation` surfaces post-backfill validation without reading private draft paths

## Next recommended packets

- Operator UI row for `last_patch_revalidation` on atlas-preview synthesis/draft panel
- Autocycle multi-cycle: re-plan after chained hook completes to pick up next tier2 action
- Document hook chain in README Operator Quickstart tier2 table
