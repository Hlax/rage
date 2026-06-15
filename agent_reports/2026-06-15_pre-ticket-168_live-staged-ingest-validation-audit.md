---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-168
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-168 Live Staged Ingest Validation Proof

## Verdict: **GO**

## Hardened scope

### In

1. `tests/unit/test_live_staged_ingest_validation.py` with `pytest.mark.live_network`
2. Opt-in env: `RGE_ALLOW_LIVE_STAGED_INGEST=1`, `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO`
3. Real `discover-sources` → `fetch-candidate` → `ingest-staged` on temp `--db` and temp staging dir
4. Assert `sources` / `chunks` rows written; `claims` count unchanged (no LLM)
5. Env gate skip test in default collection (no marker)
6. `test_ci_golden_gate.py` — assert live ingest test deselected from default collect-only

### Out

- Live LLM / extract-claims / link / build / detect / reconcile
- Public export/site
- Schema changes
- CI running live network by default
- Changing `execute_staged_fixture_mode_run` or fetcher ingest logic

## Safety

- Graph writes limited to accepted `sources` + `chunks` from validated staged artifact bytes
- No model calls; `RGE_LLM_MODE=mock` enforced in fixture
- Temp paths only (`tmp_path`)
- Default pytest remains mock-only (`live_network` deselected)

## Operator opt-in command (documented in test module docstring)

```powershell
$env:RGE_ALLOW_LIVE_STAGED_INGEST = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_ingest_validation.py -m live_network -q
```

## Recommendation

**GO** — implement ticket-168; seed ticket-169 README operator note for live staged spine opt-in proofs.
