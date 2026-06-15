---
template_id: pre_ticket_audit
status: GO
date: 2026-06-15
risk_level: medium
ticket: ticket-167
category: Phase 3 / source acquisition / product-risk reduction
---

# Pre-Ticket Audit: ticket-167 Live Staged Fetch Validation Proof

## Verdict: **GO**

## Hardened scope

### In

1. `tests/unit/test_live_staged_fetch_validation.py` with `pytest.mark.live_network`
2. Opt-in env: `RGE_ALLOW_LIVE_STAGED_FETCH=1`, `RGE_ALLOW_SOURCE_NETWORK=1`, `OPENALEX_MAILTO`
3. Real `discover-sources` + `fetch-candidate` on temp `--db` and temp staging dir
4. Assert `candidate_sources` / `research_queue` rows and staged artifact bytes on disk
5. `pyproject.toml` exclude `live_network` from default pytest (mirror `live_smoke`)
6. Unit test for env gate skip (runs in default collection)

### Out

- Live LLM / ingest-staged / extract
- Public export/site
- Schema changes
- CI running live network by default
- Changing `execute_staged_fixture_mode_run`

## Safety

- No graph writes beyond discover enqueue metadata + fetch artifact file
- Temp paths only (`tmp_path`)
- Default pytest remains mock-only (deselected marker)

## Operator opt-in command (documented in test module docstring)

```powershell
$env:RGE_ALLOW_LIVE_STAGED_FETCH = "1"
$env:RGE_ALLOW_SOURCE_NETWORK = "1"
$env:OPENALEX_MAILTO = "operator@example.com"
python -m pytest tests/unit/test_live_staged_fetch_validation.py -m live_network -q
```

## Recommendation

**GO** — implement ticket-167; seed ticket-168 live staged ingest validation (no LLM).
