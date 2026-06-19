# Agent report: ticket-367 — live staged mock-spine compatibility skip

**Date:** 2026-06-19  
**Branch:** `phase-3/ticket-367-live-staged-mock-spine-compatibility-skip`  
**Merge commit:** `7eda6b4` (fast-forward into `main`)

## Summary

Live staged orchestrator now evaluates fetched artifacts for checksum-pinned mock-spine marker phrases before ingest. When live OpenAlex HTML is fetchable but lacks those markers, the run returns `status: skipped` / `reason: unsuitable_live_artifact` instead of failing later at `link-concepts` with zero accepted claims.

## Changes

- Added `rge/modules/staged_spine_compatibility.py` with marker checks and structured diagnostics.
- Extended `fetch_rank1_with_access_fallback` to skip incompatible artifacts and raise `UnsuitableLiveArtifactError` when none match.
- `execute_staged_fixture_mode_run` catches the error and returns the skip payload.
- Tests in `tests/unit/test_live_staged_orchestrator_fetch_fallback.py`.

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_staged_orchestrator_fetch_fallback.py -q
python -m rge.cli verify --skip-site
```

- Fetch fallback tests: **7 passed**
- Full verify at merge time: **144 golden, 853 pytest, safety audit pass**

## Next ticket

**ticket-368** — live orchestrator real-data spine (live Ollama on arbitrary staged ingest).
