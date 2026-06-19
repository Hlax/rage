# Agent report: ticket-369 — fetch fallback artifact quality tuning

**Date:** 2026-06-19  
**Scope:** Tune staged fetch fallback for bot-challenge HTML, mirror URL priority, and clearer skip payloads.

## Problem

Live orchestrator runs on the evidence DB were skipping with misleading `unsuitable_live_artifact` when:

1. Publisher URLs returned HTTP 200 bot-challenge pages (~3 KB) counted as successful fetches.
2. Paywalled `science.org` / `sciencedirect.com` routes were tried before PMC/arxiv mirrors.
3. Rank-1 scan stopped on the first “completed” but unusable artifact.

## Changes

### `rge/modules/fetcher.py`

- Added `evaluate_fetch_artifact_quality()` — rejects bot-challenge HTML markers (`Client Challenge`, `noscript-container`, etc.) and HTML with insufficient extractable text (< 50 chars).
- `fetch_url_bytes_with_retry()` now treats unusable artifacts like retryable failures and continues to the next URL route.
- New failure reason: `artifact_unusable`.

### `rge/modules/source_providers/openalex_urls.py`

- Host priority bonus: PMC/arxiv/springeropen routes sort before science.org/sciencedirect/springer link.springer.com.

### `rge/modules/staged_candidate_selection.py`

- Rank-1 candidate ordering prefers PDF routes, then PMC/arxiv mirror presence, then priority score.
- `fetch_rank1_with_access_fallback()` skips completed fetches that fail artifact usability checks.
- `UnsuitableLiveArtifactError.to_payload()` distinguishes acquisition failures from mock-marker mismatches.

## Tests

- `tests/unit/test_openalex_fetch_url_candidates.py` — PMC ordering, bot-challenge retry, unusable-artifact reason.
- `tests/unit/test_live_staged_orchestrator_fetch_fallback.py` — skip unusable completed fetch, existing fallback tests updated.

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_openalex_fetch_url_candidates.py tests/unit/test_live_staged_orchestrator_fetch_fallback.py -q
python -m rge.cli verify --skip-site
```

## Verification

- Targeted tests: **23 passed**
- Full pytest: **861 passed**, 33 deselected (after fixture HTML padding fixes)

## Operator note

Re-run live orchestrator with existing ticket-368 env gates. Fetch should now skip bot walls and prefer PMC mirrors when OpenAlex exposes them. Set `RGE_LLM_TIMEOUT_SECONDS=300` for large live spines.

## Next ticket

**ticket-364** — optional CI `live_network` staged ingest smoke (deferred).
