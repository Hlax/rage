# TICKET_QUEUE.md

## Purpose

This file tracks the implementation queue for the Research Graph Engine.

Agents may propose new tickets, but they must not silently reorder or broaden the queue without explaining why.

## Status Values

```txt
proposed
ready
in_progress
blocked
done
rejected
superseded
```

## Phase 0 / 0.5 Initial Queue

| Order | Ticket ID | Status | Title | Branch | Report |
|---:|---|---|---|---|---|
| 1 | ticket-001 | done | Scaffold repo and model runtime adapter | `phase-0/ticket-001-repo-scaffold-model-runtime` | `agent_reports/2026-06-11_phase-0_ticket-001_repo-scaffold-model-runtime.md` |
| 2 | ticket-002 | superseded | Add CLI help and config loading | | |
| 3 | ticket-003 | proposed | Add SQLite schema and migration harness | | |
| 4 | ticket-004 | superseded | Add golden test skeleton and fixtures | | |
| 5 | ticket-005 | superseded | Add public-site placeholder static build | | |
| 6 | ticket-006 | proposed | Add SQLite migration harness and source ingestion | | |

## Queue Notes (2026-06-11, ticket-001 agent)

- ticket-001 was implemented per its explicit expected-file list, which already
  included CLI help + config loading (ticket-002 scope), the schema placeholder
  and golden test skeleton with fixtures (parts of ticket-003/004 scope), and
  the public-site static placeholder (ticket-005 scope). This was the ticket's
  defined scope, not a silent broadening.
- ticket-002, ticket-004, and ticket-005 are marked `superseded` because their
  acceptance surfaces now exist and are covered by `tests/golden/test_00_*`.
  If review disagrees, reopen them rather than re-implementing.
- ticket-003 remains open: the migration harness was NOT built in Phase 0
  (schema.sql is a placeholder only). ticket-006 (`tickets/ticket-006.json`)
  proposes the smallest next step combining the migration harness with Golden
  Test 1 source ingestion; ticket-003 may be folded into it at review time.

## Ticket Template

```json
{
  "title": "",
  "problem": "",
  "evidence": [],
  "affected_modules": [],
  "expected_files": [],
  "acceptance_criteria": [],
  "test_plan": [],
  "non_goals": [],
  "risk_level": "low | medium | high | critical",
  "rollback_plan": "",
  "status": "proposed"
}
```

## Current Active Ticket

```txt
ticket-006 (proposed; awaiting review)
```

## Queue Rules

- Only one ticket should be `in_progress` per branch.
- A ticket cannot be marked `done` without a report in `agent_reports/`.
- A ticket cannot be marked `done` if required tests were not run or failures were not documented.
- If a ticket creates follow-up work, add the next smallest ticket instead of broadening scope.
