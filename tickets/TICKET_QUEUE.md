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
| 8 | ticket-008 | done | Add mock concept linking (Golden Test 5) | `phase-1/ticket-008-mock-concept-linking` | `agent_reports/2026-06-11_phase-1_ticket-008_mock-concept-linking.md` |
| 9 | ticket-009 | done | Add mock relationship builder (Golden Test 6) | `phase-1/ticket-009-mock-relationship-builder` | `agent_reports/2026-06-11_phase-1_ticket-009_mock-relationship-builder.md` |
| 10 | ticket-010 | proposed | Add score reconciliation with history (Golden Test 8) | | |

## Queue Notes (2026-06-11, ticket-009 agent)

- ticket-009 implemented `research build-relationships` with mock fixture drafting,
  deterministic validation, `0002_relationship_evidence` migration, and persistence of
  active relationships plus evidence links. Golden Test 6 passes (5 tests); all 41
  golden tests pass without Ollama.
- Confidence labels from mock candidates map deterministically to REAL scores
  (low=0.25, medium=0.5, high=0.75) in Python before DB write.
- ticket-010 proposes score reconciliation for Golden Test 8.

## Queue Notes (2026-06-11, ticket-008 agent)

- ticket-008 implemented `research link-concepts` with mock fixture linking, ontology
  seeding, and `claim_concepts` persistence. Golden Test 5 passes (3 tests); all 36
  golden tests pass without Ollama.
- No prior merge-to-main workflow existed; canonical docs specify human/checkpoint merge
  (`docs/agents/04_CURSOR_BUILD_LOOP.md`). Added temporary `AGENTS.md` step 9: merge
  ticket branch to `main` and push after each done ticket until the safety evaluator
  agent owns merge gating.
- ticket-008 branch merged to `main` and pushed (includes previously unmerged 001/006/007 work).
- ticket-009 proposes mock relationship builder for Golden Test 6.

## Queue Notes (2026-06-11, ticket-007 agent)

- ticket-007 implemented `research extract-claims` with mock LLM fixtures, deterministic
  validation (quote span, scope, overgeneralization), and persistence to `claims` +
  `claim_quotes`. Golden Test 2 passes (4 tests); all 33 golden tests pass without Ollama.
- ticket-008 proposes mock concept linking for Golden Test 5.

## Queue Notes (2026-06-11, ticket-006 agent)

- ticket-006 implemented the migration harness, reconciled claims lifecycle, and
  `research ingest`. Golden Test 1 passes (5 tests).
- On Windows, `research.exe` may not be on PATH; use `python -m rge.cli`.

## Current Active Ticket

```txt
ticket-010 (proposed; awaiting review)
```

## Queue Rules

- Only one ticket should be `in_progress` per branch.
- A ticket cannot be marked `done` without a report in `agent_reports/`.
- A ticket cannot be marked `done` if required tests were not run or failures were not documented.
- If a ticket creates follow-up work, add the next smallest ticket instead of broadening scope.
- **Temporary:** after a ticket is `done`, merge its branch to `main` and push per `AGENTS.md` step 9 until the safety evaluator agent is live.
