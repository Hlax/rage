# Agent report: ticket-368 — live staged orchestrator real-data spine v0

**Date:** 2026-06-19  
**Branch:** `phase-3/ticket-368-live-staged-orchestrator-real-spine`  
**Merge commit:** `9462da6` (fast-forward into `main`)

## Summary

When operators opt into `RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR_LIVE_LLM=1` (plus existing live LLM and orchestrator gates), the staged orchestrator:

1. Accepts the first fetchable rank-1 artifact **without** mock-spine marker requirements.
2. Runs live Ollama **extract → link → build → detect** on ingest-staged source text via new `live_staged_ingest_*_fallthrough` flags.
3. Keeps **reconcile-scores** and **generate-run-report** deterministic (no LLM).

Without the new gate, ticket-367 behavior is unchanged: incompatible artifacts still skip with `unsuitable_live_artifact`.

## Operator env (real spine)

```powershell
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "you@example.com"

python -m rge.cli run --staged-spine --topic "Does AI improve creative output while reducing diversity?" --domain creativity --db data/db/live_research_evidence.sqlite
```

Requires local Ollama. Use a gitignored evidence DB path, not the default graph DB.

## Key files

- `rge/modules/live_staged_orchestrator_spine.py` — gate checks and spine runner
- `rge/modules/staged_spine_heuristics.py` — `is_staged_ingest_source`, minimum text threshold
- `live_staged_ingest_*_fallthrough` in extract/link/build/detect modules
- `rge/cli.py` — orchestrator branches on live LLM gate

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_staged_orchestrator_real_spine.py tests/unit/test_live_staged_orchestrator_fetch_fallback.py -q
python -m rge.cli verify --skip-site
```

- Targeted tests: **10 passed**
- Full verify: **144 golden, 857 pytest, safety audit pass**

## Next ticket

**ticket-364** — optional `live_network` smoke in CI (deferred operator proof bundle **ticket-361**).
