---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-181
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-181 Live Staged Detect Mock-Fixture Spine

## Verdict: **GO**

## Context

ticket-178 proves live OpenAlex discover→build with mock fixtures. ticket-147 proves
full mock spine through `detect-contradictions` with
`staged_fetch_detect_contradictions.json`, including domain opposing-context seeding
required for qualification edges. This ticket bridges: **real network through build**,
then **mock-fixture detect-contradictions**.

## Hardened scope

### In

1. `tests/unit/test_live_staged_detect_mock_spine.py` with `pytest.mark.live_network`
2. Opt-in env: `RGE_ALLOW_LIVE_STAGED_DETECT=1`, `RGE_ALLOW_SOURCE_NETWORK=1`,
   `OPENALEX_MAILTO`
3. **Local-only** domain opposing-context seed (checksum-pinned manual ingest +
   mock extract/link/build on temp DB — no network) before live discover, mirroring
   `test_staged_ingest_contradiction_spine._seed_domain_opposing_context`
4. Real discover → fetch → ingest → extract `--fixture staged_fetch_extract_claims.json`
   → link `--fixture staged_fetch_link_concepts.json` → build
   `--fixture staged_fetch_build_relationships.json` → detect
   `--fixture staged_fetch_detect_contradictions.json`
5. Assert `relationship_evidence` rows with `stance = 'qualifies'` (count ≥ 1)
6. Env gate skip test in default collection
7. `test_ci_golden_gate.py` — deselect assertion for live detect test

### Out

- Live LLM, reconcile-scores, report generation
- Auto contradiction fixture routing on unpredictable live metadata
- Public export/site, schema changes, CI live network

## Safety

- Network: OpenAlex discover/fetch only (after local seed)
- Detect uses checksum-pinned mock fixture; temp DB only
- Domain seed uses existing fixture-map manual source path (mock LLM)

## Operator opt-in

```powershell
$env:RGE_ALLOW_LIVE_STAGED_DETECT = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_detect_mock_spine.py -m live_network -q
```

## Rollback

Remove test file; retain ticket-178 build proof.

## Recommendation

**GO** — implement ticket-181; seed ticket-182 docs cross-link.
