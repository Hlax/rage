# Tier 2 Patch Staging Follow-ups (Validate Sync, Freshness Badge, Draft Backfill)

**Date:** 2026-06-22  
**Verdict:** GO

## Summary

Implemented three follow-up packets:

1. **Validate-only preview auto-sync** — `--validate` re-runs gates then refreshes Atlas preview
2. **Atlas freshness badge styling** — stale/missing preview highlighted on `/atlas-preview`
3. **Draft expected_files backfill command** — re-infer paths on existing drafts without re-handoff

## 1. Validate-only preview auto-sync

`run_tier2_patch_staging_command(validate_only=True)` now calls `_maybe_sync_patch_staging_preview()` after writing updated `bundle.json` / `validation.json`.

CLI payload includes `preview_sync` when auto-sync runs (`RGE_AUTO_SYNC_TIER2_PATCH_PREVIEW=1`, default on).

```powershell
python scripts/run_tier2_patch_staging.py --bundle PATH --validate
```

## 2. Atlas freshness badge

`/atlas-preview` Tier 2 panel shows a pill badge via:

- `tier2PatchFreshnessBadgeColor()` — green (fresh), amber (stale), red (missing)
- `tier2PatchFreshnessBadgeLabel()` — operator-facing label including “refresh recommended/required”

## 3. Draft expected_files backfill

**CLI:** `scripts/run_draft_expected_files_backfill.py`

```powershell
python scripts/run_draft_expected_files_backfill.py --latest
python scripts/run_draft_expected_files_backfill.py --draft-ticket PATH
python scripts/run_draft_expected_files_backfill.py --all
python scripts/run_draft_expected_files_backfill.py --latest --dry-run
```

Re-parses linked instruction packet when available; otherwise rebuilds parser input from draft fields. Writes `expected_files_inferred: true` and `expected_files_backfilled_at` on update.

`inspect_instruction_packet_ticket_draft_status()` surfaces `draft_expected_files_backfill_recommended` when latest draft lacks inferred files.

## Tests run

```powershell
python -m pytest tests/unit/test_tier2_patch_staging_followups2.py -q
python -m pytest tests/golden/test_12_public_site_static_render.py -q
```

**Result:** 7 new unit tests + golden static render pass.

## Safety audit

```powershell
python -m rge.modules.safety_auditor --audit full
```

**Result:** pass

## Public-site build

```powershell
cd apps/public-site && npm run build
```

**Result:** pass

## Files touched

- `rge/modules/tier2_patch_staging.py`
- `rge/modules/instruction_packet_ticket_draft.py`
- `scripts/run_draft_expected_files_backfill.py` (new)
- `apps/public-site/lib/atlasPreview.ts`
- `apps/public-site/app/atlas-preview/page.tsx`
- `tests/unit/test_tier2_patch_staging_followups2.py` (new)
- `tests/golden/test_12_public_site_static_render.py`

## Next recommended packets

1. **Operator loop backfill recommendation** — surface `run_draft_expected_files_backfill` in plan when backfill recommended
2. **Re-validate staged bundles after backfill** — optional hook to refresh patch validation when draft expected_files change
3. **Atlas GO/PARTIAL/NO-GO verdict badge** — color-coded validation verdict pill alongside freshness
