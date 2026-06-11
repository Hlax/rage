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
| 1 | ticket-001 | ready | Scaffold repo and model runtime adapter | `phase-0/ticket-001-repo-scaffold-model-runtime` | |
| 2 | ticket-002 | proposed | Add CLI help and config loading | | |
| 3 | ticket-003 | proposed | Add SQLite schema and migration harness | | |
| 4 | ticket-004 | proposed | Add golden test skeleton and fixtures | | |
| 5 | ticket-005 | proposed | Add public-site placeholder static build | | |

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
ticket-001
```

## Queue Rules

- Only one ticket should be `in_progress` per branch.
- A ticket cannot be marked `done` without a report in `agent_reports/`.
- A ticket cannot be marked `done` if required tests were not run or failures were not documented.
- If a ticket creates follow-up work, add the next smallest ticket instead of broadening scope.
