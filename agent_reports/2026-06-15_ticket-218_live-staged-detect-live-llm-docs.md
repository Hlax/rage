---
template_id: implementation_report
status: done
date: 2026-06-15
phase: 2
ticket: ticket-218
---

# ticket-218: README and AGENTS Live Staged Detect Live LLM Operator Docs

## Summary

Documented ticket-217 per-step live Ollama staged detect in README Operator Quickstart
and AGENTS.md: env gates (`RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM=1`), pytest command
(`live_network` + `live_smoke`), CLI `--live-staged-detect-fallthrough`, mock extract +
mock link + mock build upstream, domain seed requirement, and orchestrator mock-only
boundary.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-218 |
| Branch | `phase-2/ticket-218-live-staged-detect-live-llm-docs` |
| Date | 2026-06-15 |
| Risk | low |
| Principal audit gate | cadence overdue; `implementation_gate: satisfied` for docs-only ticket |
| Prior checkpoint | `agent_reports/2026-06-15_ticket-215_principal-audit-post-ticket-213.md` |
| Main tip before branch | `fa3b772` |

## Scope

**In:** README maturity bullet + Operator Quickstart live detect subsection; AGENTS.md
per-step live detect paragraph; maturity tier bullet update.

**Out:** Code changes, `.env.example`, runtime config table, CI Ollama, public export/site.

## Changed files

| File | Change |
|------|--------|
| `README.md` | Live staged detect operator block; maturity live-boundary bullet |
| `AGENTS.md` | Per-step live detect opt-in; reconcile mock-only boundary |
| `tickets/ticket-218.json` | Status `done` |
| `tickets/ticket-219.json` | Seeded principal audit post-ticket-217 |
| `tickets/TICKET_QUEUE.md` | Mark done; seed ticket-219 |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | README documents `RGE_ALLOW_LIVE_STAGED_DETECT_LIVE_LLM` opt-in pytest command | **PASS** |
| 2 | Docs preserve orchestrator mock-only boundary | **PASS** |
| 3 | Domain seed + mock upstream chain documented | **PASS** |
| 4 | Golden pass | **PASS** (142) |
| 5 | Full pytest pass | **PASS** (621, 20 deselected) |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q    # 142 passed
python -m pytest -q                 # 621 passed, 20 deselected
```

Safety audit not required (docs-only ticket).

## Manual CLI verification

Not required (docs-only ticket).

## Spec deviations

None.

## Merge to main

Pending merge commit.

## Recommended next ticket

**ticket-219** — Principal audit post-ticket-217 staged live detect checkpoint (cadence overdue).

## Suggested next prompt

`/rge-principal-audit` or `/rge-run-next-ticket` for ticket-219
