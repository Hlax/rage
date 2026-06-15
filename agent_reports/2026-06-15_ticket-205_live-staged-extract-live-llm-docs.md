---
template_id: implementation_report
status: done
date: 2026-06-15
phase: 2
ticket: ticket-205
---

# ticket-205: README and AGENTS Live Staged Extract Live LLM Operator Docs

## Summary

Documented ticket-204 per-step live Ollama staged extract in README Operator Quickstart
and AGENTS.md: env gates (`RGE_ALLOW_LIVE_STAGED_EXTRACT_LIVE_LLM=1`), pytest command
(`live_network` + `live_smoke`), CLI `--live-staged-fallthrough`, and explicit boundary
that the staged orchestrator remains mock-only.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-205 |
| Branch | `phase-2/ticket-205-live-staged-extract-live-llm-docs` |
| Date | 2026-06-15 |
| Risk | low |
| Principal audit gate | satisfied (204 since post-ticket-201 audit at ticket-202; cadence not yet overdue) |
| Main tip before branch | `1660d17` |

## Scope

**In:** README maturity table, live staged proofs intro, new live extract subsection;
AGENTS.md staged proof framing and live extract paragraph.

**Out:** Code changes, live link/build/detect docs, CI Ollama, public export/site.

## Changed files

| File | Change |
|------|--------|
| `README.md` | Live staged extract operator block; maturity/live-boundary clarifications |
| `AGENTS.md` | Per-step live extract opt-in; orchestrator mock-only boundary |
| `tickets/ticket-205.json` | Status `done` |
| `tickets/TICKET_QUEUE.md` | Mark done; seed ticket-206 |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | README documents live staged extract env gates and pytest command | **PASS** |
| 2 | AGENTS.md references per-step opt-in without implying orchestrator live LLM | **PASS** |
| 3 | Golden pass | **PASS** (142) |
| 4 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q                          # 142 passed
python -m pytest -q                                       # 605 passed, 17 deselected
python -m rge.modules.safety_auditor --audit full         # pass
```

## Manual CLI verification

Not required (docs-only ticket).

## Spec deviations

None.

## Merge to main

Placeholder — updated after merge.

## Recommended next ticket

**ticket-206** — Principal audit post-ticket-205 (cadence: 203–205 since ticket-202).

## Suggested next prompt

`/rge-principal-audit`
