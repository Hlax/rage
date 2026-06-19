# Agent Report: ticket-366 — Live staged orchestrator fetch fallback on candidate 403

**Date:** 2026-06-19  
**Phase:** 3  
**Ticket:** ticket-366  
**Branch:** `phase-3/ticket-366-live-staged-orchestrator-fetch-fallback`  
**Status:** done

## Summary

Implemented live staged orchestrator rank-1 fetch fallback when publisher URLs return `forbidden` or `paywall_blocked` after ticket-233 per-URL retry is exhausted. Rank-2 selection skips candidates blocked or consumed for rank-1.

## Changes

- `rge/modules/fetcher.py` — `FETCH_ACCESS_BLOCKED_REASONS`, `is_fetch_access_blocked()`
- `rge/modules/staged_candidate_selection.py` — `list_rank1_fetch_candidate_ids`, `fetch_rank1_with_access_fallback`, `resolve_live_staged_spine_fetch_pair`, `exclude_ids` on rank-2 selection
- `rge/cli.py` — live orchestrator uses resolve/fetch fallback path; mock pinned path unchanged
- `tests/unit/test_live_staged_orchestrator_fetch_fallback.py` — mock pytest proof (6 tests)
- `tests/conftest.py` — pin operator gate env defaults so `.env.local` does not leak into CI/dev pytest
- Test hygiene updates for explicit `setenv("0")` on gate flags

## Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_staged_orchestrator_fetch_fallback.py -q
python -m rge.cli verify --skip-site
```

| Check | Result |
|-------|--------|
| ticket-366 unit tests | 6 passed |
| Golden tests | 144 passed |
| Full pytest | 853 passed |
| Safety audit | pass |
| `verify --skip-site` | pass |

## Merge

*(filled after merge to main)*

## Next ticket

ticket-364 — CI weekly live_network staged ingest smoke (proposed)
