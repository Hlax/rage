---
template_id: implementation_report
status: done
date: 2026-06-15
phase: 2
ticket: ticket-168
---

# ticket-168: Live Staged Ingest Validation Proof

## Summary

Added opt-in `live_network` pytest proof for real OpenAlex `discover-sources` →
`fetch-candidate` → `ingest-staged` on a temp DB. Asserts `sources` and `chunks`
rows without writing claims. Default collection excludes the live test.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-168 |
| Branch | `phase-2/ticket-168-live-staged-ingest-validation` |
| Date | 2026-06-15 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-15_pre-ticket-168_live-staged-ingest-validation-audit.md` (GO) |
| Principal audit gate | `agent_reports/2026-06-15_principal-audit-post-ticket-164.md` (3 done since; pre-ticket audit satisfies medium-risk gate) |
| Main tip before branch | `abe1507` |

## Scope

### In

- `tests/unit/test_live_staged_ingest_validation.py`
- `tests/unit/test_ci_golden_gate.py` — live ingest test deselect assertion

### Out

- Live LLM, extract-claims, public export/site, CI live network by default

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Opt-in discover → fetch → ingest-staged proof | **PASS** |
| 2 | No live LLM; no claims written | **PASS** |
| 3 | Default pytest excludes live_network | **PASS** (8 deselected) |
| 4 | Golden pass | **PASS** (142) |
| 5 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_staged_ingest_validation.py -q   # 1 passed, 1 deselected
python -m pytest tests/unit/test_live_staged_fetch_validation.py -q   # 1 passed, 1 deselected
python -m pytest tests/golden -q                                        # 142 passed
python -m pytest -q                                                     # 591 passed, 8 deselected
python -m rge.modules.safety_auditor --audit full                         # pass
```

Live network test not run in CI/default suite (operator opt-in only).

## Merge to main

Merge commit: `82613c031bc50894f4f766382b3f3fb0bbf87243`

## Recommended next ticket

**ticket-169** — README operator quickstart for live staged spine opt-in proofs.

## Suggested next prompt

`/rge-run-next-ticket` (low risk; no pre-ticket audit required).
