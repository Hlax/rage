# Live Network Source Health Smoke

Date: 2026-06-20

Verdict: **GO** for operator-gated live OpenAlex source-health + purpose-gate smoke.

Live Ollama, paid APIs, PDF downloads, and public-site changes were not used.

## Goal

Prove the source-health and purpose-gate pipeline works with operator-gated live OpenAlex/arXiv discovery for the research question **"How does AI affect human creativity?"**, not only manual fixtures.

## What Changed

- Extended `rge/modules/live_arbitrary_source_health.py` with:
  - `assert_live_source_health_smoke_env()` — requires `RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE=1`, `RGE_ALLOW_SOURCE_NETWORK=1`, and `OPENALEX_MAILTO`
  - `resolve_live_network_source_records()` — bounded live resolver using metadata/abstracts only
  - `run_live_network_source_health_smoke()` — temp-DB smoke path reusing shared health persistence, abstract evidence, run report, and Atlas-safe artifact writer
  - `LIVE_NETWORK_RESOLVER_QUERY = "human AI creativity"` — OpenAlex-safe search query (full question with `?` returns HTTP 400)
- Added `tests/unit/test_live_network_source_health_smoke.py` (`live_network` marker; opt-in only)

## Live Smoke Summary

| Metric | Value |
| --- | --- |
| Research question | How does AI affect human creativity? |
| Resolver query | human AI creativity |
| Source count (capped) | 5 |
| Resolver breakdown (backend fetch) | openalex: 5, arxiv: 5 |
| Persisted resolver sources | openalex: 5 |
| Abstract availability | abstract_available: 1, oa_pdf_available: 1 |
| Metadata-only / blocked | 3 (`skip_llm_extraction`) |
| Purpose-fit | match: 5 |
| Purpose-gate decision | accepted: 5 |
| Skipped before extraction | 3 |
| Claims accepted / rejected | 0 / 2 |
| Atlas artifact | `atlas_source_health_run_latest.json` (temp output dir) |

## Pass Criteria Assessment

- Live OpenAlex discovery: **GO** (arxiv backend queried; capped set came from OpenAlex ordering)
- Source health persisted to `sources.domain_metadata_json`: **GO** (5 rows)
- Purpose-fit status assigned: **GO** (5 match)
- Unextractable/metadata-only skipped before extraction: **GO** (3 skipped)
- DB-backed run report with acquisition/source health counts: **GO**
- Atlas-safe source-health artifact generated: **GO**
- Safety audit: **GO**

Evidence thickness note: 2 extractable abstracts were processed but **0 claims were accepted** (2 rejected). Discovery and health persistence are sound; abstract claim yield remains thin on this bounded live sample.

## Top Blockers

- OpenAlex rejects the literal research question as a search string (`?` → HTTP 400); smoke uses a resolver-safe keyword query while preserving the full question for purpose gating and reports.
- arXiv results are discovered but may be displaced when the post-merge cap favors earlier OpenAlex rows.
- Accepted abstract-claim yield is still low on live metadata-only-heavy samples.

## Next 3 Recommended Packets

1. **Atlas Source Health Preview Wiring** — let `/atlas-preview` load a generated `atlas_source_health_run_latest.json` when present.
2. **Purpose-Gated Source Expansion** — improve retrieval/ranking when metadata-only dominance limits extractable yield.
3. **Live Staged Spine Source-Health Coherence** — align staged orchestrator acquisition summaries with the same `domain_metadata_json` health fields.

## Verification

```powershell
$env:RGE_ALLOW_LIVE_SOURCE_HEALTH_SMOKE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_network_source_health_smoke.py -m live_network -q
```

- `python -m pytest tests/unit/test_live_arbitrary_source_health.py -q` — **PASS** (6 passed)
- `python -m pytest tests/unit/test_live_network_source_health_smoke.py -m live_network -q` — **PASS** (2 passed, 1 deselected)
- `python -m rge.modules.safety_auditor --audit full` — **PASS**
- `npm run build` — **NOT RUN** (no public-site changes)
