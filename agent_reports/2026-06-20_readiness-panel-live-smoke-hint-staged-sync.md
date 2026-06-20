# Agent report — Readiness panel, live smoke hint, staged source-health sync

**Date:** 2026-06-20  
**Branch:** `phase-4/packets-002-004-evidence-quality-extraction`  
**Packets:** Atlas Readiness Panel · Operator Loop Combined Live Smoke Recommendation · Staged Spine Source-Health Artifact Sync

## Live combined smoke (operator opt-in)

```powershell
$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"
$env:RGE_ALLOW_LIVE_QUERY_EXPANSION_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_network_combined_source_health_smoke.py -m live_network -q
```

**Result:** 1 passed (1.68s)

## Summary

1. **Atlas Readiness Panel from Run Artifact** — `/atlas-preview` adds a dedicated readiness section via `resolveReadinessPanelPreview()`. Run artifact mode lists `readiness_warnings`; fixture mode shows readiness surfaces from `tiny_atlas_connection_preview.json`.
2. **Operator Loop Combined Live Smoke Recommendation** — plan mode surfaces `live_combined_source_health_smoke_status` and recommends `run_live_combined_source_health_smoke` when source-health work is detected but combined live gates are unset.
3. **Staged Spine Source-Health Artifact Sync** — `export_staged_spine_source_health_artifact()` bridges staged temp DB → `atlas_source_health_run_latest.json`. `refresh_atlas_preview_from_staged_spine.py` syncs by default (`RGE_SYNC_STAGED_SOURCE_HEALTH=1`; set `0` to skip).

## Files changed

- `apps/public-site/lib/atlasPreview.ts`
- `apps/public-site/app/atlas-preview/page.tsx`
- `rge/modules/operator_loop.py`
- `rge/modules/atlas_preview_curator.py`
- `rge/modules/live_arbitrary_source_health.py`
- `scripts/refresh_atlas_preview_from_staged_spine.py`
- `tests/unit/test_atlas_source_health_run_preview.py`
- `tests/unit/test_operator_loop_plan.py`
- `tests/unit/test_staged_spine_source_health_sync.py`
- `README.md`

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_atlas_source_health_run_preview.py tests/unit/test_operator_loop_plan.py tests/unit/test_staged_spine_source_health_sync.py -q
# 14 passed

cd apps/public-site; npm run build
# pass

python -m rge.modules.safety_auditor --audit full
# pass
```

## Next recommended packets

1. **Atlas Purpose Panel from Run Artifact** — dedicated purpose/affordance panel separate from question header.
2. **Operator Loop Staged Refresh Single Command** — unify staged snapshot + source-health refresh in one plan action when both are stale.
3. **Live Staged Spine Source-Health Coherence** — opt-in pytest asserting staged orchestrator temp export matches public source-health artifact thresholds.
