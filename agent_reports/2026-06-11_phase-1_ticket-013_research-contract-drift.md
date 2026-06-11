---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 1 / ticket-013 / research-contract-drift

## 1. Summary

Implemented deterministic research contract drift gating for Golden Test 10 via `research validate-contract --follow-up <question>`. Follow-up questions are evaluated against a seeded Golden Test 10 contract; out-of-scope questions are parked with `out_of_scope_topic_drift`, while on-scope divergent-prompting questions are queued with priority scores. Golden Test 10 passes (4 tests); all 55 golden tests pass without Ollama.

## 2. Ticket

- Ticket ID: ticket-013
- Ticket title: Add research contract drift gating (Golden Test 10)
- Branch: `phase-1/ticket-013-research-contract-drift`
- Phase: 1
- Agent/model: Cursor builder agent (Auto)
- Date: 2026-06-11

## 3. Scope

### In Scope

- `research_planner`: contract seeding, follow-up validation, persistence orchestration.
- `ResearchContractRepository`, extended `ResearchQueueRepository` follow-up helpers.
- `research validate-contract` CLI with optional `--contract` and `--db`.
- Golden Test 10 (`tests/golden/test_10_research_contract_drift.py`).
- Updated scaffold CLI help for `validate-contract`.

### Out of Scope / Non-Goals

- Ollama, public export, LangGraph, full research run orchestration, live search discovery.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `rge/modules/research_planner.py` | Contract validation, golden contract seed, follow-up gating. |
| `rge/db/repositories.py` | `ResearchContractRepository`; follow-up queue insert/list helpers. |
| `rge/cli.py` | `validate-contract` subcommand. |
| `tests/golden/test_10_research_contract_drift.py` | New: Golden Test 10 (4 tests). |
| `tests/golden/test_00_scaffold.py` | CLI help includes `validate-contract`. |
| `tickets/TICKET_QUEUE.md` | ticket-013 done; ticket-014 proposed. |
| `tickets/ticket-013.json` | Status `done`. |
| `tickets/ticket-014.json` | Proposed public card export ticket. |

## 5. Implementation Notes

- Golden contract `contract_golden_test_10` seeded on first validate call.
- Out-of-scope detection uses deterministic phrase rules aligned with contract concepts (`AI consciousness` → `conscious` in question).
- On-scope acceptance requires topic_fit ≥ 0.65, evidence_fit ≥ 0.60, drift_risk ≤ drift_threshold (0.35).
- Follow-up question text stored in `research_queue.last_error` for question items (no new migration); machine-readable reason in `reason`.
- Idempotent re-evaluation returns `already_evaluated`.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| `validate-contract` evaluates follow-ups without Ollama | PASS | CLI + module. |
| Out-of-scope parked with `out_of_scope_topic_drift`; in-scope accepted | PASS | Golden Test 10 asserts. |
| `pytest tests/golden/test_10_research_contract_drift.py` | PASS | 4/4. |
| Existing golden tests still pass | PASS | 55/55. |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `python -m pytest tests/golden/test_10_research_contract_drift.py` | PASS | 4 passed in 0.80s. |
| `python -m pytest tests/golden` | PASS | 55 passed in 7.18s. |
| `python -m pytest` | PASS | 55 passed in 7.28s. |

## 8. Test Results

### Passing

- `tests/golden/test_10_research_contract_drift.py` — 4/4.
- All prior golden tests — 51/51 unchanged behavior plus scaffold CLI help update.

### Failing

- None.

## 9. Manual CLI Verification

Covered by golden tests: `validate-contract --follow-up` for both GT10 questions on fresh `--db`.

## 10. Safety Audit Status

- Required: no (no public export changes).
- Status: not run.

## 11. Spec Deviations

1. **Question text storage.** Follow-up question text is stored in `research_queue.last_error` for `item_type='question'` rows to avoid a new migration for `research_questions`.

## 12. Known Failures

- None.

## 13. Rollback Plan

Revert branch `phase-1/ticket-013-research-contract-drift`. Delete follow-up queue rows and golden contract from local SQLite if needed.

## 14. Merge to Main

- Instruction source: `AGENTS.md` step 9 (temporary).
- Pre-merge `main` tip: `2e5b214661d1334a5086b7c489cb53ec25a7b4bc`
- Branch: `phase-1/ticket-013-research-contract-drift`
- Merge result: pending (record hash below after merge/push).

## 15. Recommended Next Ticket

**ticket-014: Add public card export with safety filtering (Golden Test 11)**

See `tickets/ticket-014.json`.

## 16. Can the Loop Continue?

**Yes.** Contract drift gating is in place. ticket-014 (public card export) is the smallest next step toward Golden Test 11 with safety boundaries.

## 17. Suggested Next Prompt

Run `/rge-run-next-ticket` to implement ticket-014 on branch `phase-1/ticket-014-public-card-export`.
