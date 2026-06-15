---
template_id: implementation_report
status: done
date: 2026-06-15
phase: 2
ticket: ticket-209
---

# ticket-209: README and AGENTS Live Staged Link Live LLM Operator Docs

## Summary

Documented ticket-208 per-step live Ollama staged link in README Operator Quickstart
and AGENTS.md: env gates (`RGE_ALLOW_LIVE_STAGED_LINK_LIVE_LLM=1`), pytest command
(`live_network` + `live_smoke`), CLI `--live-staged-link-fallthrough`, mock-extract
upstream note, and explicit orchestrator mock-only boundary.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-209 |
| Branch | `phase-2/ticket-209-live-staged-link-live-llm-docs` |
| Date | 2026-06-15 |
| Risk | low |
| Principal audit gate | **overdue** (206–208 since ticket-206 checkpoint); docs-only ticket; recommend audit at ticket-210 |
| Main tip before branch | `cc06123` |

## Scope

**In:** README maturity table, live staged proofs intro, new live link subsection;
AGENTS.md staged proof framing and live link paragraph.

**Out:** Code changes, live build/detect docs, CI Ollama, public export/site.

## Changed files

| File | Change |
|------|--------|
| `README.md` | Live staged link operator block; maturity/live-boundary clarifications |
| `AGENTS.md` | Per-step live link opt-in; build/detect mock-only boundary |
| `tickets/ticket-209.json` | Status `done` |
| `tickets/TICKET_QUEUE.md` | Mark done; seed ticket-210 |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | README documents live staged link env gates and pytest command | **PASS** |
| 2 | AGENTS.md references per-step opt-in without implying orchestrator live LLM | **PASS** |
| 3 | Golden pass | **PASS** (142) |
| 4 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q                          # 142 passed
python -m pytest -q                                       # 610 passed, 18 deselected
python -m rge.modules.safety_auditor --audit full         # pass
```

## Manual CLI verification

Not required (docs-only ticket).

## Spec deviations

None.

## Merge to main

Merged @ `ba6453e`. Pushed to `origin/main`.

## Recommended next ticket

**ticket-210** — Principal audit post-ticket-209 (cadence overdue).

## Suggested next prompt

`/rge-principal-audit`
