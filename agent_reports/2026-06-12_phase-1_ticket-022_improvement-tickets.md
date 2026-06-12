---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 1 / ticket-022 / improvement-tickets

## 1. Summary

Implemented deterministic improvement ticket generation for Golden Test 20. Added `ImprovementTicketRepository`, full `ticket_writer.py` with failure-mode templates, `generate-improvement-tickets` CLI command, and Golden Test 20 (4 tests). All 93 golden tests pass without Ollama.

## 2. Ticket

- Ticket ID: ticket-022
- Ticket title: Add improvement ticket generation (Golden Test 20)
- Branch: `phase-1/ticket-022-improvement-tickets`
- Phase: 1
- Agent/model: Cursor builder agent (Auto)
- Date: 2026-06-12

## 3. Scope

### In Scope

- `ticket_writer.py`: deterministic templates for `overgeneralized_scope`, `missing_quote_span`, `weak_concept_mapping`.
- `ImprovementTicketRepository` and `make_improvement_ticket_id` (no new migration).
- CLI `generate-improvement-tickets` with `--run-id`, `--db`, optional `--output-dir`.
- Golden Test 20 (`tests/golden/test_20_improvement_tickets.py`).
- Pre-ticket-022 audit report (committed on main before branch).

### Out of Scope / Non-Goals

- Ollama, LangGraph, live web discovery, public write routes, builder ticket consumption validation (GT21).

## 4. Changed Files

| File | Change Summary |
|---|---|
| `rge/modules/ticket_writer.py` | Full improvement ticket pipeline (was Phase 0 stub). |
| `rge/db/repositories.py` | `ImprovementTicketRepository`, `ImprovementTicketRecord`, `make_improvement_ticket_id`. |
| `rge/cli.py` | `generate-improvement-tickets` command. |
| `tests/golden/test_20_improvement_tickets.py` | New: Golden Test 20 (4 tests). |
| `tests/golden/test_00_scaffold.py` | CLI help scan for new command. |
| `tickets/TICKET_QUEUE.md` | ticket-022 done; ticket-023 proposed. |
| `tickets/ticket-022.json` | Status `done`. |
| `tickets/ticket-023.json` | Proposed builder-consumable ticket validation. |

## 5. Implementation Notes

- Audit gate satisfied: `agent_reports/2026-06-12_pre-ticket-022_improvement-tickets-readiness-audit.md` (commit `ce9e658`).
- Reads persisted run report via `RunReportRepository.get_by_run_id`.
- Idempotent re-runs keyed on `make_improvement_ticket_id(run_id, failure_reason)`.
- Primary golden ticket for `overgeneralized_scope`: title **"Improve claim extractor scope preservation"**, priority `high`, status `draft`.
- Writes `improvement_ticket_latest.json` under report dir when `--output-dir` is set.
- Golden spine: overgeneralized on base source + missing_quote on followup → `generate-run-report` → `generate-improvement-tickets`.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| Deterministic improvement ticket generation from run report failure modes without Ollama | PASS | GT20 spine. |
| Tickets include evidence, expected files, acceptance criteria, test plan, non-goals, rollback plan | PASS | Template fields asserted in GT20. |
| `pytest tests/golden/test_20_improvement_tickets.py` | PASS | 4/4. |
| Existing golden tests still pass (89+) | PASS | 93/93. |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `python -m pytest tests/golden/test_20_improvement_tickets.py` | PASS | 4 passed. |
| `python -m pytest tests/golden` | PASS | 93 passed. |
| `python -m pytest` | PASS | 93 passed. |

## 8. Manual CLI Verification

Not run separately; Golden Test 20 exercises `generate-improvement-tickets` on temp DB.

## 9. Safety Audit

Not required: no public export, public site, or write routes changed. Improvement tickets are internal draft artifacts only.

## 10. Spec Deviations

None.

## 11. Merge to Main

- Merge commit: `8b7375a22cdd55994278a4e7d6063e812ffd0326`
- Branch: `phase-1/ticket-022-improvement-tickets` merged to `main` and pushed to `origin/main`.
- Post-merge pytest on `main`: 93 passed.

## 12. Recommended Next Ticket

**ticket-023**: Validate improvement tickets for builder consumption (Golden Test 21).

## 13. Suggested Next Prompt

Pre-ticket audit recommended before ticket-023 if risk is medium. Then:

```txt
/rge-run-next-ticket
```
