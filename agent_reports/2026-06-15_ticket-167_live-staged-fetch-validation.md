---
template_id: implementation_report
status: done
date: 2026-06-15
phase: 2
ticket: ticket-167
---

# ticket-167: Live Staged Fetch Validation Proof

## Summary

Added opt-in `live_network` pytest proof for real OpenAlex `discover-sources` +
`fetch-candidate` on a temp DB. Default collection excludes the live test via
`pytest.mark.live_network`; env gate test runs in default suite. No live LLM, no
ingest-staged, no public export.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-167 |
| Branch | `phase-2/ticket-167-live-staged-fetch-validation` |
| Date | 2026-06-15 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-15_pre-ticket-167_live-staged-fetch-validation-audit.md` (GO) |
| Principal audit gate | `agent_reports/2026-06-15_principal-audit-post-ticket-164.md` |
| Main tip before branch | `b84dd73` |

## Scope

### In

- `tests/unit/test_live_staged_fetch_validation.py`
- `pyproject.toml` — `live_network` marker + default exclusion
- `tests/unit/test_ci_golden_gate.py` — live_network deselect assertion

### Out

- Live LLM, ingest-staged, public export/site, CI live network by default

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Opt-in env-gated live discover/fetch proof | **PASS** |
| 2 | No public export/site | **PASS** |
| 3 | Default pytest mock-only (live test deselected) | **PASS** (7 deselected) |
| 4 | Golden pass | **PASS** (142) |
| 5 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_staged_fetch_validation.py -q   # 1 passed, 1 deselected
python -m pytest tests/golden -q                                        # 142 passed
python -m pytest -q                                                     # 590 passed, 7 deselected
python -m rge.modules.safety_auditor --audit full                         # pass
```

Live network test not run in CI/default suite (operator opt-in only).

## Merge to main

Merge commit: `0aa669debb5a8757749cb8c5da3502285aa88a57`

## Recommended next ticket

**ticket-168** — Live staged ingest validation proof (opt-in network; no LLM).

## Suggested next prompt

Write pre-ticket audit for ticket-168, then `/rge-run-next-ticket`.
