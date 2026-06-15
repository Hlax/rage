---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-178
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-178 Live Staged Build Mock-Fixture Spine

## Verdict: **GO**

## Context

ticket-175 proves live OpenAlex discover→link with mock fixtures. ticket-146 proves
full mock spine through `build-relationships` with `staged_fetch_build_relationships.json`.
This ticket bridges: **real network through link**, then **mock-fixture build-relationships**.

## Hardened scope

### In

1. `tests/unit/test_live_staged_build_mock_spine.py` with `pytest.mark.live_network`
2. Opt-in env: `RGE_ALLOW_LIVE_STAGED_BUILD=1`, `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO`
3. Real discover → fetch → ingest → extract `--fixture staged_fetch_extract_claims.json` → link `--fixture staged_fetch_link_concepts.json` → build `--fixture staged_fetch_build_relationships.json`
4. Assert `relationships` rows (`relationship_count` ≥ 1 in CLI payload)
5. Env gate skip test in default collection
6. `test_ci_golden_gate.py` — deselect assertion for live build test

### Out

- Live LLM, detect/reconcile/report
- Auto relationship fixture routing on unpredictable live metadata
- Public export/site, schema changes, CI live network

## Safety

- Network: OpenAlex discover/fetch only
- Build uses checksum-pinned mock fixture; temp DB only

## Operator opt-in

```powershell
$env:RGE_ALLOW_LIVE_STAGED_BUILD = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_build_mock_spine.py -m live_network -q
```

## Rollback

Remove test file; retain ticket-175 link proof.

## Recommendation

**GO** — implement ticket-178; seed ticket-179 docs cross-link.
