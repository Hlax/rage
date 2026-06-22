# Tier 2 patch staging follow-ups batch 4

**Date:** 2026-06-22  
**Scope:** Execute-safe draft backfill hook, Atlas patch revalidation summary, backfill vs fix priority test  
**Verdict:** GO

## Summary

1. **Execute-safe draft backfill hook** — when `run_draft_expected_files_backfill` is the plan blocker and `RGE_EXECUTE_SAFE_DRAFT_BACKFILL=1`, execute-safe runs backfill after verification passes. Autocycle surfaces `draft_backfill_execute_safe_hook` on success.

2. **Atlas patch revalidation summary** — backfill persists `last_patch_revalidation` on the draft ticket; preview builder exposes `patch_revalidation_summary` (status, verdict, reason count, backfilled_at). Tier 2 panel shows a **Post-backfill revalidation** metric when present.

3. **Priority test** — confirms backfill is recommended ahead of `fix_tier2_patch_staging` when both a NO-GO/PARTIAL bundle and uninferred draft exist.

## Files changed

| Area | File |
|------|------|
| Backfill hook + draft persistence | `rge/modules/instruction_packet_ticket_draft.py` |
| Atlas artifact field | `rge/modules/tier2_patch_staging_preview.py` |
| Execute-safe wiring | `rge/modules/operator_loop.py` |
| Autocycle hook surface | `rge/modules/operator_autocycle.py` |
| Atlas UI + types | `apps/public-site/lib/atlasPreview.ts`, `apps/public-site/app/atlas-preview/page.tsx` |
| Env | `.env.example` |
| Tests | `tests/unit/test_tier2_patch_staging_followups4.py` |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_tier2_patch_staging_followups4.py tests/unit/test_tier2_patch_staging_followups3.py tests/golden/test_12_public_site_static_render.py -q
python -m rge.modules.safety_auditor --audit full
cd apps/public-site && npm run build
```

| Check | Result |
|-------|--------|
| followups3 + followups4 + golden | 21 passed |
| safety audit full | pass |
| public-site build | pass |

## Operator notes

- Enable autocycle backfill: `RGE_EXECUTE_SAFE_DRAFT_BACKFILL=1`
- Hook runs only when plan blocker is `run_draft_expected_files_backfill` (not when fix/validate/stage is higher priority)
- Post-backfill revalidation still controlled by `RGE_REVALIDATE_PATCH_AFTER_BACKFILL`

## Next recommended packets

- Chain execute-safe: backfill hook then patch staging hook in one pass when tree becomes controlled-dirty
- Operator loop plan summary row for `last_patch_revalidation` on draft status inspect
- Golden test asserting committed `atlas_tier2_patch_staging_latest.json` shape includes optional `patch_revalidation_summary`
