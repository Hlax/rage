---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 1 / ticket-021 / run-report

## 1. Summary

Implemented deterministic research run reporting for Golden Test 19. Added `ResearchRunRepository`, `RunReportRepository`, `generate-run-report` CLI command, run metric aggregation with machine-readable `top_failure_modes`, and Golden Test 19 (4 tests). All 89 golden tests pass without Ollama.

## 2. Ticket

- Ticket ID: ticket-021
- Ticket title: Add research run report (Golden Test 19)
- Branch: `phase-1/ticket-021-run-report`
- Phase: 1
- Agent/model: Cursor builder agent (Auto)
- Date: 2026-06-12

## 3. Scope

### In Scope

- `run_evaluator.py`: metric aggregation, failure mode rollup, report build/persist.
- `ResearchRunRepository` and `RunReportRepository` (no new migration).
- CLI `generate-run-report` with `--run-id`, `--topic`, `--domain`, `--contract`, `--output-dir`.
- Golden Test 19 (`tests/golden/test_19_run_report.py`).
- Pre-ticket-021 audit report (committed on main before branch).

### Out of Scope / Non-Goals

- Ollama, LangGraph, live web discovery, public write routes, full `research run` orchestrator, improvement ticket generation (GT20).

## 4. Changed Files

| File | Change Summary |
|---|---|
| `rge/modules/run_evaluator.py` | Full run report pipeline (was Phase 0 stub). |
| `rge/db/repositories.py` | `ResearchRunRepository`, `RunReportRepository`, `make_run_report_id`. |
| `rge/cli.py` | `generate-run-report` command. |
| `tests/golden/test_19_run_report.py` | New: Golden Test 19 (4 tests). |
| `tests/golden/test_00_scaffold.py` | CLI help scan for new command. |
| `tickets/TICKET_QUEUE.md` | ticket-021 done; ticket-022 proposed. |
| `tickets/ticket-021.json` | Status `done`. |
| `tickets/ticket-022.json` | Proposed improvement ticket generation. |

## 5. Implementation Notes

- Audit gate satisfied: `agent_reports/2026-06-12_pre-ticket-021_run-report-readiness-audit.md`.
- Implemented in `run_evaluator.py` per audit naming correction (ticket JSON listed `run_reporter.py`).
- Seeds golden contract before `research_runs` FK insert.
- Aggregates counters from `candidate_sources`, `sources`, `claims`, `relationships`, `score_events`, `public_cards`.
- `top_failure_modes` grouped by `rejection_reason` on rejected claims.
- Idempotent re-runs return `already_generated`.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| Deterministic run report after fixture spine without Ollama | PASS | GT19 spine. |
| Report JSON includes counters and machine-readable `top_failure_modes` | PASS | GT19 assertions. |
| `pytest tests/golden/test_19_run_report.py` | PASS | 4/4. |
| Existing golden tests still pass (85+) | PASS | 89/89. |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `python -m pytest tests/golden/test_19_run_report.py` | PASS | 4 passed. |
| `python -m pytest tests/golden` | PASS | 89 passed. |
| `python -m pytest` | PASS | 89 passed. |

## 8. Manual CLI Verification

Not run separately; Golden Test 19 exercises `generate-run-report` on temp DB.

## 9. Safety Audit

Not required: no public export, public site, or write routes changed. Run reports are internal observability artifacts only.

## 10. Spec Deviations

- Implemented `run_evaluator.py` instead of ticket JSON `run_reporter.py` (per pre-ticket-021 audit and existing module stub).
- Extended report with `report_type`, `schema_version`, `contract_id`, `cluster_reports_created`, `theory_candidates_created`, `safety_audit_status` per `08_REPORTING_SPEC.md` §6.

## 11. Merge to Main

- Merge commit: _(pending)_
- Branch: `phase-1/ticket-021-run-report` merged to `main` and pushed to `origin/main`.
- Post-merge pytest on `main`: _(pending)_

## 12. Recommended Next Ticket

**ticket-022**: Add improvement ticket generation (Golden Test 20).

## 13. Suggested Next Prompt

Pre-ticket audit recommended before ticket-022 (medium risk). Then:

```txt
/rge-run-next-ticket
```
