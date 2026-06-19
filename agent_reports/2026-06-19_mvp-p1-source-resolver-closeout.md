# MVP-P1 Source Resolver — Packet Closeout

**Date:** 2026-06-19  
**Branch:** `phase/mvp-p1-source-resolver`  
**Verdict:** **GO** (mock verification complete)

## Promotion gate checklist

| Gate | Result |
|------|--------|
| Targeted resolver tests pass | **PASS** — 20/20 |
| Golden inventory documented | **PASS** — `test_27` added to optional golden list |
| Safety / public boundary touched | **N/A** — no export schema or quote rule changes |
| Full `verify --skip-site` at closeout | **PASS** — 149 golden, 883 pytest, safety audit |
| Live network proof | **NOT RUN** — gated; mock fixtures prove contract |
| Evidence report exists | **PASS** |
| Failure modes classified | **PASS** — explicit `source_status` + evidence summaries |

## Verdict rationale

**GO elements:**

- Unified resolver interface with explicit acquisition status exists.
- OpenAlex abstract reconstruction integrated without requiring full text.
- Unpaywall enrichment is optional and non-fatal.
- arXiv metadata is first-class.
- Missing full text / missing abstract does not fail resolver runs.
- Pre-LLM evidence explanation is implemented and tested.

**PARTIAL elements (scope remaining for later packets):**

- Resolver is CLI/module-only; not connected to ingest → extract pipeline.
- No live operator proof of OpenAlex + Unpaywall + arXiv in one run.
- TEI detection and acquisition-state transitions (`download_failed`, `parse_failed`, etc.) are reserved but not exercised end-to-end.

## Product diagnosis

The repo already had OpenAlex discovery and fetch resilience. The dominant MVP gap was **not knowing what evidence exists before LLM extraction**. This packet closes that gap at the resolver layer. The unsupported-claim wall from dirty PDFs remains a **downstream** problem (Packet 5/6).

## Engineering diagnosis

Architecture placement is correct: resolver sits above providers, below fetch/ingest. Next work should consume `evidence_summaries.extraction_recommendation` to gate extract-claims.

## Next 3 improvement packets (ranked)

1. **MVP-P2 — Abstract-first evidence cards**  
   Quote-first extraction from `abstract_available` records; reject topic-shaped claims; label reports `abstract_only`.

2. **MVP-P4 — Self-improvement recommender**  
   Map resolver/extraction rejection mixes to improvement packets (parser vs OA vs ranker).

3. **MVP-P3 — Field map report**  
   Mass metadata pull + clustering + abstract-grounded synthesis once P2 proves abstract loop.

(Selective full-text acquisition MVP-P5 and PDF parser milestone MVP-P6 remain correctly deferred until abstract loop works.)

## Merge recommendation

Safe to merge as additive infrastructure. Closeout verification:

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli verify --skip-site
# PASS — 2026-06-19 (149 golden, 883 pytest, safety audit)
```
