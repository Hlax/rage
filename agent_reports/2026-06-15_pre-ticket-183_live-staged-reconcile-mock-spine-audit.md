---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-184
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-184 Live Staged Reconcile-Scores Spine

## Verdict: **GO**

## Context

ticket-181 proves live OpenAlex discover→detect with mock LLM fixtures. ticket-148 proves
full mock spine through `reconcile-scores` on staged-ingested sources (deterministic Python;
`staged_fetch_reconcile_scores.json` is a **contract fixture** for expected boosts, not an
LLM output). This ticket bridges: **real network through mock detect**, then
**deterministic reconcile-scores**.

## Hardened scope

### In

1. `tests/unit/test_live_staged_reconcile_mock_spine.py` with `pytest.mark.live_network`
2. Opt-in env: `RGE_ALLOW_LIVE_STAGED_RECONCILE=1`, `RGE_ALLOW_SOURCE_NETWORK=1`,
   `OPENALEX_MAILTO`
3. **Local-only** domain opposing-context seed before live discover (same as ticket-181)
4. Real discover → fetch → ingest → extract/link/build/detect with explicit mock fixtures
   (`staged_fetch_extract_claims.json` through `staged_fetch_detect_contradictions.json`)
5. `reconcile-scores` (no `--fixture`; deterministic `score_reconciler` path)
6. Assert `score_events` row count ≥ 1 and CLI `score_events_created` ≥ 1
7. Env gate skip test in default collection
8. `test_ci_golden_gate.py` — deselect assertion for live reconcile test

### Out

- Live LLM, report generation
- `--evidence-db-reconcile` NM-4 path
- Public export/site, schema changes, CI live network

## Safety

- Network: OpenAlex discover/fetch only (after local seed)
- Reconcile is deterministic Python on temp DB; no model writes

## Operator opt-in

```powershell
$env:RGE_ALLOW_LIVE_STAGED_RECONCILE = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_reconcile_mock_spine.py -m live_network -q
```

## Rollback

Remove test file; retain ticket-181 detect proof.

## Recommendation

**GO** — implement ticket-184; seed ticket-185 docs cross-link.
