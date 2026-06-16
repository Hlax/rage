# Operator Proof Report: Rank-2 Per-Step Live Ollama Checklist

**Date:** 2026-06-16  
**Session:** Post ticket-241 operator verification  
**Machine:** Windows 10, Python 3.14.3  
**Checklist source:** README **One-time rank-2 per-step live Ollama verification** (ticket-240)

## Executive summary

| Gate | Result |
|------|--------|
| Mock verification (`python -m rge.cli verify --skip-site`) | **PASS** — 142 golden, 666 pytest, safety audit |
| Ollama `model-health` | **PASS** — reachable; `qwen2.5:7b` available |
| Rank-2 live extract proof | **SKIP** — `unsuitable_live_rank2_artifact` |
| Rank-2 live link proof | **SKIP** — `unsuitable_live_rank2_artifact` |
| Rank-2 live build proof | **SKIP** — `unsuitable_live_rank2_artifact` |
| Rank-2 live detect proof | **FAIL** — domain seed `link-concepts` (0 accepted claims) |

**Overall checklist verdict:** **NOT FULLY GREEN** — catalog drift blocked extract/link/build; detect seed path incompatible with global live Ollama env in this session.

## Mock gate (step 2)

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli verify --skip-site
```

| Check | Exit | Result |
|-------|------|--------|
| golden_tests | 0 | 142 passed |
| full_pytest | 0 | 666 passed, 30 deselected |
| safety_audit | 0 | pass |

Mock gate remains **green** after ticket-241 merge (`6e6005a`).

## Live prerequisites (step 3)

```powershell
$env:RGE_ALLOW_LIVE_STAGED_RANK2 = "1"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m rge.cli model-health
```

| Signal | Value |
|--------|-------|
| `reachable` | `true` |
| `model_available` | `true` |
| `configured_model` | `qwen2.5:7b` |
| `effective_llm_mode` | `ollama` (with `RGE_ALLOW_LIVE_LLM=1`) |

## Per-step rank-2 live proofs

### Extract (`test_live_staged_rank2_extract_live_llm_spine.py`)

```powershell
$env:RGE_ALLOW_LIVE_STAGED_RANK2_EXTRACT_LIVE_LLM = "1"
python -m pytest tests/unit/test_live_staged_rank2_extract_live_llm_spine.py -m "live_network and live_smoke" -rs -q
```

**Result:** 1 skipped

```json
{
  "reason": "unsuitable_live_rank2_artifact",
  "detail": "Live rank-2 fetch succeeded but artifact text lacks constraint management marker required for rank-2 live extract.",
  "candidate_id": "disc_openalex_W4391579155"
}
```

**Interpretation:** Live OpenAlex discover + fetch **succeeded**; rank-2 candidate text does not match the `constraint management` heuristic required for rank-2 live proofs. Documented catalog drift per README proof-layer runbook (ticket-235) — **not** an extract-engine regression.

### Link (`test_live_staged_rank2_link_live_llm_spine.py`)

**Result:** 1 skipped — same `unsuitable_live_rank2_artifact` on `disc_openalex_W4391579155`.

### Build (`test_live_staged_rank2_build_live_llm_spine.py`)

**Result:** 1 skipped — same `unsuitable_live_rank2_artifact` on `disc_openalex_W4391579155`.

### Detect (`test_live_staged_rank2_detect_live_llm_spine.py`)

```powershell
$env:RGE_ALLOW_LIVE_STAGED_RANK2_DETECT_LIVE_LLM = "1"
python -m pytest tests/unit/test_live_staged_rank2_detect_live_llm_spine.py -m "live_network and live_smoke" -rs -q
```

**Result:** 1 failed (22.65s)

**Failure:** `seed_domain_opposing_context(temp_db)` — `link-concepts` returned exit non-zero after `extract-claims` produced **0 accepted** claims.

**Root cause (session):** With `RGE_LLM_MODE=ollama` and `RGE_ALLOW_LIVE_LLM=1`, domain seed ingest of `fixtures/sources/creativity_ai_diversity_short.txt` invoked **live Ollama** extract (no `--fixture` / checksum mock path for that source under live mode). Live model rejected both candidate claims (`overgeneralized_scope`). Without accepted claims, `link-concepts` fails with `No accepted claims found for source`.

**Note:** This is an operator-environment interaction between global live LLM env and `staged_domain_seed.py` — distinct from rank-2 catalog drift skips. Mock-gated CI and default pytest remain unaffected.

## Reconcile/report boundary

Not exercised in this session. Remains **deterministic Python** on both ranks (pre-ticket audits 221/222). No live LLM path attempted.

## Recommendations

1. **Catalog drift (extract/link/build):** Retry on a network day when OpenAlex rank-2 candidate includes `constraint management`, or run on a machine/query that yields a compatible rank-2 artifact; accept skip as expected when drift occurs.
2. **Detect seed:** Consider a follow-on hardening ticket so `seed_domain_opposing_context` forces mock LLM for GT7 seed steps when only the detect step is live (mirrors mock-upstream pattern for link/build).
3. **Mock gate:** No action required — remains green.

## Commands reference

Full shared env block documented in `docs/agents/12_RUNTIME_CONFIG.md` (**Live staged operator env profile**) and README **One-time rank-2 per-step live Ollama verification**.
