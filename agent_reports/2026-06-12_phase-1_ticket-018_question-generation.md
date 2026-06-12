---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 1 / ticket-018 / question-generation

## 1. Summary

Implemented contract-respecting follow-up question generation for Golden Test 16. Added `generate-followup-questions` CLI command, cluster/theory context proposal, extended contract validation for labor-displacement and adjacent copyright topics, mock fixture, and Golden Test 16 (4 tests). All 77 golden tests pass without Ollama.

## 2. Ticket

- Ticket ID: ticket-018
- Ticket title: Add contract-respecting question generation (Golden Test 16)
- Branch: `phase-1/ticket-018-question-generation`
- Phase: 1
- Agent/model: Cursor builder agent (Auto)
- Date: 2026-06-12

## 3. Scope

### In Scope

- `research_planner.py`: propose/generate follow-ups from cluster/theory context, extended validation rules.
- `ResearchQueueRepository.count_followups_by_status`.
- CLI `generate-followup-questions`.
- Fixture `fixtures/llm_outputs/followup_question_generation_golden_test_16.json`.
- Golden Test 16 (`tests/golden/test_16_question_generation.py`).
- Pre-ticket-018 audit report.

### Out of Scope / Non-Goals

- Ollama, LangGraph, live web discovery, public write routes, schema migrations.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `rge/modules/research_planner.py` | Follow-up proposal, batch generation, adjacent/copyright parking. |
| `rge/db/repositories.py` | `count_followups_by_status`. |
| `rge/cli.py` | `generate-followup-questions` command. |
| `fixtures/llm_outputs/followup_question_generation_golden_test_16.json` | GT16 question fixture. |
| `tests/golden/test_16_question_generation.py` | New: Golden Test 16 (4 tests). |
| `tests/golden/test_00_scaffold.py` | CLI help scan for new command. |
| `agent_reports/2026-06-12_pre-ticket-018_question-generation-readiness-audit.md` | Pre-ticket audit. |
| `tickets/TICKET_QUEUE.md` | ticket-018 done; ticket-019 proposed. |
| `tickets/ticket-018.json` | Status `done`. |
| `tickets/ticket-019.json` | Proposed ontology pressure ticket. |

## 5. Implementation Notes

- Audit gate satisfied: `agent_reports/2026-06-12_pre-ticket-018_question-generation-readiness-audit.md`.
- Reuses GT10 `validate_followup_for_contract` persistence to `research_queue`.
- Merges cluster report `candidate_next_questions` and theory `next_questions` with fixture/golden batch.
- Copyright questions parked with `adjacent_out_of_scope_topic`; consciousness/jobs use `out_of_scope_topic_drift`.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| Deterministic on-scope/parked generation from cluster/theory context | PASS | GT16 spine. |
| Active queue + parked with machine-readable reasons | PASS | GT16 assertions. |
| `pytest tests/golden/test_16_question_generation.py` | PASS | 4/4. |
| Existing golden tests still pass (73+) | PASS | 77/77. |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `python -m pytest tests/golden/test_16_question_generation.py` | PASS | 4 passed. |
| `python -m pytest tests/golden` | PASS | 77 passed. |
| `python -m pytest` | PASS | 77 passed. |

## 8. Manual CLI Verification

Not run separately; Golden Test 16 exercises full intelligence context + `generate-followup-questions`.

## 9. Safety Audit

Not required: no public export, public site, or write routes changed.

## 10. Spec Deviations

- Added fixture file (supporting artifact; not listed in ticket JSON `expected_files`).
- Extra cluster/theory context questions may queue in addition to GT16 batch when they pass contract validation.

## 11. Merge to Main

*(Updated after merge.)*

## 12. Recommended Next Ticket

**ticket-019**: Add ontology pressure report (Golden Test 17).

## 13. Suggested Next Prompt

```txt
/rge-run-next-ticket
```
