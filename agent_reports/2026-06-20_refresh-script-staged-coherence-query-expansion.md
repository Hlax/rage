# Operator Refresh Script + Live Staged Atlas Source-Health Coherence + Purpose-Aware Query Expansion

Date: 2026-06-20

Verdict: **GO** for all three packets (mock/local-safe verification).

## 1. Operator Refresh Script for Atlas Source Health — GO

Added `scripts/refresh_atlas_source_health_preview.py`.

- Default: runs local-safe arbitrary proof on a temp DB and writes validated `atlas_source_health_run_latest.json`
- `--input`: copy an existing artifact with the same validation gate
- `--output`: override destination (default `apps/public-site/public/data/atlas_source_health_run_latest.json`)
- Validates schema version, minimum source-health rows, and `assert_no_private_fields`

## 2. Live Staged Atlas Source-Health Coherence — GO

Extended `tests/unit/test_live_staged_atlas_snapshot_coherence.py` live orchestrator proof to assert:

- `source_health_preview` is present on exported atlas snapshots
- `sources_with_metadata >= 1`
- public-safe rows only (`source_id`, `local_path` absent)

## 3. Purpose-Aware Query Expansion — GO

Added `rge/modules/source_resolver/query_expansion.py` and wired it into `resolve_work_candidates()`.

- Detects metadata-only dominance after the first pass
- Tries OpenAlex-safe alternate queries derived from the research question
- Merges unique records, re-ranks by extractability, and reapplies `limit`
- Returns `query_expansion` metadata on resolver payloads

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_refresh_atlas_source_health_preview.py tests/unit/test_purpose_aware_query_expansion.py tests/unit/test_live_staged_atlas_snapshot_coherence.py::test_require_live_staged_atlas_coherence_skips_without_opt_in -q
python scripts/refresh_atlas_source_health_preview.py
python -m rge.modules.safety_auditor --audit full
```

- Targeted pytest: **11 passed**
- Refresh script: **pass**
- Safety audit: **pass**
- Live-network atlas coherence source-health assertions: operator opt-in (`live_network` marker)

## Next 3 Recommended Packets

1. **README / Operator Quickstart Refresh Hooks** — document both atlas preview refresh scripts side by side
2. **Live Network Query-Expansion Smoke** — operator pytest proving alternate queries improve extractable yield on temp DB
3. **Atlas Gaps Panel from Run Artifact** — wire `readiness_warnings` and `next_recommended_packet` into `/atlas-preview`
