# Agent report: ticket-371 — clean live orchestrator timing proof (in progress)

**Date:** 2026-06-19  
**Scope:** Fresh temp DB + isolated staging; full live Ollama dual-rank orchestrator timing.

## Operator command

```powershell
$db = "data/db/live_orchestrator_clean_timing.sqlite"
$staging = "data/sources/staged/clean_timing"
$log = "data/reports/live_orchestrator_clean_timing.log"

Remove-Item $db -ErrorAction SilentlyContinue
Remove-Item $staging -Recurse -Force -ErrorAction SilentlyContinue

$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR_LIVE_LLM = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_TIMEOUT_SECONDS = "300"
$env:RGE_STAGED_RANK2_SCAN_MAX = "30"
$env:PYTHONUNBUFFERED = "1"

python -m rge.cli run --staged-spine `
  --topic "Does AI improve creative output while reducing diversity?" `
  --domain creativity `
  --db $db `
  --staging-dir $staging
```

## Prerequisite fixes discovered during proof

| Issue | Fix |
|-------|-----|
| Seed extract under live Ollama rejected GT7 fixture claims on fresh DB | `_mock_llm_seed_env()` in `rge/cli.py` (ticket-243 parity) |
| Relative `--staging-dir` resolved to wrong repo root on ingest-staged | Use `_REPO_ROOT` + absolute resolve in orchestrator |
| PMC PoW + DOI redirect stubs passed 200-char gate | Added PMC PoW + redirect gate markers in `fetcher.py` |
| Only 1 usable fetch among default discover limit 10 | Live orchestrator discover uses `--limit 25` |

## Run status (2026-06-19 ~17:15 UTC) — **PARTIAL / EXIT 1**

**Resume run** (`live_orchestrator_clean_timing_resume.log`): exit **1** after **2220 s (~37 min)**.

| Milestone | Status |
|-----------|--------|
| Fresh DB | `data/db/live_orchestrator_clean_timing.sqlite` |
| Isolated staging | `data/sources/staged/clean_timing/` (real PDFs) |
| Discover | 25 candidates enqueued |
| Rank-1 live spine + report | **Done** |
| Rank-2 live spine | **Failed** — 0 accepted claims |

### Rank-1 (success)

- Candidate: `disc_openalex_W4213435830` (~952 KB PDF)
- Report: `run_staged_fixture_mode_spine_rank1` @ 2026-06-19T16:39:31Z
- `claims_accepted`: 5 (2 seed + 3 staged); `relationships_updated`: 2

### Rank-2 (failure)

- Candidate: `disc_openalex_W4386693657` (~569 KB PDF, “Generative AI”)
- Source: `src_231c8d5c586f18c0` — **186 rejected claims, 0 accepted**
- Error: `No accepted claims found for source`

### Timing

| Phase | Wall clock |
|-------|------------|
| Resume run (seed skip → rank-1 report → rank-2 extract fail) | **2220 s (~37 min)** |

## Next

- Rank-2 path should fall back when live extract yields 0 accepted claims (try next fetchable candidate).
- Re-run clean proof after extract-fallback or with a smaller rank-2 source.
