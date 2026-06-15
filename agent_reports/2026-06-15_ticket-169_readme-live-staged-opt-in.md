---
template_id: implementation_report
status: done
date: 2026-06-15
phase: 2
ticket: ticket-169
---

# ticket-169: README Operator Quickstart for Live Staged Opt-In Proofs

## Summary

Documented opt-in `live_network` pytest commands and env gates for ticket-167
(discover→fetch) and ticket-168 (discover→fetch→ingest-staged) in README Operator
Quickstart. Updated maturity table to note these proofs are operator opt-in, not CI.

## Ticket metadata

| Field | Value |
|-------|-------|
| Ticket ID | ticket-169 |
| Branch | `phase-2/ticket-169-readme-live-staged-opt-in` |
| Date | 2026-06-15 |
| Risk | low |
| Principal audit gate | `agent_reports/2026-06-15_principal-audit-post-ticket-168.md` (committed on main before branch) |
| Main tip before branch | `f7626a2` (includes principal audit commit) |

## Scope

### In

- `README.md` — maturity table + Operator Quickstart live staged proofs section

### Out

- Code, CI, public site, live LLM

## Acceptance criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | README documents env gates and pytest for 167/168 | **PASS** |
| 2 | Maturity table notes opt-in operator proof | **PASS** |
| 3 | Golden pass | **PASS** (142) |
| 4 | Safety audit pass | **PASS** |

## Commands run

```powershell
$env:RGE_LLM_MODE = "mock"
python -m pytest tests/golden -q   # 142 passed
python -m pytest -q                # 591 passed, 8 deselected
python -m rge.modules.safety_auditor --audit full  # pass
```

## Merge to main

Pending merge (see post-merge commit for hash).

## Recommended next ticket

**ticket-170** — AGENTS.md cross-link live staged opt-in operator proofs.

## Suggested next prompt

`/rge-run-next-ticket`
