---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 1 / ticket-012 / mock-research-queue

## 1. Summary

Implemented deterministic research queue ranking for Golden Test 9 via `research queue-sources`. Added migration `0003_candidate_sources_research_queue`, fixture-driven ranking with contract formula `golden_v0.1.0`, and persistence to `candidate_sources` plus `research_queue`. Empirical paper ranks first; marketing page is rejected; all queue items carry required scores and reasons. Golden Test 9 passes (3 tests); all 51 golden tests pass without Ollama.

## 2. Ticket

- Ticket ID: ticket-012
- Ticket title: Add mock research queue ranking (Golden Test 9)
- Branch: `phase-1/ticket-012-mock-research-queue`
- Phase: 1
- Agent/model: Cursor builder agent (Auto)
- Date: 2026-06-11

## 3. Scope

### In Scope

- `research_queue`: fixture load, deterministic ranking, enqueue orchestration.
- Migration `0003_candidate_sources_research_queue.sql` and `schema.sql` mirror.
- `CandidateSourceRepository`, `ResearchQueueRepository`.
- `research queue-sources` CLI with optional `--fixture`, `--question`, `--db`.
- Golden Test 9 (`tests/golden/test_09_research_queue.py`).
- Updated scaffold and ingestion golden tests for new tables/migration.

### Out of Scope / Non-Goals

- Ollama, live source discovery, public export, LangGraph, full research run orchestration.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `rge/db/migrations/0003_candidate_sources_research_queue.sql` | New: `candidate_sources`, `research_queue` tables. |
| `rge/db/schema.sql` | Mirror migration 0003 tables. |
| `rge/modules/research_queue.py` | Fixture ranking, priority formula, enqueue. |
| `rge/db/repositories.py` | Candidate/queue repositories. |
| `rge/cli.py` | `queue-sources` subcommand. |
| `tests/golden/test_09_research_queue.py` | New: Golden Test 9 (3 tests). |
| `tests/golden/test_00_scaffold.py` | CLI help + schema tables. |
| `tests/golden/test_01_ingestion.py` | Expect migration 0003. |
| `tickets/TICKET_QUEUE.md` | ticket-012 done; ticket-013 proposed. |
| `tickets/ticket-012.json` | Status `done`. |
| `tickets/ticket-013.json` | Proposed contract drift ticket. |

## 5. Implementation Notes

- Ranking uses deterministic per-candidate profiles keyed by fixture IDs plus source-type credibility weights from `domain_packs/creativity/source_preferences.yaml`.
- Priority formula matches `09_RESEARCH_RUN_CONTRACT.md` section 7 weights.
- Marketing pages get `status=rejected` and are excluded from active `research_queue` rows.
- Idempotent re-run returns `already_queued`.
- Default fixture: `fixtures/candidate_sources/source_ranking_fixture.json`.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| CLI ranks fixture candidates without Ollama | PASS | `queue-sources`. |
| Empirical above marketing; required fields on items | PASS | Golden Test 9 asserts. |
| `pytest tests/golden/test_09_research_queue.py` | PASS | 3/3. |
| Existing golden tests still pass | PASS | 51/51. |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `python -m pytest tests/golden/test_09_research_queue.py` | PASS | 3 passed in 0.76s. |
| `python -m pytest tests/golden` | PASS | 51 passed in 6.59s. |
| `python -m pytest` | PASS | 51 passed in 6.51s. |

## 8. Test Results

### Passing

- `tests/golden/test_09_research_queue.py` — 3/3.
- All prior golden tests — 48/48 plus migration/scaffold updates.

### Failing

- None.

## 9. Manual CLI Verification

Covered by golden tests: `queue-sources --db <temp>` emits ranked queue JSON; SQLite contains 5 candidates (4 queued, 1 rejected marketing).

## 10. Safety Audit Status

- Required: no.
- Status: not run.

## 11. Spec Deviations

1. **Migration 0003 added** though not listed in ticket JSON `expected_files`; required for durable queue persistence (same pattern as ticket-009 `0002`).
2. **Rejected marketing** stored in `candidate_sources` with `status=rejected` but omitted from active `research_queue` rows.

## 12. Known Failures

- None.

## 13. Rollback Plan

Revert branch `phase-1/ticket-012-mock-research-queue`. Delete candidate/queue rows from local SQLite or recreate DB.

## 14. Merge to Main

- Instruction source: `AGENTS.md` step 9 (temporary).
- Pre-merge `main` tip: `f4188174e0e707377e64ac091cbb186ac393638b`
- Branch: `phase-1/ticket-012-mock-research-queue`
- Merge result: pending (record hash below after merge/push).

## 15. Recommended Next Ticket

**ticket-013: Add research contract drift gating (Golden Test 10)**

See `tickets/ticket-013.json`.

## 16. Can the Loop Continue?

**Yes.** Queue ranking is in place. ticket-013 (contract drift) is the smallest next step toward Golden Test 10.

## 17. Suggested Next Prompt

Run `/rge-run-next-ticket` to implement ticket-013 on branch `phase-1/ticket-013-research-contract-drift`.
