---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 1 / ticket-028 / full-mvp-run

## 1. Summary

Implemented Golden Test 26 fixture-mode full MVP orchestration via `research run --fixture-mode`. Added `execute_fixture_mode_run()` in `rge/cli.py` chaining contract creation, fixture queueing, three-source ingest/extract/link/relationship/contradiction/score pipeline, cluster/theory reports, public export, run report, improvement tickets, and full safety audit validation. Added Golden Test 26 (4 tests). All 118 golden tests pass without Ollama; public site builds 11 static pages; full safety audit returns `pass`.

## 2. Ticket

- Ticket ID: ticket-028
- Ticket title: Full MVP end-to-end golden run (Golden Test 26)
- Branch: `phase-1/ticket-028-full-mvp-run`
- Phase: 1
- Agent/model: Cursor builder agent (GPT-5.5)
- Date: 2026-06-12
- Main tip before branch: `08d0940` (includes pre-ticket-028 env audit)

## 3. Scope

### In Scope

- Fixture-mode `research run` orchestrator in `rge/cli.py`.
- Golden Test 26 (`tests/golden/test_26_full_mvp_run.py`).
- Scaffold test update for non-fixture `run` placeholder behavior.
- Full safety audit GT26 evidence check.

### Out of Scope / Non-Goals

- Ollama, LangGraph, live web discovery, public write routes, provider API adapters.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `rge/cli.py` | `execute_fixture_mode_run()`, fixture-mode `_cmd_run`, CLI flags (`--db`, `--run-id`, `--output-dir`, `--ticket-dir`, `--export-dir`). |
| `tests/golden/test_26_full_mvp_run.py` | New: Golden Test 26 (4 tests). |
| `tests/golden/test_00_scaffold.py` | Non-fixture `run` remains not implemented. |
| `rge/modules/safety_auditor.py` | Full audit GT26 evidence check. |
| `tickets/TICKET_QUEUE.md` | ticket-028 done; ticket-029 proposed. |
| `tickets/ticket-028.json` | Status `done`. |

## 5. Implementation Notes

- Audit gate satisfied: `agent_reports/2026-06-12_pre-ticket-028_env-and-model-config-audit.md` (commit `08d0940`).
- Pipeline forces `RGE_LLM_MODE=mock` for all LLM steps; no provider keys required.
- Default artifact paths: `data/db/`, `data/reports/`, `data/exports/`, `apps/public-site/public/data/`, `tickets/improvement_ticket_latest.json`.
- Live `research run` without `--fixture-mode` still returns `not_implemented`.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| Fixture-mode `research run` produces accepted claims, public cards, improvement tickets | PASS | GT26 graph artifact test. |
| Public export and safety audit pass after full run | PASS | Orchestrator validates export + `run_safety_audit(full)`. |
| `pytest tests/golden/test_26_full_mvp_run.py` | PASS | 4/4. |
| Existing golden tests still pass (114+) | PASS | 118/118. |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| `RGE_LLM_MODE=mock python -m pytest tests/golden/test_26_full_mvp_run.py` | PASS | 4 passed. |
| `RGE_LLM_MODE=mock python -m pytest tests/golden` | PASS | 118 passed. |
| `RGE_LLM_MODE=mock python -m pytest` | PASS | 118 passed. |
| `RGE_LLM_MODE=mock python -m rge.modules.safety_auditor --audit full` | PASS | status `pass`, exit 0. |
| `cd apps/public-site && npm run build` | PASS | 11 static pages. |

## 8. Manual CLI Verification

```powershell
$env:RGE_LLM_MODE = "mock"
python -m rge.cli run `
  --topic "Does AI improve creative output while reducing diversity?" `
  --domain creativity `
  --fixture-mode
```

Returns `status: completed` JSON with artifacts map when run against default DB paths.

## 9. Safety Audit

Full safety audit passes and now includes GT26 evidence in `checked_files`:

- `rge/cli.py` (contains `execute_fixture_mode_run`)
- `tests/golden/test_26_full_mvp_run.py`

## 10. Spec Deviations

- Updated `test_00_scaffold.py` because fixture-mode `run` is no longer a placeholder.
- Extended full safety audit with `full_mvp_run` check beyond ticket minimum (mirrors GT24/GT25 pattern).

## 11. Merge to Main

- Merge commit: `5d0c214`
- Branch: `phase-1/ticket-028-full-mvp-run` merged to `main`.
- Post-merge pytest on `main`: 118 passed.
- Post-merge safety audit on `main`: `pass`.

## 12. Recommended Next Ticket

**ticket-029**: Extend builder golden gate coverage for full MVP run (Golden Test 26).

## 13. Suggested Next Prompt

```txt
/rge-run-next-ticket
```
