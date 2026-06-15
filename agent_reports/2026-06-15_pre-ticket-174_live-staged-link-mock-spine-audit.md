---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-175
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-175 Live Staged Link Mock-Fixture Spine

## Verdict: **GO**

## Context

ticket-172 proves live OpenAlex discover→fetch→ingest→mock extract. ticket-145 proves
full mock spine through link-concepts with `staged_fetch_link_concepts.json`. This
ticket bridges: **real network through extract**, then **mock-fixture link-concepts**.

## Hardened scope

### In

1. `tests/unit/test_live_staged_link_mock_spine.py` with `pytest.mark.live_network`
2. Opt-in env: `RGE_ALLOW_LIVE_STAGED_LINK=1`, `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO`
3. Real discover → fetch → ingest → extract `--fixture staged_fetch_extract_claims.json` → link `--fixture staged_fetch_link_concepts.json`
4. Assert `claim_concepts` rows for accepted claims (`link_count` ≥ 2 in CLI payload)
5. Env gate skip test in default collection
6. `test_ci_golden_gate.py` — deselect assertion for live link test

### Out

- Live LLM
- build-relationships / detect / reconcile / report
- Auto link fixture routing on unpredictable live source titles (use explicit `--fixture`)
- Public export/site, schema changes, CI live network

## Safety

- Network: OpenAlex discover/fetch only (same as 167–172)
- Link uses checksum-pinned mock fixture
- Temp DB paths only; `RGE_LLM_MODE=mock`

## Operator opt-in

```powershell
$env:RGE_ALLOW_LIVE_STAGED_LINK = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_link_mock_spine.py -m live_network -q
```

## Rollback

Remove test file; retain ticket-172 extract proof.

## Recommendation

**GO** — implement ticket-175; seed ticket-176 docs cross-link.
