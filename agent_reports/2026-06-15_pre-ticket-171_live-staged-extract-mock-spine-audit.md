---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-172
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-172 Live Staged Extract Mock-Fixture Spine

## Verdict: **GO**

## Context

ticket-167/168 prove live OpenAlex discover→fetch and discover→fetch→ingest-staged
on temp DBs without live LLM. ticket-144 proves full mock discover→extract with
patched network. This ticket bridges: **real network through ingest**, then
**mock-fixture extract-claims** (explicit `--fixture`, not live LLM).

## Hardened scope

### In

1. `tests/unit/test_live_staged_extract_mock_spine.py` with `pytest.mark.live_network`
2. Opt-in env: `RGE_ALLOW_LIVE_STAGED_EXTRACT=1`, `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO`
3. Real `discover-sources` → `fetch-candidate` → `ingest-staged` → `extract-claims --fixture staged_fetch_extract_claims.json`
4. Assert `claims` rows written (`accepted` ≥ 1); `RGE_LLM_MODE=mock` enforced
5. Env gate skip test in default collection (no marker)
6. `test_ci_golden_gate.py` — assert live extract test deselected from default collect-only

### Out

- Live LLM / `extract-claims-live`
- Auto fixture routing on unpredictable live HTML (use explicit `--fixture`)
- link-concepts / build / detect / reconcile / report
- Public export/site
- Schema changes
- CI live network by default

## Safety

- Network limited to OpenAlex discover/fetch (same as 167/168)
- Extract uses checksum-pinned mock fixture only
- Temp paths only (`tmp_path`)
- Default pytest remains mock-only

## Operator opt-in command (document in test module docstring)

```powershell
$env:RGE_ALLOW_LIVE_STAGED_EXTRACT = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_extract_mock_spine.py -m live_network -q
```

## Rollback

Remove `test_live_staged_extract_mock_spine.py`; retain ticket-167/168 ingest proofs.

## Recommendation

**GO** — implement ticket-172; seed ticket-173 README/AGENTS doc cross-link for extract opt-in proof.
