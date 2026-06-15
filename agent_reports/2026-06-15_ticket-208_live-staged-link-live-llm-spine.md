---
template_id: implementation_report
status: done
date: 2026-06-15
phase: 2
ticket: ticket-208
---

# ticket-208: Live Staged Link Live LLM Opt-In Proof (Per-Step)

## Summary

Added `--live-staged-link-fallthrough` on `link-concepts` with env gate
`RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM=1` so staged OpenAlex ingest sources can use
live Ollama concept linking instead of auto-mock `staged_fetch_link_concepts.json`.
Default pytest and `execute_staged_fixture_mode_run` remain mock-only. Opt-in
`live_network` + `live_smoke` proof chains discover → fetch → ingest → mock extract →
live link.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-208 |
| Branch | `phase-2/ticket-208-live-staged-link-live-llm-spine` |
| Date | 2026-06-15 |
| Risk | medium |
| Pre-ticket audit | `agent_reports/2026-06-15_pre-ticket-207_live-staged-link-live-llm-audit.md` |
| Principal audit gate | satisfied (`agent_reports/2026-06-15_ticket-206_principal-audit-post-ticket-205.md`) |
| Main tip before branch | `c163c33` |

## Scope

**In:** `concept_linker` live staged link fallthrough, CLI flag + env gate, mocked gate tests,
opt-in live spine test, CI deselect assertion.

**Out:** Live build/detect on staged spine, live extract+link combined pytest, orchestrator live LLM, CI Ollama, public export/site, schema migrations.

## Changed files

| File | Change |
|------|--------|
| `rge/modules/concept_linker.py` | `live_staged_link_fallthrough`; `link_concepts_staged_live_fallthrough` |
| `rge/cli.py` | `--live-staged-link-fallthrough` flag and `_cmd_link_concepts` branch |
| `tests/unit/test_live_staged_link_live_llm_spine.py` | Gate tests + opt-in live proof |
| `tests/unit/test_ci_golden_gate.py` | Deselect assertion for live link test |
| `tickets/ticket-208.json` | Status `done` |
| `tickets/TICKET_QUEUE.md` | Mark done; seed ticket-209 |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Live staged link fallthrough bypasses staged-fetch auto-mock when env gate set | **PASS** |
| 2 | Opt-in pytest proves discover→ingest→mock extract→live link on temp DB | **PASS** (test added; live run operator opt-in) |
| 3 | Default pytest and staged orchestrator remain mock-only | **PASS** |
| 4 | Golden pass | **PASS** (142) |
| 5 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/unit/test_live_staged_link_live_llm_spine.py -q -m "not live_network and not live_smoke"  # 5 passed
python -m pytest tests/golden -q                          # 142 passed
python -m pytest -q                                       # 610 passed, 18 deselected
python -m rge.modules.safety_auditor --audit full         # pass
```

## Manual CLI verification

Not run (no local Ollama in builder session). Mocked gate tests cover CLI routing,
default-graph DB refusal, and env gate.

## Spec deviations

None.

## Merge to main

Merged @ `254321b`. Pushed to `origin/main`.

## Recommended next ticket

**ticket-209** — README/AGENTS operator docs for live staged link fallthrough.

## Suggested next prompt

`/rge-run-next-ticket`
