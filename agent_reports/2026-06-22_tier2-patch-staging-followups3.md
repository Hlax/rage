# Tier 2 patch staging follow-ups batch 3

**Date:** 2026-06-22  
**Scope:** Operator loop backfill recommendation, post-backfill patch revalidation hook, Atlas validation verdict badge  
**Verdict:** GO

## Summary

Three operator-facing hardening items for the Tier 2 patch staging airlock:

1. **Operator loop backfill recommendation** — plan mode now surfaces `run_draft_expected_files_backfill` (`safe_autonomous`) when `draft_expected_files_backfill_recommended` is true, ahead of patch staging actions. Synthesis governor status merges draft backfill flags and commands; local implementation handoff is suppressed until backfill completes.

2. **Re-validate staged bundles after backfill** — when draft `expected_files` change, optional hook re-runs patch bundle validation and syncs the Atlas preview. Controlled by `RGE_REVALIDATE_PATCH_AFTER_BACKFILL` (default `1`).

3. **Atlas GO/PARTIAL/NO-GO verdict badge** — color-coded validation verdict pill rendered alongside the existing freshness badge on `/atlas-preview` Tier 2 panel.

## Files changed

| Area | File |
|------|------|
| Operator loop | `rge/modules/operator_loop.py` |
| Autocycle safe actions | `rge/modules/operator_autocycle.py` |
| Synthesis governor merge | `rge/modules/autonomous_synthesis_governor.py` |
| Backfill + revalidation hook | `rge/modules/instruction_packet_ticket_draft.py` |
| Revalidation helper | `rge/modules/tier2_patch_staging.py` |
| Atlas UI | `apps/public-site/lib/atlasPreview.ts`, `apps/public-site/app/atlas-preview/page.tsx` |
| Env | `.env.example` |
| Tests | `tests/unit/test_tier2_patch_staging_followups3.py`, `tests/unit/test_tier2_local_implementation.py` |

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_tier2_patch_staging_followups3.py tests/golden/test_12_public_site_static_render.py -q
python -m rge.modules.safety_auditor --audit full
cd apps/public-site && npm run build
```

| Check | Result |
|-------|--------|
| followups3 + golden site render | 16 passed |
| safety audit full | pass |
| public-site build | pass |

## Operator notes

- **Backfill command:** `python scripts/run_draft_expected_files_backfill.py --latest`
- **Disable post-backfill revalidation:** `RGE_REVALIDATE_PATCH_AFTER_BACKFILL=0`
- **Action priority:** backfill → fix patch → validate → refresh preview → apply → stage

## Next recommended packets

- Wire backfill into execute-safe autocycle when draft backfill is the only blocker
- Surface `patch_revalidation` summary in Atlas preview artifact
- Add operator loop test for backfill vs fix_tier2_patch_staging priority when both apply
