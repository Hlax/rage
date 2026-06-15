# Agent Report: ticket-234 — Decouple live staged mock-spine proofs from fixture phrases

**Date:** 2026-06-15  
**Phase:** 3  
**Ticket:** ticket-234  
**Branch:** `phase-3/ticket-234-live-staged-proof-layers`  
**Status:** implemented (mock gate pass; live acquisition pass; combined proofs skip clearly when unsuitable)

## Summary

Split live staged operator proofs into three explicit layers so live OpenAlex source acquisition can pass independently of checksum-pinned mock fixture phrases. Combined live mock-spine tests now `pytest.skip` with structured `unsuitable_live_artifact` diagnostics when fetched text does not satisfy mock preconditions — not a fetch/reconcile/report regression.

## Problem addressed

Ticket-233 fixed fetch resilience, but combined live proofs still failed or blocked on `artifact_marker_mismatch` when today's OpenAlex top-N results did not contain fixture phrases like `human-ai co-creativity` + `songwriting`. That looked like downstream spine failure when acquisition had actually succeeded.

## Implementation

| Layer | Purpose | Where |
|-------|---------|-------|
| **1 — Live acquisition** | OpenAlex discover + top-N fetch (no phrase coupling) | `test_live_openalex_source_acquisition_*`, `test_live_staged_fetch_validation.py`, `test_live_staged_ingest_validation.py` |
| **2 — Deterministic mock spine** | Ingest → reconcile/report with fixture-backed text | Existing network-free `tests/unit/test_staged_ingest_*_spine.py` |
| **3 — Combined live proof** | Full live spine only when artifact matches mock markers | `test_live_openalex_combined_*` in live mock-spine modules |

New shared module: `tests/unit/live_staged_proof_layers.py`

- `run_live_openalex_discover()` — layer-1 discover helper
- `run_live_source_acquisition()` — layer-1 top-N fetch (delegates to ticket-233 helper)
- `evaluate_mock_spine_compatibility()` — structured compatibility diagnostics
- `require_mock_spine_compatible_fetch_or_skip()` — layer-3 gate; skips with JSON body when fetchable but unsuitable

Removed `artifact_text_markers` from `fetch_first_fetchable_staged_candidate()` so acquisition is never coupled to fixture phrases.

## Skip diagnostic shape (layer 3)

When fetch succeeds but no top-N artifact matches mock markers:

```json
{
  "proof_layer": "combined_live_mock_spine",
  "reason": "unsuitable_live_artifact",
  "detail": "Live source acquisition succeeded for one or more candidates, but none of the fetched top-N artifacts satisfy mock-spine marker preconditions.",
  "required_markers": ["human-ai co-creativity", "songwriting"],
  "unsuitable_candidates": [...],
  "fetch_failures": [...],
  "assessment": "Not a fetch/reconcile/report regression — live OpenAlex catalog text does not match checksum-pinned mock fixture phrases for this query."
}
```

## Verification

### Mock / CI (required)

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli verify --skip-site
```

**Result:** PASS — golden 142, full pytest **642** passed, safety audit ok.

Focused:

```powershell
python -m pytest tests/unit/test_live_staged_proof_layers.py -q
```

**Result:** 5 passed.

### Live network (operator opt-in)

```powershell
$env:RGE_ALLOW_LIVE_STAGED_FETCH = "1"
$env:RGE_ALLOW_LIVE_STAGED_RECONCILE = "1"
$env:RGE_ALLOW_LIVE_STAGED_REPORT = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_fetch_validation.py -m live_network -q
python -m pytest tests/unit/test_live_staged_reconcile_mock_spine.py -m live_network -q
```

**Result:** 2 passed, 1 skipped in 4.84s on operator machine:

- `test_live_openalex_discover_and_fetch_writes_staged_artifact` — **PASS** (layer 1)
- `test_live_openalex_source_acquisition_for_reconcile_spine` — **PASS** (layer 1)
- `test_live_openalex_combined_reconcile_mock_spine` — **SKIPPED** with `unsuitable_live_artifact` (layer 3; expected when live catalog lacks fixture phrases)

## Operator guidance

1. Run layer-1 acquisition proofs to validate discover + fetch after ticket-233 hardening.
2. Run layer-3 combined proofs only when expecting fixture-compatible catalog results (or accept skip as catalog drift, not engine failure).
3. Use network-free `test_staged_ingest_*_spine.py` for deterministic mock-spine CI coverage.

## Next ticket recommendation

**ticket-235** (optional): README operator runbook section documenting the three proof layers and how to interpret `unsuitable_live_artifact` skips.

## Merge checkpoint

Not merged (awaiting operator review).
