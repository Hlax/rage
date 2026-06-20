# Atlas Source Health Preview Wiring + Purpose-Gated Source Expansion + Live Staged Spine Source-Health Coherence

Date: 2026-06-20

Verdict: **GO** for all three packets (mock/local-safe verification).

## 1. Atlas Source Health Preview Wiring — GO

`/atlas-preview` now prefers a committed Atlas-safe run artifact when present.

- Added `apps/public-site/public/data/atlas_source_health_run_latest.json` (generated from local-safe proof)
- Added `resolveSourceHealthPreview()` and `mapRunArtifactToSourceHealthPanel()` in `apps/public-site/lib/atlasPreview.ts`
- Source health panel reads the resolver output and labels whether data comes from the run artifact or fixture fallback
- Safety auditor now audits `atlas_source_health_run_latest.json` as required atlas preview public data

## 2. Purpose-Gated Source Expansion — GO

Improved retrieval/ranking when metadata-only records dominate resolver output.

- Added `source_status_rank()` and `rank_records_by_extractability()` in `rge/modules/source_resolver/status.py`
- `resolve_work_candidates()` now re-ranks merged records by extractability before applying `limit`
- `score_discovered_candidate()` adds a `+0.15` abstract-availability bonus (aligned with field-map ranking)

## 3. Live Staged Spine Source-Health Coherence — GO

Staged ingest now persists the same durable health metadata shape used by arbitrary/live smoke paths.

- Added `staged_ingest_health_metadata()` in `rge/modules/acquisition_quality.py`
- `ingest_staged_artifact()` merges health metadata (status, parser backend, purpose-fit fields) onto `sources.domain_metadata_json`
- `generate-run-report` acquisition summaries now include staged ingest health counts in the staged spine test

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_atlas_source_health_run_preview.py tests/unit/test_source_resolver_extractability_rank.py tests/unit/test_staged_ingest_source_health.py tests/unit/test_staged_ingest_run_report_spine.py tests/unit/test_live_arbitrary_source_health.py -q
python -m rge.modules.safety_auditor --audit full
cd apps/public-site; npm run build
```

- Targeted pytest: **13 passed**
- Safety audit: **pass**
- `npm run build`: **pass**

## Next 3 Recommended Packets

1. **Operator Refresh Script for Atlas Source Health** — copy latest `atlas_source_health_run_latest.json` from proof runs with validation
2. **Live Staged Atlas Source-Health Coherence** — assert `source_health_preview` in live orchestrator atlas snapshot pytest
3. **Purpose-Aware Query Expansion** — alternate resolver queries when metadata-only dominance persists after re-rank
