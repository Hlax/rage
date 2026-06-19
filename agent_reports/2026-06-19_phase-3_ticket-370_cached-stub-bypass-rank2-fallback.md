# Agent report: ticket-370 — cached stub bypass and rank-2 fetch fallback

**Date:** 2026-06-19  
**Scope:** Reject unusable cached staged artifacts, rank-2 access fallback for live orchestrator, ingest guard.

## Problem

Live orchestrator on `data/db/live_research_evidence.sqlite` (ticket-368 env) partially failed:

- Rank-1 completed on prior run; rank-2 failed on `disc_openalex_W4391579155` with `already_fetched` from a ~2.6 KB DOI landing stub.
- Live extract returned 0 claims; `link-concepts` errored.
- Rank-2 path did not mirror rank-1 fetch fallback or artifact quality checks on cache hits.

## Changes

### `rge/modules/fetcher.py`

- `MIN_FETCH_HTML_TEXT_CHARS` aligned to `MIN_STAGED_INGEST_TEXT_CHARS` (200).
- `evaluate_fetch_artifact_quality()` — publisher stub markers; short HTML allowed only for checksum-pinned mock-spine markers.
- `clear_unusable_cached_staged_artifacts()` — deletes cached files failing quality before refetch.
- `_fetch_success_payload()` — validates quality before `completed` / `already_fetched`.
- `fetch_staged_candidate_artifact()` — clears unusable cache pre-fetch; validates on success.
- `ingest_staged_artifact()` — rejects text below 200 chars unless mock-spine markers present.

### `rge/modules/staged_spine_heuristics.py`

- Moved `MOCK_STAGED_RANK1_ARTIFACT_MARKERS` here (breaks circular import with `staged_spine_compatibility`).

### `rge/modules/staged_candidate_selection.py`

- `list_rank2_fetch_candidate_ids()`, `fetch_rank2_with_access_fallback()` — mirror rank-1 scan with usability checks.
- `resolve_live_staged_spine_fetch_pair()` — rank-2 uses fallback when `require_mock_spine_markers=False`; treats `already_fetched` like `completed` on failure paths.

### `rge/cli.py`

- Live orchestrator LLM path: rank-2 ingest-only after resolve (fetch already done in resolve).

## Tests

- `test_clear_unusable_cached_staged_artifacts_deletes_stub`
- `test_fetch_rank2_with_access_fallback_skips_unusable_artifact`
- Padded generic test HTML to meet 200-char extractable threshold.

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_openalex_fetch_url_candidates.py tests/unit/test_live_staged_orchestrator_fetch_fallback.py tests/unit/test_staged_candidate_fetch.py tests/unit/test_live_staged_proof_layers.py -q
python -m rge.cli verify --skip-site
```

**Results:** 35 fetch-related unit tests passed; `verify --skip-site` exit 0.

## Live operator proof (evidence DB)

```powershell
$env:RGE_LLM_MODE = "ollama"
$env:RGE_ALLOW_LIVE_LLM = "1"
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR = "1"
$env:RGE_ALLOW_LIVE_STAGED_ORCHESTRATOR_LIVE_LLM = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_TIMEOUT_SECONDS = "300"
$env:RGE_STAGED_RANK2_SCAN_MAX = "30"
python -m rge.cli run --staged-spine --topic "Does AI improve creative output while reducing diversity?" --domain creativity --db data/db/live_research_evidence.sqlite
```

**Result:** exit 0 (~54s; prior rank-1 spine reused). Log: `data/reports/live_orchestrator_run5.log`.

| Field | Value |
|-------|-------|
| `status` | `completed` |
| `rank1_candidate_id` | `disc_openalex_W4388292415` |
| `rank2_candidate_id` | `disc_openalex_W2969625533` (not prior failing `W4391579155`) |
| `rank1_accepted` | 2 |
| `rank2_accepted` | 1 |
| `steps_completed` | seed → discover → rank1/2 fetch+ingest → rank1/2 live spine → reports |

Rank-2 selected a fetchable OpenAlex artifact (945 extractable chars) instead of reusing the prior stub path.

## Next ticket

- Optional: fresh temp-DB live orchestrator proof with no prior spine reuse (full Ollama timing evidence).
- Monitor rank-1 re-ingest idempotency when checksum matches prior source (`src_fdb60839` vs new `src_7f019bed`).
