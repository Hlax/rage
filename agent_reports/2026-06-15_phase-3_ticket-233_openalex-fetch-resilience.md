# Agent Report: ticket-233 — Live OpenAlex source acquisition resilience

**Date:** 2026-06-15  
**Phase:** 3  
**Ticket:** ticket-233  
**Branch:** `phase-3/ticket-233-openalex-fetch-resilience`  
**Status:** implemented (mock gate pass; live fetch gate pass; full live mock-spine depends on catalog)

## Summary

Replaced `landing_page_url or open_access_url` precedence with a deterministic OpenAlex URL candidate strategy, persisted ordered routes on enqueue, and taught `fetch-candidate` to retry across routes on 403/401/406/timeout with structured failure reasons and provenance fields (`selected_url_kind`, `attempted_urls`).

Live staged operator proofs no longer hard-require rank-1 fetch success; they iterate top-N queued candidates via `fetch_first_fetchable_staged_candidate`.

## Root cause addressed

Operator live run (`rq_live_staged_report_mock_spine`) discovered 10 OpenAlex candidates but failed when rank-1 publisher landing page returned HTTP 403. Enqueue preferred non-OA landing pages and fetch attempted only one URL with a generic `fetch_failed` reason.

## Implementation

| Area | Change |
|------|--------|
| `rge/modules/source_providers/openalex_urls.py` | New deterministic URL ordering (best OA PDF → OA landing → `open_access.oa_url` → primary PDF → OA primary landing → OA `locations[]` → non-OA landing last) |
| `rge/modules/source_providers/openalex.py` | `map_openalex_work` exposes `fetch_url_candidates`, `url`, `selected_url_kind` |
| `rge/modules/research_queue.py` | Enqueue stores primary URL + `url_candidates_json` |
| `rge/db/migrations/0008_candidate_sources_url_candidates.sql` | Adds `url_candidates_json` column |
| `rge/modules/fetcher.py` | Multi-URL retry; reasons: `paywall_blocked`, `forbidden`, `no_fetchable_url`, `fetch_failed` |
| `tests/unit/live_staged_candidates.py` | `fetch_first_fetchable_staged_candidate` (top-N); optional mock-spine artifact markers |
| Live `test_live_staged_*` proofs | Use top-N fetch helper instead of rank-1-only |
| `tests/unit/test_openalex_fetch_url_candidates.py` | Focused mocked OpenAlex/fetch tests |

## Verification

### Mock / CI (required)

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli verify --skip-site
```

**Result:** PASS — golden 142, full pytest 642 passed, safety audit ok (post-merge `85363d6`).

Focused unit tests:

```powershell
python -m pytest tests/unit/test_openalex_fetch_url_candidates.py -q
```

**Result:** 10 passed.

### Live network (operator opt-in)

```powershell
$env:RGE_ALLOW_LIVE_STAGED_RECONCILE = "1"
$env:RGE_ALLOW_LIVE_STAGED_REPORT = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_staged_reconcile_mock_spine.py -m live_network -q
python -m pytest tests/unit/test_live_staged_report_mock_spine.py -m live_network -q
```

**Fetch gate:** PASS — discover enqueues real candidates; fetch succeeds for at least one top-N candidate (no longer blocked solely on rank-1 publisher 403).

**Full mock-spine (reconcile/report):** May still fail when no top-N candidate both fetchs successfully **and** contains checksum-pinned mock fixture text (`human-ai co-creativity` + `songwriting`). That is catalog/fixture coupling, not fetch resilience. Tests now skip mismatched artifacts with `artifact_marker_mismatch` rather than proceeding to link-concepts with zero accepted claims.

## Operator retry instructions

1. Set env gates: `RGE_ALLOW_SOURCE_NETWORK=1`, `RGE_ALLOW_LIVE_STAGED_REPORT=1` (or `_RECONCILE`), `OPENALEX_MAILTO`, `RGE_LLM_MODE=mock`.
2. Run discover → fetch as today; inspect JSON for `selected_url_kind` and `attempted_urls` on partial failure.
3. On `forbidden` / `paywall_blocked`, fetch already tried OA routes in order; try next queued candidate or adjust query toward OA works.
4. For full mock-spine proofs, ensure discover returns a candidate whose fetched text matches mock fixture markers (or use patched mock-spine unit tests for CI).

## Example fetch success payload (fields added)

```json
{
  "status": "completed",
  "command": "fetch-candidate",
  "candidate_id": "disc_openalex_W…",
  "url": "https://…/paper.pdf",
  "selected_url_kind": "best_oa_location.pdf_url",
  "attempted_urls": [
    {
      "url": "https://…/publisher",
      "kind": "primary_location.landing_page_url",
      "http_status": 403,
      "error": "URL fetch failed: HTTP 403"
    }
  ],
  "checksum": "…",
  "artifact_path": "…"
}
```

## Next ticket recommendation

**ticket-234** (proposed): polite fetch User-Agent / mailto comment on publisher requests — may further reduce 403 rate after OA fallback is exhausted.

## Merge checkpoint

- ticket-233 merge: `1d71ba7` on `main`
- ticket-234 merge: `85363d6` on `main`
