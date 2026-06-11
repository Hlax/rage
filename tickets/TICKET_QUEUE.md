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
| 3 | ticket-003 | superseded | Add SQLite schema and migration harness | | |
| 4 | ticket-004 | superseded | Add golden test skeleton and fixtures | | |
| 5 | ticket-005 | superseded | Add public-site placeholder static build | | |
| 6 | ticket-006 | done | Add SQLite migration harness and source ingestion | `phase-1/ticket-006-sqlite-migration-source-ingestion` | `agent_reports/2026-06-11_phase-1_ticket-006_sqlite-migration-source-ingestion.md` |

## Phase 1 Queue

| Order | Ticket ID | Status | Title | Branch | Report |
|---:|---|---|---|---|---|
| 7 | ticket-007 | done | Add mock claim extraction (Golden Test 2) | `phase-1/ticket-007-mock-claim-extraction` | `agent_reports/2026-06-11_phase-1_ticket-007_mock-claim-extraction.md` |
| 8 | ticket-008 | proposed | Add mock concept linking (Golden Test 5) | | |

## Queue Notes (2026-06-11, ticket-007 agent)

- ticket-007 implemented `research extract-claims` with mock LLM fixtures, deterministic
  validation (quote span, scope, overgeneralization), and persistence to `claims` +
  `claim_quotes`. Golden Test 2 passes (4 tests); all 33 golden tests pass without Ollama.
- Added `claim_extraction_creativity_scoped.json` for two accepted scoped claims; existing
  fixtures used for missing-quote and overgeneralized rejection tests via `--fixture`.
- ticket-008 proposes mock concept linking for Golden Test 5.

## Queue Notes (2026-06-11, ticket-006 agent)

- ticket-006 implemented the migration harness (`schema_migrations` + `0001_initial.sql`),
  reconciled claims lifecycle (`claims` + `claim_quotes` per 05_DATA_MODEL.md), and local
  text-file ingestion via `research ingest`. Golden Test 1 passes (5 tests); all 29 golden
  tests pass without Ollama.
- ticket-003 is marked `superseded` because its migration-harness scope is now delivered by
  ticket-006. Reopen only if review wants a separate migration-only ticket.
- On Windows, `research.exe` may not be on PATH; use `python -m rge.cli ingest ...`.

## Queue Notes (2026-06-11, ticket-001 agent)

- ticket-001 was implemented per its explicit expected-file list, which already
  included CLI help + config loading (ticket-002 scope), the schema placeholder
  and golden test skeleton with fixtures (parts of ticket-003/004 scope), and
  the public-site static placeholder (ticket-005 scope). This was the ticket's
  defined scope, not a silent broadening.
- ticket-002, ticket-004, and ticket-005 are marked `superseded` because their
  acceptance surfaces now exist and are covered by `tests/golden/test_00_*`.
  If review disagrees, reopen them rather than re-implementing.

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
ticket-008 (proposed; awaiting review)
```

## Queue Rules

- Only one ticket should be `in_progress` per branch.
- A ticket cannot be marked `done` without a report in `agent_reports/`.
- A ticket cannot be marked `done` if required tests were not run or failures were not documented.
- If a ticket creates follow-up work, add the next smallest ticket instead of broadening scope.
