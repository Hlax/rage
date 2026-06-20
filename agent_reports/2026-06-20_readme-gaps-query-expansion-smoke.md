# README Refresh Hooks + Live Query-Expansion Smoke + Atlas Gaps Panel

Date: 2026-06-20

Verdict: **GO** for all three packets.

## 1. README / Operator Quickstart Refresh Hooks — GO

Documented both atlas preview refresh paths side by side in README Operator Quickstart:

- `scripts/refresh_atlas_preview_from_staged_spine.py` (staged-spine snapshot + coherence)
- `scripts/refresh_atlas_source_health_preview.py` (source-health + gaps run artifact)
- Updated verify/stage commands to include `atlas_source_health_run_latest.json` and regression tests

## 2. Live Network Query-Expansion Smoke — GO

Added operator-gated live smoke:

- `assert_live_query_expansion_smoke_env()` in `query_expansion.py`
- `tests/unit/test_live_network_query_expansion_smoke.py` (`live_network` marker)
- Gates: `RGE_ALLOW_LIVE_QUERY_EXPANSION_SMOKE=1`, `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO`
- `openalex_safe_query()` rewrites research questions containing `?` before the first live discovery pass

## 3. Atlas Gaps Panel from Run Artifact — GO

`/atlas-preview` gaps panel now prefers run artifact fields:

- `resolveGapsNextMovePreview()` maps `readiness_warnings`, `next_recommended_packet`, `next_recommended_reason`, and failure-reason blockers from `atlas_source_health_run_latest.json`
- Falls back to `tiny_atlas_connection_preview.json` when artifact schema is absent

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_atlas_source_health_run_preview.py tests/unit/test_purpose_aware_query_expansion.py tests/unit/test_live_network_query_expansion_smoke.py::test_live_query_expansion_smoke_blocked_without_opt_in -q
$env:RGE_ALLOW_LIVE_QUERY_EXPANSION_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_network_query_expansion_smoke.py -m live_network -q
cd apps/public-site; npm run build
python -m rge.modules.safety_auditor --audit full
```

## Next 3 Recommended Packets

1. **Atlas Question Header from Run Artifact** — prefer artifact `question`/`purpose` in preview header when present
2. **Operator Loop Refresh Hook** — surface both refresh scripts in `operator_loop` plan recommendations
3. **Live Source-Health + Query-Expansion Combined Smoke** — single operator pytest chaining health persistence and expansion yield
