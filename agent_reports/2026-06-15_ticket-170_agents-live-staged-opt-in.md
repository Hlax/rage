---
template_id: implementation_report
status: done
date: 2026-06-15
phase: 2
ticket: ticket-170
---

# ticket-170: AGENTS.md Cross-Link Live Staged Opt-In Proofs

## Summary

Added AGENTS.md maturity-tier cross-link and env gate summary for opt-in live staged
network proofs (tickets 167–169), pointing operators to README Operator Quickstart
for full pytest commands.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-170 |
| Branch | `phase-2/ticket-170-agents-live-staged-opt-in` |
| Date | 2026-06-15 |
| Risk | low |
| Principal audit gate | `agent_reports/2026-06-15_principal-audit-post-ticket-169.md` (included in commit) |
| Main tip before branch | `21d20ed` |

## Scope

### In

- `AGENTS.md` — arbitrary-source maturity bullet + live staged network proofs paragraph
- `agent_reports/2026-06-15_principal-audit-post-ticket-169.md` (untracked from prior audit run)

### Out

- Code, CI, public site, live LLM

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | AGENTS.md references README live staged proofs + env gates | **PASS** |
| 2 | Golden pass | **PASS** (142) |
| 3 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q   # 142 passed
python -m pytest -q                # 591 passed, 8 deselected
python -m rge.modules.safety_auditor --audit full  # pass
```

## Merge to main

Merge commit: `7e953cf5dcade097d3f964009ff82390b0b02500`

## Recommended next ticket

**ticket-171** — Pre-ticket audit for live staged extract mock-fixture spine (medium risk).

## Suggested next prompt

Write pre-ticket audit for ticket-171, then `/rge-run-next-ticket`.
