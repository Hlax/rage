---
template_id: implementation_report
status: done
date: 2026-06-15
phase: 2
ticket: ticket-217
---

# ticket-217: Live Staged Detect Live LLM Opt-In Proof (Per-Step)

## Summary

Added per-step live Ollama **detect-contradictions** fallthrough for staged rank-1
OpenAlex ingest sources. Mirrors ticket-212 build pattern: env gate
`RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM=1`, CLI `--live-staged-detect-fallthrough`,
mock upstream in pytest, domain seed before live discover, orchestrator unchanged.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-217 |
| Branch | `phase-2/ticket-217-live-staged-detect-live-llm-spine` |
| Date | 2026-06-15 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-15_pre-ticket-216_live-staged-detect-live-llm-audit.md` |
| Principal audit gate | satisfied (cadence overdue note only; implementation_gate satisfied) |
| Main tip before branch | `8f12385` |

## Scope

**In:** `contradiction_detector.py` staged live fallthrough; CLI flag; gate tests + live proof; CI deselect.

**Out:** Orchestrator live LLM, rank-2, live reconcile/report, combined all-live upstream pytest.

## Changed files

- `rge/modules/contradiction_detector.py`
- `rge/cli.py`
- `tests/unit/test_live_staged_detect_live_llm_spine.py`
- `tests/unit/test_ci_golden_gate.py`
- `tickets/ticket-217.json`
- `tickets/TICKET_QUEUE.md`

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Live staged detect fallthrough bypasses staged-fetch auto-mock when env gate set | **PASS** |
| 2 | Opt-in pytest proves domain seed + discover→ingest→mock upstream→live detect | **PASS** (mocked gate + live_network deselected) |
| 3 | Default pytest and staged orchestrator remain mock-only | **PASS** |
| 4 | Golden pass | **PASS** (142) |
| 5 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_staged_detect_live_llm_spine.py -q -m "not live_network and not live_smoke"  # 6 passed
python -m pytest tests/golden -q    # 142 passed
python -m pytest -q                 # 621 passed, 20 deselected
python -m rge.modules.safety_auditor --audit full  # pass
```

Live Ollama proof (`live_network` + `live_smoke`) not run in this session (operator opt-in).

## Spec deviations

- Added CLI-level rejection when `--fixture` is combined with `--live-staged-detect-fallthrough` (audit mutual-exclusion; staged live path does not pass fixture to module).

## Merge to main

Pending merge commit.

## Recommended next ticket

**ticket-218** — README and AGENTS live staged detect live LLM operator docs.

## Suggested next prompt

`/rge-run-next-ticket`
