---
template_id: implementation_report
status: done
date: 2026-06-15
phase: 2
ticket: ticket-201
---

# ticket-201: Live Staged Run Without Fixture-Mode Flag

## Summary

Updated `_cmd_run` so `research run --staged-spine` routes to
`execute_staged_fixture_mode_run` without requiring `--fixture-mode`. Bare
`run --topic --domain` remains `not_implemented` (GT26). Added patched-network unit
test and README/AGENTS contract clarification.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-201 |
| Branch | `phase-2/ticket-201-live-staged-run-without-fixture-mode` |
| Date | 2026-06-15 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-15_pre-ticket-200_research-run-non-fixture-audit.md` |
| Principal audit gate | cadence overdue (198–200 since post-ticket-197); pre-ticket audit satisfied |
| Main tip before branch | `29073aa` |

## Scope

**In:** CLI routing, parser help, unit test, docs.

**Out:** Full live MVP, live Ollama orchestration, CI live network, public export/site, schema.

## Changed files

| File | Change |
|------|--------|
| `rge/cli.py` | Route `--staged-spine` without `--fixture-mode`; updated help and not_implemented hint |
| `tests/unit/test_staged_fixture_mode_run_spine.py` | New `test_staged_spine_run_cli_entry_without_fixture_mode` |
| `README.md` | Primary `--staged-spine` entry; contract note; command table |
| `AGENTS.md` | Maturity framing and live staged docs |
| `tickets/ticket-201.json` | Status `done` |
| `tickets/TICKET_QUEUE.md` | Mark done; seed ticket-202 |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `--staged-spine` works without `--fixture-mode` | **PASS** |
| 2 | Bare run without flags remains not_implemented | **PASS** (GT26) |
| 3 | Patched-network unit test for new entry | **PASS** |
| 4 | Docs clarify staged-spine vs fixture MVP | **PASS** |
| 5 | Golden pass | **PASS** (142) |
| 6 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden/test_26_full_mvp_run.py -q  # 8 passed
python -m pytest tests/golden -q                          # 142 passed
python -m pytest tests/unit/test_staged_fixture_mode_run_spine.py -q  # 4 passed
python -m pytest -q                                       # 600 passed, 16 deselected
python -m rge.modules.safety_auditor --audit full         # pass
```

## Manual CLI verification

Not run (patched-network unit test covers new CLI entry; no live OpenAlex in builder).

## Spec deviations

None.

## Merge to main

Merged @ `036701e`. Pushed to `origin/main`.

## Recommended next ticket

**ticket-202** — Principal audit post-ticket-201 (cadence overdue).

## Suggested next prompt

`/rge-principal-audit`
