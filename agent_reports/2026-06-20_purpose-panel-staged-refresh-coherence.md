# Agent report — Purpose panel, staged single refresh, live source-health coherence

**Date:** 2026-06-20  
**Branch:** `phase-4/packets-002-004-evidence-quality-extraction`  
**Packets:** Atlas Purpose Panel · Operator Loop Staged Refresh Single Command · Live Staged Spine Source-Health Coherence

## Summary

1. **Atlas Purpose Panel from Run Artifact** — `/atlas-preview` adds a dedicated purpose section via `resolvePurposePanelPreview()` / `mapRunArtifactToPurposePanel()`: research intents, affordances, evidence need, maturity/training, output targets, and purpose-fit/gate counts from the run artifact.
2. **Operator Loop Staged Refresh Single Command** — `atlas_preview_refresh_status` now exposes `single_refresh_recommended`; plan mode `refresh_atlas_public_previews` prefers one `refresh_atlas_preview_from_staged_spine.py` command (syncs snapshot + coherence + source-health) plus site build when staged outputs are stale.
3. **Live Staged Spine Source-Health Coherence** — `test_live_staged_spine_source_health_coherence.py` asserts staged temp DB `source_health_preview` matches `export_staged_spine_source_health_artifact` (mock default pytest + opt-in `live_network` layer).

## Files changed

- `apps/public-site/lib/atlasPreview.ts`
- `apps/public-site/app/atlas-preview/page.tsx`
- `rge/modules/operator_loop.py`
- `tests/unit/test_atlas_source_health_run_preview.py`
- `tests/unit/test_operator_loop_plan.py`
- `tests/unit/test_live_staged_spine_source_health_coherence.py`
- `README.md`

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_atlas_source_health_run_preview.py tests/unit/test_operator_loop_plan.py tests/unit/test_live_staged_spine_source_health_coherence.py::test_mock_staged_spine_source_health_coherence -q
# 15 passed

cd apps/public-site; npm run build
# pass

python -m rge.modules.safety_auditor --audit full
# pass
```

**Live layer (operator opt-in; not run in this session):**

```powershell
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_staged_spine_source_health_coherence.py -m live_network -q
```

## Next recommended packets

1. **Atlas Graph Summary Panel from Run Artifact** — surface `graph_summary` / connection metrics as a dedicated preview panel.
2. **Operator Loop Full Atlas Refresh Checklist** — plan-mode command bundle when all three preview JSON files are stale.
3. **Public Site Purpose + Readiness Panel Golden Gate** — extend GT12 static render checks for new panels.
