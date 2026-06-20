# Agent report — Atlas question header, operator refresh hook, combined live smoke

**Date:** 2026-06-20  
**Branch:** `phase-4/packets-002-004-evidence-quality-extraction`  
**Packets:** Atlas Question Header from Run Artifact · Operator Loop Refresh Hook · Live Source-Health + Query-Expansion Combined Smoke

## Summary

1. **Atlas Question Header from Run Artifact** — `/atlas-preview` now prefers `atlas_source_health_run_latest.json` for the page title, subtitle, and research-question header panel via `resolveQuestionHeaderPreview()` / `mapRunArtifactToQuestionHeader()` in `apps/public-site/lib/atlasPreview.ts`.
2. **Operator Loop Refresh Hook** — `inspect_atlas_preview_refresh_status()` surfaces missing/stale public preview JSON in plan mode; `refresh_atlas_public_previews` is recommended when no open ticket blocks refresh.
3. **Live Combined Smoke** — `assert_live_combined_source_health_smoke_env()` and `run_live_combined_source_health_query_expansion_smoke()` chain full-question query expansion with live source-health persistence.

## Files changed

- `apps/public-site/lib/atlasPreview.ts`
- `apps/public-site/app/atlas-preview/page.tsx`
- `rge/modules/operator_loop.py`
- `rge/modules/live_arbitrary_source_health.py`
- `tests/unit/test_atlas_source_health_run_preview.py`
- `tests/unit/test_operator_loop_plan.py`
- `tests/unit/test_live_network_combined_source_health_smoke.py`
- `README.md`

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_atlas_source_health_run_preview.py tests/unit/test_operator_loop_plan.py tests/unit/test_live_network_combined_source_health_smoke.py::test_live_combined_source_health_smoke_blocked_without_opt_in -q
# 12 passed

cd apps/public-site; npm run build
# pass

python -m rge.modules.safety_auditor --audit full
# pass
```

**Live combined smoke (operator opt-in; not run in this session):**

```powershell
$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"
$env:RGE_ALLOW_LIVE_QUERY_EXPANSION_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_network_combined_source_health_smoke.py -m live_network -q
```

## Next recommended packets

1. **Atlas Readiness Panel from Run Artifact** — surface `readiness_warnings` as a dedicated panel (beyond gaps/next-move).
2. **Operator Loop Combined Live Smoke Recommendation** — plan-mode hint when both live smoke gates are unset after source-health work.
3. **Staged Spine Source-Health Artifact Sync** — optional bridge from staged orchestrator temp export to `atlas_source_health_run_latest.json`.
