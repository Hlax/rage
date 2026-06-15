---
template_id: implementation_report
status: done
date: 2026-06-15
phase: 2
ticket: ticket-172
---

# ticket-172: Live Staged Extract Mock-Fixture Spine

## Summary

Added opt-in `live_network` pytest proving real OpenAlex discover→fetch→ingest-staged
followed by mock-fixture `extract-claims` (`staged_fetch_extract_claims.json`). No live
LLM; default collection excludes the live test.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-172 |
| Branch | `phase-2/ticket-172-live-staged-extract-mock-spine` |
| Date | 2026-06-15 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-15_pre-ticket-171_live-staged-extract-mock-spine-audit.md` (GO) |
| Principal audit gate | `agent_reports/2026-06-15_principal-audit-post-ticket-169.md` |
| Main tip before branch | `7d0a1c6` |

## Scope

### In

- `tests/unit/test_live_staged_extract_mock_spine.py`
- `tests/unit/test_ci_golden_gate.py` — live extract test deselect assertion

### Out

- Live LLM, link/build/detect/reconcile, public export/site, CI live network

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Opt-in discover→ingest→extract --fixture proof | **PASS** |
| 2 | Mock fixture only; no live LLM | **PASS** |
| 3 | Default pytest excludes live_network | **PASS** |
| 4 | Golden pass | **PASS** (142) |
| 5 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_staged_extract_mock_spine.py -q   # 1 passed, 1 deselected
python -m pytest tests/unit/test_live_staged_ingest_validation.py -q   # 1 passed, 1 deselected
python -m pytest tests/golden -q                                        # 142 passed
python -m pytest -q                                                     # 592 passed, 9 deselected
python -m rge.modules.safety_auditor --audit full                         # pass
```

Live network test not run in CI/default suite (operator opt-in only).

## Merge to main

Merge commit: `9beb87a65335aef431795003d03dc55a090322f5`

## Recommended next ticket

**ticket-173** — README and AGENTS.md live staged extract opt-in proof docs.

## Suggested next prompt

`/rge-run-next-ticket`
