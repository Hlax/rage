---
template_id: implementation_report
status: done
date: 2026-06-14
phase: 2
ticket: ticket-133
---

# ticket-133: README NM-4 Evidence DB Operator Quickstart

## Summary

Added a single **NM-4 evidence DB operator spine** section to README Operator
Quickstart documenting the gitignored evidence DB path, live `--live-manual-*`
fall-through CLI sequence (tickets 127–130), deterministic follow-up reconcile with
`--evidence-db-reconcile` (ticket-131), and `nm4_evidence_spine_status` in
`operator_loop --mode plan` (ticket-132).

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-133 |
| Branch | `phase-2/ticket-133-readme-nm4-evidence-operator-quickstart` |
| Date | 2026-06-14 |
| Risk | low |
| Pre-ticket audit | Not required |
| Principal audit gate | `agent_reports/2026-06-14_principal-audit-post-ticket-130.md` (2 done since at start; 3 after this merge triggers cadence) |
| Main tip before branch | `a104f4b` |

## Scope

### In

- README Operator Quickstart NM-4 section (steps 1–8 + plan visibility)

### Out

- Code/schema changes
- AGENTS.md rewrite
- Maturity table update
- Public export/site changes

## Changed files

| File | Change |
|------|--------|
| `README.md` | NM-4 evidence DB operator spine quickstart |
| `tickets/ticket-133.json` | status done |
| `tickets/ticket-134.json` | seeded principal audit checkpoint |
| `tickets/TICKET_QUEUE.md` | ticket-133 done |

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | README documents evidence DB path and CLI spine | **PASS** |
| 2 | Documents operator_loop `nm4_evidence_spine_status` | **PASS** |
| 3 | No code or schema changes | **PASS** |
| 4 | Golden tests mock-only pass | **PASS** (142) |
| 5 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"; $env:RGE_ALLOW_LIVE_LLM = "0"
python -m pytest tests/golden -q   # 142 passed
python -m pytest -q              # 487 passed, 6 deselected
python -m rge.modules.safety_auditor --audit full   # pass
```

## Manual CLI verification

Not required (docs-only ticket). README commands match ticket-127/131 operator proofs and ticket-132 plan block fields.

## Spec deviations

None.

## Merge to main

Pending merge.

## Recommended next ticket

**ticket-134** — Principal audit checkpoint post-ticket-133 (cadence: 3 done since post-ticket-130 audit).

## Suggested next prompt

`/rge-principal-audit` or `/rge-run-next-ticket` for ticket-134 audit checkpoint before further NM-4 work.
