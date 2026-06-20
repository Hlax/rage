# Public Site Graph Panel Golden Gate

**Date:** 2026-06-20  
**Branch:** `phase-4/packets-002-004-evidence-quality-extraction`  
**Verdict:** **GO**

## Goal

Refresh committed `atlas_source_health_run_latest.json` with live `trace_summary` so `/atlas-preview` evidence trace panel uses the run artifact by default (not fixture fallback).

## What shipped

### Refresh script (`scripts/refresh_atlas_source_health_preview.py`)

- `--source {local-safe,live-atom-trace}` generation modes when `--input` omitted
- `--require-trace-summary` validation gate (`trace_count >= 1`, non-empty `atlas_trace_preview`)
- Refresh result reports `trace_count`, `atom_count`, `accepted_claim_count`

### Committed public artifact

Refreshed from live atom-trace export:

```powershell
python scripts/refresh_atlas_source_health_preview.py `
  --input data/exports/live_atom_trace_public_refresh/atlas_source_health_run_latest.json `
  --require-trace-summary
```

Committed snapshot (`apps/public-site/public/data/atlas_source_health_run_latest.json`):

| Field | Value |
|-------|------:|
| `sources_with_metadata` | 5 |
| `accepted_claim_count` | 5 |
| `trace_count` | 5 |
| `atom_count` | 5 |
| `graph_summary.totals.relationships` | 5 |
| `graph_summary.totals.frontend_ready_trace_count` | 5 |

`/atlas-preview` `resolveTracePanelPreview()` now returns `preview_source: 'run_artifact'` because `trace_summary.atlas_trace_preview` is non-empty.

### Golden gate tests

- `test_atlas_source_health_run_artifact_includes_trace_summary_fields` — hard assert (no skip)
- `test_committed_artifact_enables_run_artifact_trace_panel_by_default`
- `test_refresh_atlas_source_health_preview.py` — trace summary validation + local-safe trace rows
- `test_refresh_live_atom_trace_source_writes_trace_summary` — opt-in `live_network`

## Operator refresh

```powershell
# Live network (recommended for public preview)
$env:RGE_ALLOW_LIVE_ABSTRACT_EVIDENCE_ATOM_TRACE_SMOKE = "1"
$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python scripts/refresh_atlas_source_health_preview.py --source live-atom-trace --require-trace-summary
cd apps/public-site; npm run build
```

Mock CI fallback:

```powershell
$env:RGE_LLM_MODE = "mock"
python scripts/refresh_atlas_source_health_preview.py --require-trace-summary
```

## Verification

| Check | Result |
|-------|--------|
| `pytest tests/unit/test_refresh_atlas_source_health_preview.py tests/unit/test_atlas_source_health_run_preview.py -q` | **15 passed** |
| `cd apps/public-site && npm run build` | **PASS** |

## Next recommended packet

**Operator Loop Full Atlas Refresh Checklist** — single operator command chaining staged-spine + source-health + trace-summary refresh + site build.
