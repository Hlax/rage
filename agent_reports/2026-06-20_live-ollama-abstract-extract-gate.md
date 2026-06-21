# Agent Report: Live Ollama Abstract Extract Gate

**Date:** 2026-06-20  
**Packet:** live-ollama-abstract-extract-gate  
**Verdict:** GO (gate logic); operator live run remains opt-in

## Goal

Compare local Ollama extraction against mock baseline on live abstracts with
honest readiness — Ollama is not default.

## Changes

Enhanced `rge/modules/local_model_extraction_comparison.py`:

- `classify_local_model_readiness()` — readiness stays **PARTIAL** until
  Ollama quote-validity meets mock baseline (or 0.95 fallback threshold)
- Artifact `local_model_readiness` exposes threshold, literal-quote requirement,
  and unsupported-claim rejection policy
- Existing validation pipeline already rejects non-literal quotes and unsupported
  claims before acceptance

## Required env (operator opt-in)

```powershell
$env:RGE_ALLOW_LOCAL_MODEL_EXTRACTION_COMPARISON = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
# plus live source expansion / network gates
python scripts/run_local_model_extraction_comparison.py --sync-public
```

## Verification

| Check | Result |
|-------|--------|
| `test_local_model_readiness_partial_without_quote_validity` | PASS |
| `test_local_model_readiness_go_when_quote_validity_meets_mock` | PASS |
| `python -m rge.cli verify --skip-site` | exit 0 |

## Next recommended packet

**multi-claim-atom-clustering**
