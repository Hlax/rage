# Live Source Expansion

**Date:** 2026-06-20  
**Packet:** Live Source Expansion  
**Cycle:** Operator loop cycle 3 — after multi-question live abstract restart  
**Verdict:** **GO**

## Live run summary (2026-06-20 — cycle 3)

| Signal | Result |
| --- | ---: |
| Discovery backends | openalex, arxiv |
| Resolver breakdown | openalex: 5, arxiv: 5 |
| Persisted sources | openalex: 1, arxiv: 5 |
| Source diversity | 2 |
| Claims accepted | 5 |
| Trace rows | 6 |

## Operator command

```powershell
$env:RGE_ALLOW_LIVE_SOURCE_EXPANSION_SMOKE = "1"
$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python scripts/run_live_source_expansion_smoke.py --sync-public
```

## Verification

| Command | Status |
| --- | --- |
| Live smoke `--sync-public` | **PASS** (GO) |
| `pytest tests/unit/test_live_source_expansion.py -q` | **PASS** (6 passed) |
| Safety audit | **PASS** |
| `npm run build` | **PASS** |

## Next recommended packet

**Local Model Extraction Comparison** (`local-model-extraction-comparison`)

```powershell
$env:RGE_ALLOW_LOCAL_MODEL_EXTRACTION_COMPARISON = "1"
$env:RGE_ALLOW_LIVE_SOURCE_EXPANSION_SMOKE = "1"
$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
python scripts/run_local_model_extraction_comparison.py --sync-public --limit 5
```
